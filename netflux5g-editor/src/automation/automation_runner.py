import os
import subprocess
import threading
import time
import signal
import yaml
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from export.compose_export import DockerComposeExporter
from export.mininet_export import MininetExporter
from manager.debug import debug_print, error_print, warning_print
from prerequisites.checker import PrerequisitesChecker

class AutomationRunner(QObject):
    """Handler for running automated deployment of Docker Compose and Mininet scripts."""
    
    # Signals for status updates
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    execution_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.docker_compose_exporter = DockerComposeExporter(main_window)
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
            
            # Step 1: Create working directory
            self.status_updated.emit("Creating working directory...")
            self.progress_updated.emit(10)
            self.export_dir = self._create_working_directory()
            
            # Step 2: Generate Docker Compose
            self.status_updated.emit("Generating Docker Compose configuration...")
            self.progress_updated.emit(25)
            self._generate_docker_compose()
            
            # Step 3: Generate Mininet script
            self.status_updated.emit("Generating Mininet script...")
            self.progress_updated.emit(40)
            self._generate_mininet_script()
            
            # Step 4: Start Docker Compose
            self.status_updated.emit("Starting Docker Compose services...")
            self.progress_updated.emit(60)
            self._start_docker_compose()
            
            # Step 5: Wait for services to be ready
            self.status_updated.emit("Waiting for services to initialize...")
            self.progress_updated.emit(75)
            self._wait_for_services()
            
            # Step 6: Start Mininet
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
        import tempfile
        from datetime import datetime
        
        # Create a timestamped directory in the project root or temp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        export_dir = os.path.join(base_dir, "..", "export", "started", f"netflux5g_deploy_{timestamp}")
        
        os.makedirs(export_dir, exist_ok=True)
        debug_print(f"Created working directory: {export_dir}")
        return export_dir
    
    def _generate_docker_compose(self):
        """Generate Docker Compose files."""
        self.docker_compose_exporter.export_docker_compose_files(self.export_dir)
        
        # Verify the docker-compose.yaml was created
        compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
        if not os.path.exists(compose_file):
            raise Exception("Docker Compose file was not generated")
            
        debug_print(f"Docker Compose generated at: {compose_file}")
    
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
    
    def _start_docker_compose(self):
        """Start Docker Compose services."""
        compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
        
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Docker is not installed or not accessible")
        
        # Check if docker-compose is available
        try:
            subprocess.run(["docker-compose", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try docker compose (newer syntax)
            try:
                subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise Exception("Docker Compose is not installed or not accessible")
        
        # Start Docker Compose services
        cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
        debug_print(f"Starting Docker Compose with command: {' '.join(cmd)}")
        
        self.docker_process = subprocess.Popen(
            cmd,
            cwd=self.export_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the process to complete
        stdout, stderr = self.docker_process.communicate()
        
        if self.docker_process.returncode != 0:
            raise Exception(f"Docker Compose failed: {stderr}")
            
        debug_print(f"Docker Compose started successfully: {stdout}")
    
    def _wait_for_services(self):
        """Wait for Docker services to be ready."""
        # Simple wait - in a real implementation, you might want to check service health
        time.sleep(10)
        
        # Check if services are running
        try:
            result = subprocess.run(
                ["docker-compose", "-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
                capture_output=True,
                text=True,
                cwd=self.export_dir
            )
            debug_print(f"Docker services status: {result.stdout}")
        except Exception as e:
            warning_print(f"Could not check service status: {e}")
    
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
            
            # Stop Docker Compose
            if self.export_dir:
                compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
                if os.path.exists(compose_file):
                    debug_print("Stopping Docker Compose...")
                    subprocess.run(
                        ["docker-compose", "-f", compose_file, "down"],
                        cwd=self.export_dir,
                        capture_output=True
                    )
            
            self.status_updated.emit("All services stopped")
            
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
            'docker_compose_file': os.path.join(self.export_dir, "docker-compose.yaml"),
            'mininet_script': self.mininet_script_path,
            'is_running': self.is_running
        }