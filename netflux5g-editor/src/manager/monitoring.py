"""
Monitoring deployment manager for NetFlux5G Editor
Handles Prometheus, Grafana, and other monitoring container creation and removal using individual Docker commands
"""

import os
import subprocess
import time
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread, QMutex
from manager.debug import debug_print, error_print, warning_print

cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class MonitoringDeploymentWorker(QThread):
    """Worker thread for monitoring operations to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation, container_prefix=None, network_name=None):
        super().__init__()
        self.operation = operation  # 'deploy', 'stop', or 'cleanup'
        # Use simple service-based names instead of file-based names
        self.container_prefix = "netflux5g"  # Fixed prefix for all deployments
        # Use netflux5g network for service deployments
        self.network_name = "netflux5g"
        self.mutex = QMutex()
        
    def run(self):
        """Execute the monitoring operation in background thread."""
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
    
    def _deploy_monitoring(self):
        """Deploy all monitoring containers using individual Docker commands."""
        try:
            total_containers = len(self.monitoring_containers)
            progress_step = 80 // total_containers
            current_progress = 10
            
            # Deploy each container
            for container_name, config in self.monitoring_containers.items():
                full_container_name = f"{self.container_prefix}_{container_name}"
                
                self.status_updated.emit(f"Deploying {container_name}...")
                self.progress_updated.emit(current_progress)
                
                # Check if container already exists
                if self._container_exists(full_container_name):
                    if self._is_container_running(full_container_name):
                        debug_print(f"{full_container_name} is already running")
                        current_progress += progress_step
                        continue
                    else:
                        # Start existing container
                        subprocess.run(['docker', 'start', full_container_name], 
                                     check=True, timeout=30)
                        current_progress += progress_step
                        continue
                
                # Create new container
                self._create_container(container_name, config, full_container_name)
                
                current_progress += progress_step
                
            self.status_updated.emit("Waiting for containers to be ready...")
            self.progress_updated.emit(90)
            
            # Wait for containers to be healthy
            time.sleep(3)
            
            self.progress_updated.emit(100)
            self.operation_finished.emit(True, 
                f"Monitoring stack deployed successfully!\n"
                f"• Grafana: http://localhost:3000 (admin/admin)\n"
                f"• Prometheus: http://localhost:9090\n"
                f"• cAdvisor: http://localhost:8080\n"
                f"• Blackbox Exporter: http://localhost:9115")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Monitoring deployment timed out")
        except subprocess.CalledProcessError as e:
            self.operation_finished.emit(False, f"Docker command failed: {e.stderr}")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")
    
    # Define monitoring containers configuration
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
                # 'grafana-data:/var/lib/grafana',
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
        },
        'blackbox-exporter': {
            'image': 'prom/blackbox-exporter',
            'ports': ['9115:9115'],
            'volumes': []
        }
    }
    
    def _create_container(self, container_name, config, full_container_name):
        """Create a single monitoring container."""
        run_cmd = [
            'docker', 'run', '-d',
            '--name', full_container_name,
            '--restart', 'unless-stopped',
            '--network', self.network_name
        ]
        
        # Add port mappings
        for port in config.get('ports', []):
            run_cmd.extend(['-p', port])
        
        # Add volume mounts
        for volume in config.get('volumes', []):
            run_cmd.extend(['-v', volume])
        
        # Add environment variables
        for env_var in config.get('env', []):
            run_cmd.extend(['-e', env_var])
        
        # Add special configurations
        if 'pid_mode' in config:
            run_cmd.extend(['--pid', config['pid_mode']])
        
        # Add the image
        run_cmd.append(config['image'])
        
        # Add extra arguments
        if 'extra_args' in config:
            run_cmd.extend(config['extra_args'])
        
        # Execute the command
        result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, run_cmd, result.stderr)
        
        debug_print(f"Created container: {full_container_name}")
    
    def _stop_monitoring(self):
        """Stop all monitoring containers."""
        try:
            containers = list(self.monitoring_containers.keys())
            total_containers = len(containers)
            progress_step = 80 // total_containers if total_containers > 0 else 80
            current_progress = 10
            
            self.status_updated.emit("Stopping monitoring containers...")
            self.progress_updated.emit(current_progress)
            
            stopped_containers = []
            
            for container_name in containers:
                full_container_name = f"{self.container_prefix}_{container_name}"
                
                self.status_updated.emit(f"Stopping {container_name}...")
                self.progress_updated.emit(current_progress)
                
                if self._container_exists(full_container_name):
                    try:
                        # Stop container
                        subprocess.run(['docker', 'stop', full_container_name], 
                                     capture_output=True, text=True, timeout=30)
                        # Remove container
                        subprocess.run(['docker', 'rm', full_container_name], 
                                     capture_output=True, text=True, timeout=10)
                        stopped_containers.append(container_name)
                        debug_print(f"Stopped and removed: {full_container_name}")
                    except subprocess.CalledProcessError as e:
                        warning_print(f"Could not stop {full_container_name}: {e}")
                
                current_progress += progress_step
            
            self.progress_updated.emit(100)
            
            if stopped_containers:
                self.operation_finished.emit(True, f"Monitoring containers stopped: {', '.join(stopped_containers)}")
            else:
                self.operation_finished.emit(True, "No monitoring containers were running")
            
        except subprocess.TimeoutExpired:
            self.operation_finished.emit(False, "Monitoring stop operation timed out")
        except Exception as e:
            self.operation_finished.emit(False, f"Unexpected error: {str(e)}")
    
    def _cleanup_monitoring(self):
        """Completely remove all monitoring containers."""
        try:
            self._stop_monitoring()
            
            # Note: We don't remove the netflux5g network since it's shared by other services
            
            self.operation_finished.emit(True, "Monitoring stack completely removed")
            
        except Exception as e:
            self.operation_finished.emit(False, f"Cleanup failed: {str(e)}")
    
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


class MonitoringManager:
    """Manager for monitoring deployment operations."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_worker = None
        self.progress_dialog = None
        
    def deployMonitoring(self):
        """Deploy monitoring stack (Prometheus, Grafana, etc.)."""
        debug_print("Deploy Monitoring triggered", force=True)
        
        # Use fixed service name instead of file-based naming
        container_prefix = "netflux5g"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if netflux5g network exists, prompt to create if not
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.prompt_create_netflux5g_network():
                self.main_window.status_manager.showCanvasStatus("Monitoring deployment cancelled - netflux5g network required")
                return
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        
        # Check if any monitoring containers are already running
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
            
            # Stop existing containers first
            self._stop_containers_sync(container_prefix)
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Deploy Monitoring Stack",
            f"This will deploy the comprehensive monitoring stack using Docker :\n\n"
            f"📊 Services to be deployed:\n"
            f"• Prometheus (metrics collection) - port 9090\n"
            f"• Grafana (visualization) - port 3000\n" 
            f"• Node Exporter (system metrics) - port 9100\n"
            f"• cAdvisor (container metrics) - port 8080\n"
            f"• Blackbox Exporter (connectivity) - port 9115\n\n"
            f"🔧 Features included:\n"
            f"• Enhanced dashboard with 5G Core monitoring\n"
            f"• Real-time UE status tracking\n"
            f"• Container auto-discovery\n"
            f"🌐 Access URLs after deployment:\n"
            f"• Grafana: http://localhost:3000 (admin/admin)\n"
            f"• Prometheus: http://localhost:9090\n"
            f"Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start deployment with netflux5g network
        self._start_operation('deploy', container_prefix, "netflux5g")
    
    def stopMonitoring(self):
        """Stop and remove monitoring stack."""
        debug_print("Stop Monitoring triggered")
        
        # Use fixed service name instead of file-based naming
        container_prefix = "netflux5g"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return
        
        # Check if any monitoring containers exist
        existing_containers = self._get_existing_monitoring_containers(container_prefix)
        if not existing_containers:
            QMessageBox.information(
                self.main_window,
                "No Monitoring Containers",
                f"No monitoring containers found with prefix '{container_prefix}'."
            )
            return
        
        # Show confirmation dialog
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
        
        # Start stop operation
        self._start_operation('stop', container_prefix, None)
    
    def deploy_monitoring_sync(self):
        """Deploy monitoring stack synchronously for automation."""
        debug_print("Deploy Monitoring synchronously triggered")
        
        # Use fixed service name instead of file-based naming
        container_prefix = "netflux5g"
        network_name = "netflux5g"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return False, "Docker not available"
        
        # Check if netflux5g network exists, create if not
        if hasattr(self.main_window, 'docker_network_manager'):
            if not self.main_window.docker_network_manager.ensure_netflux5g_network():
                return False, "Could not create netflux5g network"
        else:
            warning_print("Docker network manager not available, proceeding without network check")
        
        # Check if any monitoring containers are already running
        running_containers = self._get_running_monitoring_containers(container_prefix)
        if running_containers:
            debug_print(f"Some monitoring containers already running: {running_containers}")
            # Stop existing containers first
            self._stop_containers_sync(container_prefix)
        
        try:
            # Deploy monitoring containers directly
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
                },
                'blackbox-exporter': {
                    'image': 'prom/blackbox-exporter',
                    'ports': ['9115:9115'],
                    'volumes': []
                }
            }
            
            # Deploy each container
            for container_name, config in monitoring_containers.items():
                full_container_name = f"{container_prefix}_{container_name}"
                
                debug_print(f"Deploying monitoring container: {container_name}")
                
                # Check if container already exists
                if self._container_exists(full_container_name):
                    if self._is_container_running(full_container_name):
                        debug_print(f"{full_container_name} is already running")
                        continue
                    else:
                        # Start existing container
                        result = subprocess.run(['docker', 'start', full_container_name], 
                                              capture_output=True, text=True, timeout=30)
                        if result.returncode != 0:
                            debug_print(f"Failed to start existing container {full_container_name}: {result.stderr}")
                            return False, f"Failed to start {container_name}: {result.stderr}"
                        continue
                
                # Create new container
                success, error = self._create_container_sync(container_name, config, full_container_name, network_name)
                if not success:
                    return False, f"Failed to create {container_name}: {error}"
            
            # Wait for containers to be ready
            time.sleep(3)
            
            debug_print("Monitoring stack deployed successfully")
            return True, "Monitoring stack deployed successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Monitoring deployment timed out"
        except subprocess.CalledProcessError as e:
            return False, f"Docker command failed: {e.stderr}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _create_container_sync(self, container_name, config, full_container_name, network_name):
        """Create a single monitoring container synchronously."""
        try:
            run_cmd = [
                'docker', 'run', '-d',
                '--name', full_container_name,
                '--restart', 'unless-stopped',
                '--network', network_name
            ]
            
            # Add port mappings
            for port in config.get('ports', []):
                run_cmd.extend(['-p', port])
            
            # Add volume mounts
            for volume in config.get('volumes', []):
                run_cmd.extend(['-v', volume])
            
            # Add environment variables
            for env_var in config.get('env', []):
                run_cmd.extend(['-e', env_var])
            
            # Add special configurations
            if 'pid_mode' in config:
                run_cmd.extend(['--pid', config['pid_mode']])
            
            # Add the image
            run_cmd.append(config['image'])
            
            # Add extra arguments
            if 'extra_args' in config:
                run_cmd.extend(config['extra_args'])
            
            # Execute the command
            result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return False, result.stderr
            
            debug_print(f"Created container: {full_container_name}")
            return True, f"Container {full_container_name} created successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Container creation timed out"
        except Exception as e:
            return False, str(e)
    
    def _check_file_saved(self):
        """Check if the current file is saved."""
        if not hasattr(self.main_window, 'current_file') or not self.main_window.current_file:
            reply = QMessageBox.warning(
                self.main_window,
                "File Not Saved",
                "The current file must be saved before deploying monitoring.\n\n"
                "The container names will be based on the filename.\n\n"
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
    
    def _get_container_prefix(self):
        """Get container prefix from current file."""
        if not hasattr(self.main_window, 'current_file') or not self.main_window.current_file:
            return None
        
        # Get filename without extension
        filename = os.path.basename(self.main_window.current_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Clean name for Docker (remove invalid characters)
        clean_name = "".join(c for c in name_without_ext if c.isalnum() or c in '-_').lower()
        
        if not clean_name:
            clean_name = "netflux5g_topology"
        
        return f"monitoring_{clean_name}"
    
    def _get_docker_network_name(self):
        """Get the Docker network name for the current topology."""
        if hasattr(self.main_window, 'docker_network_manager'):
            return self.main_window.docker_network_manager.get_current_network_name()
        return None
    
    def _check_docker_available(self):
        """Check if Docker are available."""
        try:
            # Check Docker
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
            )
            return False
    
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
    
    def _get_running_monitoring_containers(self, container_prefix):
        """Get list of running monitoring containers with the given prefix."""
        running_containers = []
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor', 'blackbox-exporter']
        
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}_{monitoring_type}"
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if container_name in result.stdout:
                    running_containers.append(monitoring_type)
            except:
                continue
        
        return running_containers
    
    def _get_existing_monitoring_containers(self, container_prefix):
        """Get list of existing monitoring containers (running or stopped) with the given prefix."""
        existing_containers = []
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor', 'blackbox-exporter']
        
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}_{monitoring_type}"
            try:
                result = subprocess.run(
                    ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if container_name in result.stdout:
                    existing_containers.append(monitoring_type)
            except:
                continue
        
        return existing_containers
    
    def _stop_containers_sync(self, container_prefix):
        """Stop containers synchronously (for restart scenarios)."""
        monitoring_types = ['prometheus', 'grafana', 'node-exporter', 'cadvisor', 'blackbox-exporter']
        
        for monitoring_type in monitoring_types:
            container_name = f"{container_prefix}_{monitoring_type}"
            try:
                subprocess.run(['docker', 'stop', container_name], timeout=30, capture_output=True)
                subprocess.run(['docker', 'rm', container_name], timeout=10, capture_output=True)
            except:
                pass  # Ignore errors for restart scenario
    
    def _start_operation(self, operation, container_prefix, network_name=None):
        """Start monitoring operation in worker thread."""
        # Create progress dialog
        operation_text = "Deploying" if operation == 'deploy' else "Stopping" if operation == 'stop' else "Cleaning up"
        self.progress_dialog = QProgressDialog(
            f"{operation_text} monitoring stack...",
            "Cancel",
            0,
            100,
            self.main_window
        )
        self.progress_dialog.setWindowTitle(f"Monitoring {operation_text}")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self._cancel_operation)
        self.progress_dialog.show()
        
        # Create and start worker
        self.current_worker = MonitoringDeploymentWorker(operation, container_prefix, network_name)
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
        
        self.main_window.status_manager.showCanvasStatus("Monitoring operation cancelled")
    
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
                f"Monitoring operation failed:\n{message}"
            )
            self.main_window.status_manager.showCanvasStatus(f"Monitoring operation failed: {message}")
        
        # Cleanup
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
    
    def getMonitoringStatus(self):
        """Get the status of the monitoring containers."""
        # Use fixed service name instead of file-based naming
        container_prefix = "netflux5g"
        
        try:
            running_containers = self._get_running_monitoring_containers(container_prefix)
            existing_containers = self._get_existing_monitoring_containers(container_prefix)
            
            if running_containers:
                return f"Running: {', '.join(running_containers)}"
            elif existing_containers:
                return f"Stopped: {', '.join(existing_containers)}"
            else:
                return f"Not deployed: {container_prefix}"
            
        except:
            return "Docker not available"
    
    def is_monitoring_running(self):
        """Check if monitoring stack is currently running."""
        container_prefix = "netflux5g"
        running_containers = self._get_running_monitoring_containers(container_prefix)
        
        # Consider monitoring running if at least prometheus and grafana are running
        essential_services = ['prometheus', 'grafana']
        running_essential = [svc for svc in essential_services if svc in running_containers]
        
        return len(running_essential) >= 2  # Both prometheus and grafana must be running
    
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

    def stop_monitoring_sync(self):
        """Stop monitoring stack synchronously for automation."""
        debug_print("Stop Monitoring synchronously triggered")
        
        # Use fixed service name instead of file-based naming
        container_prefix = "netflux5g"
        
        # Check if Docker is available
        if not self._check_docker_available():
            return False, "Docker not available"
        
        # Check if any monitoring containers exist
        existing_containers = self._get_existing_monitoring_containers(container_prefix)
        if not existing_containers:
            debug_print(f"No monitoring containers found with prefix '{container_prefix}'")
            return True, "No monitoring containers to stop"
        
        try:
            # Stop containers synchronously
            self._stop_containers_sync(container_prefix)
            
            debug_print(f"Monitoring containers stopped: {existing_containers}")
            return True, f"Monitoring containers stopped: {', '.join(existing_containers)}"
            
        except Exception as e:
            error_print(f"Failed to stop monitoring containers: {e}")
            return False, f"Failed to stop monitoring containers: {str(e)}"
