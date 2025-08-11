from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QProgressDialog
from utils.debug import debug_print, error_print, warning_print
import os
import subprocess

class AutomationManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.progress_dialog = None
        
    def promptControllerChoice(self):
        """Prompt the user to choose between Ryu and ONOS controller."""
        options = ["ONOS Controller", "Ryu Controller"]
        choice, ok = QInputDialog.getItem(
            self.main_window,
            "Select SDN Controller",
            "Choose which controller to deploy:",
            options,
            0,
            False
        )
        if ok:
            if "ONOS" in choice:
                return "onos"
            else:
                return "ryu"
        return None

    def runAllComponents(self):
        """Run All - Deploy and start all components including controller, database, monitoring, and topology, with stepwise waiting."""
        from PyQt5.QtCore import QEventLoop
        debug_print("DEBUG: RunAll triggered - comprehensive deployment")
        # Prompt for controller type
        controller_type = self.promptControllerChoice()
        if not controller_type:
            debug_print("DEBUG: User cancelled controller selection.")
            return
        self.main_window.selected_controller_type = controller_type
        # Disable Run All button immediately
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(False)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(False)

        def wait_for_worker(manager, worker_attr='current_worker'):
            """Wait for a manager's worker to finish using QEventLoop."""
            if hasattr(manager, worker_attr):
                worker = getattr(manager, worker_attr)
                if worker and worker.isRunning():
                    loop = QEventLoop()
                    def on_finished(*_):
                        loop.quit()
                    worker.operation_finished.connect(on_finished)
                    loop.exec_()

        try:
            self.main_window.status_manager.showCanvasStatus("Starting comprehensive deployment...")
            # Step 1: Ensure Docker network exists
            debug_print("DEBUG: Step 1 - Creating Docker network")
            self.main_window.status_manager.showCanvasStatus("Creating Docker network...")
            if hasattr(self.main_window, 'docker_network_manager'):
                self.main_window.docker_network_manager.create_netflux5g_network_if_needed()
                # No worker, so no wait needed

            # Step 2: Deploy Controller (Ryu or ONOS)
            debug_print(f"DEBUG: Step 2 - Deploying {controller_type.upper()} controller")
            self.main_window.status_manager.showCanvasStatus(f"Deploying {controller_type.upper()} controller...")
            if hasattr(self.main_window, 'controller_manager'):
                if controller_type == 'onos':
                    self.main_window.controller_manager.deployOnosController()
                else:
                    self.main_window.controller_manager.deployController()
                wait_for_worker(self.main_window.controller_manager, 'deployment_worker')

            # Step 3: Deploy Database (MongoDB)
            debug_print("DEBUG: Step 3 - Deploying MongoDB database")
            self.main_window.status_manager.showCanvasStatus("Deploying MongoDB database...")
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.deployDatabase()
                wait_for_worker(self.main_window.database_manager)

            # Step 4: Deploy WebUI (User Manager)
            debug_print("DEBUG: Step 4 - Deploying WebUI User Manager")
            self.main_window.status_manager.showCanvasStatus("Deploying WebUI User Manager...")
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.deployWebUI()
                wait_for_worker(self.main_window.database_manager)

            # Step 5: Deploy Monitoring Stack
            debug_print("DEBUG: Step 5 - Deploying Monitoring stack")
            self.main_window.status_manager.showCanvasStatus("Deploying Monitoring stack...")
            if hasattr(self.main_window, 'monitoring_manager'):
                self.main_window.monitoring_manager.deployMonitoring()
                wait_for_worker(self.main_window.monitoring_manager)

            # Step 6: Deploy Packet Analyzer (Webshark)
            debug_print("DEBUG: Step 6 - Deploying Packet Analyzer")
            self.main_window.status_manager.showCanvasStatus("Deploying Packet Analyzer...")
            if hasattr(self.main_window, 'packet_analyzer_manager'):
                self.main_window.packet_analyzer_manager.deployPacketAnalyzer()
                wait_for_worker(self.main_window.packet_analyzer_manager)

            # Step 7: Run Topology
            debug_print("DEBUG: Step 7 - Running topology")
            self.main_window.status_manager.showCanvasStatus("Starting topology...")
            if hasattr(self.main_window, 'automation_runner'):
                self.main_window.automation_runner.run_topology_only()

            # Update UI state after successful deployment
            if hasattr(self.main_window, 'actionStop_All'):
                self.main_window.actionStop_All.setEnabled(True)
            if hasattr(self.main_window, 'actionStopAll'):
                self.main_window.actionStopAll.setEnabled(True)
            if hasattr(self.main_window, 'actionStop'):
                self.main_window.actionStop.setEnabled(True)

            self.main_window.status_manager.showCanvasStatus("All services deployed successfully!")

            QMessageBox.information(
                self.main_window,
                "Services Started",
                "All NetFlux5G services have been started successfully.\n\nServices deployed:\n" +
                f"- {controller_type.upper()} Controller\n" +
                "- MongoDB Database\n" +
                "- WebUI User Manager\n" +
                "- Monitoring Stack\n" +
                "- Packet Analyzer\n" +
                "- Network Topology\n\n" +
                "You can now use the topology."
            )
                
        except Exception as e:
            error_print(f"ERROR: Failed to start automation: {e}")
            
            # Re-enable Run All button on error
            if hasattr(self.main_window, 'actionRun_All'):
                self.main_window.actionRun_All.setEnabled(True)
            if hasattr(self.main_window, 'actionRunAll'):
                self.main_window.actionRunAll.setEnabled(True)
                
            QMessageBox.critical(
                self.main_window,
                "Deployment Error",
                f"Failed to start deployment:\n{str(e)}"
            )
    
    def stopAllComponents(self):
        """Stop All - Stop all running services including controller, database, monitoring, and clean mininet"""
        debug_print("DEBUG: StopAll triggered - comprehensive cleanup")
        
        # Use the selected controller type for cleanup
        controller_type = getattr(self.main_window, 'selected_controller_type', 'ryu')
        
        reply = QMessageBox.question(
            self.main_window,
            "Stop All Services",
            f"Are you sure you want to stop all running services?\n\nThis will:\n- Stop MongoDB Database\n- Stop WebUI (User Manager)\n- Stop Monitoring Stack\n- Stop {controller_type.upper()} Controller\n- Clean up Mininet with 'sudo mn -c'\n- Terminate all processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._performComprehensiveStopAll(controller_type=controller_type)

    def _performComprehensiveStopAll(self, controller_type='ryu'):
        """Perform cleanup for all services, using the selected controller type, with stepwise waiting."""
        from PyQt5.QtCore import QEventLoop
        debug_print("DEBUG: Performing comprehensive stop of all services")

        # Hide deployment monitoring panel if active
        if hasattr(self.main_window, 'deployment_monitor_manager'):
            self.main_window.deployment_monitor_manager.hideMonitoringPanel()

        # Show progress dialog for stopping services
        self.progress_dialog = QProgressDialog(
            "Stopping all NetFlux5G services...",
            "Cancel",
            0,
            100,
            self.main_window
        )
        self.progress_dialog.setWindowTitle("NetFlux5G Stop All Progress")
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        progress = 0
        self.progress_dialog.setValue(progress)

        def wait_for_worker(manager, worker_attr='current_worker'):
            """Wait for a manager's worker to finish using QEventLoop."""
            if hasattr(manager, worker_attr):
                worker = getattr(manager, worker_attr)
                if worker and worker.isRunning():
                    loop = QEventLoop()
                    def on_finished(*_):
                        loop.quit()
                    worker.operation_finished.connect(on_finished)
                    loop.exec_()

        try:
            # 1. Stop Mininet first (if running)
            if self.main_window.automation_runner.is_deployment_running():
                self.main_window.status_manager.showCanvasStatus("Stopping Mininet and cleaning up...")
                self.progress_dialog.setLabelText("Stopping Mininet and cleaning up...")
                self.progress_dialog.setValue(10)
                self.main_window.automation_runner.stop_topology()
                wait_for_worker(self.main_window.automation_runner, 'current_worker')
            else:
                self.main_window.status_manager.showCanvasStatus("Cleaning up Mininet...")
                self.progress_dialog.setLabelText("Cleaning up Mininet...")
                self.progress_dialog.setValue(20)
                self._cleanupMininet()

            # 2. Stop all NetFlux5G Docker containers comprehensively
            self.main_window.status_manager.showCanvasStatus("Stopping all NetFlux5G containers...")
            self.progress_dialog.setLabelText("Stopping all NetFlux5G containers...")
            self.progress_dialog.setValue(60)
            self._stop_all_netflux5g_containers()

            # Reset all UI states after stopping
            self.progress_dialog.setValue(90)
            self._resetAllUIStates()
            self.main_window.status_manager.showCanvasStatus("All services stopped successfully")
            self.progress_dialog.setLabelText("All services stopped successfully!")
            self.progress_dialog.setValue(100)
            QTimer.singleShot(1000, self.progress_dialog.close)

        except Exception as e:
            debug_print(f"ERROR: Error during comprehensive stop: {e}")
            QMessageBox.critical(
                self.main_window,
                "Stop All Error",
                f"An error occurred while stopping services:\n{str(e)}\n\nSome services may still be running."
            )
            self.progress_dialog.close()

    def _cleanupMininet(self):
        """Clean up Mininet using sudo mn -c"""
        try:
            debug_print("DEBUG: Executing 'sudo mn -c' for Mininet cleanup")
            result = subprocess.run(
                ["sudo", "mn", "-c"], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                debug_print("DEBUG: Mininet cleanup successful")
            else:
                debug_print(f"WARNING: Mininet cleanup warning: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            debug_print("ERROR: Mininet cleanup timed out")
        except subprocess.CalledProcessError as e:
            debug_print(f"ERROR: Mininet cleanup failed: {e}")
        except Exception as e:
            debug_print(f"ERROR: Unexpected error during Mininet cleanup: {e}")

    def _resetAllUIStates(self):
        """Reset all UI states after stopping services"""
        # Reset Run All / Stop All buttons
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(True)
        if hasattr(self.main_window, 'actionStop_All'):
            self.main_window.actionStop_All.setEnabled(False)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(True)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(False)
        if hasattr(self.main_window, 'actionRun'):
            self.main_window.actionRun.setEnabled(True)
        if hasattr(self.main_window, 'actionStop'):
            self.main_window.actionStop.setEnabled(False)

    def stopTopology(self):
        """Stop and clean up the current topology - Simple cleanup with mn -c"""
        debug_print("DEBUG: Stop topology triggered")
        
        # Hide deployment monitoring panel if active
        if hasattr(self.main_window, 'deployment_monitor_manager'):
            self.main_window.deployment_monitor_manager.hideMonitoringPanel()
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Clean Topology",
            "Are you sure you want to clean up the current topology?\n\nThis will:\n- Execute 'sudo mn -c' to clean Mininet\n- Stop any running topology processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Notify challenge system that topology is being stopped
            if hasattr(self.main_window, 'challenge_manager'):
                self.main_window.challenge_manager.onTopologyStopped()
                
            # Delegate to automation runner's stop_topology
            self.main_window.automation_runner.stop_topology()
        # Update UI state
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(True)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(True)
        if hasattr(self.main_window, 'actionRun'):
            self.main_window.actionRun.setEnabled(True)
        if hasattr(self.main_window, 'actionStop_All'):
            self.main_window.actionStop_All.setEnabled(False)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(False)
        if hasattr(self.main_window, 'actionStop'):
            self.main_window.actionStop.setEnabled(False)
                # Continue with other services even if one fails

    def runTopology(self):
        """Run the topology (actionRun) with proper UI state management."""
        debug_print("DEBUG: Run topology triggered")
        
        # Check if already running
        if self.main_window.automation_runner.is_deployment_running():
            reply = QMessageBox.question(
                self.main_window,
                "Already Running",
                "Deployment is already running. Do you want to stop it first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stopTopology()
                QTimer.singleShot(2000, self.runTopology)
            return
        
        # Start the topology
        self.main_window.automation_runner.run_topology_only()
        
        # Update UI state
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(False)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(False)
        if hasattr(self.main_window, 'actionRun'):
            self.main_window.actionRun.setEnabled(False)
        if hasattr(self.main_window, 'actionStop_All'):
            self.main_window.actionStop_All.setEnabled(True)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(True)
        if hasattr(self.main_window, 'actionStop'):
            self.main_window.actionStop.setEnabled(True)
                # Continue with other services even if one fails
    
    def _stop_service(self, manager, service_type):
        """Generic service stopper."""
        stop_method_name = f'stop_{service_type}_sync' if hasattr(manager, f'stop_{service_type}_sync') else f'stop{service_type.title()}'
        if hasattr(manager, stop_method_name):
            getattr(manager, stop_method_name)()
    
    def _stop_controller(self, controller_type):
        """Stop the controller."""
        if hasattr(self.main_window.controller_manager, '_stop_controller_sync'):
            container_name = f"netflux5g-{controller_type}-controller"
            self.main_window.controller_manager._stop_controller_sync(container_name, controller_type)
    
    def _cleanup_mininet(self):
        """Clean up Mininet using sudo mn -c"""
        import subprocess
        try:
            result = subprocess.run(
                ['sudo', 'mn', '-c'], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                debug_print("Mininet cleaned up successfully")
            else:
                warning_print(f"Mininet cleanup warning: {result.stderr}")
        except subprocess.TimeoutExpired:
            warning_print("Mininet cleanup timed out")
        except subprocess.CalledProcessError as e:
            warning_print(f"Mininet cleanup failed: {e}")
        except Exception as e:
            warning_print(f"Mininet cleanup error: {e}")

    def _stop_all_netflux5g_containers(self):
        """Stop all NetFlux5G containers systematically."""
        try:
            debug_print("DEBUG: Stopping all NetFlux5G containers")
            
            # List of all possible NetFlux5G container names
            container_names = [
                "netflux5g-ryu-controller",
                "netflux5g-onos-controller", 
                "netflux5g-mongodb",
                "netflux5g-webui",
                "netflux5g-cadvisor",
                "netflux5g-grafana",
                "netflux5g-prometheus",
                "netflux5g-node-exporter",
                "netflux5g-webshark"
            ]
            
            # Use DockerUtils to stop containers
            from utils.docker_utils import DockerUtils
            
            for container_name in container_names:
                if DockerUtils.is_container_running(container_name):
                    self.main_window.status_manager.showCanvasStatus(f"Stopping container: {container_name}")
                    debug_print(f"DEBUG: Stopping container: {container_name}")
                    DockerUtils.stop_container(container_name)
                    
            debug_print("DEBUG: All NetFlux5G containers stopped")
            
        except Exception as e:
            error_print(f"ERROR: Failed to stop all containers: {e}")

    # Individual service management methods (delegate to specific managers)
    def exportToMininet(self):
        """Export topology to Mininet script."""
        if hasattr(self.main_window, 'mininet_exporter'):
            self.main_window.mininet_exporter.export_to_mininet()
        else:
            from export.mininet_export import MininetExporter
            exporter = MininetExporter(self.main_window)
            exporter.export_to_mininet()

    def createDockerNetwork(self):
        """Create Docker network."""
        if hasattr(self.main_window, 'docker_network_manager'):
            self.main_window.docker_network_manager.create_docker_network()

    def deleteDockerNetwork(self):
        """Delete Docker network."""
        if hasattr(self.main_window, 'docker_network_manager'):
            self.main_window.docker_network_manager.delete_docker_network()

    def deployDatabase(self):
        """Deploy database service."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.deployDatabase()

    def stopDatabase(self):
        """Stop database service."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.stopDatabase()

    def getDatabaseStatus(self):
        """Get database status."""
        if hasattr(self.main_window, 'database_manager'):
            return self.main_window.database_manager.getContainerStatus()
        return False

    def deployWebUI(self):
        """Deploy WebUI service."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.deployWebUI()

    def stopWebUI(self):
        """Stop WebUI service."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.stopWebUI()

    def getWebUIStatus(self):
        """Get WebUI status."""
        if hasattr(self.main_window, 'database_manager'):
            return self.main_window.database_manager.getWebUIStatus()
        return False

    def deployMonitoring(self):
        """Deploy monitoring service."""
        if hasattr(self.main_window, 'monitoring_manager'):
            self.main_window.monitoring_manager.deployMonitoring()

    def stopMonitoring(self):
        """Stop monitoring service."""
        if hasattr(self.main_window, 'monitoring_manager'):
            self.main_window.monitoring_manager.stopMonitoring()

    def getMonitoringStatus(self):
        """Get monitoring status."""
        if hasattr(self.main_window, 'monitoring_manager'):
            if hasattr(self.main_window.monitoring_manager, 'is_monitoring_running'):
                return self.main_window.monitoring_manager.is_monitoring_running()
        return False

    def deployPacketAnalyzer(self):
        """Deploy packet analyzer service."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            self.main_window.packet_analyzer_manager.deployPacketAnalyzer()

    def stopPacketAnalyzer(self):
        """Stop packet analyzer service."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            self.main_window.packet_analyzer_manager.stopPacketAnalyzer()

    def getPacketAnalyzerStatus(self):
        """Get packet analyzer status."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            if hasattr(self.main_window.packet_analyzer_manager, 'is_packet_analyzer_running'):
                return self.main_window.packet_analyzer_manager.is_packet_analyzer_running()
        return False

    def deployController(self):
        """Deploy controller service."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.deployController()

    def stopController(self):
        """Stop controller service."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.stopController()

    def getControllerStatus(self):
        """Get controller status."""
        if hasattr(self.main_window, 'controller_manager'):
            return self.main_window.controller_manager.getControllerStatus()
        return False

    def deployOnosController(self):
        """Deploy ONOS controller service."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.deployOnosController()

    def stopOnosController(self):
        """Stop ONOS controller service."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.stopOnosController()

    def getOnosControllerStatus(self):
        """Get ONOS controller status."""
        if hasattr(self.main_window, 'controller_manager'):
            return self.main_window.controller_manager.getOnosControllerStatus()
        return False