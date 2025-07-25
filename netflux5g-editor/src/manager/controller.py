"""
Ryu SDN Controller deployment manager for NetFlux5G Editor
Handles Ryu controller container creation and removal with automatic image building
"""

import os
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import pyqtSignal, QThread, QMutex
from utils.debug import debug_print, error_print, warning_print
from utils.docker_utils import DockerUtils, DockerContainerBuilder

def _find_onos_controller_dockerfile():
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

def _find_ryu_controller_dockerfile():
    """Find the Ryu controller Dockerfile in the project structure."""
    # Common paths to check for Ryu controller Dockerfile
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
        """Deploy Ryu controller using DockerUtils and DockerContainerBuilder."""
        try:
            self.status_updated.emit("Checking if Ryu controller image exists...")
            image_name = "ryu_controller"  # Replace with actual image name
            if not DockerUtils.image_exists(image_name):
                DockerUtils.pull_image(image_name)
            builder = DockerContainerBuilder(image=image_name, container_name="ryu_controller")
            builder.set_network("netflux5g")
            # Add ports, volumes, env as needed
            builder.run()
            self.operation_finished.emit(True, "Ryu controller deployed successfully.")
        except Exception as e:
            error_print(f"Failed to deploy Ryu controller: {e}")
            self.operation_finished.emit(False, str(e))

    def _stop_controller(self):
        """Stop controller using DockerUtils."""
        try:
            DockerUtils.stop_container("ryu_controller")
            self.operation_finished.emit(True, "Controller stopped successfully.")
        except Exception as e:
            error_print(f"Failed to stop controller: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _deploy_onos_controller(self):
        """Deploy ONOS controller container using DockerUtils and DockerContainerBuilder."""
        try:
            self.status_updated.emit("Checking if ONOS container already exists...")
            self.progress_updated.emit(10)
            if DockerUtils.container_exists(self.container_name):
                if DockerUtils.is_container_running(self.container_name):
                    self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' is already running")
                    return
                else:
                    self.status_updated.emit("Starting existing ONOS container...")
                    self.progress_updated.emit(50)
                    DockerUtils.start_container(self.container_name)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' started successfully")
                    return
            self.status_updated.emit("Checking ONOS controller image...")
            self.progress_updated.emit(20)
            image_name = 'adaptive/onos:latest'
            if not DockerUtils.image_exists(image_name):
                self.status_updated.emit("Building ONOS controller image...")
                self.progress_updated.emit(30)
                controller_dir = _find_onos_controller_dockerfile()
                if not controller_dir:
                    raise Exception("ONOS Controller Dockerfile not found in expected locations")
                DockerUtils.build_image(image_name, controller_dir)
                self.progress_updated.emit(60)
            else:
                self.progress_updated.emit(60)
            self.status_updated.emit("Checking network...")
            self.progress_updated.emit(70)
            if not DockerUtils.network_exists(self.network_name):
                DockerUtils.create_network(self.network_name)
            self.status_updated.emit("Creating ONOS controller container...")
            self.progress_updated.emit(80)
            builder = DockerContainerBuilder(image=image_name, container_name=self.container_name)
            builder.set_network(self.network_name)
            builder.add_port('6653:6653')
            builder.add_port('6640:6640')
            builder.add_port('8181:8181')
            builder.add_port('8101:8101')
            builder.add_port('9876:9876')
            builder.run()
            self.progress_updated.emit(90)
            time.sleep(5)
            if not DockerUtils.is_container_running(self.container_name):
                raise Exception("Container started but is not running")
            self.progress_updated.emit(100)
            ip = DockerUtils.get_container_ip(self.container_name)
            self.operation_finished.emit(True, f"ONOS controller '{self.container_name}' deployed successfully\nContainer IP: {ip}\nPorts: 6653 (OpenFlow), 6640 (OVSDB), 8181 (GUI), 8101 (CLI), 9876 (Cluster)")
        except Exception as e:
            error_print(f"Unexpected error: {e}")
            self.operation_finished.emit(False, str(e))

    def _stop_controller(self):
        """Stop controller using DockerUtils."""
        try:
            DockerUtils.stop_container(self.container_name)
            DockerUtils.remove_container(self.container_name)
            self.operation_finished.emit(True, "Controller stopped and removed successfully.")
        except Exception as e:
            error_print(f"Failed to stop controller: {e}")
            self.operation_finished.emit(False, str(e))


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
        if not DockerUtils.check_docker_available(self.main_window, show_error=True):
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
        if not DockerUtils.check_docker_available(self.main_window, show_error=True):
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
            status = DockerUtils.get_container_status(container_name)
            if status.startswith("Running"):
                return {'status': 'running', 'container_name': container_name, 'details': status}
            elif status.startswith("Stopped"):
                return {'status': 'stopped', 'container_name': container_name, 'details': status}
            elif status.startswith("Not deployed") or status.startswith("Container does not exist"):
                return {'status': 'not_deployed', 'container_name': container_name, 'details': status}
            else:
                return {'status': 'unknown', 'container_name': container_name, 'details': status}
        except Exception as e:
            error_print(f"Failed to get ONOS controller status: {e}")
            return {'status': 'unknown', 'container_name': container_name, 'details': str(e)}

    def getControllerStatus(self):
        """Get the current status of the Ryu controller."""
        container_name = "netflux5g-ryu-controller"
        try:
            status = DockerUtils.get_container_status(container_name)
            if status.startswith("Running"):
                return {'status': 'running', 'container_name': container_name, 'details': status}
            elif status.startswith("Stopped"):
                return {'status': 'stopped', 'container_name': container_name, 'details': status}
            elif status.startswith("Not deployed") or status.startswith("Container does not exist"):
                return {'status': 'not_deployed', 'container_name': container_name, 'details': status}
            else:
                return {'status': 'unknown', 'container_name': container_name, 'details': status}
        except Exception as e:
            error_print(f"Failed to get controller status: {e}")
            return {'status': 'unknown', 'container_name': container_name, 'details': str(e)}

    def get_controller_container_names(self):
        """Return a list of controller container names (Ryu and ONOS)."""
        return ["netflux5g-ryu-controller", "netflux5g-onos-controller"]

    def _stop_controller_sync(self, container_name, controller_type):
        """Stop a controller container synchronously (for conflict resolution) using DockerUtils."""
        try:
            debug_print(f"Stopping {controller_type} controller synchronously: {container_name}")
            DockerUtils.stop_container(container_name)
            DockerUtils.remove_container(container_name)
            debug_print(f"{controller_type} controller '{container_name}' stopped and removed")
            self.main_window.status_manager.showCanvasStatus(f"{controller_type} controller stopped to avoid conflict")
        except Exception as e:
            warning_print(f"Failed to stop {controller_type} controller: {e}")
            QMessageBox.warning(
                self.main_window,
                "Controller Stop Failed",
                f"Failed to stop {controller_type} controller '{container_name}'.\nYou may need to stop it manually using: docker stop {container_name} && docker rm {container_name}"
            )

    def _is_controller_running(self, container_name):
        """Check if the controller container is currently running using DockerUtils."""
        return DockerUtils.is_container_running(container_name)

    def _container_exists(self, container_name):
        """Check if a container exists (running or stopped) using DockerUtils."""
        return DockerUtils.container_exists(container_name)

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
                
                # Deploy ONOS using consolidated logic
                return self._deploy_controller_internal('onos', container_name, "netflux5g")
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
                
                # Deploy RYU using consolidated logic
                return self._deploy_controller_internal('ryu', container_name, "netflux5g")
                
        except Exception as e:
            error_print(f"ERROR: Failed to deploy {controller_type} controller: {e}")
            return False

    def _deploy_controller_internal(self, controller_type, container_name, network_name):
        """Internal consolidated deployment logic for both RYU and ONOS controllers using DockerUtils and DockerContainerBuilder."""
        try:
            # Remove existing container if it exists but is not running
            if self._container_exists(container_name) and not self._is_controller_running(container_name):
                debug_print(f"Removing existing stopped container: {container_name}")
                DockerUtils.remove_container(container_name)
            if controller_type == 'ryu':
                debug_print("Checking Ryu controller image...")
                if not DockerUtils.image_exists('adaptive/ryu:latest'):
                    debug_print("Building Ryu controller image...")
                    controller_dir = _find_ryu_controller_dockerfile()
                    if not controller_dir:
                        error_print("Controller Dockerfile not found")
                        return False
                    DockerUtils.build_image('adaptive/ryu:latest', controller_dir)
                    debug_print("Successfully built adaptive/ryu:latest image")
                debug_print(f"Creating Ryu controller container: {container_name}")
                builder = DockerContainerBuilder(image='adaptive/ryu:latest', container_name=container_name)
                builder.set_network(network_name)
                builder.add_port('6633:6633')
                builder.add_port('6653:6653')
                builder.run()
                wait_time = 20
            elif controller_type == 'onos':
                debug_print("Checking Onos controller image...")
                if not DockerUtils.image_exists('adaptive/onos:latest'):
                    debug_print("Building ONOS controller image...")
                    controller_dir = _find_onos_controller_dockerfile()
                    if not controller_dir:
                        error_print("Controller Dockerfile not found")
                        return False
                    DockerUtils.build_image('adaptive/onos:latest', controller_dir)
                    debug_print("Successfully built adaptive/onos:latest image")
                debug_print(f"Creating ONOS controller container: {container_name}")
                builder = DockerContainerBuilder(image='adaptive/onos:latest', container_name=container_name)
                builder.set_network(network_name)
                builder.add_port('6653:6653')
                builder.add_port('6640:6640')
                builder.add_port('8181:8181')
                builder.add_port('8101:8101')
                builder.add_port('9876:9876')
                builder.add_extra_arg('--restart=always')
                builder.run()
                wait_time = 30
            else:
                error_print(f"Unknown controller type: {controller_type}")
                return False
            debug_print(f"Waiting for {controller_type} controller to be ready...")
            for i in range(wait_time):
                if self._is_controller_running(container_name):
                    debug_print(f"{controller_type} controller is ready")
                    return True
                time.sleep(1)
            error_print(f"{controller_type} controller container started but failed to become ready")
            return False
        except Exception as e:
            error_print(f"Failed to deploy {controller_type} controller: {e}")
            return False
