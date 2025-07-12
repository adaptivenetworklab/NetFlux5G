"""
Database deployment manager for NetFlux5G Editor
Handles MongoDB container creation and removal based on webui-db.yaml configuration
"""

import os
import subprocess
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from manager.debug import debug_print, error_print, warning_print

class DatabaseDeploymentWorker(QThread):
    """Worker thread for database operations to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation, container_name, volume_name=None, network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy', 'stop', or 'cleanup'
        self.container_name = container_name
        self.volume_name = volume_name
        # Use netflux5g network for service deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        """Execute the database operation in background thread."""
        try:
            if self.operation == 'deploy':
                self._deploy_database()
            elif self.operation == 'stop':
                self._stop_database()
            elif self.operation == 'cleanup':
                self._cleanup_database()
            elif self.operation == 'deploy_webui':
                self._deploy_webui()
            elif self.operation == 'stop_webui':
                self._stop_database()  # Same logic as stop database
            elif self.operation == 'cleanup_webui':
                self._cleanup_database()  # Same logic as cleanup database
        except Exception as e:
            error_print(f"Database operation failed: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _deploy_database(self):
        """Deploy MongoDB container with volume."""
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
                    self.operation_finished.emit(True, f"Database container '{self.container_name}' is already running")
                    return
                else:
                    # Container exists but not running, start it
                    self.status_updated.emit("Starting existing container...")
                    self.progress_updated.emit(50)
                    start_cmd = ['docker', 'start', self.container_name]
                    subprocess.run(start_cmd, check=True, timeout=30)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"Database container '{self.container_name}' started successfully")
                    return
            
            # Create volume if it doesn't exist
            self.status_updated.emit("Creating Docker volume...")
            self.progress_updated.emit(20)
            
            volume_cmd = ['docker', 'volume', 'create', self.volume_name]
            subprocess.run(volume_cmd, check=True, timeout=10)
            debug_print(f"Created volume: {self.volume_name}")
            
            # Pull MongoDB image if not present
            self.status_updated.emit("Checking MongoDB image...")
            self.progress_updated.emit(30)
            
            pull_cmd = ['docker', 'pull', 'mongo:latest']
            subprocess.run(pull_cmd, check=True, timeout=120)  # Allow more time for image pull
            
            # Create and run MongoDB container
            self.status_updated.emit("Creating MongoDB container...")
            self.progress_updated.emit(60)
            
            run_cmd = [
                'docker', 'run', '-d',
                '--name', self.container_name,
                '--restart', 'always',
                '--network', self.network_name,
                '-e', 'MONGO_INITDB_DATABASE=open5gs',
                '-p', '27017:27017',
                '-v', f'{self.volume_name}:/data/db'
            ]
            
            run_cmd.append('mongo:latest')
            
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, run_cmd, result.stderr)
            
            # Wait for container to be healthy
            self.status_updated.emit("Waiting for database to be ready...")
            self.progress_updated.emit(80)
            
            # Simple health check - wait for container to be running
            for i in range(10):  # Wait up to 10 seconds
                health_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Status}}']
                health_result = subprocess.run(health_cmd, capture_output=True, text=True, timeout=5)
                
                if 'Up' in health_result.stdout:
                    break
                time.sleep(1)
            
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Database container '{self.container_name}' deployed successfully")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Operation timed out")
        except subprocess.CalledProcessError as e:
            self.operation_finished.emit(False, f"Docker command failed: {e.stderr}")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")
    
    def _stop_database(self):
        """Stop and remove MongoDB container and volume."""
        try:
            self.status_updated.emit("Checking container status...")
            self.progress_updated.emit(10)
            
            # Check if container exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name not in result.stdout:
                self.operation_finished.emit(True, f"Database container '{self.container_name}' does not exist")
                return
            
            # Stop container
            self.status_updated.emit("Stopping container...")
            self.progress_updated.emit(30)
            
            stop_cmd = ['docker', 'stop', self.container_name]
            subprocess.run(stop_cmd, capture_output=True, text=True, timeout=30)
            
            # Remove container
            self.status_updated.emit("Removing container...")
            self.progress_updated.emit(60)
            
            remove_cmd = ['docker', 'rm', self.container_name]
            subprocess.run(remove_cmd, check=True, timeout=10)
            
            # Note: Volume is preserved for data persistence
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Database container '{self.container_name}' stopped and removed successfully (volume preserved)")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Operation timed out")
        except subprocess.CalledProcessError as e:
            self.operation_finished.emit(False, f"Docker command failed: {e.stderr}")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")
    
    def _cleanup_database(self):
        """Completely remove MongoDB container and volume."""
        try:
            self.status_updated.emit("Starting complete cleanup...")
            self.progress_updated.emit(10)
            
            # Stop and remove container if it exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name in result.stdout:
                self.status_updated.emit("Stopping container...")
                self.progress_updated.emit(30)
                
                stop_cmd = ['docker', 'stop', self.container_name]
                subprocess.run(stop_cmd, capture_output=True, text=True, timeout=30)
                
                self.status_updated.emit("Removing container...")
                self.progress_updated.emit(50)
                
                remove_cmd = ['docker', 'rm', self.container_name]
                subprocess.run(remove_cmd, check=True, timeout=10)
            
            # Remove volume if it exists and is specified
            if self.volume_name:
                self.status_updated.emit("Removing volume and all data...")
                self.progress_updated.emit(70)
                
                volume_remove_cmd = ['docker', 'volume', 'rm', self.volume_name]
                result = subprocess.run(volume_remove_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0 and "no such volume" not in result.stderr.lower():
                    warning_print(f"Warning: Could not remove volume {self.volume_name}: {result.stderr}")
            
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Complete cleanup finished: container and volume removed")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Cleanup operation timed out")
        except subprocess.CalledProcessError as e:
            self.operation_finished.emit(False, f"Docker command failed during cleanup: {e.stderr}")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error during cleanup: {str(e)}")

    def _deploy_webui(self):
        """Deploy Web UI container."""
        try:
            self.status_updated.emit("Checking if Web UI container already exists...")
            self.progress_updated.emit(10)
            
            # Check if container already exists
            check_cmd = ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            
            if self.container_name in result.stdout:
                # Container exists, check if it's running
                status_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}']
                status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=10)
                
                if self.container_name in status_result.stdout:
                    self.operation_finished.emit(True, f"Web UI container '{self.container_name}' is already running")
                    return
                else:
                    # Container exists but not running, start it
                    self.status_updated.emit("Starting existing Web UI container...")
                    self.progress_updated.emit(50)
                    start_cmd = ['docker', 'start', self.container_name]
                    subprocess.run(start_cmd, check=True, timeout=30)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"Web UI container '{self.container_name}' started successfully")
                    return
            
            # Pull Web UI image if not present
            self.status_updated.emit("Checking Web UI image...")
            self.progress_updated.emit(30)
            
            pull_cmd = ['docker', 'pull', 'gradiant/open5gs-webui:2.7.5']
            subprocess.run(pull_cmd, check=True, timeout=120)  # Allow more time for image pull
            
            # Create and run Web UI container
            self.status_updated.emit("Creating Web UI container...")
            self.progress_updated.emit(60)
            
            # Get MongoDB container name for dependency - use fixed naming
            mongo_container_name = "netflux5g-mongodb"
            
            run_cmd = [
                'docker', 'run', '-d',
                '--name', self.container_name,
                '--restart', 'on-failure',
                '--network', self.network_name,
                '-p', '9999:9999'
            ]
            
            # Use network-based container communication since we're on the same network
            run_cmd.extend(['-e', f'DB_URI=mongodb://{mongo_container_name}:27017/open5gs'])
            
            # Add environment variable
            run_cmd.extend(['-e', 'NODE_ENV=dev'])

            run_cmd.append('gradiant/open5gs-webui:2.7.5')

            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, run_cmd, result.stderr)
            
            # Wait for container to be healthy
            self.status_updated.emit("Waiting for Web UI to be ready...")
            self.progress_updated.emit(80)
            
            # Simple health check - wait for container to be running
            for i in range(10):  # Wait up to 10 seconds
                health_cmd = ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Status}}']
                health_result = subprocess.run(health_cmd, capture_output=True, text=True, timeout=5)
                
                if 'Up' in health_result.stdout:
                    break
                time.sleep(1)
            
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Web UI container '{self.container_name}' deployed successfully")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Web UI deployment timed out")
        except subprocess.CalledProcessError as e:
            self.operation_finished.emit(False, f"Docker command failed: {e.stderr}")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")
        

class DatabaseManager:
    """Manager for database deployment operations."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_worker = None
        self.progress_dialog = None
        
    def deployDatabase(self):
        """Deploy MongoDB database container."""
        debug_print("Deploy Database triggered")
        
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-mongodb"
        volume_name = "netflux5g-mongodb-data"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if netflux5g network exists, prompt to create if not
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                self.main_window.status_manager.showCanvasStatus("Database deployment cancelled - netflux5g network required")
                return
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        
        # Check if already running
        if self._is_container_running(container_name):
            reply = QMessageBox.question(
                self.main_window,
                "Container Already Running",
                f"Database container '{container_name}' is already running.\n\nDo you want to restart it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Stop first, then deploy
            self._stop_container_sync(container_name)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Database",
            f"This will create a MongoDB container with:\n"
            f"• Container name: {container_name}\n"
            f"• Volume name: {volume_name}\n"
            f"• Port: 27017\n"
            f"• Network: netflux5g\n"
            f"• Database: open5gs\n\n"
            f"Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start deployment with netflux5g network
        self._start_operation('deploy', container_name, volume_name, "netflux5g")
    
    def stopDatabase(self):
        """Stop and remove MongoDB database container."""
        debug_print("Stop Database triggered")
        
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-mongodb"
        volume_name = "netflux5g-mongodb-data"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if container exists
        if not self._container_exists(container_name):
            QMessageBox.information(
                self.main_window,
                "Container Not Found",
                f"Database container '{container_name}' does not exist."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop Database",
            f"This will stop and remove the container:\n"
            f"• Container: {container_name}\n\n"
            f"The data volume ({volume_name}) will be preserved\n"
            f"and can be reused when deploying again.\n\n"
            f"Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start stop operation (without volume removal)
        self._start_operation('stop', container_name, None, None)
    
    def cleanupDatabase(self):
        """Completely remove MongoDB database container and volume (for complete cleanup)."""
        debug_print("Cleanup Database triggered")
        
        # Check if file is saved to get container name
        if not self._check_file_saved():
            return
        
        container_name, volume_name = self._get_container_names()
        
        if not container_name:
            QMessageBox.warning(
                self.main_window,
                "Error",
                "Could not determine container name from current file."
            )
            return
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if container or volume exists
        container_exists = self._container_exists(container_name)
        volume_exists = self._volume_exists(volume_name)
        
        if not container_exists and not volume_exists:
            QMessageBox.information(
                self.main_window,
                "Nothing to Clean",
                f"No database container or volume found for '{container_name}'."
            )
            return
        
        # Show confirmation dialog with strong warning
        reply = QMessageBox.question(
            self.main_window,
            "Complete Database Cleanup",
            f"⚠️ WARNING: This will permanently delete ALL data!\n\n"
            f"This will remove:\n"
            f"• Container: {container_name} {'(exists)' if container_exists else '(not found)'}\n"
            f"• Volume: {volume_name} {'(exists)' if volume_exists else '(not found)'}\n\n"
            f"🚨 ALL DATABASE DATA WILL BE LOST PERMANENTLY!\n\n"
            f"Are you absolutely sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start cleanup operation
        self._start_operation('cleanup', container_name, volume_name, None)
        
    def deployWebUI(self):
        """Deploy Web UI container."""
        debug_print("Deploy Web UI triggered")
        
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-webui"
        mongo_container_name = "netflux5g-mongodb"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if netflux5g network exists, prompt to create if not
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                self.main_window.status_manager.showCanvasStatus("Web UI deployment cancelled - netflux5g network required")
                return
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        
        # Check if MongoDB container exists (dependency)
        if not self._container_exists(mongo_container_name):
            reply = QMessageBox.question(
                self.main_window,
                "MongoDB Required",
                f"Web UI requires MongoDB to be running.\n\n"
                f"MongoDB container '{mongo_container_name}' does not exist.\n\n"
                f"Do you want to deploy MongoDB first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.deployDatabase()
                return
            else:
                self.main_window.status_manager.showCanvasStatus("Web UI deployment cancelled - MongoDB required")
                return
        
        # Check if MongoDB is running
        if not self._is_container_running(mongo_container_name):
            reply = QMessageBox.question(
                self.main_window,
                "MongoDB Not Running",
                f"Web UI requires MongoDB to be running.\n\n"
                f"MongoDB container '{mongo_container_name}' exists but is not running.\n\n"
                f"Do you want to start MongoDB first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Start MongoDB container
                try:
                    subprocess.run(['docker', 'start', mongo_container_name], check=True, timeout=30)
                    self.main_window.status_manager.showCanvasStatus(f"Started MongoDB container: {mongo_container_name}")
                except Exception as e:
                    QMessageBox.critical(
                        self.main_window,
                        "Failed to Start MongoDB",
                        f"Could not start MongoDB container: {e}"
                    )
                    return
            else:
                self.main_window.status_manager.showCanvasStatus("Web UI deployment cancelled - MongoDB not running")
                return
        
        # Check if already running
        if self._is_container_running(container_name):
            reply = QMessageBox.question(
                self.main_window,
                "Container Already Running",
                f"Web UI container '{container_name}' is already running.\n\nDo you want to restart it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Stop first, then deploy
            self._stop_container_sync(container_name)
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Web UI",
            f"This will create a Web UI container with:\n"
            f"• Container name: {container_name}\n"
            f"• Port: 9999\n"
            f"• Network: netflux5g\n"
            f"• MongoDB dependency: {mongo_container_name}\n"
            f"• Environment: development\n\n"
            f"Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start deployment with netflux5g network
        self._start_operation('deploy_webui', container_name, None, "netflux5g")
    
    def stopWebUI(self):
        """Stop and remove Web UI container."""
        debug_print("Stop Web UI triggered")
        
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-webui"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if container exists
        if not self._container_exists(container_name):
            QMessageBox.information(
                self.main_window,
                "Container Not Found",
                f"Web UI container '{container_name}' does not exist."
            )
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop Web UI",
            f"This will stop and remove the container:\n"
            f"• Container: {container_name}\n\n"
            f"The Web UI will be stopped but MongoDB will remain running.\n\n"
            f"Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start stop operation (without volume removal)
        self._start_operation('stop_webui', container_name, None, None)
    
    def is_database_running(self):
        """Check if the database container is running."""
        container_name = "netflux5g-mongodb"
        return self._is_container_running(container_name)
    
    def is_webui_running(self):
        """Check if the WebUI container is running."""
        container_name = "netflux5g-webui"
        return self._is_container_running(container_name)
    
    def deploy_database(self):
        """Deploy MongoDB database for the current topology."""
        debug_print("DEBUG: deploy_database called")
        try:
            # Use fixed service names instead of file-based naming
            container_name = "netflux5g-mongodb"
            volume_name = "netflux5g-mongodb-data"
            
            # Check if Docker is available
            if not self._check_docker_available():
                return False
            
            # Check if netflux5g network exists, prompt to create if not
            if hasattr(self.main_window, 'docker_network_manager'):
                if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                    self.main_window.status_manager.showCanvasStatus("Database deployment cancelled - netflux5g network required")
                    return False
            else:
                warning_print("Docker network manager not available, proceeding without network check")
            
            # Check if already running
            if self._is_container_running(container_name):
                reply = QMessageBox.question(
                    self.main_window,
                    "Container Already Running",
                    f"Database container '{container_name}' is already running.\n\nDo you want to restart it?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return False
                
                # Stop first, then deploy
                self._stop_container_sync(container_name)

            # Show confirmation dialog
            reply = QMessageBox.question(
                self.main_window,
                "Deploy Database",
                f"This will create a MongoDB container with:\n"
                f"• Container name: {container_name}\n"
                f"• Volume name: {volume_name}\n"
                f"• Port: 27017\n"
                f"• Network: netflux5g\n"
                f"• Database: open5gs\n\n"
                f"Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                return False
            
            # Start deployment with netflux5g network
            result = self._start_operation('deploy', container_name, volume_name, "netflux5g")
            debug_print(f"DEBUG: deploy_database result: {result}")
            return result
        except Exception as e:
            error_print(f"ERROR: Failed to deploy MongoDB Database: {e}")
            return False
    
    def deploy_webui(self):
        """Deploy WebUI and return success status."""
        self.deployWebUI()
        # Give it some time to start
        time.sleep(3)
        return self.is_webui_running()

    def deploy_database_sync(self):
        """Deploy MongoDB database synchronously for automation."""
        debug_print("DEBUG: deploy_database_sync called")
        try:
            # Use fixed service names instead of file-based naming
            container_name = "netflux5g-mongodb"
            volume_name = "netflux5g-mongodb-data"
            
            # Check if Docker is available
            if not self._check_docker_available():
                error_print("Docker is not available")
                return False
            
            # Ensure netflux5g network exists
            if hasattr(self.main_window, 'docker_network_manager'):
                if not self.main_window.docker_network_manager._network_exists("netflux5g"):
                    debug_print("Creating netflux5g network")
                    if not self.main_window.docker_network_manager._create_network("netflux5g"):
                        error_print("Failed to create netflux5g network")
                        return False
            
            # Check if already running
            if self._is_container_running(container_name):
                debug_print(f"Database container '{container_name}' is already running")
                return True
            
            # Deploy directly without user prompts for automation
            debug_print(f"Deploying MongoDB container: {container_name}")
            return self._deploy_database_direct(container_name, volume_name, "netflux5g")
            
        except Exception as e:
            error_print(f"ERROR: Failed to deploy MongoDB Database: {e}")
            return False
    
    def deploy_webui_sync(self):
        """Deploy WebUI synchronously for automation."""
        debug_print("DEBUG: deploy_webui_sync called")
        try:
            # Use fixed service names
            container_name = "netflux5g-webui"
            
            # Check if Docker is available
            if not self._check_docker_available():
                error_print("Docker is not available")
                return False
            
            # Ensure netflux5g network exists
            if hasattr(self.main_window, 'docker_network_manager'):
                if not self.main_window.docker_network_manager._network_exists("netflux5g"):
                    debug_print("Creating netflux5g network")
                    if not self.main_window.docker_network_manager._create_network("netflux5g"):
                        error_print("Failed to create netflux5g network")
                        return False
            
            # Check if already running
            if self._is_container_running(container_name):
                debug_print(f"WebUI container '{container_name}' is already running")
                return True
            
            # Deploy directly without user prompts for automation
            debug_print(f"Deploying WebUI container: {container_name}")
            return self._deploy_webui_direct(container_name, "netflux5g")
            
        except Exception as e:
            error_print(f"ERROR: Failed to deploy WebUI: {e}")
            return False

    def _deploy_database_direct(self, container_name, volume_name, network_name):
        """Deploy MongoDB container directly without threads."""
        try:
            # Create volume if it doesn't exist
            if not self._volume_exists(volume_name):
                debug_print(f"Creating volume: {volume_name}")
                volume_cmd = ['docker', 'volume', 'create', volume_name]
                result = subprocess.run(volume_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    error_print(f"Failed to create volume: {result.stderr}")
                    return False
            
            # Remove existing container if it exists but is not running
            if self._container_exists(container_name) and not self._is_container_running(container_name):
                debug_print(f"Removing existing stopped container: {container_name}")
                remove_cmd = ['docker', 'rm', container_name]
                subprocess.run(remove_cmd, capture_output=True, timeout=10)
            
            # Create and run MongoDB container
            debug_print(f"Creating MongoDB container: {container_name}")
            run_cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', network_name,
                '-p', '27017:27017',
                '-v', f'{volume_name}:/data/db',
                '-e', 'MONGO_INITDB_DATABASE=open5gs',
                'mongo:latest'
            ]
            
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                error_print(f"Failed to create MongoDB container: {result.stderr}")
                return False
            
            # Wait for container to be ready
            debug_print("Waiting for MongoDB to be ready...")
            for i in range(30):  # Wait up to 30 seconds
                if self._is_container_running(container_name):
                    # Test connection
                    test_cmd = ['docker', 'exec', container_name, 'mongosh', '--eval', 'db.runCommand("ping")']
                    test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                    if test_result.returncode == 0:
                        debug_print("MongoDB is ready")
                        return True
                time.sleep(1)
            
            error_print("MongoDB container started but failed to become ready")
            return False
            
        except Exception as e:
            error_print(f"Failed to deploy MongoDB directly: {e}")
            return False

    def _deploy_webui_direct(self, container_name, network_name):
        """Deploy WebUI container directly without threads."""
        try:
            # Remove existing container if it exists but is not running
            if self._container_exists(container_name) and not self._is_container_running(container_name):
                debug_print(f"Removing existing stopped container: {container_name}")
                remove_cmd = ['docker', 'rm', container_name]
                subprocess.run(remove_cmd, capture_output=True, timeout=10)
            
            # Create and run WebUI container
            debug_print(f"Creating WebUI container: {container_name}")
            run_cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', network_name,
                '-p', '9999:9999',
                '-e', 'DB_URI=mongodb://netflux5g-mongodb:27017/open5gs',
                'gradiant/open5gs-webui:2.7.5'
            ]
            
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                error_print(f"Failed to create WebUI container: {result.stderr}")
                return False
            
            # Wait for container to be ready
            debug_print("Waiting for WebUI to be ready...")
            for i in range(20):  # Wait up to 20 seconds
                if self._is_container_running(container_name):
                    debug_print("WebUI is ready")
                    return True
                time.sleep(1)
            
            error_print("WebUI container started but failed to become ready")
            return False
            
        except Exception as e:
            error_print(f"Failed to deploy WebUI directly: {e}")
            return False

    def _check_file_saved(self):
        """Check if the current file is saved."""
        if not hasattr(self.main_window, 'current_file') or not self.main_window.current_file:
            reply = QMessageBox.warning(
                self.main_window,
                "File Not Saved",
                "The current file must be saved before deploying the database.\n\n"
                "The container name will be based on the filename.\n\n"
                "Do you want to save the file now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                if hasattr(self.main_window, 'file_manager'):
                    self.main_window.file_manager.saveTopologyAs()
                    # Check again if file was saved
                    return hasattr(self.main_window, 'current_file') and self.main_window.current_file
                else:
                    QMessageBox.critical(
                        self.main_window,
                        "Error",
                        "File manager not available. Please save the file manually."
                    )
            
            return False
        
        return True
    
    def _get_container_names(self):
        """Get container and volume names from current file."""
        if not hasattr(self.main_window, 'current_file') or not self.main_window.current_file:
            return None, None
        
        # Get filename without extension
        filename = os.path.basename(self.main_window.current_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Clean name for Docker (remove invalid characters)
        clean_name = "".join(c for c in name_without_ext if c.isalnum() or c in '-_').lower()
        
        if not clean_name:
            clean_name = "netflux5g_topology"
        
        container_name = f"mongo_{clean_name}"
        volume_name = f"mongo_data_{clean_name}"
        
        return container_name, volume_name
    
    def _check_docker_available(self):
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ['docker', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, 'docker --version')
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            QMessageBox.critical(
                self.main_window,
                "Docker Not Available",
                "Docker is not installed or not accessible.\n\n"
                "Please install Docker and ensure it's running:\n"
                "https://docs.docker.com/desktop/setup/install/linux/"
            )
            return False
    
    def _is_container_running(self, container_name):
        """Check if container is currently running."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return container_name in result.stdout
        except:
            return False
    
    def _container_exists(self, container_name):
        """Check if container exists (running or stopped)."""
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return container_name in result.stdout
        except:
            return False
    
    def _volume_exists(self, volume_name):
        """Check if Docker volume exists."""
        try:
            result = subprocess.run(
                ['docker', 'volume', 'ls', '--filter', f'name={volume_name}', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return volume_name in result.stdout
        except:
            return False
    
    def _get_docker_network_name(self):
        """Get the Docker network name for the current topology."""
        if hasattr(self.main_window, 'docker_network_manager'):
            return self.main_window.docker_network_manager.get_current_network_name()
        return None
    
    def _network_exists(self, network_name):
        """Check if Docker network exists."""
        if not network_name:
            return False
        
        try:
            result = subprocess.run(
                ['docker', 'network', 'ls', '--filter', f'name={network_name}', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return network_name in result.stdout
        except:
            return False
    
    def _stop_container_sync(self, container_name):
        """Stop container synchronously (for restart scenarios)."""
        try:
            subprocess.run(['docker', 'stop', container_name], timeout=30)
            subprocess.run(['docker', 'rm', container_name], timeout=10)
        except:
            pass  # Ignore errors for restart scenario
    
    def _start_operation(self, operation, container_name, volume_name=None, network_name=None):
        """Start database operation in worker thread."""
        # Create progress dialog
        operation_text = "Deploying" if operation == 'deploy' else "Stopping" if operation == 'stop' else "Cleaning up"
        self.progress_dialog = QProgressDialog(
            f"{operation_text} database...",
            "Cancel",
            0,
            100,
            self.main_window
        )
        self.progress_dialog.setWindowTitle(f"Database {operation_text}")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self._cancel_operation)
        self.progress_dialog.show()
        
        # Create and start worker
        self.current_worker = DatabaseDeploymentWorker(operation, container_name, volume_name, network_name)
        self.current_worker.progress_updated.connect(self.progress_dialog.setValue)
        self.current_worker.status_updated.connect(self._update_progress_text)
        self.current_worker.operation_finished.connect(self._on_operation_finished)
        self.current_worker.start()
    
    def _update_progress_text(self, status):
        """Update progress dialog text."""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(status)
    
    def _cancel_operation(self):
        """Cancel the current operation."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait(3000)  # Wait up to 3 seconds
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.main_window.status_manager.showCanvasStatus("Database operation cancelled")
    
    def _on_operation_finished(self, success, message):
        """Handle operation completion."""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        if success:
            QMessageBox.information(
                self.main_window,
                "Success",
                message
            )
            self.main_window.status_manager.showCanvasStatus(message)
        else:
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"Database operation failed:\n{message}"
            )
            self.main_window.status_manager.showCanvasStatus(f"Database operation failed: {message}")
        
        # Cleanup
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
    
    def getContainerStatus(self):
        """Get the status of the database container."""
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-mongodb"
        volume_name = "netflux5g-mongodb-data"
        
        try:
            # Check if container exists and is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Check if volume exists
            volume_exists = self._volume_exists(volume_name)
            volume_status = " (with data)" if volume_exists else " (no data)"
            
            if result.stdout.strip():
                return f"Running: {container_name}{volume_status}"
            
            # Check if container exists but is stopped
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                return f"Stopped: {container_name}{volume_status}"
            
            return f"Not deployed: {container_name}{volume_status}"
            
        except:
            return "Docker not available"
    
    def getWebUIStatus(self):
        """Get the status of the Web UI container."""
        # Use fixed service names instead of file-based naming
        container_name = "netflux5g-webui"
        
        try:
            # Check if container exists and is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                return f"Running: {container_name}"
            
            # Check if container exists but is stopped
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                return f"Stopped: {container_name}"
            
            return f"Not deployed: {container_name}"
            
        except:
            return "Docker not available"
