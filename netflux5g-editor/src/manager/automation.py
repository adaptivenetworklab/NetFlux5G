from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel
from manager.debug import debug_print
from prerequisites.checker import PrerequisitesChecker
import os

class AutomationManager:
    def __init__(self, main_window):
        self.main_window = main_window
        # Connect test results signal
        if hasattr(self.main_window, 'automation_runner'):
            self.main_window.automation_runner.test_results_ready.connect(self.showTestResults)
        
    def runAllComponents(self):
        """Run All - Deploy and start all components"""
        debug_print("DEBUG: RunAll triggered")
        
        # Check prerequisites first
        all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
        if not all_ok:
            missing = [tool for tool, ok in checks.items() if not ok]
            instructions = PrerequisitesChecker.get_installation_instructions()
            
            error_msg = f"Missing prerequisites: {', '.join(missing)}\n\n"
            for tool in missing:
                error_msg += f"{tool.upper()}:\n{instructions[tool]}\n"
            
            QMessageBox.critical(
                self.main_window,
                "Missing Prerequisites",
                error_msg
            )
            return
        
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
        
        # Check prerequisites first
        all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
        if not all_ok:
            missing = [tool for tool, ok in checks.items() if not ok]
            instructions = PrerequisitesChecker.get_installation_instructions()
            
            error_msg = f"Missing prerequisites for testing: {', '.join(missing)}\n\n"
            for tool in missing:
                error_msg += f"{tool.upper()}:\n{instructions[tool]}\n"
            
            QMessageBox.critical(
                self.main_window,
                "Missing Prerequisites",
                error_msg
            )
            return
        
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
        """Stop All - Stop all running services and clean up containers."""
        debug_print("DEBUG: StopAll triggered")
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.main_window,
            "Stop All Services",
            "Are you sure you want to stop all running services?\n\nThis will:\n- Stop Docker containers\n- Clean up Mininet\n- Remove orphaned containers\n- Terminate all processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.main_window.automation_runner.stop_all()
            
            # Wait a moment for cleanup to complete
            QTimer.singleShot(3000, self._update_ui_after_stop)

    def _update_ui_after_stop(self):
        """Update UI state after stopping services."""
        # Update UI state
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(True)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(False)
        
        self.main_window.showCanvasStatus("All services stopped and cleaned up")

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

    def showTestResults(self, test_results):
        """Display end-to-end test results in a dialog."""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("End-to-End Test Results")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Summary
        summary = test_results.get('summary', {})
        summary_text = f"Test Summary: {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed, {summary.get('total', 0)} total"
        summary_label = QLabel(summary_text)
        layout.addWidget(summary_label)
        
        # Detailed results
        results_text = QTextEdit()
        results_content = "DETAILED TEST RESULTS\n" + "="*50 + "\n\n"
        
        for test in test_results.get('tests', []):
            results_content += f"Test: {test.get('name', 'Unknown')}\n"
            results_content += f"Result: {test.get('result', 'UNKNOWN')}\n"
            results_content += f"Message: {test.get('message', 'No message')}\n"
            results_content += f"Duration: {test.get('duration', 0):.2f}s\n"
            results_content += "-" * 30 + "\n\n"
        
        # Add deployment info
        deployment_info = self.main_window.automation_runner.get_deployment_info()
        if deployment_info:
            results_content += "\nDEPLOYMENT INFORMATION\n" + "="*50 + "\n"
            results_content += f"Export Directory: {deployment_info.get('export_dir', 'Unknown')}\n"
            results_content += f"Docker Compose: {deployment_info.get('docker_compose_file', 'Unknown')}\n"
            results_content += f"Results saved to: {deployment_info.get('export_dir', 'Unknown')}/test_results.json\n"
        
        results_text.setPlainText(results_content)
        results_text.setReadOnly(True)
        layout.addWidget(results_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save Results")
        save_button.clicked.connect(lambda: self._saveTestResults(test_results))
        button_layout.addWidget(save_button)
        
        open_dir_button = QPushButton("Open Test Directory")
        open_dir_button.clicked.connect(self._openTestDirectory)
        button_layout.addWidget(open_dir_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def _saveTestResults(self, test_results):
        """Save test results to a file."""
        try:
            deployment_info = self.main_window.automation_runner.get_deployment_info()
            if deployment_info and deployment_info.get('export_dir'):
                import json
                from datetime import datetime
                
                results_file = os.path.join(deployment_info['export_dir'], "test_results.json")
                
                # Add timestamp if not present
                if 'timestamp' not in test_results:
                    test_results['timestamp'] = datetime.now().isoformat()
                
                with open(results_file, 'w') as f:
                    json.dump(test_results, f, indent=2)
                
                QMessageBox.information(
                    self.main_window,
                    "Results Saved",
                    f"Test results saved to:\n{results_file}"
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Save Failed",
                    "Could not determine test directory location."
                )
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Save Error",
                f"Failed to save test results:\n{str(e)}"
            )

    def _openTestDirectory(self):
        """Open the test directory in file explorer."""
        try:
            deployment_info = self.main_window.automation_runner.get_deployment_info()
            if deployment_info and deployment_info.get('export_dir'):
                import subprocess
                import platform
                
                export_dir = deployment_info['export_dir']
                
                if platform.system() == "Windows":
                    os.startfile(export_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", export_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", export_dir])
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Directory Not Found",
                    "Test directory location not available."
                )
        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                "Open Failed",
                f"Could not open directory:\n{str(e)}"
            )