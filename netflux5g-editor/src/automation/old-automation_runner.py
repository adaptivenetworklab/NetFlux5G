import os
import subprocess
import threading
import time
import signal
import yaml
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot, Qt
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
        
        # Connect signals - ensure they're connected on the main thread
        if hasattr(self.main_window, 'status_manager'):
            self.status_updated.connect(self.main_window.status_manager.showCanvasStatus, Qt.QueuedConnection)
        else:
            # Fallback to main window method
            self.status_updated.connect(self.main_window.showCanvasStatus, Qt.QueuedConnection)
        
    def run_all(self, controller_type=None):
        """Main entry point for RunAll functionality."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "Automation is already running. Please stop it first."
            )
            return
        
        # Store controller type for this run
        self.controller_type = controller_type or getattr(self.main_window, 'selected_controller_type', 'ryu')
        
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

        # Connect progress updates to dialog
        self.progress_updated.connect(self.progress_dialog.setValue, Qt.QueuedConnection)
        
        # Run the automation sequence on the main thread
        # Use QTimer to run it asynchronously on the main thread
        QTimer.singleShot(100, lambda: self._run_automation_sequence_main_thread(self.controller_type))

    def _run_automation_sequence_main_thread(self, controller_type):
        """Run the complete automation sequence on the main thread to avoid Qt threading issues."""
        try:
            self.is_running = True
            
            # Step 0: Check/Create Docker network if needed
            self.status_updated.emit("Checking Docker network...")
            self.progress_updated.emit(5)
            self._ensure_docker_network()
            
            # Step 1: Check prerequisites (MongoDB, WebUI, Controller) - ON MAIN THREAD
            self.status_updated.emit("Checking prerequisites...")
            self.progress_updated.emit(10)
            self._check_and_deploy_prerequisites(controller_type=controller_type)
            
            # Step 2: Create working directory
            self.status_updated.emit("Creating working directory...")
            self.progress_updated.emit(20)
            self.export_dir = self._create_working_directory()
            
            # Step 3: Copy 5G configuration files
            self.status_updated.emit("Copying 5G configuration files...")
            self.progress_updated.emit(25)
            copied_count, missing_count = self._copy_5g_configs()
            if copied_count > 0:
                self.status_updated.emit(f"Copied {copied_count} 5G configuration files")
            if missing_count > 0:
                warning_print(f"WARNING: {missing_count} configuration files could not be copied")
            
            # Step 4: Generate Mininet script
            self.status_updated.emit("Generating Mininet script...")
            self.progress_updated.emit(30)
            self._generate_mininet_script()
            
            # Step 5: Start Mininet (use background thread for this)
            self.status_updated.emit("Starting Mininet network...")
            self.progress_updated.emit(90)
            self._start_mininet_background()
            
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
                self.progress_dialog = None
    
    def _create_working_directory(self):
        """Create a working directory for the deployment."""
        from datetime import datetime
        
        # Create a timestamped directory in the mininet folder with proper numbering
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get the base directory (where the main script is located)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Create mininet directory if it doesn't exist
        mininet_dir = os.path.join(base_dir, "export","mininet")
        os.makedirs(mininet_dir, exist_ok=True)
        
        # Create timestamped export directory
        export_dir = os.path.join(mininet_dir, f"netflux5g_export_{timestamp}")
        os.makedirs(export_dir, exist_ok=True)
        
        debug_print(f"Created working directory: {export_dir}")
        return export_dir
    
    def _check_and_deploy_prerequisites(self, controller_type=None):
        """Check and deploy prerequisites: MongoDB, WebUI, Controller (dynamic) - Main thread only."""
        from PyQt5.QtWidgets import QMessageBox
        
        # Step 1: Check Controller - Deploy if needed
        self.status_updated.emit("Checking controller...")
        if not self._check_controller_running(controller_type):
            reply = QMessageBox.question(
                self.main_window,
                "Deploy Controller",
                f"The {controller_type.upper()} controller is not running. Deploy it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._deploy_controller(controller_type)
            else:
                raise Exception("Controller deployment cancelled by user")
        else:
            self.status_updated.emit(f"{controller_type.upper()} controller is already running")
        
        # Step 2: Check Database - Deploy if needed
        self.status_updated.emit("Checking database...")
        if not self._check_database_running():
            reply = QMessageBox.question(
                self.main_window,
                "Deploy Database",
                "MongoDB database is not running. Deploy it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._deploy_database()
            else:
                raise Exception("Database deployment cancelled by user")
        else:
            self.status_updated.emit("MongoDB database is already running")
        
        # Step 3: Check User Manager - Deploy if needed
        self.status_updated.emit("Checking user manager...")
        if not self._check_user_manager_running():
            reply = QMessageBox.question(
                self.main_window,
                "Deploy User Manager",
                "User Manager (WebUI) is not running. Deploy it now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._deploy_user_manager()
            else:
                raise Exception("User Manager deployment cancelled by user")
        else:
            self.status_updated.emit("User Manager is already running")
        
        # Step 4: Check Monitoring (optional)
        self.status_updated.emit("Checking monitoring stack...")
        if not self._check_monitoring_running():
            reply = QMessageBox.question(
                self.main_window,
                "Deploy Monitoring",
                "Monitoring stack is not running. Deploy it now?\n\n(This is optional and can be skipped)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._deploy_monitoring()
        else:
            self.status_updated.emit("Monitoring stack is already running")
        
        self.status_updated.emit("All prerequisites are ready")
    
    def _check_controller_running(self, controller_type=None):
        """Check if the specified controller is running."""
        if not hasattr(self.main_window, 'controller_manager'):
            return False
            
        if controller_type == 'onos':
            return self.main_window.controller_manager.is_onos_controller_running()
        else:
            return self.main_window.controller_manager.is_controller_running()
    
    def _deploy_controller(self, controller_type=None):
        """Deploy the specified controller."""
        if not hasattr(self.main_window, 'controller_manager'):
            raise Exception("Controller manager not available")
            
        self.status_updated.emit(f"Deploying {controller_type.upper()} controller...")
        
        success = self.main_window.controller_manager.deploy_controller_sync(controller_type)
        if not success:
            raise Exception(f"Failed to deploy {controller_type.upper()} controller")
        
        # Wait a moment for deployment
        time.sleep(3)
        
        # Verify deployment
        if not self._check_controller_running(controller_type):
            raise Exception(f"Failed to deploy {controller_type.upper()} controller")
        
        self.status_updated.emit(f"{controller_type.upper()} controller deployed successfully")
    
    def _check_database_running(self):
        """Check if MongoDB database is running."""
        if not hasattr(self.main_window, 'database_manager'):
            return False
        return self.main_window.database_manager.is_database_running()
    
    def _deploy_database(self):
        """Deploy MongoDB database."""
        if not hasattr(self.main_window, 'database_manager'):
            raise Exception("Database manager not available")
            
        self.status_updated.emit("Deploying MongoDB database...")
        
        success = self.main_window.database_manager.deploy_database_sync()
        if not success:
            raise Exception("Failed to deploy MongoDB database")
        
        # Wait a moment for deployment
        time.sleep(3)
        
        # Verify deployment
        if not self._check_database_running():
            raise Exception("Database deployment failed - not running after deployment")
        
        self.status_updated.emit("MongoDB database deployed successfully")
    
    def _check_user_manager_running(self):
        """Check if User Manager (WebUI) is running."""
        if not hasattr(self.main_window, 'database_manager'):
            return False
        return self.main_window.database_manager.is_webui_running()
    
    def _deploy_user_manager(self):
        """Deploy User Manager (WebUI)."""
        if not hasattr(self.main_window, 'database_manager'):
            raise Exception("Database manager not available")
            
        self.status_updated.emit("Deploying User Manager (WebUI)...")
        
        success = self.main_window.database_manager.deploy_webui_sync()
        if not success:
            raise Exception("Failed to deploy User Manager")
        
        # Wait a moment for deployment
        time.sleep(3)
        
        # Verify deployment
        if not self._check_user_manager_running():
            raise Exception("User Manager deployment failed - not running after deployment")
        
        self.status_updated.emit("User Manager deployed successfully")
    
    def _check_monitoring_running(self):
        """Check if monitoring stack is running."""
        if not hasattr(self.main_window, 'monitoring_manager'):
            return False
        if hasattr(self.main_window.monitoring_manager, 'is_monitoring_running'):
            return self.main_window.monitoring_manager.is_monitoring_running()
        return False
    
    def _deploy_monitoring(self):
        """Deploy monitoring stack."""
        if not hasattr(self.main_window, 'monitoring_manager'):
            raise Exception("Monitoring manager not available")
            
        self.status_updated.emit("Deploying monitoring stack...")
        
        try:
            # Use synchronous deployment for automation
            if hasattr(self.main_window.monitoring_manager, 'deploy_monitoring_sync'):
                success, message = self.main_window.monitoring_manager.deploy_monitoring_sync()
                if success:
                    self.status_updated.emit("Monitoring stack deployed successfully")
                    debug_print(f"Monitoring deployment successful: {message}")
                else:
                    warning_print(f"WARNING: Failed to deploy monitoring stack: {message}")
                    self.status_updated.emit("Monitoring stack deployment failed (continuing anyway)")
            else:
                # Fallback to async method
                self.main_window.monitoring_manager.deploy_monitoring()
                # Wait a moment for deployment
                time.sleep(3)
                self.status_updated.emit("Monitoring stack deployed successfully")
        except Exception as e:
            warning_print(f"WARNING: Failed to deploy monitoring stack: {str(e)}")
            self.status_updated.emit("Monitoring stack deployment failed (continuing anyway)")
    
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
    
    def _debug_component_properties(self, component):
        """Debug utility to show detailed component properties structure."""
        component_name = component.get('name', 'Unknown')
        properties = component.get('properties', {})
        
        debug_print(f"DEBUG: === Component '{component_name}' Properties Debug ===")
        debug_print(f"DEBUG: Total properties: {len(properties)}")
        
        # Show all property keys
        config_keys = [key for key in properties.keys() if 'config' in key.lower()]
        table_keys = [key for key in properties.keys() if 'table' in key.lower()]
        
        debug_print(f"DEBUG: Config-related keys: {config_keys}")
        debug_print(f"DEBUG: Table-related keys: {table_keys}")
        
        # Show the specific patterns we're looking for
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        for comp_type in component_types:
            expected_key = f'{comp_type}_configs'
            if expected_key in properties:
                data = properties[expected_key]
                debug_print(f"DEBUG: Found {expected_key}: {type(data)} with {len(data) if isinstance(data, list) else 'non-list'} items")
                if isinstance(data, list) and data:
                    debug_print(f"DEBUG: First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
        debug_print(f"DEBUG: === End Component '{component_name}' Debug ===")
    
    def _copy_5g_configs(self):
        """Copy 5G configuration files from VGCore components to export directory."""
        import shutil
        import os
        
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
            debug_print(f"DEBUG: Processing VGCore component '{component_name}' with {len(properties)} properties")
            
            # Debug component properties structure
            self._debug_component_properties(component)
            
            # Check for 5G component configurations using the correct key format
            component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
            
            for comp_type in component_types:
                # Use the correct key format: {comp_type}_configs
                config_key = f'{comp_type}_configs'
                
                if config_key in properties:
                    config_data = properties[config_key]
                    debug_print(f"DEBUG: Found {config_key} with {len(config_data) if isinstance(config_data, list) else 'non-list'} items")
                    
                    if isinstance(config_data, list):
                        for i, config_item in enumerate(config_data):
                            if not isinstance(config_item, dict):
                                continue
                                
                            # Get the configuration name
                            config_name = config_item.get('name', f"{comp_type.lower()}{i + 1}")
                            
                            # Try to get the config file path from multiple possible sources
                            config_file_path = None
                            config_content = None
                            
                            # Method 1: Direct file path stored in config_file_path
                            if 'config_file_path' in config_item and config_item['config_file_path']:
                                config_file_path = config_item['config_file_path']
                                debug_print(f"DEBUG: Found config_file_path: {config_file_path}")
                            
                            # Method 2: Path stored in config_path column
                            elif 'config_path' in config_item and config_item['config_path']:
                                config_file_path = config_item['config_path']
                                debug_print(f"DEBUG: Found config_path: {config_file_path}")
                            
                            # Method 3: Check if config content is embedded
                            if 'config_content' in config_item and config_item['config_content']:
                                config_content = config_item['config_content']
                                debug_print(f"DEBUG: Found embedded config content for {config_name}")
                            
                            # Process the configuration
                            if config_file_path and os.path.isfile(config_file_path):
                                # Copy the actual file with simplified naming
                                try:
                                    # Use simplified naming: {comp_type.lower()}.yaml or {comp_type.lower()}_{index}.yaml
                                    if i == 0:  # First instance gets simple name
                                        dest_filename = f"{comp_type.lower()}.yaml"
                                    else:  # Additional instances get numbered
                                        dest_filename = f"{comp_type.lower()}_{i+1}.yaml"
                                    
                                    dest_path = os.path.join(configs_dir, dest_filename)
                                    shutil.copy2(config_file_path, dest_path)
                                    copied_configs.append({
                                        'component': comp_type,
                                        'name': config_name,
                                        'source': config_file_path,
                                        'destination': dest_path,
                                        'filename': dest_filename
                                    })
                                    debug_print(f"DEBUG: Copied {config_file_path} to {dest_path}")
                                except Exception as e:
                                    error_msg = f"Failed to copy {config_file_path}: {str(e)}"
                                    debug_print(f"DEBUG: {error_msg}")
                                    missing_configs.append({
                                        'component': comp_type,
                                        'name': config_name,
                                        'path': config_file_path,
                                        'error': error_msg
                                    })
                            
                            elif config_content:
                                # Save embedded content to file with simplified naming
                                try:
                                    # Use simplified naming: {comp_type.lower()}.yaml or {comp_type.lower()}_{index}.yaml
                                    if i == 0:  # First instance gets simple name
                                        dest_filename = f"{comp_type.lower()}.yaml"
                                    else:  # Additional instances get numbered
                                        dest_filename = f"{comp_type.lower()}_{i+1}.yaml"
                                    
                                    dest_path = os.path.join(configs_dir, dest_filename)
                                    
                                    # Save the content to file
                                    if isinstance(config_content, str):
                                        with open(dest_path, 'w', encoding='utf-8') as f:
                                            f.write(config_content)
                                    else:
                                        # Assume it's structured data that needs YAML formatting
                                        import yaml
                                        with open(dest_path, 'w', encoding='utf-8') as f:
                                            yaml.dump(config_content, f, default_flow_style=False)
                                    
                                    copied_configs.append({
                                        'component': comp_type,
                                        'name': config_name,
                                        'source': 'embedded_content',
                                        'destination': dest_path,
                                        'filename': dest_filename
                                    })
                                    debug_print(f"DEBUG: Saved embedded config content to {dest_path}")
                                except Exception as e:
                                    error_msg = f"Failed to save embedded config for {config_name}: {str(e)}"
                                    debug_print(f"DEBUG: {error_msg}")
                                    missing_configs.append({
                                        'component': comp_type,
                                        'name': config_name,
                                        'path': 'embedded_content',
                                        'error': error_msg
                                    })
                            
                            else:
                                # No configuration found
                                missing_configs.append({
                                    'component': comp_type,
                                    'name': config_name,
                                    'path': 'not_specified',
                                    'error': 'No configuration file path or content specified'
                                })
                                debug_print(f"DEBUG: No config found for {comp_type} component '{config_name}'")
                else:
                    debug_print(f"DEBUG: Key {config_key} not found in properties")
        
        # Report results
        if copied_configs:
            debug_print(f"DEBUG: Successfully copied {len(copied_configs)} configuration files:")
            for config in copied_configs:
                debug_print(f"  - {config['component']} '{config['name']}': {config['source']} -> {config['filename']}")
        
        if missing_configs:
            debug_print(f"DEBUG: {len(missing_configs)} configuration files could not be copied:")
            for config in missing_configs:
                debug_print(f"  - {config['component']} '{config['name']}': {config['error']}")
        
        return len(copied_configs), len(missing_configs)

    def _start_mininet(self):
        """Start Mininet in a new terminal."""
        if not self.mininet_script_path:
            raise Exception("Mininet script path not set")
        
        # Check if mininet is available
        try:
            subprocess.run(["sudo", "mn", "--version"], capture_output=True, check=True)
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
    
    def _start_mininet_background(self):
        """Start Mininet in a background thread to avoid blocking the UI."""
        def run_mininet():
            try:
                self._start_mininet()
            except Exception as e:
                error_msg = f"Failed to start Mininet: {str(e)}"
                error_print(f"ERROR: {error_msg}")
                self.status_updated.emit(error_msg)
        
        # Start Mininet in a background thread
        mininet_thread = threading.Thread(target=run_mininet)
        mininet_thread.daemon = True
        mininet_thread.start()
    
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
                    debug_print("Mininet process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    debug_print("Mininet process did not terminate gracefully, force killing...")
                    self.mininet_process.kill()
                    debug_print("Mininet process killed")
                    
                self.mininet_process = None
                
            # Clean up Mininet with sudo mn -c
            debug_print("Executing 'sudo mn -c' to clean Mininet...")
            self.status_updated.emit("Executing 'sudo mn -c' to clean Mininet...")
            
            try:
                result = subprocess.run(
                    ["sudo", "mn", "-c"], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                if result.returncode == 0:
                    debug_print("Mininet cleanup successful")
                    self.status_updated.emit("Mininet cleanup completed successfully")
                else:
                    warning_print(f"Mininet cleanup warning: {result.stderr}")
                    self.status_updated.emit("Mininet cleanup completed with warnings")
                    
            except subprocess.TimeoutExpired:
                error_print("Mininet cleanup timed out")
                self.status_updated.emit("Mininet cleanup timed out")
            except subprocess.CalledProcessError as e:
                error_print(f"Mininet cleanup failed: {e}")
                self.status_updated.emit(f"Mininet cleanup failed: {e}")
            except Exception as e:
                error_print(f"Unexpected error during Mininet cleanup: {e}")
                self.status_updated.emit(f"Cleanup error: {e}")
            
            # Stop Docker containers if they exist
            if self.docker_process and self.docker_process.poll() is None:
                debug_print("Stopping Docker containers...")
                try:
                    self.docker_process.terminate()
                    self.docker_process.wait(timeout=10)
                    debug_print("Docker process terminated gracefully")
                except subprocess.TimeoutExpired:
                    debug_print("Docker process did not terminate gracefully, force killing...")
                    self.docker_process.kill()
                    debug_print("Docker process killed")
                    
                self.docker_process = None
            
            # Stop monitoring stack if it was deployed
            try:
                if hasattr(self.main_window, 'monitoring_manager') and hasattr(self.main_window.monitoring_manager, 'stop_monitoring_sync'):
                    debug_print("Stopping monitoring stack...")
                    self.status_updated.emit("Stopping monitoring stack...")
                    success, message = self.main_window.monitoring_manager.stop_monitoring_sync()
                    if success:
                        debug_print(f"Monitoring stack stopped: {message}")
                        self.status_updated.emit("Monitoring stack stopped")
                    else:
                        warning_print(f"Failed to stop monitoring stack: {message}")
                        self.status_updated.emit("Failed to stop monitoring stack (continuing)")
            except Exception as e:
                warning_print(f"Error stopping monitoring stack: {e}")
                self.status_updated.emit(f"Error stopping monitoring stack: {e}")
            
            # Additional cleanup for any leftover processes
            try:
                # Clean up any remaining Open vSwitch processes
                debug_print("Cleaning up Open vSwitch processes...")
                subprocess.run(["sudo", "ovs-vsctl", "del-br", "ovs-br"], capture_output=True)
                
                # Clean up any remaining network namespaces
                debug_print("Cleaning up network namespaces...")
                subprocess.run(["sudo", "ip", "netns", "del", "mn-ns"], capture_output=True)
                
            except Exception as e:
                # These are optional cleanup steps, don't fail if they don't work
                debug_print(f"Optional cleanup step failed (this is normal): {e}")
            
        except Exception as e:
            error_print(f"Error stopping services: {e}")
            self.status_updated.emit(f"Error stopping services: {e}")
        finally:
            self.is_running = False
            # Close progress dialog on main thread
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                QTimer.singleShot(0, self.progress_dialog.close)
                self.progress_dialog = None
            
            debug_print("All services stopped")
            self.execution_finished.emit(True, "All services stopped successfully")
    
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

        # Connect progress updates to dialog
        self.progress_updated.connect(self.progress_dialog.setValue, Qt.QueuedConnection)
        
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
                copied_count, missing_count = self._copy_5g_configs()
                if copied_count > 0:
                    self.status_updated.emit(f"Copied {copied_count} 5G configuration files")
                if missing_count > 0:
                    warning_print(f"WARNING: {missing_count} configuration files could not be copied")
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
            # Close progress dialog on main thread
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                QTimer.singleShot(0, self.progress_dialog.close)
                self.progress_dialog = None
    
    def stop_topology(self):
        """Stop and clean up the topology (actionStop) - focused on mininet cleanup."""
        debug_print("DEBUG: Stop topology called")
        self.status_updated.emit("Cleaning up topology...")
        try:
            # Stop Mininet process if it's running
            if self.mininet_process and self.mininet_process.poll() is None:
                debug_print("Stopping Mininet process...")
                try:
                    # Try graceful shutdown first
                    self.mininet_process.terminate()
                    self.mininet_process.wait(timeout=10)
                    debug_print("Mininet process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    debug_print("Mininet process did not terminate gracefully, force killing...")
                    self.mininet_process.kill()
                    debug_print("Mininet process killed")
                except Exception as e:
                    error_print(f"Error stopping Mininet process: {e}")
                    
                self.mininet_process = None
            
            # Clean up Mininet with sudo mn -c
            debug_print("Executing 'sudo mn -c' to clean Mininet...")
            self.status_updated.emit("Executing 'sudo mn -c' to clean Mininet...")
            
            try:
                result = subprocess.run(
                    ["sudo", "mn", "-c"], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                if result.returncode == 0:
                    debug_print("Mininet cleanup successful")
                    self.status_updated.emit("Mininet cleanup completed successfully")
                else:
                    warning_print(f"Mininet cleanup warning: {result.stderr}")
                    self.status_updated.emit("Mininet cleanup completed with warnings")
                    
            except subprocess.TimeoutExpired:
                error_print("Mininet cleanup timed out")
                self.status_updated.emit("Mininet cleanup timed out")
            except subprocess.CalledProcessError as e:
                error_print(f"Mininet cleanup failed: {e}")
                self.status_updated.emit(f"Mininet cleanup failed: {e}")
            except Exception as e:
                error_print(f"Unexpected error during Mininet cleanup: {e}")
                self.status_updated.emit(f"Cleanup error: {e}")
            
            # Additional cleanup for any leftover processes
            try:
                # Clean up any remaining Open vSwitch processes
                debug_print("Cleaning up Open vSwitch processes...")
                subprocess.run(["sudo", "ovs-vsctl", "del-br", "ovs-br"], capture_output=True)
                
                # Clean up any remaining network namespaces
                debug_print("Cleaning up network namespaces...")
                subprocess.run(["sudo", "ip", "netns", "del", "mn-ns"], capture_output=True)
                
            except Exception as e:
                # These are optional cleanup steps, don't fail if they don't work
                debug_print(f"Optional cleanup step failed (this is normal): {e}")
            
        except Exception as e:
            error_print(f"Error during topology cleanup: {e}")
            self.status_updated.emit(f"Cleanup error: {e}")
        finally:
            self.is_running = False
            # Close progress dialog on main thread
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                QTimer.singleShot(0, self.progress_dialog.close)
                self.progress_dialog = None
            debug_print("Topology cleanup completed")
            self.execution_finished.emit(True, "Topology cleanup completed")