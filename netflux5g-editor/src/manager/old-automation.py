from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from manager.debug import debug_print
import os
import subprocess

class AutomationManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def promptControllerChoice(self):
        """Prompt the user to choose between Ryu and ONOS controller."""
        from PyQt5.QtWidgets import QInputDialog
        options = ["Ryu Controller", "ONOS Controller"]
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
        """Run All - Deploy and start all components including controller, database, monitoring, and topology"""
        debug_print("DEBUG: RunAll triggered - comprehensive deployment")
        
        # Prompt for controller type
        controller_type = self.promptControllerChoice()
        if not controller_type:
            debug_print("DEBUG: User cancelled controller selection.")
            return
        self.main_window.selected_controller_type = controller_type
        
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
                self.stopAllComponents()
                QTimer.singleShot(2000, lambda: self.main_window.automation_runner.run_all(controller_type=controller_type))
            return
        
        # Start the comprehensive automation (includes controller, database, monitoring, and topology)
        self.main_window.automation_runner.run_all(controller_type=controller_type)
        
        # Update UI state
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(False)
        if hasattr(self.main_window, 'actionStop_All'):
            self.main_window.actionStop_All.setEnabled(True)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(False)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(True)

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
        """Perform cleanup for all services, using the selected controller type."""
        debug_print("DEBUG: Performing comprehensive stop of all services")
        
        try:
            # 1. Stop Mininet first (if running)
            if self.main_window.automation_runner.is_deployment_running():
                self.main_window.status_manager.showCanvasStatus("Stopping Mininet and cleaning up...")
                self.main_window.automation_runner.stop_all()
            else:
                # Run mininet cleanup even if automation runner isn't running
                self.main_window.status_manager.showCanvasStatus("Cleaning up Mininet...")
                self._cleanupMininet()
            
            # 2. Stop Database and WebUI
            self.main_window.status_manager.showCanvasStatus("Stopping Database and WebUI...")
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.stopWebUI()
                self.main_window.database_manager.stopDatabase()
            
            # 3. Stop Monitoring Stack
            self.main_window.status_manager.showCanvasStatus("Stopping Monitoring Stack...")
            if hasattr(self.main_window, 'monitoring_manager'):
                self.main_window.monitoring_manager.stopMonitoring()
            
            # 4. Stop Controllers
            self.main_window.status_manager.showCanvasStatus("Stopping Controllers...")
            if hasattr(self.main_window, 'controller_manager'):
                if controller_type == 'onos':
                    self.main_window.controller_manager.stopOnosController()
                else:
                    self.main_window.controller_manager.stopController()
            
            # Reset all UI states after stopping
            self._resetAllUIStates()
            
            self.main_window.status_manager.showCanvasStatus("All services stopped successfully")
            
        except Exception as e:
            debug_print(f"ERROR: Error during comprehensive stop: {e}")
            QMessageBox.critical(
                self.main_window,
                "Stop All Error",
                f"An error occurred while stopping services:\n{str(e)}\n\nSome services may still be running."
            )

    def _cleanupMininet(self):
        """Clean up Mininet using sudo mn -c"""
        import subprocess
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

    def onAutomationFinished(self, success, message):
        """Handle automation completion."""
        if success:
            # Check if this is a stop/cleanup operation based on the message
            if "cleanup" in message.lower() or "stop" in message.lower() or "terminated" in message.lower():
                # This is a stop/cleanup operation
                QMessageBox.information(self.main_window, "Operation Completed", message)
                
                # Reset all UI states after successful stop/cleanup
                self._resetAllUIStates()
            else:
                # This is a deployment/start operation
                deployment_info = self.main_window.automation_runner.get_deployment_info()
                info_text = f"Deployment completed successfully!\n\n"
                
                if deployment_info:
                    info_text += f"Working directory: {deployment_info['export_dir']}\n"
                    info_text += f"Mininet Script: {os.path.basename(deployment_info['mininet_script'])}\n\n"
                
                info_text += "Services are now running. Use 'Stop All' or 'Stop' to terminate when done."
                
                QMessageBox.information(self.main_window, "Deployment Successful", info_text)
                
                # Update UI state for successful deployment
                if hasattr(self.main_window, 'actionRun_All'):
                    self.main_window.actionRun_All.setEnabled(False)
                if hasattr(self.main_window, 'actionStop_All'):
                    self.main_window.actionStop_All.setEnabled(True)
                if hasattr(self.main_window, 'actionRunAll'):
                    self.main_window.actionRunAll.setEnabled(False)
                if hasattr(self.main_window, 'actionStopAll'):
                    self.main_window.actionStopAll.setEnabled(True)
                if hasattr(self.main_window, 'actionRun'):
                    self.main_window.actionRun.setEnabled(False)
                if hasattr(self.main_window, 'actionStop'):
                    self.main_window.actionStop.setEnabled(True)
        else:
            # Check if this is a stop/cleanup failure
            if "cleanup" in message.lower() or "stop" in message.lower() or "terminated" in message.lower():
                QMessageBox.critical(self.main_window, "Operation Failed", f"Stop/cleanup operation failed:\n\n{message}")
            else:
                QMessageBox.critical(self.main_window, "Deployment Failed", f"Deployment failed:\n\n{message}")
            
            # Reset UI state on failure
            self._resetAllUIStates()

    def exportToMininet(self):
        """Export the current topology to a Mininet script."""
        self.main_window.mininet_exporter.export_to_mininet()

    def createDockerNetwork(self):
        """Create Docker network for the current topology."""
        if hasattr(self.main_window, 'docker_network_manager'):
            self.main_window.docker_network_manager.create_docker_network()

    def deleteDockerNetwork(self):
        """Delete Docker network for the current topology."""
        if hasattr(self.main_window, 'docker_network_manager'):
            self.main_window.docker_network_manager.delete_docker_network()

    def deployDatabase(self):
        """Deploy MongoDB database for the current topology."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.deployDatabase()

    def stopDatabase(self):
        """Stop MongoDB database for the current topology."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.stopDatabase()

    def getDatabaseStatus(self):
        """Get the current database status."""
        if hasattr(self.main_window, 'database_manager'):
            return self.main_window.database_manager.getContainerStatus()
        return "Database manager not available"

    def deployWebUI(self):
        """Deploy Web UI for the current topology."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.deployWebUI()

    def stopWebUI(self):
        """Stop Web UI for the current topology."""
        if hasattr(self.main_window, 'database_manager'):
            self.main_window.database_manager.stopWebUI()

    def getWebUIStatus(self):
        """Get the current Web UI status."""
        if hasattr(self.main_window, 'database_manager'):
            return self.main_window.database_manager.getWebUIStatus()
        return "Database manager not available"

    def deployMonitoring(self):
        """Deploy monitoring stack for the current topology."""
        if hasattr(self.main_window, 'monitoring_manager'):
            self.main_window.monitoring_manager.deployMonitoring()

    def stopMonitoring(self):
        """Stop monitoring stack for the current topology."""
        if hasattr(self.main_window, 'monitoring_manager'):
            self.main_window.monitoring_manager.stopMonitoring()

    def getMonitoringStatus(self):
        """Get the current monitoring status."""
        if hasattr(self.main_window, 'monitoring_manager'):
            return self.main_window.monitoring_manager.getMonitoringStatus()
        return "Monitoring manager not available"

    def deployController(self):
        """Deploy Ryu SDN controller for the current topology."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.deployController()

    def stopController(self):
        """Stop Ryu SDN controller for the current topology."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.stopController()

    def getControllerStatus(self):
        """Get the current controller status."""
        if hasattr(self.main_window, 'controller_manager'):
            return self.main_window.controller_manager.getControllerStatus()
        return "Controller manager not available"

    def deployOnosController(self):
        """Deploy ONOS SDN controller for the current topology."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.deployOnosController()

    def stopOnosController(self):
        """Stop ONOS SDN controller for the current topology."""
        if hasattr(self.main_window, 'controller_manager'):
            self.main_window.controller_manager.stopOnosController()

    def getOnosControllerStatus(self):
        """Get the current ONOS controller status."""
        if hasattr(self.main_window, 'controller_manager'):
            return self.main_window.controller_manager.getOnosControllerStatus()
        return "Controller manager not available"
    
    def stopTopology(self):
        """Stop and clean up the current topology - Simple cleanup with mn -c"""
        debug_print("DEBUG: Stop topology triggered")
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Clean Topology",
            "Are you sure you want to clean up the current topology?\n\nThis will:\n- Execute 'sudo mn -c' to clean Mininet\n- Stop any running topology processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Use the automation runner's stop_topology method for proper cleanup
            self.main_window.automation_runner.stop_topology()
            self.main_window.status_manager.showCanvasStatus("Topology cleaned up successfully")
            
            # Reset all UI states after stopping
            if hasattr(self.main_window, 'actionRunAll'):
                self.main_window.actionRunAll.setEnabled(True)
            if hasattr(self.main_window, 'actionStopAll'):
                self.main_window.actionStopAll.setEnabled(False)
            if hasattr(self.main_window, 'actionRun'):
                self.main_window.actionRun.setEnabled(True)
            if hasattr(self.main_window, 'actionStop'):
                self.main_window.actionStop.setEnabled(False)

    def runTopology(self):
        """Run the topology (actionRun) with proper UI state management."""
        debug_print("DEBUG: Run topology triggered")
        
        # Check if already running
        if self.main_window.automation_runner.is_deployment_running():
            QMessageBox.warning(
                self.main_window,
                "Already Running", 
                "A topology is already running. Please stop it first."
            )
            return
        
        # Start the topology
        self.main_window.automation_runner.run_topology_only()
        
        # Update UI state
        if hasattr(self.main_window, 'actionRun'):
            self.main_window.actionRun.setEnabled(False)
        if hasattr(self.main_window, 'actionStop'):
            self.main_window.actionStop.setEnabled(True)