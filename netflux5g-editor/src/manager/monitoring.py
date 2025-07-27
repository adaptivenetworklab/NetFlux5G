"""
Monitoring deployment manager for NetFlux5G Editor
Handles Prometheus, Grafana, and other monitoring container creation and removal using DockerUtils and DockerContainerBuilder
"""

import os
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import pyqtSignal, QThread, QMutex
from utils.debug import debug_print, error_print, warning_print
from utils.docker_utils import DockerUtils, DockerContainerBuilder

cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MonitoringDeploymentWorker(QThread):
    """Worker thread for monitoring operations to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation, container_prefix=None, network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy', 'stop', or 'cleanup'
        self.container_prefix = "netflux5g"  # Fixed prefix for all deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        try:
            if self.operation == 'deploy':
                self._deploy_monitoring()
            elif self.operation == 'stop':
                self._stop_monitoring()
            elif self.operation == 'cleanup':
                self._cleanup_monitoring()
        except Exception as e:
            error_print(f"Monitoring operation failed: {e}")
            self.operation_finished.emit(False, str(e))

    monitoring_containers = {
        'prometheus': {
            'image': 'prom/prometheus',
            'ports': ['9090:9090'],
            'volumes': [
                cwd + '/automation/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml'
            ]
        },
        'grafana': {
            'image': 'grafana/grafana',
            'ports': ['3000:3000'],
            'volumes': [
                cwd + '/automation/monitoring/grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml',
                cwd + '/automation/monitoring/grafana/dashboard.json:/var/lib/grafana/dashboards/dashboard.json',
                cwd + '/automation/monitoring/grafana/default.yaml:/etc/grafana/provisioning/dashboards/default.yaml'
            ],
            'env': [
                'GF_PATHS_PROVISIONING=/etc/grafana/provisioning',
                'DS_PROMETHEUS=prometheus'
            ]
        },
        'node-exporter': {
            'image': 'prom/node-exporter',
            'ports': [],
            'volumes': ['/:/host:ro,rslave'],
            'extra_args': ['--path.rootfs=/host'],
            'pid_mode': 'host'
        },
        'cadvisor': {
            'image': 'gcr.io/cadvisor/cadvisor:latest',
            'ports': ['8080:8080'],
            'volumes': [
                '/:/rootfs:ro',
                '/var/run:/var/run:ro', 
                '/sys:/sys:ro',
                '/var/lib/docker/:/var/lib/docker:ro',
                '/dev/disk/:/dev/disk:ro'
            ]
        }
    }

    def _deploy_monitoring(self):
        try:
            self.status_updated.emit("Starting monitoring deployment...")
            self.progress_updated.emit(10)
            total_containers = len(self.monitoring_containers)
            progress_step = 80 // total_containers
            current_progress = 10
            for container_name, config in self.monitoring_containers.items():
                full_container_name = f"{self.container_prefix}-{container_name}"
                
                self.progress_updated.emit(current_progress)
                self.status_updated.emit(f"Checking if {container_name} container exists...")
                if DockerUtils.container_exists(full_container_name):
                    continue
                if not DockerUtils.image_exists(config['image']):
                    self.progress_updated.emit(current_progress)
                    self.status_updated.emit(f"Docker Image doesn't exist. Pulling image {config['image']}...")
                    DockerUtils.pull_image(config['image'])
                builder = DockerContainerBuilder(image=config['image'], container_name=full_container_name)
                builder.set_network(self.network_name)
                for port in config.get('ports', []):
                    builder.add_port(port)
                for volume in config.get('volumes', []):
                    builder.add_volume(volume)
                for env in config.get('env', []):
                    builder.add_env(env)
                # Ensure --pid=host is added as an extra arg if pid_mode is present
                if 'pid_mode' in config and config['pid_mode']:
                    builder.add_extra_arg(f'--pid={config["pid_mode"]}')
                # For node-exporter, pass --path.rootfs=/host as a command arg, not extra arg
                if container_name == 'node-exporter':
                    for arg in config.get('extra_args', []):
                        builder.add_command_arg(arg)
                else:
                    for arg in config.get('extra_args', []):
                        builder.add_extra_arg(arg)
                self.status_updated.emit(f"Deploying {container_name}...")
                builder.run()
                current_progress += progress_step
            self.status_updated.emit("Waiting for containers to be ready...")
            self.progress_updated.emit(90)
            time.sleep(3)
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, 
                f"Monitoring stack deployed successfully!\n"
                f"• Grafana: http://localhost:3000 (admin/admin)\n"
                f"• Prometheus: http://localhost:9090\n"
                f"• cAdvisor: http://localhost:8080")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")

    def _stop_monitoring(self):
        try:
            for container_name in self.monitoring_containers:
                full_container_name = f"{self.container_prefix}-{container_name}"
                total_containers = len(self.monitoring_containers)
                progress_step = 80 // total_containers
                current_progress = 10 + (progress_step * list(self.monitoring_containers.keys()).index(container_name))
                self.progress_updated.emit(current_progress)
                DockerUtils.stop_container(full_container_name)
            self.operation_finished.emit(True, "All monitoring containers stopped successfully.")
        except Exception as e:
            error_print(f"Failed to stop monitoring: {e}")
            self.operation_finished.emit(False, str(e))

    def _cleanup_monitoring(self):
        try:
            for container_name in self.monitoring_containers:
                full_container_name = f"{self.container_prefix}-{container_name}"
                DockerUtils.stop_container(full_container_name)
                if DockerUtils.container_exists(full_container_name):
                    DockerUtils.stop_container(full_container_name)
            self.operation_finished.emit(True, "Monitoring stack completely removed")
        except Exception as e:
            self.operation_finished.emit(False, f"Cleanup failed: {str(e)}")

class MonitoringManager:
    """Manager for monitoring deployment operations."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_worker = None
        self.progress_dialog = None
        
    def deployMonitoring(self):
        container_prefix = "netflux5g"
        if not self._check_docker_available():
            return
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                self.main_window.status_manager.showCanvasStatus("Monitoring deployment cancelled - netflux5g network required")
                return
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        running_containers = self._get_running_monitoring_containers(container_prefix)
        if running_containers:
            reply = QMessageBox.question(
                self.main_window,
                "Monitoring Already Running",
                f"Some monitoring containers are already running:\n{', '.join(running_containers)}\n\n"
                f"Do you want to restart the monitoring stack?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            self._stop_containers_sync(container_prefix)
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Monitoring Stack",
            f"This will deploy the comprehensive monitoring stack using Docker\n\n"
            f"📊 Services to be deployed:\n"
            f"• Prometheus (metrics collection) - port 9090\n"
            f"• Grafana (visualization) - port 3000\n" 
            f"• Node Exporter (system metrics) - port 9100\n"
            f"• cAdvisor (container metrics) - port 8080\n\n"
            f"🔧 Features included:\n"
            f"• Enhanced dashboard with 5G Core monitoring\n"
            f"• Near Real-time UE status tracking\n"
            f"• Container auto-discovery\n\n"
            f"🌐 Access URLs after deployment:\n"
            f"• Grafana: http://localhost:3000 (admin/admin)\n"
            f"• Prometheus: http://localhost:9090\n\n"
            f"Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.No:
            return
        self._start_operation('deploy', container_prefix, "netflux5g")
    
    def stopMonitoring(self):
        debug_print("Stop Monitoring triggered")
        container_prefix = "netflux5g"
        if not self._check_docker_available():
            return
        existing_containers = self._get_existing_monitoring_containers(container_prefix)
        if not existing_containers:
            QMessageBox.information(
                self.main_window,
                "No Monitoring Containers",
                f"No monitoring containers found with prefix '{container_prefix}'."
            )
            return
        reply = QMessageBox.question(
            self.main_window,
            "Stop Monitoring Stack",
            f"This will stop and remove monitoring containers:\n"
            f"• Found containers: {', '.join(existing_containers)}\n\n"
            f"The containers will be stopped but no data will be lost.\n\n"
            f"Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self._start_operation('stop', container_prefix, None)

    def _check_docker_available(self):
        return DockerUtils.check_docker_available(self.main_window, show_error=True)
    
    def _get_running_monitoring_containers(self, container_prefix):
        running_containers = []
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor']
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}-{monitoring_type}"
            if DockerUtils.is_container_running(container_name):
                running_containers.append(monitoring_type)
        return running_containers

    def _get_existing_monitoring_containers(self, container_prefix):
        existing_containers = []
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor']
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}-{monitoring_type}"
            if DockerUtils.container_exists(container_name):
                existing_containers.append(monitoring_type)
        return existing_containers
    
    def _stop_containers_sync(self, container_prefix):
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor']
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}-{monitoring_type}"
            try:
                DockerUtils.stop_container(container_name)
                DockerUtils.stop_container(container_name)
            except Exception:
                pass

    def _start_operation(self, operation, container_prefix, network_name):
        """Start a MonitoringDeploymentWorker thread for the given operation, with progress dialog."""
        if self.current_worker is not None and self.current_worker.isRunning():
            warning_print("A monitoring operation is already in progress.")
            return
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Monitoring operation in progress...",
            "Cancel",
            0,
            100,
            self.main_window
        )
        self.progress_dialog.setWindowTitle("Monitoring Operation")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        self.current_worker = MonitoringDeploymentWorker(operation, container_prefix, network_name)
        self.current_worker.progress_updated.connect(self._on_progress_updated)
        self.current_worker.status_updated.connect(self._on_status_updated)
        self.current_worker.operation_finished.connect(self._on_operation_finished)
        self.progress_dialog.canceled.connect(self._on_operation_canceled)
        self.current_worker.start()

    def _on_operation_canceled(self):
        if self.current_worker:
            # If you add cancellation logic to MonitoringDeploymentWorker, call it here
            self.current_worker.terminate()
            self.current_worker.wait(3000)
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

    def _on_progress_updated(self, value):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def _on_status_updated(self, status):
        if self.progress_dialog:
            self.progress_dialog.setLabelText(status)

    def _on_operation_finished(self, success, message):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        if success:
            QMessageBox.information(self.main_window, "Monitoring Operation Complete", message)
        else:
            QMessageBox.critical(self.main_window, "Monitoring Operation Failed", message)