"""
Docker Network Manager for NetFlux5G Editor
Handles creation and deletion of Docker networks for network topologies
"""

import os
import subprocess
import re
from PyQt5.QtWidgets import QMessageBox
from manager.debug import debug_print, error_print, warning_print

class DockerNetworkManager:
    """Manager for Docker network operations."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def create_docker_network(self):
        """Create the universal 'netflux5g' Docker network for all deployments."""
        network_name = "netflux5g"
        
        # Check if network already exists
        if self._network_exists(network_name):
            self.main_window.status_manager.showCanvasStatus(f"Universal Docker network '{network_name}' already exists")
            QMessageBox.information(
                self.main_window,
                "Network Exists",
                f"The universal Docker network '{network_name}' already exists and is ready for use.\n\n"
                f"This network is used by all NetFlux5G services:\n"
                f"• MongoDB Database\n"
                f"• Web UI (User Manager)\n"
                f"• Monitoring Stack\n"
                f"• Ryu Controller\n"
                f"• 5G Core Components\n"
                f"• UE and gNB containers"
            )
            return True
        
        # Create the network
        success = self._create_network(network_name)
        if success:
            self.main_window.status_manager.showCanvasStatus(f"Universal Docker network '{network_name}' created successfully")
            QMessageBox.information(
                self.main_window,
                "Network Created",
                f"The universal Docker network '{network_name}' has been created successfully.\n\n"
                f"Network Type: Bridge\n"
                f"Network Name: {network_name}\n\n"
                f"This network will be used by all NetFlux5G services:\n"
                f"• MongoDB Database\n"
                f"• Web UI (User Manager)\n" 
                f"• Monitoring Stack\n"
                f"• Ryu Controller\n"
                f"• 5G Core Components\n"
                f"• UE and gNB containers"
            )
        else:
            self.main_window.status_manager.showCanvasStatus(f"Failed to create universal Docker network '{network_name}'")
        
        return success
    
    def delete_docker_network(self):
        """Delete the universal 'netflux5g' Docker network."""
        network_name = "netflux5g"
        
        # Check if network exists
        if not self._network_exists(network_name):
            QMessageBox.information(
                self.main_window,
                "Network Not Found",
                f"The universal Docker network '{network_name}' does not exist."
            )
            return True
        
        # Confirm deletion
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Deletion",
            f"Are you sure you want to delete the universal Docker network '{network_name}'?\n\n"
            f"This will disconnect all NetFlux5G services currently connected to this network:\n"
            f"• MongoDB Database\n"
            f"• Web UI (User Manager)\n"
            f"• Monitoring Stack\n"
            f"• Ryu Controller\n"
            f"• 5G Core Components\n"
            f"• UE and gNB containers\n\n"
            f"You should stop all services before deleting the network.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            self.main_window.status_manager.showCanvasStatus("Universal Docker network deletion cancelled")
            return False
        
        # Delete the network
        success = self._delete_network(network_name)
        if success:
            self.main_window.status_manager.showCanvasStatus(f"Universal Docker network '{network_name}' deleted successfully")
            QMessageBox.information(
                self.main_window,
                "Network Deleted",
                f"The universal Docker network '{network_name}' has been deleted successfully."
            )
        else:
            self.main_window.status_manager.showCanvasStatus(f"Failed to delete universal Docker network '{network_name}'")
        
        return success
    
    def _get_network_name_from_file(self):
        """Extract network name from the current file path."""
        if not self.main_window.current_file:
            return None
        
        # Get the base filename without extension
        filename = os.path.basename(self.main_window.current_file)
        network_name = os.path.splitext(filename)[0]
        
        # Sanitize network name for Docker (only alphanumeric, hyphens, underscores)
        network_name = re.sub(r'[^a-zA-Z0-9_-]', '_', network_name)
        
        # Ensure it doesn't start with a hyphen or underscore
        network_name = re.sub(r'^[-_]+', '', network_name)
        
        # Ensure it's not empty and not too long
        if not network_name or len(network_name) > 63:
            return None
        
        # Add prefix to avoid conflicts with system networks
        network_name = f"netflux5g_{network_name}"
        
        return network_name
    
    def _network_exists(self, network_name):
        """Check if a Docker network exists."""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                networks = result.stdout.strip().split('\n')
                return network_name in networks
            else:
                warning_print(f"Failed to check network existence: {result.stderr}")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_print(f"Error checking Docker network: {e}")
            return False
    
    def _create_network(self, network_name):
        """Create a Docker network in bridge mode."""
        try:
            debug_print(f"Creating Docker network: {network_name}")
            
            cmd = [
                "docker", "network", "create",
                "--driver", "bridge",
                "--attachable",  # Allow manual container attachment
                network_name
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                debug_print(f"Successfully created Docker network: {network_name}")
                return True
            else:
                error_print(f"Failed to create Docker network: {result.stderr}")
                QMessageBox.critical(
                    self.main_window,
                    "Network Creation Failed",
                    f"Failed to create Docker network '{network_name}':\n\n{result.stderr}"
                )
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_print(f"Error creating Docker network: {e}")
            QMessageBox.critical(
                self.main_window,
                "Network Creation Error",
                f"Error creating Docker network '{network_name}':\n\n{str(e)}"
            )
            return False
    
    def _delete_network(self, network_name):
        """Delete a Docker network."""
        try:
            debug_print(f"Deleting Docker network: {network_name}")
            
            cmd = ["docker", "network", "rm", network_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                debug_print(f"Successfully deleted network: {network_name}")
                return True
            else:
                error_print(f"Failed to delete network {network_name}: {result.stderr}")
                QMessageBox.critical(
                    self.main_window,
                    "Network Deletion Error",
                    f"Error deleting Docker network '{network_name}':\n\n{result.stderr}"
                )
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_print(f"Error deleting Docker network: {e}")
            QMessageBox.critical(
                self.main_window,
                "Network Deletion Error",
                f"Error deleting Docker network '{network_name}':\n\n{str(e)}"
            )
            return False

    def check_netflux5g_network_exists(self):
        """Check if the dedicated 'netflux5g' network exists."""
        return self._network_exists("netflux5g")

    def create_netflux5g_network_if_needed(self):
        """Create the dedicated 'netflux5g' network if it doesn't exist."""
        if self.check_netflux5g_network_exists():
            debug_print("netflux5g network already exists")
            return True
        
        debug_print("Creating netflux5g network for service deployments")
        return self._create_network("netflux5g")

    def prompt_create_netflux5g_network(self):
        """Prompt user to create the netflux5g network if it doesn't exist."""
        if self.check_netflux5g_network_exists():
            return True
        
        reply = QMessageBox.question(
            self.main_window,
            "NetFlux5G Network Required",
            "The 'netflux5g' Docker network is required for deploying services but does not exist.\n\n"
            "This network is used by:\n"
            "• Database (MongoDB)\n"
            "• Web UI (User Manager)\n"
            "• Monitoring stack (Prometheus, Grafana, etc.)\n\n"
            "Do you want to create the 'netflux5g' network now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            success = self.create_netflux5g_network_if_needed()
            if success:
                QMessageBox.information(
                    self.main_window,
                    "Network Created",
                    "The 'netflux5g' Docker network has been created successfully.\n\n"
                    "All service containers will now connect to this network."
                )
                return True
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Network Creation Failed",
                    "Failed to create the 'netflux5g' Docker network.\n\n"
                    "Please check Docker is running and try again."
                )
                return False
        else:
            return False

    def get_current_network_name(self):
        """Get the universal network name for all NetFlux5G deployments."""
        return "netflux5g"

    def list_netflux_networks(self):
        """List all NetFlux5G Docker networks."""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--filter", "name=netflux5g", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                networks = [net.strip() for net in result.stdout.strip().split('\n') if net.strip()]
                return networks
            else:
                warning_print(f"Failed to list networks: {result.stderr}")
                return []
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_print(f"Error listing Docker networks: {e}")
            return []

    def get_network_info(self, network_name):
        """Get detailed information about a Docker network."""
        try:
            result = subprocess.run(
                ["docker", "network", "inspect", network_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                network_info = json.loads(result.stdout)
                return network_info[0] if network_info else None
            else:
                warning_print(f"Failed to get network info: {result.stderr}")
                return None
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            error_print(f"Error getting Docker network info: {e}")
            return None

    def ensure_netflux5g_network(self):
        """Ensure the netflux5g network exists, create if needed."""
        return self.create_netflux5g_network_if_needed()
