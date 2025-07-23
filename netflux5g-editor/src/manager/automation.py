from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from utils.debug import debug_print, error_print, warning_print
import os
import subprocess

class AutomationManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def stopAllComponents(self):
        """Stop All - Stop all running services including controller, database, monitoring, and clean mininet"""
        debug_print("DEBUG: StopAll triggered - comprehensive cleanup")
        
        # Get the selected controller type for cleanup
        controller_type = getattr(self.main_window, 'selected_controller_type', 'ryu')
        
        reply = QMessageBox.question(
            self.main_window,
            "Stop All Services",
            f"Are you sure you want to stop all running services?\n\n"
            f"This will:\n"
            f"• Stop {controller_type.upper()} Controller\n"
            f"• Stop MongoDB Database\n"
            f"• Stop WebUI (User Manager)\n"
            f"• Stop Monitoring Stack\n"
            f"• Stop Packet Analyzer\n"
            f"• Clean up Mininet with 'sudo mn -c'\n"
            f"• Terminate all processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Create progress dialog for stopping
        progress = QMessageBox(self.main_window)
        progress.setWindowTitle("Stopping Services")
        progress.setText("Stopping all services...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.setModal(True)
        progress.show()
        
        try:
            self._stop_all_services(controller_type, progress)
            
            progress.close()
            self._update_ui_state(False)
            
            QMessageBox.information(
                self.main_window,
                "Services Stopped",
                "All NetFlux5G services have been stopped successfully."
            )
            
        except Exception as e:
            progress.close()
            error_print(f"Failed to stop all services: {e}")
            QMessageBox.critical(
                self.main_window,
                "Stop Failed",
                f"Failed to stop some services: {str(e)}\n\n"
                f"Please check the debug output for more details."
            )
    
    def _stop_all_services(self, controller_type, progress_dialog):
        """Stop all services in reverse deployment order."""
        services = [
            ("Cleaning up Mininet", self._cleanup_mininet),
            ("Stopping packet analyzer", lambda: self._stop_service(self.main_window.packet_analyzer_manager, 'packet_analyzer')),
            ("Stopping monitoring", lambda: self._stop_service(self.main_window.monitoring_manager, 'monitoring')),
            ("Stopping WebUI", lambda: self._stop_service(self.main_window.database_manager, 'webui')),
            ("Stopping database", lambda: self._stop_service(self.main_window.database_manager, 'database')),
            ("Stopping controller", lambda: self._stop_controller(controller_type))
        ]
        
        for message, stop_func in services:
            progress_dialog.setText(message)
            try:
                stop_func()
            except Exception as e:
                warning_print(f"Warning: {message} failed: {e}")
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

    def promptControllerChoice(self):
        """Prompt the user to choose between Ryu and ONOS controller."""
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
        
        # Check if already running
        if self._is_any_service_running():
            reply = QMessageBox.question(
                self.main_window,
                "Services Already Running",
                "Some services are already running. Do you want to stop them first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stopAllComponents()
                # Wait a moment then retry
                QTimer.singleShot(2000, self.runAllComponents)
            return
        
        # Prompt for controller type
        controller_type = self.promptControllerChoice()
        if not controller_type:
            debug_print("DEBUG: User cancelled controller selection.")
            return
        
        # Store controller type for this session
        self.main_window.selected_controller_type = controller_type
        
        # Check if we have components to deploy
        nodes, links = self.main_window.extractTopology()
        if not self._has_deployable_components(nodes):
            QMessageBox.information(
                self.main_window,
                "No Components",
                "No deployable components found in the topology.\n\n"
                "Please add 5G components (VGcore, GNB, UE) or network elements (Host, STA) to deploy."
            )
            return
        
        # Create progress dialog
        self.progress_dialog = QMessageBox(self.main_window)
        self.progress_dialog.setWindowTitle("NetFlux5G Deployment")
        self.progress_dialog.setText("Deploying services...")
        self.progress_dialog.setStandardButtons(QMessageBox.Cancel)
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        
        # Start deployment sequence
        self._deploy_all_services(controller_type)
    
    def _is_any_service_running(self):
        """Check if any NetFlux5G service is currently running."""
        managers = [
            ('controller', self.main_window.controller_manager),
            ('database', self.main_window.database_manager),
            ('monitoring', self.main_window.monitoring_manager),
            ('packet_analyzer', self.main_window.packet_analyzer_manager)
        ]
        
        for name, manager in managers:
            if hasattr(manager, f'is_{name}_running') and getattr(manager, f'is_{name}_running')():
                return True
        return False
    
    def _has_deployable_components(self, nodes):
        """Check if topology has deployable components."""
        deployable_types = ['VGcore', 'GNB', 'UE', 'Host', 'STA', 'AP']
        return any(n['type'] in deployable_types for n in nodes)
    
    def _deploy_all_services(self, controller_type):
        """Deploy all services in the correct order."""
        try:
            # Step 1: Ensure Docker network exists
            self.progress_dialog.setText("Checking Docker network...")
            if not self._ensure_docker_network():
                return
            
            # Step 2: Deploy Controller
            self.progress_dialog.setText(f"Deploying {controller_type.upper()} controller...")
            if not self._deploy_controller(controller_type):
                return
            
            # Step 3: Deploy Database
            self.progress_dialog.setText("Deploying MongoDB database...")
            if not self._deploy_database():
                return
            
            # Step 4: Deploy WebUI
            self.progress_dialog.setText("Deploying Web UI...")
            if not self._deploy_webui():
                return
            
            # Step 5: Deploy Monitoring
            self.progress_dialog.setText("Deploying monitoring stack...")
            if not self._deploy_monitoring():
                return
            
            # Step 6: Deploy Packet Analyzer
            self.progress_dialog.setText("Deploying packet analyzer...")
            if not self._deploy_packet_analyzer():
                return
            
            # Step 7: Export and run topology
            self.progress_dialog.setText("Generating and running topology...")
            if not self._run_topology():
                return
            
            # Success!
            self.progress_dialog.close()
            self._update_ui_state(True)
            
            QMessageBox.information(
                self.main_window,
                "Deployment Complete",
                f"All services deployed successfully!\n\n"
                f"Services running:\n"
                f"• {controller_type.upper()} Controller\n"
                f"• MongoDB Database\n"
                f"• Web UI (User Manager)\n"
                f"• Monitoring Stack (Prometheus, Grafana)\n"
                f"• Packet Analyzer (Webshark)\n"
                f"• Mininet Topology\n\n"
                f"You can now interact with your topology."
            )
            
        except Exception as e:
            self.progress_dialog.close()
            error_print(f"Deployment failed: {e}")
            QMessageBox.critical(
                self.main_window,
                "Deployment Failed",
                f"Failed to deploy services: {str(e)}\n\n"
                f"Please check the debug output for more details."
            )
    
    def _ensure_docker_network(self):
        """Ensure netflux5g Docker network exists."""
        try:
            return self.main_window.docker_network_manager.create_netflux5g_network_if_needed()
        except Exception as e:
            error_print(f"Failed to create Docker network: {e}")
            return False
    
    def _deploy_controller(self, controller_type):
        """Deploy the selected controller."""
        try:
            if controller_type == "ryu":
                return self.main_window.controller_manager.deploy_controller_sync()
            elif controller_type == "onos":
                return self.main_window.controller_manager.deploy_controller_sync("onos")
            return False
        except Exception as e:
            error_print(f"Failed to deploy controller: {e}")
            return False
    
    def _deploy_database(self):
        """Deploy MongoDB database."""
        try:
            return self.main_window.database_manager.deploy_database_sync()
        except Exception as e:
            error_print(f"Failed to deploy database: {e}")
            return False
    
    def _deploy_webui(self):
        """Deploy Web UI."""
        try:
            return self.main_window.database_manager.deploy_webui_sync()
        except Exception as e:
            error_print(f"Failed to deploy WebUI: {e}")
            return False
    
    def _deploy_monitoring(self):
        """Deploy monitoring stack."""
        try:
            return self.main_window.monitoring_manager.deploy_monitoring_sync()
        except Exception as e:
            error_print(f"Failed to deploy monitoring: {e}")
            return False
    
    def _deploy_packet_analyzer(self):
        """Deploy packet analyzer."""
        try:
            return self.main_window.packet_analyzer_manager.deploy_packet_analyzer_sync()
        except Exception as e:
            error_print(f"Failed to deploy packet analyzer: {e}")
            return False
    
    def _run_topology(self):
        """Export and run the topology."""
        try:
            # Export topology to Mininet script
            self.main_window.mininet_exporter.export_to_mininet()
            
            # TODO: Add actual Mininet execution here when ready
            debug_print("Topology exported successfully")
            return True
        except Exception as e:
            error_print(f"Failed to run topology: {e}")
            return False
    
    def _update_ui_state(self, deployment_active):
        """Update UI buttons based on deployment state."""
        # Update Run All / Stop All buttons
        if hasattr(self.main_window, 'actionRun_All'):
            self.main_window.actionRun_All.setEnabled(not deployment_active)
        if hasattr(self.main_window, 'actionStop_All'):
            self.main_window.actionStop_All.setEnabled(deployment_active)
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.setEnabled(not deployment_active)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.setEnabled(deployment_active)

    # Individual service management methods (delegate to specific managers)
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

    def deployPacketAnalyzer(self):
        """Deploy packet analyzer for the current topology."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            self.main_window.packet_analyzer_manager.deployPacketAnalyzer()

    def stopPacketAnalyzer(self):
        """Stop packet analyzer for the current topology."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            self.main_window.packet_analyzer_manager.stopPacketAnalyzer()

    def getPacketAnalyzerStatus(self):
        """Get the current packet analyzer status."""
        if hasattr(self.main_window, 'packet_analyzer_manager'):
            return "Running on port 8085" if self.main_window.packet_analyzer_manager.is_packet_analyzer_running() else "Not running"
        return "Packet analyzer manager not available"

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
    
    def runTopology(self):
        """Run topology only (export and start Mininet without services)."""
        debug_print("DEBUG: Run topology triggered")
        
        # Check if we have components to deploy
        nodes, links = self.main_window.extractTopology()
        if not self._has_deployable_components(nodes):
            QMessageBox.information(
                self.main_window,
                "No Components",
                "No deployable components found in the topology.\n\n"
                "Please add network elements to deploy."
            )
            return
        
        try:
            # Export topology to Mininet script
            self.main_window.mininet_exporter.export_to_mininet()
            self._update_ui_state(True)
            
            QMessageBox.information(
                self.main_window,
                "Topology Exported",
                "Topology has been exported to Mininet script successfully.\n\n"
                "You can now run the script manually or use 'Run All' for full deployment."
            )
            
        except Exception as e:
            error_print(f"Failed to run topology: {e}")
            QMessageBox.critical(
                self.main_window,
                "Topology Export Failed",
                f"Failed to export topology: {str(e)}"
            )

    def stopTopology(self):
        """Stop and clean up the current topology."""
        debug_print("DEBUG: Stop topology triggered")
        
        reply = QMessageBox.question(
            self.main_window,
            "Clean Topology",
            "Are you sure you want to clean up the current topology?\n\n"
            "This will execute 'sudo mn -c' to clean Mininet.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._cleanup_mininet()
            self._update_ui_state(False)
            
            QMessageBox.information(
                self.main_window,
                "Topology Cleaned",
                "Topology has been cleaned up successfully."
            )

    def onAutomationFinished(self, success, message):
        """Handle automation completion events from AutomationRunner."""
        debug_print(f"Automation finished: success={success}, message={message}")
        
        if success:
            QMessageBox.information(
                self.main_window,
                "Automation Complete",
                message or "Automation completed successfully."
            )
        else:
            QMessageBox.critical(
                self.main_window,
                "Automation Failed", 
                message or "Automation failed. Check the debug output for details."
            )
        
        # Update UI state after automation completes
        self._update_ui_state(success)