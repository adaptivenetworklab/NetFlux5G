"""
Packet Analyzer (Webshark) deployment manager for NetFlux5G Editor
Handles Webshark container creation and removal with bind mount to captures folder
"""

import os
import subprocess
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import pyqtSignal, QThread, QMutex
from utils.debug import debug_print, error_print, warning_print

class PacketAnalyzerDeploymentWorker(QThread):
    """Worker thread for packet analyzer operations to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation, container_name, captures_path=None, network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy' or 'stop'
        self.container_name = container_name
        self.captures_path = captures_path
        # Use netflux5g network for service deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        """Execute the packet analyzer operation in background thread."""
        debug_print(f"DEBUG: Worker thread starting operation: {self.operation}")
        try:
            if self.operation == 'deploy':
                self._deploy_packet_analyzer()
            elif self.operation == 'stop':
                self._stop_packet_analyzer()
        except Exception as e:
            error_print(f"Packet analyzer operation failed: {e}")
            debug_print(f"DEBUG: Worker emitting failure signal due to exception: {e}")
            self.operation_finished.emit(False, str(e))
        debug_print("DEBUG: Worker thread ending")
    
    def _deploy_packet_analyzer(self):
        """Deploy Webshark container with bind mount to captures folder."""
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
                    self.operation_finished.emit(True, f"Webshark container '{self.container_name}' is already running")
                    return
                else:
                    # Container exists but not running, start it
                    self.status_updated.emit("Starting existing container...")
                    self.progress_updated.emit(50)
                    start_cmd = ['docker', 'start', self.container_name]
                    subprocess.run(start_cmd, check=True, timeout=30)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"Webshark container '{self.container_name}' started successfully")
                    return
            
            # Build the Webshark image if needed
            self.status_updated.emit("Building Webshark image...")
            self.progress_updated.emit(20)
            
            # Get the webshark directory path
            webshark_path = self._get_webshark_path()
            if not webshark_path:
                self.operation_finished.emit(False, "Webshark directory not found")
                return
            
            # Build the Docker image
            build_cmd = ['docker', 'build', '-t', 'adaptive/netflux5g-webshark:latest', '.']
            subprocess.run(build_cmd, cwd=webshark_path, check=True, timeout=300)  # Allow 5 minutes for build
            debug_print("Built Webshark image: adaptive/netflux5g-webshark:latest")
            
            # Create and run Webshark container
            self.status_updated.emit("Creating Webshark container...")
            self.progress_updated.emit(60)
            
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', self.container_name,
                '--restart', 'always',
                '--network', self.network_name,
                '-p', '8085:8085',
                '-v', f'{self.captures_path}:/captures',
                '--env', 'SHARKD_SOCKET=/home/node/sharkd.sock',
                '--env', 'CAPTURES_PATH=/captures/',
                'adaptive/netflux5g-webshark:latest'
            ]
            
            subprocess.run(run_cmd, check=True, timeout=60)
            debug_print(f"Started Webshark container: {self.container_name}")
            
            # Wait a moment for container to fully start
            self.status_updated.emit("Verifying container startup...")
            self.progress_updated.emit(80)
            time.sleep(2)
            
            # Verify container is running
            verify_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name in verify_result.stdout:
                self.progress_updated.emit(100)
                debug_print("DEBUG: Worker emitting success signal")
                self.operation_finished.emit(True, f"Webshark container '{self.container_name}' deployed successfully on port 8085")
            else:
                debug_print("DEBUG: Worker emitting failure signal - container not running")
                self.operation_finished.emit(False, "Container deployment failed - container not running")
                
        except subprocess.TimeoutExpired:
            debug_print("DEBUG: Worker emitting failure signal - timeout")
            self.operation_finished.emit(False, "Operation timed out")
        except subprocess.CalledProcessError as e:
            error_print(f"Docker command failed: {e}")
            debug_print("DEBUG: Worker emitting failure signal - docker command failed")
            self.operation_finished.emit(False, f"Docker command failed: {e}")
        except Exception as e:
            error_print(f"Unexpected error during deployment: {e}")
            debug_print("DEBUG: Worker emitting failure signal - unexpected error during deployment")
            self.operation_finished.emit(False, f"Unexpected error: {e}")
    
    def _stop_packet_analyzer(self):
        """Stop and remove the Webshark container."""
        try:
            self.status_updated.emit("Stopping Webshark container...")
            self.progress_updated.emit(30)
            
            # Stop the container
            stop_cmd = ['docker', 'stop', self.container_name]
            subprocess.run(stop_cmd, check=True, timeout=30)
            debug_print(f"Stopped container: {self.container_name}")
            
            self.status_updated.emit("Removing container...")
            self.progress_updated.emit(70)
            
            # Remove the container
            remove_cmd = ['docker', 'rm', self.container_name]
            subprocess.run(remove_cmd, check=True, timeout=30)
            debug_print(f"Removed container: {self.container_name}")
            
            self.progress_updated.emit(100)
            debug_print("DEBUG: Worker emitting success signal for stop")
            self.operation_finished.emit(True, f"Webshark container '{self.container_name}' stopped and removed successfully")
            
        except subprocess.CalledProcessError as e:
            # Container might not exist or already stopped
            if "No such container" in str(e):
                debug_print("DEBUG: Worker emitting success signal - container was not running")
                self.operation_finished.emit(True, f"Webshark container '{self.container_name}' was not running")
            else:
                error_print(f"Failed to stop container: {e}")
                debug_print("DEBUG: Worker emitting failure signal - failed to stop container")
                self.operation_finished.emit(False, f"Failed to stop container: {e}")
        except Exception as e:
            error_print(f"Unexpected error during stop: {e}")
            debug_print("DEBUG: Worker emitting failure signal - unexpected error during stop")
            self.operation_finished.emit(False, f"Unexpected error: {e}")
    
    def _get_webshark_path(self):
        """Get the path to the webshark directory."""
        # Try to find webshark directory relative to current location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webshark_path = os.path.join(os.path.dirname(current_dir), "automation", "webshark")
        
        if os.path.exists(webshark_path) and os.path.isfile(os.path.join(webshark_path, "Dockerfile")):
            return webshark_path
        
        error_print(f"Webshark directory not found. Tried: {webshark_path}")
        return None


class PacketAnalyzerManager:
    """Manager for Webshark packet analyzer deployment operations."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.deployment_worker = None
        self.progress_dialog = None
        self.operation_mutex = QMutex()
        
    def deployPacketAnalyzer(self):
        """Deploy Webshark packet analyzer with UI feedback."""
        debug_print("DEBUG: Starting Webshark deployment process")
        
        # Check if already running
        if self.is_packet_analyzer_running():
            QMessageBox.information(
                self.main_window, 
                "Webshark Running", 
                "Webshark packet analyzer is already running on port 8085"
            )
            return
        
        # Get container name and captures path
        container_name = "netflux5g-webshark"
        captures_path = self._get_captures_path()
        
        if not captures_path:
            QMessageBox.warning(
                self.main_window,
                "Configuration Error",
                "Could not find webshark captures directory"
            )
            return
        
        # Check if Docker is available
        if not self._check_docker_available():
            QMessageBox.warning(
                self.main_window,
                "Docker Not Available",
                "Docker is not available or not running. Please install Docker and ensure it's running."
            )
            return
        
        # Check if netflux5g network exists
        if not self._network_exists("netflux5g"):
            reply = QMessageBox.question(
                self.main_window,
                "Network Required",
                "The 'netflux5g' Docker network is required but doesn't exist. Create it now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if not self._create_network("netflux5g"):
                    QMessageBox.warning(
                        self.main_window,
                        "Network Creation Failed",
                        "Failed to create the 'netflux5g' network. Please create it manually."
                    )
                    return
            else:
                return
        
        # Start deployment in background thread
        self._start_operation('deploy', container_name, captures_path, "netflux5g")
    
    def stopPacketAnalyzer(self):
        """Stop Webshark packet analyzer with UI feedback."""
        debug_print("DEBUG: Starting Webshark stop process")
        
        # Check if running
        if not self.is_packet_analyzer_running():
            QMessageBox.information(
                self.main_window, 
                "Webshark Not Running", 
                "Webshark packet analyzer is not currently running"
            )
            return
        
        # Get container name
        container_name = "netflux5g-webshark"
        
        # Confirm stop
        reply = QMessageBox.question(
            self.main_window,
            "Stop Webshark",
            "Are you sure you want to stop the Webshark packet analyzer?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Start stop operation in background thread
            self._start_operation('stop', container_name, None, None)
    
    def is_packet_analyzer_running(self):
        """Check if the Webshark container is running."""
        container_name = "netflux5g-webshark"
        return self._is_container_running(container_name)
    
    def deploy_packet_analyzer(self):
        """Deploy packet analyzer and return success status."""
        self.deployPacketAnalyzer()
        # Wait a moment for deployment to complete
        time.sleep(1)
        return self.is_packet_analyzer_running()
    
    def deploy_packet_analyzer_sync(self):
        """Synchronously deploy packet analyzer and return success status."""
        debug_print("DEBUG: Starting synchronous Webshark deployment")
        
        container_name = "netflux5g-webshark"
        captures_path = self._get_captures_path()
        
        if not captures_path:
            error_print("Could not find webshark captures directory")
            return False
        
        success = self._deploy_packet_analyzer_direct(container_name, captures_path, "netflux5g")
        return success
    
    def _deploy_packet_analyzer_direct(self, container_name, captures_path, network_name):
        """Direct deployment without UI - used for automation."""
        try:
            # Check if already running
            if self._is_container_running(container_name):
                debug_print(f"Webshark container '{container_name}' is already running")
                return True
            
            # Build the Webshark image if needed
            webshark_path = self._get_webshark_path()
            if not webshark_path:
                error_print("Webshark directory not found")
                return False
            
            debug_print("Building Webshark image...")
            build_cmd = ['docker', 'build', '-t', 'adaptive/netflux5g-webshark:latest', '.']
            subprocess.run(build_cmd, cwd=webshark_path, check=True, timeout=300)
            
            # Create and run container
            debug_print("Creating Webshark container...")
            run_cmd = [
                'docker', 'run', '-itd',
                '--name', container_name,
                '--restart', 'always',
                '--network', network_name,
                '-p', '8085:8085',
                '-v', f'{captures_path}:/captures',
                '--env', 'SHARKD_SOCKET=/home/node/sharkd.sock',
                '--env', 'CAPTURES_PATH=/captures/',
                'adaptive/netflux5g-webshark:latest'
            ]
            
            subprocess.run(run_cmd, check=True, timeout=60)
            debug_print(f"Started Webshark container: {container_name}")
            
            # Wait for container to start
            time.sleep(2)
            
            # Verify container is running
            return self._is_container_running(container_name)
            
        except Exception as e:
            error_print(f"Failed to deploy Webshark: {e}")
            return False
    
    def _check_file_saved(self):
        """Check if the current topology file has been saved."""
        return hasattr(self.main_window, 'current_file') and self.main_window.current_file is not None
    
    def _get_container_names(self):
        """Get the container names for packet analyzer."""
        return "netflux5g-webshark"
    
    def _check_docker_available(self):
        """Check if Docker is available and running."""
        try:
            subprocess.run(['docker', '--version'], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _is_container_running(self, container_name):
        """Check if a specific container is running."""
        try:
            cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
    
    def _container_exists(self, container_name):
        """Check if a container exists (running or stopped)."""
        try:
            cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
    
    def _get_captures_path(self):
        """Get the path to the captures directory."""
        # Try to find webshark directory relative to current location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webshark_path = os.path.join(os.path.dirname(current_dir), "automation", "webshark")
        captures_path = os.path.join(webshark_path, "captures")
        
        if os.path.exists(captures_path):
            return captures_path
        
        error_print(f"Captures directory not found. Tried: {captures_path}")
        return None
    
    def _get_webshark_path(self):
        """Get the path to the webshark directory."""
        # Try to find webshark directory relative to current location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webshark_path = os.path.join(os.path.dirname(current_dir), "automation", "webshark")
        
        if os.path.exists(webshark_path) and os.path.isfile(os.path.join(webshark_path, "Dockerfile")):
            return webshark_path
        
        error_print(f"Webshark directory not found. Tried: {webshark_path}")
        return None
    
    def _network_exists(self, network_name):
        """Check if a Docker network exists."""
        try:
            cmd = ['docker', 'network', 'ls', '--filter', f'name={network_name}', '--format', '{{.Name}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return network_name in result.stdout
        except Exception:
            return False
    
    def _create_network(self, network_name):
        """Create a Docker network."""
        try:
            cmd = ['docker', 'network', 'create', network_name]
            subprocess.run(cmd, check=True, timeout=30)
            debug_print(f"Created network: {network_name}")
            return True
        except Exception as e:
            error_print(f"Failed to create network {network_name}: {e}")
            return False
    
    def _stop_container_sync(self, container_name):
        """Synchronously stop and remove a container."""
        try:
            # Stop container
            stop_cmd = ['docker', 'stop', container_name]
            subprocess.run(stop_cmd, check=True, timeout=30)
            
            # Remove container
            remove_cmd = ['docker', 'rm', container_name]
            subprocess.run(remove_cmd, check=True, timeout=30)
            
            debug_print(f"Stopped and removed container: {container_name}")
            return True
        except subprocess.CalledProcessError as e:
            if "No such container" in str(e):
                debug_print(f"Container '{container_name}' was not running")
                return True
            else:
                error_print(f"Failed to stop container: {e}")
                return False
        except Exception as e:
            error_print(f"Unexpected error stopping container: {e}")
            return False
    
    def _start_operation(self, operation, container_name, captures_path, network_name):
        """Start a deployment operation in background thread with progress dialog."""
        debug_print(f"DEBUG: Starting operation: {operation}")
        
        if self.deployment_worker and self.deployment_worker.isRunning():
            QMessageBox.warning(
                self.main_window,
                "Operation in Progress",
                "Another deployment operation is already in progress. Please wait for it to complete."
            )
            return
        
        # Create progress dialog
        operation_text = "Deploying" if operation == 'deploy' else "Stopping"
        self.progress_dialog = QProgressDialog(
            f"{operation_text} Webshark...",
            "Cancel",
            0,
            100,
            self.main_window
        )
        self.progress_dialog.setWindowTitle(f"Webshark {operation_text}")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self._on_deployment_canceled)
        self.progress_dialog.show()
        
        # Create and start worker thread
        debug_print("DEBUG: Creating worker thread")
        self.deployment_worker = PacketAnalyzerDeploymentWorker(
            operation, container_name, captures_path, network_name
        )
        debug_print("DEBUG: Connecting worker signals")
        self.deployment_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.deployment_worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.deployment_worker.operation_finished.connect(self._on_deployment_finished)
        
        debug_print("DEBUG: Starting worker thread")
        self.deployment_worker.start()
    
    def _on_deployment_finished(self, success, message):
        """Handle deployment completion."""
        debug_print(f"DEBUG: _on_deployment_finished called with success={success}, message={message}")
        
        # Disconnect the canceled signal to prevent automatic cancellation
        if self.progress_dialog:
            debug_print("DEBUG: Disconnecting canceled signal and closing progress dialog")
            self.progress_dialog.canceled.disconnect()
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if success:
            debug_print("DEBUG: Showing success message")
            QMessageBox.information(self.main_window, "Success", message)
            if hasattr(self.main_window, 'status_manager'):
                self.main_window.status_manager.showCanvasStatus("Webshark deployment completed")
        else:
            debug_print("DEBUG: Showing failure message")
            QMessageBox.warning(self.main_window, "Deployment Failed", message)
            if hasattr(self.main_window, 'status_manager'):
                self.main_window.status_manager.showCanvasStatus("Webshark deployment failed")
        
        # Update main window state if needed
        if hasattr(self.main_window, 'updateWindowState'):
            self.main_window.updateWindowState()
    
    def _on_deployment_canceled(self):
        """Handle deployment cancellation."""
        debug_print("DEBUG: _on_deployment_canceled called")
        
        if self.deployment_worker and self.deployment_worker.isRunning():
            debug_print("DEBUG: Terminating deployment worker")
            self.deployment_worker.terminate()
            self.deployment_worker.wait(3000)  # Wait up to 3 seconds
        
        if self.progress_dialog:
            debug_print("DEBUG: Closing progress dialog from cancel")
            self.progress_dialog.close()
            self.progress_dialog = None
        
        debug_print("DEBUG: Showing cancelled message")
        QMessageBox.information(self.main_window, "Cancelled", "Webshark operation was cancelled")
        
        if hasattr(self.main_window, 'status_manager'):
            self.main_window.status_manager.showCanvasStatus("Webshark operation cancelled")
