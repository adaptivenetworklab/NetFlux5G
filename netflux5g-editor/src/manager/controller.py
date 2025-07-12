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
    
    def __init__(self, operation, container_name, controller_type="ryu", network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy' or 'stop'
        self.container_name = container_name
        self.controller_type = controller_type  # 'ryu' or 'onos'
        # Use netflux5g network for service deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        """Execute the controller operation in background thread."""
        try:
            if self.operation == 'deploy':
                if self.controller_type == 'ryu':
                    self._deploy_ryu_controller()
                elif self.controller_type == 'onos':
                    self._deploy_onos_controller()
            elif self.operation == 'stop':
                self._stop_controller()
        except Exception as e:
            error_print(f"Controller operation failed: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _deploy_ryu_controller(self):
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
            
            image_check_cmd = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}', 'adaptive/ryu:latest']
            image_result = subprocess.run(image_check_cmd, capture_output=True, text=True, timeout=10)
            
            if 'adaptive/ryu:latest' not in image_result.stdout:
                # Image doesn't exist, build it
                self.status_updated.emit("Building Ryu controller image...")
                self.progress_updated.emit(30)
                
                # Find the controller Dockerfile path
                controller_dir = self._find_controller_dockerfile()
                if not controller_dir:
                    raise Exception("Controller Dockerfile not found in expected locations")
                
                # Build the image
                build_cmd = ['docker', 'build', '-t', 'adaptive/ryu:latest', controller_dir]
                build_process = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
                
                if build_process.returncode != 0:
                    raise Exception(f"Failed to build Ryu image: {build_process.stderr}")
                
                debug_print("Successfully built adaptive/ryu:latest image")
                self.progress_updated.emit(60)
            else:
                debug_print("Ryu image adaptive/ryu:latest already exists")
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
                'adaptive/ryu:latest'
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
    
    def _deploy_onos_controller(self):
        """Deploy ONOS controller container."""
        try:
            self.status_updated.emit("Checking if ONOS container already exists...")
            self.progress_updated.emit(10)
            
            # Check if container already exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name in result.stdout:
                # Container exists, check if it's running
                status_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
                status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
                
                if self.container_name in status_result.stdout:
                    self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' is already running")
                    return
                else:
                    # Container exists but not running, start it
                    self.status_updated.emit("Starting existing ONOS container...")
                    self.progress_updated.emit(50)
                    start_cmd = ['docker', 'start', self.container_name]
                    subprocess.run(start_cmd, check=True, timeout=30)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' started successfully")
                    return
            
            # Check if the ONOS image exists
            self.status_updated.emit("Checking ONOS controller image...")
            self.progress_updated.emit(20)
            
            image_check_cmd = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}', 'adaptive/onos:latest']
            image_result = subprocess.run(image_check_cmd, capture_output=True, text=True, timeout=10)
            
            if 'adaptive/onos:latest' not in image_result.stdout:
                # Image doesn't exist, build it
                self.status_updated.emit("Building ONOS controller image...")
                self.progress_updated.emit(30)
                
                # Find the ONOS controller Dockerfile path
                controller_dir = self._find_onos_controller_dockerfile()
                if not controller_dir:
                    raise Exception("ONOS Controller Dockerfile not found in expected locations")
                
                # Build the image
                build_cmd = ['docker', 'build', '-t', 'adaptive/onos:latest', controller_dir]
                build_process = subprocess.run(build_cmd, capture_output=True, text=True, timeout=600)  # Longer timeout for ONOS build
                
                if build_process.returncode != 0:
                    raise Exception(f"Failed to build ONOS image: {build_process.stderr}")
                
                debug_print("Successfully built adaptive/onos:latest image")
                self.progress_updated.emit(60)
            else:
                debug_print("ONOS image adaptive/onos:latest already exists")
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
            
            # Create and run ONOS controller container
            self.status_updated.emit("Creating ONOS controller container...")
            self.progress_updated.emit(80)
            
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', self.container_name,
                '--restart', 'always',
                '--network', self.network_name,
                '-p', '6653:6653',  # OpenFlow
                '-p', '6640:6640',  # OVSDB
                '-p', '8181:8181',  # GUI
                '-p', '8101:8101',  # ONOS CLI
                '-p', '9876:9876',  # ONOS intra-cluster communication
                'adaptive/onos:latest'
            ]
            
            run_result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            
            if run_result.returncode != 0:
                raise Exception(f"Failed to start ONOS controller: {run_result.stderr}")
            
            self.progress_updated.emit(90)
            
            # Verify container is running
            time.sleep(5)  # ONOS takes longer to start
            verify_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name not in verify_result.stdout:
                raise Exception("Container started but is not running")
            
            self.progress_updated.emit(100)
            debug_print(f"ONOS controller '{self.container_name}' deployed successfully")
            
            # Get container IP for status message
            ip_cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', self.container_name]
            ip_result = subprocess.run(ip_cmd, capture_output=True, text=True, timeout=10)
            container_ip = ip_result.stdout.strip() if ip_result.returncode == 0 else "unknown"
            
            self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' deployed successfully\nContainer IP: {container_ip}\nPorts: 6653 (OpenFlow), 6640 (OVSDB), 8181 (GUI), 8101 (CLI), 9876 (Cluster)")
            
        except subprocess.CalledProcessError as e:
            error_print(f"Command failed: {e.cmd}")
            self.operation_finished.emit(False, f"Command failed: {' '.join(e.cmd)}\nError: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        except subprocess.TimeoutExpired:
            error_print("Operation timed out")
            self.operation_finished.emit(False, "Operation timed out. ONOS build can take several minutes. Please check Docker daemon and try again.")
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
    
    def _find_onos_controller_dockerfile(self):
        """Find the ONOS controller Dockerfile in the project structure."""
        # Common paths to check for ONOS controller Dockerfile
        possible_paths = [
            # Path relative to src directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "automation", "onos-controller"),
            # Path relative to project root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "onos-controller"),
            # Absolute path based on current working directory
            os.path.join(os.getcwd(), "onos-controller"),
            # Check in netflux5g-editor directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "netflux5g-editor", "src", "automation", "onos-controller")
        ]
        
        for path in possible_paths:
            dockerfile_path = os.path.join(path, "Dockerfile")
            if os.path.exists(dockerfile_path):
                debug_print(f"Found ONOS Dockerfile at: {dockerfile_path}")
                return path
        
        return None

    def _find_controller_dockerfile(self):
        """Find the controller Dockerfile in the project structure."""
        # Common paths to check for controller Dockerfile
        possible_paths = [
            # Path relative to src directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "automation", "ryu-controller"),
            # Path relative to project root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ryu-controller"),
            # Absolute path based on current working directory
            os.path.join(os.getcwd(), "ryu-controller"),
            # Check in netflux5g-editor directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "netflux5g-editor", "src", "automation", "ryu-controller")
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
        
    def deployOnosController(self):
        """Deploy ONOS SDN controller container."""
        debug_print("DEBUG: Deploy ONOS Controller triggered")
        
        # Check for conflicts with RYU controller
        ryu_container_name = "netflux5g-ryu-controller"
        onos_container_name = "netflux5g-onos-controller"
        
        # Check if RYU controller is running
        if self._is_controller_running(ryu_container_name):
            reply = QMessageBox.question(
                self.main_window,
                "Controller Conflict",
                f"RYU controller '{ryu_container_name}' is already running.\n\nOnly one controller can be active at a time.\n\nDo you want to stop RYU controller and deploy ONOS controller?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                self.main_window.status_manager.showCanvasStatus("ONOS controller deployment cancelled")
                return
            
            # Stop RYU controller first
            self._stop_controller_sync(ryu_container_name, "RYU")
        
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
        if self._is_controller_running(onos_container_name):
            QMessageBox.information(
                self.main_window,
                "Controller Running",
                f"ONOS controller '{onos_container_name}' is already running.\n\nUse 'Stop ONOS Controller' to stop it first."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy ONOS Controller",
            f"Deploy ONOS SDN Controller?\n\nContainer name: {onos_container_name}\nPorts: 6653, 6640, 8181, 8101, 9876\n\nThis will:\n- Build adaptive/onos:latest image if needed\n- Create controller container\n- Connect to netflux5g network\n\nNote: ONOS build may take several minutes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Deploying ONOS controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("ONOS Controller Deployment")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Create and start deployment worker
        self.deployment_worker = ControllerDeploymentWorker('deploy', onos_container_name, 'onos')
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        
        self.deployment_worker.start()
    
    def stopOnosController(self):
        """Stop ONOS SDN controller container."""
        debug_print("DEBUG: Stop ONOS Controller triggered")
        
        # Use fixed service name instead of file-based naming
        container_name = "netflux5g-onos-controller"
        
        # Check if controller is running
        if not self._is_controller_running(container_name):
            QMessageBox.information(
                self.main_window,
                "Controller Not Running", 
                f"ONOS controller '{container_name}' is not currently running."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop ONOS Controller",
            f"Stop ONOS SDN Controller '{container_name}'?\n\nThis will:\n- Stop the controller container\n- Remove the container\n- Disconnect from network",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Stopping ONOS controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("ONOS Controller Stop")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Create and start stop worker
        self.deployment_worker = ControllerDeploymentWorker('stop', container_name, 'onos')
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        
        self.deployment_worker.start()
    
    def deployController(self):
        """Deploy Ryu SDN controller container."""
        debug_print("DEBUG: Deploy Ryu Controller triggered")
        
        # Use fixed service name instead of file-based naming
        container_name = "netflux5g-ryu-controller"
        onos_container_name = "netflux5g-onos-controller"
        
        # Check for conflicts with ONOS controller
        if self._is_controller_running(onos_container_name):
            reply = QMessageBox.question(
                self.main_window,
                "Controller Conflict",
                f"ONOS controller '{onos_container_name}' is already running.\n\nOnly one controller can be active at a time.\n\nDo you want to stop ONOS controller and deploy RYU controller?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                self.main_window.status_manager.showCanvasStatus("RYU controller deployment cancelled")
                return
            
            # Stop ONOS controller first
            self._stop_controller_sync(onos_container_name, "ONOS")
        elif self._is_controller_running(container_name):
            QMessageBox.information(
                self.main_window,
                "Controller Running",
                f"Ryu controller '{container_name}' is already running.\n\nUse 'Stop Ryu Controller' to stop it first."
            )
            return
        
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
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Ryu Controller",
            f"Deploy Ryu SDN Controller?\n\nContainer name: {container_name}\nPorts: 6633, 6653\n\nThis will:\n- Build adaptive/ryu:latest image if needed\n- Create controller container\n- Connect to netflux5g network",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Deploying controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("Controller Deployment")
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
        debug_print("DEBUG: Stop Controller triggered")
        
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
            "Stop Controller",
            f"Stop Controller '{container_name}'?\n\nThis will:\n- Stop the controller container\n- Remove the container\n- Disconnect from network",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Stopping controller...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("Controller Stop")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Create and start stop worker
        self.deployment_worker = ControllerDeploymentWorker('stop', container_name)
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        
        self.deployment_worker.start()
    
    def getOnosControllerStatus(self):
        """Get the current status of the ONOS controller."""
        container_name = "netflux5g-onos-controller"
        
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
            error_print(f"Failed to get ONOS controller status: {e}")
            return {
                'status': 'unknown',
                'container_name': container_name,
                'details': str(e)
            }

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
    
    def is_controller_running(self):
        """Check if Ryu controller is running."""
        container_name = "netflux5g-ryu-controller"
        return self._is_controller_running(container_name)

    def is_onos_controller_running(self):
        """Check if ONOS controller is running."""
        container_name = "netflux5g-onos-controller"
        return self._is_controller_running(container_name)

    def _stop_controller_sync(self, container_name, controller_type):
        """Stop a controller container synchronously (for conflict resolution)."""
        try:
            debug_print(f"Stopping {controller_type} controller synchronously: {container_name}")
            
            # Stop container if running
            stop_cmd = ['docker', 'stop', container_name]
            subprocess.run(stop_cmd, check=True, timeout=30)
            
            # Remove container
            remove_cmd = ['docker', 'rm', container_name]
            subprocess.run(remove_cmd, check=True, timeout=10)
            
            debug_print(f"{controller_type} controller '{container_name}' stopped and removed")
            self.main_window.status_manager.showCanvasStatus(f"{controller_type} controller stopped to avoid conflict")
            
        except subprocess.CalledProcessError as e:
            warning_print(f"Failed to stop {controller_type} controller: {e}")
            QMessageBox.warning(
                self.main_window,
                "Controller Stop Failed",
                f"Failed to stop {controller_type} controller '{container_name}'.\nYou may need to stop it manually using: docker stop {container_name} && docker rm {container_name}"
            )
        except Exception as e:
            error_print(f"Unexpected error stopping {controller_type} controller: {e}")

    def _get_container_name(self, controller_type="ryu"):
        """Generate container name based on current file or use default."""
        if hasattr(self.main_window, 'current_file') and self.main_window.current_file:
            # Use filename without extension
            filename = os.path.basename(self.main_window.current_file)
            name_without_ext = os.path.splitext(filename)[0]
            # Sanitize name for Docker (only alphanumeric, underscore, dash)
            sanitized = ''.join(c if c.isalnum() or c in '_-' else '_' for c in name_without_ext)
            return f"{controller_type}_{sanitized}"
        else:
            return f"{controller_type}_default"
    
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
        
        # Determine controller type from worker
        controller_type = "Controller"
        if self.deployment_worker:
            if self.deployment_worker.controller_type == "onos":
                controller_type = "ONOS controller"
            elif self.deployment_worker.controller_type == "ryu":
                controller_type = "RYU controller"
        
        if success:
            QMessageBox.information(self.main_window, "Controller Deployment", message)
            if "deployed successfully" in message:
                self.main_window.status_manager.showCanvasStatus(f"{controller_type} deployed successfully")
            elif "started successfully" in message:
                self.main_window.status_manager.showCanvasStatus(f"{controller_type} started successfully")
            elif "stopped and removed" in message:
                self.main_window.status_manager.showCanvasStatus(f"{controller_type} stopped successfully")
            else:
                self.main_window.status_manager.showCanvasStatus(f"{controller_type} operation completed")
        else:
            QMessageBox.critical(self.main_window, "Controller Operation Failed", message)
            self.main_window.status_manager.showCanvasStatus(f"{controller_type} operation failed")
        
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
        
        # Determine controller type from worker
        controller_type = "Controller"
        if self.deployment_worker:
            if self.deployment_worker.controller_type == "onos":
                controller_type = "ONOS controller"
            elif self.deployment_worker.controller_type == "ryu":
                controller_type = "RYU controller"
        
        self.main_window.status_manager.showCanvasStatus(f"{controller_type} operation canceled")
    
    def deploy_controller_sync(self, controller_type='ryu'):
        """Deploy controller synchronously for automation."""
        debug_print(f"DEBUG: deploy_controller_sync called for {controller_type}")
        try:
            if controller_type == 'onos':
                container_name = "netflux5g-onos-controller"
                ryu_container_name = "netflux5g-ryu-controller"
                
                # Check if RYU controller is running and stop it
                if self._is_controller_running(ryu_container_name):
                    debug_print("Stopping RYU controller before deploying ONOS")
                    self._stop_controller_sync(ryu_container_name, "RYU")
                
                # Check if already running
                if self._is_controller_running(container_name):
                    debug_print(f"ONOS controller '{container_name}' is already running")
                    return True
                
                # Deploy ONOS directly
                return self._deploy_onos_direct(container_name, "netflux5g")
            else:
                container_name = "netflux5g-ryu-controller"
                onos_container_name = "netflux5g-onos-controller"
                
                # Check if ONOS controller is running and stop it
                if self._is_controller_running(onos_container_name):
                    debug_print("Stopping ONOS controller before deploying RYU")
                    self._stop_controller_sync(onos_container_name, "ONOS")
                
                # Check if already running
                if self._is_controller_running(container_name):
                    debug_print(f"RYU controller '{container_name}' is already running")
                    return True
                
                # Deploy RYU directly
                return self._deploy_ryu_direct(container_name, "netflux5g")
                
        except Exception as e:
            error_print(f"ERROR: Failed to deploy {controller_type} controller: {e}")
            return False

    def _deploy_ryu_direct(self, container_name, network_name):
        """Deploy RYU controller directly without threads."""
        try:
            # Check if the Ryu image exists
            debug_print("Checking Ryu controller image...")
            image_check_cmd = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}', 'adaptive/ryu:latest']
            image_result = subprocess.run(image_check_cmd, capture_output=True, text=True, timeout=10)
            
            if 'adaptive/ryu:latest' not in image_result.stdout:
                # Image doesn't exist, build it
                debug_print("Building Ryu controller image...")
                controller_dir = self._find_controller_dockerfile()
                if not controller_dir:
                    error_print("Controller Dockerfile not found")
                    return False
                
                # Build the image
                build_cmd = ['docker', 'build', '-t', 'adaptive/ryu:latest', controller_dir]
                build_process = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
                
                if build_process.returncode != 0:
                    error_print(f"Failed to build Ryu image: {build_process.stderr}")
                    return False
                
                debug_print("Successfully built adaptive/ryu:latest image")
            
            # Remove existing container if it exists but is not running
            if self._container_exists(container_name) and not self._is_controller_running(container_name):
                debug_print(f"Removing existing stopped container: {container_name}")
                remove_cmd = ['docker', 'rm', container_name]
                subprocess.run(remove_cmd, capture_output=True, timeout=10)
            
            # Create and run Ryu controller container
            debug_print(f"Creating Ryu controller container: {container_name}")
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', container_name,
                '--network', network_name,
                '-p', '6633:6633',
                '-p', '6653:6653',
                'adaptive/ryu:latest'
            ]
            
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                error_print(f"Failed to create Ryu controller container: {result.stderr}")
                return False
            
            # Wait for container to be ready
            debug_print("Waiting for Ryu controller to be ready...")
            for i in range(20):  # Wait up to 20 seconds
                if self._is_controller_running(container_name):
                    debug_print("Ryu controller is ready")
                    return True
                time.sleep(1)
            
            error_print("Ryu controller container started but failed to become ready")
            return False
            
        except Exception as e:
            error_print(f"Failed to deploy Ryu controller directly: {e}")
            return False

    def _deploy_onos_direct(self, container_name, network_name):
        """Deploy ONOS controller directly without threads."""
        try:
            # Remove existing container if it exists but is not running
            if self._container_exists(container_name) and not self._is_controller_running(container_name):
                debug_print(f"Removing existing stopped container: {container_name}")
                remove_cmd = ['docker', 'rm', container_name]
                subprocess.run(remove_cmd, capture_output=True, timeout=10)
            
            # Create and run ONOS controller container
            debug_print(f"Creating ONOS controller container: {container_name}")
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', container_name,
                '--restart', 'always',
                '--network', network_name,
                '-p', '6653:6653',  # OpenFlow
                '-p', '6640:6640',  # OVSDB
                '-p', '8181:8181',  # GUI
                '-p', '8101:8101',  # ONOS CLI
                '-p', '9876:9876',  # ONOS intra-cluster communication
                'adaptive/onos:latest'
            ]
            
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                error_print(f"Failed to create ONOS controller container: {result.stderr}")
                return False
            
            # Wait for container to be ready
            debug_print("Waiting for ONOS controller to be ready...")
            for i in range(30):  # Wait up to 30 seconds (ONOS takes longer to start)
                if self._is_controller_running(container_name):
                    debug_print("ONOS controller is ready")
                    return True
                time.sleep(1)
            
            error_print("ONOS controller container started but failed to become ready")
            return False
            
        except Exception as e:
            error_print(f"Failed to deploy ONOS controller directly: {e}")
            return False

    def _container_exists(self, container_name):
        """Check if a container exists (running or stopped)."""
        try:
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
