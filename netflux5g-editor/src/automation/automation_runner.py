import os
import subprocess
import threading
import time
import signal
import yaml
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from export.mininet_export import MininetExporter
from manager.debug import debug_print, error_print, warning_print
from prerequisites.checker import PrerequisitesChecker

class AutomationRunner(QObject):
    """Handler for running automated deployment of Mininet scripts."""
    
    # Signals for status updates
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    execution_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.mininet_exporter = MininetExporter(main_window)
        
        # Process tracking
        self.docker_process = None
        self.mininet_process = None
        self.is_running = False
        self.export_dir = None
        self.mininet_script_path = None
        
        # Connect signals
        self.status_updated.connect(self.main_window.showCanvasStatus)
        
    def run_all(self):
        """Main entry point for RunAll functionality."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "Automation is already running. Please stop it first."
            )
            return
        
        all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
        if not all_ok:
            missing = [tool for tool, ok in checks.items() if not ok]
            instructions = PrerequisitesChecker.get_installation_instructions()
            
            error_msg = f"Missing prerequisites: {', '.join(missing)}\n\n"
            for tool in missing:
                error_msg += f"{tool.upper()}:\n{instructions[tool]}\n"
            
            QMessageBox.critical(
                self.main_window,
                "Missing Prerequisites",
                error_msg
            )
            return

        # Check if we have components to export
        nodes, links = self.main_window.extractTopology()
        core5g_components = [n for n in nodes if n['type'] == 'VGcore']
        
        if not core5g_components and not any(n['type'] in ['GNB', 'UE', 'Host', 'STA'] for n in nodes):
            QMessageBox.information(
                self.main_window,
                "No Components",
                "No 5G components or network elements found to deploy."
            )
            return
            
        # Show progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing deployment...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("NetFlux5G Automation")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self.stop_all)
        self.progress_dialog.show()
        
        # Connect progress signal
        self.progress_updated.connect(self.progress_dialog.setValue)
        
        # Start the automation in a separate thread
        self.automation_thread = threading.Thread(target=self._run_automation_sequence)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
    def _run_automation_sequence(self):
        """Run the complete automation sequence."""
        try:
            self.is_running = True
            
            # Step 0: Check/Create Docker network if needed
            self.status_updated.emit("Checking Docker network...")
            self.progress_updated.emit(5)
            self._ensure_docker_network()
            
            # Step 1: Check prerequisites (MongoDB, WebUI, Ryu Controller)
            self.status_updated.emit("Checking prerequisites...")
            self.progress_updated.emit(10)
            self._check_and_deploy_prerequisites()
            
            # Step 2: Create working directory
            self.status_updated.emit("Creating working directory...")
            self.progress_updated.emit(20)
            self.export_dir = self._create_working_directory()
            
            # Step 3: Copy 5G configuration files
            self.status_updated.emit("Copying 5G configuration files...")
            self.progress_updated.emit(25)
            self._copy_5g_configs()
            
            # Step 4: Generate Mininet script
            self.status_updated.emit("Generating Mininet script...")
            self.progress_updated.emit(30)
            self._generate_mininet_script()
            
            # Step 5: Start Mininet
            self.status_updated.emit("Starting Mininet network...")
            self.progress_updated.emit(90)
            self._start_mininet()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Deployment completed successfully!")
            self.execution_finished.emit(True, "All services started successfully")
            
        except Exception as e:
            error_msg = f"Automation failed: {str(e)}"
            error_print(f"ERROR: {error_msg}")
            self.status_updated.emit(error_msg)
            self.execution_finished.emit(False, error_msg)
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def _create_working_directory(self):
        """Create a working directory for the deployment."""
        from datetime import datetime
        
        # Create a timestamped directory in the mininet folder with proper numbering
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get the base directory (where the main script is located)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Create mininet directory if it doesn't exist
        mininet_dir = os.path.join(base_dir, "mininet")
        os.makedirs(mininet_dir, exist_ok=True)
        
        # Create timestamped export directory
        export_dir = os.path.join(mininet_dir, f"netflux5g_export_{timestamp}")
        os.makedirs(export_dir, exist_ok=True)
        
        debug_print(f"Created working directory: {export_dir}")
        return export_dir
    
    def _check_and_deploy_prerequisites(self):
        """Check and deploy prerequisites: MongoDB, WebUI, Ryu Controller."""
        from PyQt5.QtWidgets import QMessageBox
        
        missing_services = []
        
        # Check MongoDB Database
        if hasattr(self.main_window, 'database_manager'):
            if not self.main_window.database_manager.is_database_running():
                missing_services.append("MongoDB Database")
        else:
            missing_services.append("MongoDB Database (manager not available)")
        
        # Check WebUI (User Manager)  
        if hasattr(self.main_window, 'database_manager'):
            if not self.main_window.database_manager.is_webui_running():
                missing_services.append("WebUI (User Manager)")
        else:
            missing_services.append("WebUI (User Manager)")
            
        # Check Ryu Controller
        if hasattr(self.main_window, 'controller_manager'):
            # For now, assume controller is not running - add proper check later
            missing_services.append("Ryu Controller")
        else:
            missing_services.append("Ryu Controller")
        
        # Check Monitoring Stack (optional)
        monitoring_running = False
        if hasattr(self.main_window, 'monitoring_manager'):
            # For now, assume monitoring is not running - add proper check later
            monitoring_running = False
        
        # If missing services, prompt user to deploy them
        if missing_services:
            self.status_updated.emit("Missing prerequisites detected...")
            
            # Show dialog on main thread using a simple signal
            self.missing_services = missing_services
            self.monitoring_running = monitoring_running
            
            # Use a timer to call the dialog on main thread
            QTimer.singleShot(100, self._show_prerequisites_dialog_delayed)
            
            # Wait for user response
            import time
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while not hasattr(self, '_prerequisites_response') and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                QApplication.processEvents()
            
            if not hasattr(self, '_prerequisites_response'):
                raise Exception("Timeout waiting for prerequisites deployment decision")
                
            if not self._prerequisites_response:
                raise Exception("Prerequisites deployment cancelled by user")
                
            # Deploy missing services
            self._deploy_prerequisites(missing_services)
            
            # Clean up response
            delattr(self, '_prerequisites_response')
    
    def _show_prerequisites_dialog_delayed(self):
        """Show prerequisites dialog on main thread."""
        self._show_prerequisites_dialog(self.missing_services, self.monitoring_running)
    
    def _show_prerequisites_dialog(self, missing_services, monitoring_running):
        """Show prerequisites dialog on main thread."""
        msg = f"The following prerequisites are not running:\n\n"
        msg += "\n".join(f"• {service}" for service in missing_services)
        msg += f"\n\nMonitoring Stack: {'Running' if monitoring_running else 'Not running (optional)'}"
        msg += "\n\nWould you like to deploy the missing prerequisites now?"
        
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Prerequisites",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        self._prerequisites_response = (reply == QMessageBox.Yes)
    
    def _deploy_prerequisites(self, missing_services):
        """Deploy the missing prerequisite services."""
        total_services = len(missing_services)
        progress_increment = 50 // max(total_services, 1)  # Use 50% of progress for prerequisites
        current_progress = 15  # Start from current progress
        
        for service in missing_services:
            self.status_updated.emit(f"Deploying {service}...")
            self.progress_updated.emit(current_progress)
            
            success = False
            if "MongoDB Database" in service and hasattr(self.main_window, 'database_manager'):
                success = self.main_window.database_manager.deploy_database()
            elif "WebUI" in service and hasattr(self.main_window, 'database_manager'):
                success = self.main_window.database_manager.deploy_webui()
            elif "Ryu Controller" in service and hasattr(self.main_window, 'controller_manager'):
                self.main_window.controller_manager.deployController()
                success = True  # Assume success for now - add proper check later
            
            if not success:
                raise Exception(f"Failed to deploy {service}")
                
            current_progress += progress_increment
            self.progress_updated.emit(current_progress)
            
            # Wait a bit for service to start
            time.sleep(2)
    
    def _generate_mininet_script(self):
        """Generate Mininet script."""
        script_name = "netflux5g_topology.py"
        self.mininet_script_path = os.path.join(self.export_dir, script_name)
        self.mininet_exporter.export_to_mininet_script(self.mininet_script_path)
        
        # Verify the script was created
        if not os.path.exists(self.mininet_script_path):
            raise Exception("Mininet script was not generated")
            
        # Make the script executable
        os.chmod(self.mininet_script_path, 0o755)
        debug_print(f"Mininet script generated at: {self.mininet_script_path}")
    
    def _copy_5g_configs(self):
        """Copy 5G configuration files from VGCore components to export directory."""
        import shutil
        
        # Get nodes to check for VGCore components
        nodes, _ = self.main_window.extractTopology()
        core5g_components = [n for n in nodes if n['type'] == 'VGcore']
        
        if not core5g_components:
            debug_print("DEBUG: No VGCore components found, skipping config copy")
            return
        
        # Create 5g-configs directory
        configs_dir = os.path.join(self.export_dir, "5g-configs")
        os.makedirs(configs_dir, exist_ok=True)
        debug_print(f"DEBUG: Created 5g-configs directory: {configs_dir}")
        
        missing_configs = []
        copied_configs = []
        
        for component in core5g_components:
            component_name = component.get('name', 'Unknown')
            properties = component.get('properties', {})
            
            # Check for 5G component table data
            component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
            
            for comp_type in component_types:
                table_key = f'table_data_{comp_type}'
                if table_key in properties:
                    table_data = properties[table_key]
                    
                    if isinstance(table_data, list):
                        for row_idx, row_data in enumerate(table_data):
                            if isinstance(row_data, dict):
                                config_file_path = row_data.get('config_file_path', '')
                                config_content = row_data.get('config_content', '')
                                config_filename = row_data.get('config_filename', f'{comp_type.lower()}_{row_idx + 1}.yaml')
                                
                                if config_file_path and os.path.exists(config_file_path):
                                    # Copy the actual file
                                    try:
                                        dest_filename = f"{component_name}_{comp_type}_{row_idx + 1}_{os.path.basename(config_file_path)}"
                                        dest_path = os.path.join(configs_dir, dest_filename)
                                        shutil.copy2(config_file_path, dest_path)
                                        copied_configs.append(f"{component_name}/{comp_type}: {os.path.basename(config_file_path)}")
                                        debug_print(f"DEBUG: Copied config file: {config_file_path} -> {dest_path}")
                                    except Exception as e:
                                        error_print(f"ERROR: Failed to copy config file {config_file_path}: {e}")
                                        missing_configs.append(f"{component_name}/{comp_type}: {config_file_path} (copy failed)")
                                        
                                elif config_content:
                                    # Write the config content to a file
                                    try:
                                        dest_filename = f"{component_name}_{comp_type}_{row_idx + 1}_{config_filename}"
                                        dest_path = os.path.join(configs_dir, dest_filename)
                                        with open(dest_path, 'w') as f:
                                            f.write(config_content)
                                        copied_configs.append(f"{component_name}/{comp_type}: {config_filename} (from imported content)")
                                        debug_print(f"DEBUG: Wrote config content to: {dest_path}")
                                    except Exception as e:
                                        error_print(f"ERROR: Failed to write config content: {e}")
                                        missing_configs.append(f"{component_name}/{comp_type}: {config_filename} (write failed)")
                                        
                                else:
                                    # No configuration provided
                                    missing_configs.append(f"{component_name}/{comp_type} (row {row_idx + 1}): No configuration provided")
        
        # Report results
        if copied_configs:
            self.status_updated.emit(f"Copied {len(copied_configs)} 5G configuration files")
            debug_print(f"DEBUG: Successfully copied configs: {copied_configs}")
        
        if missing_configs:
            error_msg = f"Missing or invalid 5G configurations detected:\n\n"
            error_msg += "\n".join(f"• {config}" for config in missing_configs[:10])  # Show first 10
            if len(missing_configs) > 10:
                error_msg += f"\n... and {len(missing_configs) - 10} more"
            
            error_msg += "\n\nPlease ensure all VGCore components have valid configuration files imported in their properties."
            
            raise Exception(f"Missing 5G configurations: {len(missing_configs)} components need configuration files")
    
    def _start_mininet(self):
        """Start Mininet in a new terminal."""
        if not self.mininet_script_path:
            raise Exception("Mininet script path not set")
        
        # Check if mininet is available
        try:
            subprocess.run(["mn", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Mininet is not installed or not accessible")
        
        # Create a script to run Mininet in a new terminal
        terminal_script = os.path.join(self.export_dir, "run_mininet.sh")
        with open(terminal_script, 'w') as f:
            f.write(f"""#!/bin/bash
