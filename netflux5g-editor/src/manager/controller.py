"""
Ryu SDN Controller deployment manager for NetFlux5G Editor
Handles Ryu controller container creation and removal with automatic image building
"""

import os
import subprocess
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from manager.debug import debug_print, error_print, warning_print

class ControllerDeploymentWorker(QThread):
    """Worker thread for controller operations to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation, container_name, network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy' or 'stop'
        self.container_name = container_name
        # Use netflux5g network for service deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        """Execute the controller operation in background thread."""
        try:
            if self.operation == 'deploy':
                self._deploy_controller()
            elif self.operation == 'stop':
                self._stop_controller()
        except Exception as e:
            error_print(f"Controller operation failed: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _deploy_controller(self):
        """Deploy Ryu controller container."""
        try:
            self.status_updated.emit("Checking if container already exists...")
            self.progress_updated.emit(10)
            
            # Check if container already exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name in result.stdout:
                # Container exists, check if it's running
                status_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
                status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
                
                if self.container_name in status_result.stdout:
                    self.operation_finished.emit(True, f"Ryu controller '{self.container_name}' is already running")
                    return
                else:
                    # Container exists but not running, start it
                    self.status_updated.emit("Starting existing container...")
                    self.progress_updated.emit(50)
                    start_cmd = ['docker', 'start', self.container_name]
                    subprocess.run(start_cmd, check=True, timeout=30)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"Ryu controller '{self.container_name}' started successfully")
                    return
            
            # Check if the Ryu image exists
            self.status_updated.emit("Checking Ryu controller image...")
            self.progress_updated.emit(20)
            
            image_check_cmd = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}', 'adaptive/ryu:1.0']
            image_result = subprocess.run(image_check_cmd, capture_output=True, text=True, timeout=10)
            
            if 'adaptive/ryu:1.0' not in image_result.stdout:
                # Image doesn't exist, build it
                self.status_updated.emit("Building Ryu controller image...")
                self.progress_updated.emit(30)
                
                # Find the controller Dockerfile path
                controller_dir = self._find_controller_dockerfile()
                if not controller_dir:
                    raise Exception("Controller Dockerfile not found in expected locations")
                
                # Build the image
                build_cmd = ['docker', 'build', '-t', 'adaptive/ryu:1.0', controller_dir]
                build_process = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
                
                if build_process.returncode != 0:
                    raise Exception(f"Failed to build Ryu image: {build_process.stderr}")
                
                debug_print("Successfully built adaptive/ryu:1.0 image")
                self.progress_updated.emit(60)
            else:
                debug_print("Ryu image adaptive/ryu:1.0 already exists")
                self.progress_updated.emit(60)
            
            # Check if netflux5g network exists
            self.status_updated.emit("Checking network...")
            self.progress_updated.emit(70)
            
            network_check_cmd = ['docker', 'network', 'ls', '--filter', f'name={self.network_name}', '--format', '{{.Name}}']
            network_result = subprocess.run(network_check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.network_name not in network_result.stdout:
                # Create network if it doesn't exist
                network_create_cmd = ['docker', 'network', 'create', self.network_name]
                subprocess.run(network_create_cmd, check=True, timeout=10)
                debug_print(f"Created network: {self.network_name}")
            
            # Create and run Ryu controller container
            self.status_updated.emit("Creating Ryu controller container...")
            self.progress_updated.emit(80)
            
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', self.container_name,
                '--restart', 'always',
                '--network', self.network_name,
                '-p', '6633:6633',
                '-p', '6653:6653',
                'adaptive/ryu:1.0'
            ]
            
            run_result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
            
            if run_result.returncode != 0:
                raise Exception(f"Failed to start Ryu controller: {run_result.stderr}")
            
            self.progress_updated.emit(90)
            
            # Verify container is running
            time.sleep(2)
            verify_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name not in verify_result.stdout:
                raise Exception("Container started but is not running")
            
            self.progress_updated.emit(100)
            debug_print(f"Ryu controller '{self.container_name}' deployed successfully")
            
            # Get container IP for status message
            ip_cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', self.container_name]
            ip_result = subprocess.run(ip_cmd, capture_output=True, text=True, timeout=10)
            container_ip = ip_result.stdout.strip() if ip_result.returncode == 0 else "unknown"
            
            self.operation_finished.emit(True, f"Ryu controller '{self.container_name}' deployed successfully\nContainer IP: {container_ip}\nPorts: 6633, 6653")
            
        except subprocess.CalledProcessError as e:
            error_print(f"Command failed: {e.cmd}")
            self.operation_finished.emit(False, f"Command failed: {' '.join(e.cmd)}\nError: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        except subprocess.TimeoutExpired:
            error_print("Operation timed out")
            self.operation_finished.emit(False, "Operation timed out. Please check Docker daemon and try again.")
        except Exception as e:
            error_print(f"Unexpected error: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _stop_controller(self):
        """Stop and remove Ryu controller container."""
        try:
            self.status_updated.emit("Checking container status...")
            self.progress_updated.emit(20)
            
            # Check if container exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name not in result.stdout:
                self.operation_finished.emit(True, f"Ryu controller '{self.container_name}' was not running")
                return
            
            # Stop container if running
            self.status_updated.emit("Stopping container...")
            self.progress_updated.emit(50)
            
            stop_cmd = ['docker', 'stop', self.container_name]
            subprocess.run(stop_cmd, check=True, timeout=30)
            
            # Remove container
            self.status_updated.emit("Removing container...")
            self.progress_updated.emit(80)
            
            remove_cmd = ['docker', 'rm', self.container_name]
            subprocess.run(remove_cmd, check=True, timeout=10)
            
            self.progress_updated.emit(100)
            debug_print(f"Ryu controller '{self.container_name}' stopped and removed")
            self.operation_finished.emit(True, f"Ryu controller '{self.container_name}' stopped and removed successfully")
            
        except subprocess.CalledProcessError as e:
            error_print(f"Command failed: {e.cmd}")
            self.operation_finished.emit(False, f"Failed to stop controller: {' '.join(e.cmd)}")
        except subprocess.TimeoutExpired:
            error_print("Stop operation timed out")
            self.operation_finished.emit(False, "Stop operation timed out")
        except Exception as e:
            error_print(f"Unexpected error during stop: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _find_controller_dockerfile(self):
        """Find the controller Dockerfile in the project structure."""
        # Common paths to check for controller Dockerfile
        possible_paths = [
            # Path relative to src directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "automation", "controller"),
            # Path relative to project root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "controller"),
            # Absolute path based on current working directory
            os.path.join(os.getcwd(), "controller"),
            # Check in netflux5g-editor directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "netflux5g-editor", "src", "automation", "controller")
        ]
        
        for path in possible_paths:
            dockerfile_path = os.path.join(path, "Dockerfile")
            if os.path.exists(dockerfile_path):
                debug_print(f"Found Dockerfile at: {dockerfile_path}")
                return path
        
        return None


class ControllerManager:
    """Manager for Ryu SDN Controller deployment and lifecycle."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.deployment_worker = None
        self.progress_dialog = None
        
    def deployController(self):
        """Deploy Ryu SDN controller container."""
        debug_print("DEBUG: Deploy Ryu Controller triggered")
        
        # Use fixed service name instead of file-based naming
        container_name = "netflux5g-ryu-controller"
        
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            QMessageBox.critical(
                self.main_window,
                "Docker Not Available",
                "Docker is not installed or not running.\n\nPlease install and start Docker before deploying the controller."
            )
            return
        
        # Check if netflux5g network exists, prompt to create if not
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                self.main_window.status_manager.showCanvasStatus("Controller deployment cancelled - netflux5g network required")
                return
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        
        # Check if already running
        if self._is_controller_running(container_name):
            QMessageBox.information(
                self.main_window,
                "Controller Running",
                f"Ryu controller '{container_name}' is already running.\n\nUse 'Stop Ryu Controller' to stop it first."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Ryu Controller",
            f"Deploy Ryu SDN Controller?\n\nContainer name: {container_name}\nPorts: 6633, 6653\n\nThis will:\n- Build adaptive/ryu:1.0 image if needed\n- Create controller container\n- Connect to netflux5g network",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Deploying Ryu controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("Ryu Controller Deployment")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Create and start deployment worker
        self.deployment_worker = ControllerDeploymentWorker('deploy', container_name)
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        
        self.deployment_worker.start()
    
    def stopController(self):
        """Stop Ryu SDN controller container."""
        debug_print("DEBUG: Stop Ryu Controller triggered")
        
        # Use fixed service name instead of file-based naming
        container_name = "netflux5g-ryu-controller"
        
        # Check if controller is running
        if not self._is_controller_running(container_name):
            QMessageBox.information(
                self.main_window,
                "Controller Not Running", 
                f"Ryu controller '{container_name}' is not currently running."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop Ryu Controller",
            f"Stop Ryu SDN Controller '{container_name}'?\n\nThis will:\n- Stop the controller container\n- Remove the container\n- Disconnect from network",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Stopping Ryu controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("Ryu Controller Stop")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Create and start stop worker
        self.deployment_worker = ControllerDeploymentWorker('stop', container_name)
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        
        self.deployment_worker.start()
    
    def getControllerStatus(self):
        """Get the current status of the Ryu controller."""
        container_name = "netflux5g-ryu-controller"
        
        try:
            # Check if container exists and is running
            status_cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}} {{.Status}}']
            result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
            
            if container_name in result.stdout:
                return {
                    'status': 'running',
                    'container_name': container_name,
                    'details': result.stdout.strip()
                }
            else:
                # Check if container exists but is stopped
                all_cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}} {{.Status}}']
                all_result = subprocess.run(all_cmd, capture_output=True, text=True, timeout=10)
                
                if container_name in all_result.stdout:
                    return {
                        'status': 'stopped',
                        'container_name': container_name,
                        'details': all_result.stdout.strip()
                    }
                else:
                    return {
                        'status': 'not_deployed',
                        'container_name': container_name,
                        'details': 'Container not found'
                    }
        except Exception as e:
            error_print(f"Failed to get controller status: {e}")
            return {
                'status': 'unknown',
                'container_name': container_name,
                'details': str(e)
            }
    
    def _get_container_name(self):
        """Generate container name based on current file or use default."""
        if hasattr(self.main_window, 'current_file') and self.main_window.current_file:
            # Use filename without extension
            filename = os.path.basename(self.main_window.current_file)
            name_without_ext = os.path.splitext(filename)[0]
            # Sanitize name for Docker (only alphanumeric, underscore, dash)
            sanitized = ''.join(c if c.isalnum() or c in '_-' else '_' for c in name_without_ext)
            return f"ryu_{sanitized}"
        else:
            return "ryu_default"
    
    def _is_controller_running(self, container_name):
        """Check if the controller container is currently running."""
        try:
            check_cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
    
    def _on_deployment_finished(self, success, message):
        """Handle deployment operation completion."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if success:
            QMessageBox.information(self.main_window, "Controller Deployment", message)
            self.main_window.status_manager.showCanvasStatus("Ryu controller deployed successfully")
        else:
            QMessageBox.critical(self.main_window, "Controller Deployment Failed", message)
            self.main_window.status_manager.showCanvasStatus("Ryu controller deployment failed")
        
        # Clean up worker
        if self.deployment_worker:
            self.deployment_worker.deleteLater()
            self.deployment_worker = None
    
    def _on_deployment_canceled(self):
        """Handle deployment cancellation."""
        if self.deployment_worker and self.deployment_worker.isRunning():
            self.deployment_worker.terminate()
            self.deployment_worker.wait()
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.main_window.status_manager.showCanvasStatus("Controller deployment canceled")
