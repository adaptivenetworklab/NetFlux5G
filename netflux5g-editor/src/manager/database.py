"""
Database deployment manager for NetFlux5G Editor
Handles MongoDB container creation and removal based on webui-db.yaml configuration
"""

import os
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import pyqtSignal, QThread, QMutex
from utils.debug import debug_print, error_print, warning_print
from utils.docker_utils import DockerUtils, DockerContainerBuilder

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
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True
        
    def run(self):
        """Execute the database operation in background thread."""
        try:
            if self._cancel_requested:
                self.operation_finished.emit(False, "Operation canceled.")
                return
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
        """Deploy MongoDB container with DockerUtils and DockerContainerBuilder."""
        try:
            self.status_updated.emit("Checking if MongoDB image exists...")
            self.progress_updated.emit(10)
            image_name = "mongo:latest"
            if not DockerUtils.image_exists(image_name):
                self.status_updated.emit("Pulling MongoDB image...")
                self.progress_updated.emit(40)
                DockerUtils.pull_image(image_name)
            builder = DockerContainerBuilder(image=image_name, container_name=self.container_name)
            builder.set_network(self.network_name)
            # Add volumes, ports as needed
            builder.add_volume(f'{self.volume_name}:/data/db')
            builder.add_env('MONGO_INITDB_DATABASE=open5gs')
            self.status_updated.emit("Creating MongoDB container...")
            self.progress_updated.emit(70)
            builder.run()
            self.operation_finished.emit(True, f"MongoDB container '{self.container_name}' deployed successfully.")
        except Exception as e:
            error_print(f"Failed to deploy MongoDB: {e}")
            self.operation_finished.emit(False, str(e))

    def _stop_database(self):
        """Stop MongoDB container using DockerUtils."""
        try:
            self.status_updated.emit("Stopping MongoDB container...")
            self.progress_updated.emit(50)
            DockerUtils.stop_container(self.container_name)
            self.operation_finished.emit(True, f"MongoDB container '{self.container_name}' stopped successfully.")
        except Exception as e:
            error_print(f"Failed to stop MongoDB: {e}")
            self.operation_finished.emit(False, str(e))
    
    def _cleanup_database(self):
        """Completely remove MongoDB container and volume using DockerUtils."""
        try:
            self.status_updated.emit("Starting complete cleanup...")
            self.progress_updated.emit(10)
            if DockerUtils.container_exists(self.container_name):
                self.status_updated.emit("Stopping container...")
                self.progress_updated.emit(30)
                DockerUtils.stop_container(self.container_name)
                self.status_updated.emit("Removing container...")
                self.progress_updated.emit(50)
                DockerUtils.stop_container(self.container_name)
            if self.volume_name and DockerUtils.volume_exists(self.volume_name):
                self.status_updated.emit("Removing volume and all data...")
                self.progress_updated.emit(70)
                DockerUtils.remove_volume(self.volume_name)
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Complete cleanup finished: container and volume removed")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error during cleanup: {str(e)}")

    def _deploy_webui(self):
        """Deploy Web UI container using DockerUtils and DockerContainerBuilder."""
        try:
            self.status_updated.emit("Checking if Web UI container already exists...")
            self.progress_updated.emit(10)
            if DockerUtils.container_exists(self.container_name):
                if DockerUtils.is_container_running(self.container_name):
                    self.operation_finished.emit(True, f"Web UI container '{self.container_name}' is already running")
                    return
                else:
                    self.status_updated.emit("Starting existing Web UI container...")
                    self.progress_updated.emit(50)
                    DockerUtils.start_container(self.container_name)
                    self.progress_updated.emit(100)
                    self.operation_finished.emit(True, f"Web UI container '{self.container_name}' started successfully")
                    return
            self.status_updated.emit("Checking Web UI image...")
            self.progress_updated.emit(30)
            webui_image = 'gradiant/open5gs-webui:2.7.5'
            if not DockerUtils.image_exists(webui_image):
                self.status_updated.emit("Pulling Web UI image...")
                self.progress_updated.emit(35)
                DockerUtils.pull_image(webui_image, timeout=120)
            self.progress_updated.emit(50)
            self.status_updated.emit("Creating Web UI container...")
            self.progress_updated.emit(60)
            mongo_container_name = "netflux5g-mongodb"
            builder = DockerContainerBuilder(image=webui_image, container_name=self.container_name)
            builder.set_network(self.network_name)
            builder.add_port('9999:9999')
            builder.add_env(f'DB_URI=mongodb://{mongo_container_name}:27017/open5gs')
            builder.add_env('NODE_ENV=dev')
            builder.run()
            self.status_updated.emit("Waiting for Web UI to be ready...")
            self.progress_updated.emit(80)
            for i in range(10):
                if DockerUtils.is_container_running(self.container_name):
                    break
                time.sleep(1)
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, f"Web UI container '{self.container_name}' deployed successfully")
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
            self.stopDatabase()

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
        
        container_name = "netflux5g-mongodb"
        volume_name = "netflux5g-mongodb-data"
        
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
                # Start MongoDB container using DockerUtils
                try:
                    success, msg = DockerUtils.start_container(mongo_container_name)
                    if success:
                        self.main_window.status_manager.showCanvasStatus(f"Started MongoDB container: {mongo_container_name}")
                    else:
                        QMessageBox.critical(
                            self.main_window,
                            "Failed to Start MongoDB",
                            f"Could not start MongoDB container: {msg}"
                        )
                        return
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
            self.stopDatabase()
        
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

    def getContainerStatus(self):
        """Get the status of the database container using DockerUtils."""
        container_name = "netflux5g-mongodb"
        volume_name = "netflux5g-mongodb-data"
        try:
            # Check if container exists and is running
            if DockerUtils.is_container_running(container_name):
                volume_exists = self._volume_exists(volume_name)
                volume_status = " (with data)" if volume_exists else " (no data)"
                return f"Running: {container_name}{volume_status}"
            # Check if container exists but is stopped
            elif DockerUtils.container_exists(container_name):
                volume_exists = self._volume_exists(volume_name)
                volume_status = " (with data)" if volume_exists else " (no data)"
                return f"Stopped: {container_name}{volume_status}"
            else:
                volume_exists = self._volume_exists(volume_name)
                volume_status = " (with data)" if volume_exists else " (no data)"
                return f"Not deployed: {container_name}{volume_status}"
        except Exception:
            return "Docker not available"

    def getWebUIStatus(self):
        """Get the status of the Web UI container using DockerUtils."""
        container_name = "netflux5g-webui"
        try:
            if DockerUtils.is_container_running(container_name):
                return f"Running: {container_name}"
            elif DockerUtils.container_exists(container_name):
                return f"Stopped: {container_name}"
            else:
                return f"Not deployed: {container_name}"
        except Exception:
            return "Docker not available"
    
    def _check_docker_available(self):
        """Check if Docker is available using DockerUtils."""
        return DockerUtils.check_docker_available(self.main_window, show_error=True)
    
    def _is_container_running(self, container_name):
        """Check if container is currently running using DockerUtils."""
        return DockerUtils.is_container_running(container_name)
    
    def _container_exists(self, container_name):
        """Check if container exists (running or stopped) using DockerUtils."""
        return DockerUtils.container_exists(container_name)

    def _volume_exists(self, volume_name):
        """Check if Docker volume exists using DockerUtils."""
        return DockerUtils.volume_exists(volume_name)
    
    def _start_operation(self, operation, container_name, volume_name=None, network_name=None):
        """Start database operation in worker thread."""
        # Create progress dialog
        operation_text = (
            "Deploying" if operation == 'deploy' else
            "Stopping" if operation == 'stop' else
            "Cleaning up" if operation == 'cleanup' else
            "Deploying WebUI" if operation == 'deploy_webui' else
            "Stopping WebUI" if operation == 'stop_webui' else
            "Cleaning up WebUI" if operation == 'cleanup_webui' else
            "Working"
        )
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
        """Cancel the current operation safely."""
        if self.current_worker:
            self.current_worker.request_cancel()
            self.current_worker.wait(3000)  # Wait up to 3 seconds for graceful exit
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