echo "Starting Mininet topology..."
echo "Working directory: {self.export_dir}"
cd "{self.export_dir}"
sudo python3 "{self.mininet_script_path}"
echo "Mininet session ended. Press Enter to close..."
read
""")
        
        os.chmod(terminal_script, 0o755)
        
        # Launch in a new terminal window
        try:
            # Try different terminal emulators
            terminal_commands = [
                ["gnome-terminal", "--", "bash", terminal_script],
                ["xterm", "-e", f"bash {terminal_script}"],
                ["konsole", "-e", f"bash {terminal_script}"],
                ["lxterminal", "-e", f"bash {terminal_script}"]
            ]
            
            launched = False
            for cmd in terminal_commands:
                try:
                    self.mininet_process = subprocess.Popen(cmd)
                    launched = True
                    debug_print(f"Mininet launched with: {' '.join(cmd)}")
                    break
                except FileNotFoundError:
                    continue
            
            if not launched:
                # Fallback: run in background and log to file
                log_file = os.path.join(self.export_dir, "mininet.log")
                self.mininet_process = subprocess.Popen(
                    ["sudo", "python3", self.mininet_script_path],
                    cwd=self.export_dir,
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT
                )
                debug_print(f"Mininet started in background, logging to: {log_file}")
        
        except Exception as e:
            raise Exception(f"Failed to start Mininet: {str(e)}")
    
    def stop_all(self):
        """Stop all running processes."""
        if not self.is_running:
            return
            
        self.status_updated.emit("Stopping all services...")
        
        try:
            # Stop Mininet
            if self.mininet_process and self.mininet_process.poll() is None:
                debug_print("Stopping Mininet...")
                try:
                    # Try graceful shutdown first
                    self.mininet_process.terminate()
                    self.mininet_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    self.mininet_process.kill()
                    
                # Clean up Mininet
                try:
                    subprocess.run(["sudo", "mn", "-c"], capture_output=True)
                except:
                    pass
            
            
        except Exception as e:
            error_print(f"Error stopping services: {e}")
            self.status_updated.emit(f"Error stopping services: {e}")
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def is_deployment_running(self):
        """Check if deployment is currently running."""
        return self.is_running
    
    def get_deployment_info(self):
        """Get information about the current deployment."""
        if not self.export_dir:
            return None
            
        return {
            'export_dir': self.export_dir,
            'mininet_script': self.mininet_script_path,
            'is_running': self.is_running
        }
    
    def _ensure_docker_network(self):
        """Ensure that the universal 'netflux5g' Docker network exists for all deployments."""
        if not hasattr(self.main_window, 'docker_network_manager'):
            warning_print("Docker network manager not available")
            return
        
        # Always use the universal netflux5g network
        network_name = "netflux5g"
        
        # Check if network exists, create if needed
        if not self.main_window.docker_network_manager._network_exists(network_name):
            debug_print(f"Universal Docker network '{network_name}' does not exist, creating...")
            success = self.main_window.docker_network_manager._create_network(network_name)
            if success:
                debug_print(f"Universal Docker network '{network_name}' created successfully")
            else:
                warning_print(f"Failed to create universal Docker network '{network_name}'")
                raise Exception(f"Failed to create required Docker network '{network_name}'")
        else:
            debug_print(f"Universal Docker network '{network_name}' already exists")
    
    def run_topology_only(self):
        """Run only the topology export and Mininet execution (actionRun)."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "Automation is already running. Please stop it first."
            )
            return
        
        # Check if we have components to export
        nodes, links = self.main_window.extractTopology()
        
        if not nodes:
            QMessageBox.information(
                self.main_window,
                "No Components",
                "No network components found to export and run."
            )
            return
            
        # Show progress dialog
        self.progress_dialog = QProgressDialog(
            "Exporting and running topology...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("NetFlux5G Topology Runner")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self.stop_all)
        self.progress_dialog.show()
        
        # Connect progress signal
        self.progress_updated.connect(self.progress_dialog.setValue)
        
        # Start the simple automation in a separate thread
        self.automation_thread = threading.Thread(target=self._run_topology_sequence)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
    def _run_topology_sequence(self):
        """Run the simple topology export and execution sequence."""
        try:
            self.is_running = True
            
            # Step 1: Create working directory
            self.status_updated.emit("Creating working directory...")
            self.progress_updated.emit(20)
            self.export_dir = self._create_working_directory()
            
            # Step 2: Copy 5G configuration files (if any VGCore components exist)
            self.status_updated.emit("Copying 5G configuration files...")
            self.progress_updated.emit(30)
            try:
                self._copy_5g_configs()
            except Exception as e:
                # For simple topology run, only warn about missing configs, don't fail
                warning_print(f"WARNING: 5G config copy failed: {e}")
                self.status_updated.emit("Warning: Some 5G configurations may be missing")
            
            # Step 3: Generate Mininet script
            self.status_updated.emit("Generating Mininet script...")
            self.progress_updated.emit(60)
            self._generate_mininet_script()
            
            # Step 4: Start Mininet
            self.status_updated.emit("Starting Mininet network...")
            self.progress_updated.emit(90)
            self._start_mininet()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Topology exported and started successfully!")
            self.execution_finished.emit(True, "Mininet topology started successfully")
            
        except Exception as e:
            error_msg = f"Topology run failed: {str(e)}"
            error_print(f"ERROR: {error_msg}")
            self.status_updated.emit(error_msg)
            self.execution_finished.emit(False, error_msg)
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()