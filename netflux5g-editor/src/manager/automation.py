from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from manager.debug import debug_print
import os

class AutomationManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def runAllComponents(self):
        """Run All - Deploy and start all components"""
        debug_print("DEBUG: RunAll triggered")
        
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
                # Wait a moment for cleanup
                QTimer.singleShot(2000, self.main_window.automation_runner.run_all)
            return
        
        # Start the automation
        self.main_window.automation_runner.run_all()
        
        # Update UI state
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(False)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(True)

    def runEndToEndTest(self):
        """Run complete end-to-end testing sequence."""
        debug_print("DEBUG: End-to-end test triggered")
        
        if self.main_window.automation_runner.is_deployment_running():
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "A deployment is already running. Please stop it first."
            )
            return
        
        # Verify topology has required components
        nodes, links = self.main_window.extractTopology()
        required_components = ['VGcore', 'GNB', 'UE']
        found_components = set(node['type'] for node in nodes)
        
        missing = [comp for comp in required_components if comp not in found_components]
        if missing:
            QMessageBox.warning(
                self.main_window,
                "Incomplete Topology",
                f"Missing required components for testing: {', '.join(missing)}\n\n"
                "Please ensure your topology includes:\n"
                "• 5G Core components (VGcore)\n"
                "• gNodeB (GNB)\n"
                "• User Equipment (UE)"
            )
            return
        
        # Start end-to-end test
        self.main_window.automation_runner.run_end_to_end_test()

    def stopAllComponents(self):
        """Stop All - Stop all running services"""
        debug_print("DEBUG: StopAll triggered")
        
        if not self.main_window.automation_runner.is_deployment_running():
            self.main_window.status_manager.showCanvasStatus("No services are currently running")
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop All Services",
            "Are you sure you want to stop all running services?\n\nThis will:\n- Stop Docker containers\n- Clean up Mininet\n- Terminate all processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.main_window.automation_runner.stop_all()
            
            # Update UI state
            if hasattr(self.main_window, 'actionRunAll'):
                self.main_window.actionRunAll.setEnabled(True)
            if hasattr(self.main_window, 'actionStopAll'):
                self.main_window.actionStopAll.setEnabled(False)    

    def onAutomationFinished(self, success, message):
        """Handle automation completion."""
        if success:
            deployment_info = self.main_window.automation_runner.get_deployment_info()
            info_text = f"Deployment completed successfully!\n\n"
            
            if deployment_info:
                info_text += f"Working directory: {deployment_info['export_dir']}\n"
                info_text += f"Docker Compose: {os.path.basename(deployment_info['docker_compose_file'])}\n"
                info_text += f"Mininet Script: {os.path.basename(deployment_info['mininet_script'])}\n\n"
            
            info_text += "Services are now running. Use 'Stop All' to terminate when done."
            
            QMessageBox.information(self.main_window, "Deployment Successful", info_text)
        else:
            QMessageBox.critical(self.main_window, "Deployment Failed", f"Deployment failed:\n\n{message}")
            
            # Re-enable RunAll button
            if hasattr(self.main_window, 'actionRunAll'):
                self.main_window.actionRunAll.setEnabled(True)
            if hasattr(self.main_window, 'actionStopAll'):
                self.main_window.actionStopAll.setEnabled(False)

    def exportToDockerCompose(self):
        """Export 5G Core components to docker-compose.yaml and configuration files."""
        self.main_window.docker_compose_exporter.export_to_docker_compose()

    def exportToMininet(self):
        """Export the current topology to a Mininet script."""
        self.main_window.mininet_exporter.export_to_mininet()