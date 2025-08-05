"""
Deployment Status Monitor for NetFlux5G Editor

This module creates a monitoring panel that shows the real-time status of deployed
components in the topology. It appears after running a topology and monitors:
- Container status (running, stopped, error, restarting)
- 5G Core components
- gNB and UE components
- Network components (APs, STAs, Hosts)
- Controllers and other services

The panel is positioned in the upper right corner of the canvas.
"""

import os
import subprocess
import time
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QWidget, QProgressBar,
                           QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QIcon
from utils.debug import debug_print, error_print, warning_print
from utils.docker_utils import DockerUtils

class ComponentStatusWorker(QThread):
    """Worker thread to check component status without blocking the UI."""
    
    status_updated = pyqtSignal(dict)  # {component_name: status_info}
    
    def __init__(self, deployed_components):
        super().__init__()
        self.deployed_components = deployed_components
        self.running = True
        
    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        
    def run(self):
        """Main monitoring loop."""
        while self.running:
            status_dict = {}
            
            for component_name, component_info in self.deployed_components.items():
                try:
                    component_type = component_info.get('type', 'unknown')
                    container_name = component_info.get('container_name', component_name)
                    
                    # Check container status
                    if DockerUtils.container_exists(container_name):
                        if DockerUtils.is_container_running(container_name):
                            # Get detailed status
                            status_info = self._get_detailed_status(container_name, component_type)
                            status_dict[component_name] = {
                                'status': 'running',
                                'details': status_info,
                                'type': component_type,
                                'health': self._check_component_health(container_name, component_type),
                                'connections': self._check_component_connections(container_name, component_type)
                            }
                        else:
                            # Container exists but not running
                            exit_code = self._get_exit_code(container_name)
                            status_dict[component_name] = {
                                'status': 'stopped',
                                'details': f'Exit code: {exit_code}',
                                'type': component_type,
                                'health': 'unhealthy',
                                'connections': 'disconnected'
                            }
                    else:
                        # Container doesn't exist
                        status_dict[component_name] = {
                            'status': 'not_found',
                            'details': 'Container not found',
                            'type': component_type,
                            'health': 'unknown',
                            'connections': 'unknown'
                        }
                        
                except Exception as e:
                    status_dict[component_name] = {
                        'status': 'error',
                        'details': f'Error checking status: {str(e)}',
                        'type': component_info.get('type', 'unknown'),
                        'health': 'error',
                        'connections': 'error'
                    }
            
            self.status_updated.emit(status_dict)
            
            # Wait 3 seconds before next check
            for _ in range(30):  # 30 * 0.1 = 3 seconds
                if not self.running:
                    break
                self.msleep(100)
    
    def _get_detailed_status(self, container_name, component_type):
        """Get detailed status information for a container."""
        try:
            # Get basic container status
            cmd = ['docker', 'inspect', container_name, '--format', '{{.State.Status}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                state = result.stdout.strip()
                
                # Get uptime
                cmd_uptime = ['docker', 'inspect', container_name, '--format', '{{.State.StartedAt}}']
                uptime_result = subprocess.run(cmd_uptime, capture_output=True, text=True, timeout=5)
                
                uptime = "Unknown"
                if uptime_result.returncode == 0:
                    started_at = uptime_result.stdout.strip()
                    uptime = f"Started: {started_at[:19]}"  # Just date and time
                
                return f"{state.title()} ({uptime})"
            else:
                return "Unknown status"
                
        except Exception as e:
            return f"Status check failed: {str(e)}"
    
    def _get_exit_code(self, container_name):
        """Get the exit code of a stopped container."""
        try:
            cmd = ['docker', 'inspect', container_name, '--format', '{{.State.ExitCode}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Unknown"
        except Exception:
            return "Unknown"
    
    def _check_component_health(self, container_name, component_type):
        """Check component-specific health indicators."""
        try:
            # For 5G components, check if their services are running
            if component_type in ['AMF', 'SMF', 'UPF', 'NRF', 'UDR', 'UDM', 'AUSF', 'PCF', 'NSSF', 'BSF', 'SCP']:
                # For Mininet containers (mn.xxx), we need to check inside the container
                # Try to check if the Open5GS service process is running
                service_name = f"open5gs-{component_type.lower()}d"
                
                # First try to check if the service is running with pgrep
                cmd = ['docker', 'exec', container_name, 'pgrep', '-f', service_name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    return 'healthy'
                
                # If pgrep doesn't work, try ps command
                cmd = ['docker', 'exec', container_name, 'ps', 'aux']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and service_name in result.stdout:
                    return 'healthy'
                
                # If service is not found, mark as service down
                return 'service_down'
            
            elif component_type in ['GNB']:
                # Check if nr-gnb is running
                # Try multiple possible process names for gNB
                gnb_processes = ['nr-gnb', 'gnb', 'ueransim-gnb']
                for process_name in gnb_processes:
                    cmd = ['docker', 'exec', container_name, 'pgrep', '-f', process_name]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        return 'healthy'
                
                # Try ps command for gNB
                cmd = ['docker', 'exec', container_name, 'ps', 'aux']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for process_name in gnb_processes:
                        if process_name in result.stdout:
                            return 'healthy'
                
                return 'service_down'
            
            elif component_type in ['UE']:
                # Check if nr-ue is running
                # Try multiple possible process names for UE
                ue_processes = ['nr-ue', 'ue', 'ueransim-ue']
                for process_name in ue_processes:
                    cmd = ['docker', 'exec', container_name, 'pgrep', '-f', process_name]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        return 'healthy'
                
                # Try ps command for UE
                cmd = ['docker', 'exec', container_name, 'ps', 'aux']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for process_name in ue_processes:
                        if process_name in result.stdout:
                            return 'healthy'
                
                return 'service_down'
            
            else:
                # For other components, if container is running, consider healthy
                return 'healthy'
                
        except subprocess.TimeoutExpired:
            return 'timeout'
        except Exception as e:
            debug_print(f"Health check error for {container_name}: {e}")
            return 'unknown'
    
    def _check_component_connections(self, container_name, component_type):
        """Check component-specific connection status from log files."""
        try:
            # Extract the actual component name from container name (remove mn. prefix)
            actual_component_name = container_name.replace('mn.', '')
            log_file_path = f"/logging/{actual_component_name}.log"
            
            debug_print(f"Checking connections for {container_name} ({component_type}) - log file: {log_file_path}")
            
            # Read log file from inside the container
            cmd = ['docker', 'exec', container_name, 'cat', log_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Try alternative: check if log file exists
                check_cmd = ['docker', 'exec', container_name, 'ls', '/logging/']
                check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)
                if check_result.returncode == 0:
                    debug_print(f"Available log files in {container_name}: {check_result.stdout}")
                debug_print(f"Log file not found for {container_name}: {result.stderr}")
                return 'log_not_found'
            
            log_content = result.stdout + result.stderr
            debug_print(f"Read {len(log_content)} characters from log file for {container_name}")
            
            # Check connection status based on component type
            connection_status = 'unknown'
            if component_type in ['AMF', 'SMF', 'UPF', 'NRF', 'UDR', 'UDM', 'AUSF', 'PCF', 'NSSF', 'BSF', 'SCP']:
                connection_status = self._check_5g_core_connections(log_content, component_type)
            elif component_type == 'GNB':
                connection_status = self._check_gnb_connections(log_content)
            elif component_type == 'UE':
                connection_status = self._check_ue_connections(log_content)
            else:
                connection_status = 'not_applicable'
            
            debug_print(f"Connection status for {container_name}: {connection_status}")
            return connection_status
                
        except subprocess.TimeoutExpired:
            debug_print(f"Timeout checking connections for {container_name}")
            return 'timeout'
        except Exception as e:
            debug_print(f"Connection check error for {container_name}: {e}")
            return 'unknown'
    
    def _check_5g_core_connections(self, log_content, component_type):
        """Check 5G Core component connections from logs."""
        connections_status = []
        
        # Check NRF registration (most 5G core components register with NRF)
        if 'NF registered' in log_content:
            connections_status.append('NRF: registered')
        elif 'Failed to connect' in log_content and 'nrf' in log_content.lower():
            connections_status.append('NRF: failed')
        
        # Component-specific connection checks
        if component_type == 'UPF':
            # Check PFCP associations (UPF connects to SMF via PFCP)
            if 'PFCP associated' in log_content:
                connections_status.append('SMF: connected')
            
            # Check for UE sessions (indicates active data plane)
            if 'Number of UPF-Sessions' in log_content:
                import re
                sessions = re.findall(r'Number of UPF-Sessions is now (\d+)', log_content)
                if sessions:
                    last_count = sessions[-1]
                    connections_status.append(f'UE Sessions: {last_count}')
        
        elif component_type == 'AMF':
            # Check N2 interface connections (gNB to AMF)
            if 'NG Setup Request' in log_content or 'NG Setup Response' in log_content:
                connections_status.append('gNB: connected')
            
            # Check for UE registrations
            if 'Registration accept' in log_content or 'UE Context' in log_content:
                connections_status.append('UE: registered')
        
        elif component_type == 'UDR':
            # Check MongoDB connection
            if 'MongoDB URI' in log_content and 'initialize...done' in log_content:
                connections_status.append('MongoDB: connected')
        
        elif component_type in ['UDM', 'AUSF']:
            # Check SBI connections to UDR
            if 'Setup NF Instance [type:UDR]' in log_content:
                connections_status.append('UDR: connected')
        
        elif component_type == 'SMF':
            # Check N4 interface to UPF
            if 'UPF associated' in log_content or 'PFCP' in log_content:
                connections_status.append('UPF: connected')
        
        # Check SCP connections (many components use SCP for service communication)
        if 'Setup NF EndPoint' in log_content and 'scp' in log_content.lower():
            connections_status.append('SCP: connected')
        
        # Return connection status
        if not connections_status:
            if 'initialize...done' in log_content:
                return 'initialized'
            else:
                return 'starting'
        else:
            return ', '.join(connections_status)
    
    def _check_gnb_connections(self, log_content):
        """Check gNB connections from logs."""
        connections_status = []
        
        # Check SCTP connection to AMF
        if 'SCTP' in log_content and ('connected' in log_content or 'established' in log_content):
            connections_status.append('AMF: connected')
        elif 'Connection refused' in log_content and 'amf' in log_content.lower():
            connections_status.append('AMF: failed')
        
        # Check for UE connections
        if 'UE context' in log_content or 'RRC Setup' in log_content:
            connections_status.append('UE: connected')
        
        # Check NG setup with AMF
        if 'NG Setup Request' in log_content or 'NG Setup Response' in log_content:
            connections_status.append('NG Setup: success')
        
        if not connections_status:
            if 'UERANSIM' in log_content and 'started' in log_content:
                return 'started'
            else:
                return 'starting'
        else:
            return ', '.join(connections_status)
    
    def _check_ue_connections(self, log_content):
        """Check UE connections from logs."""
        connections_status = []
        
        # Check RRC connection
        if 'RRC connection established' in log_content:
            connections_status.append('gNB: connected')
        elif 'Signal lost for cell' in log_content or 'Radio link failure' in log_content:
            connections_status.append('gNB: disconnected')
        
        # Check NAS registration
        if 'Initial Registration is successful' in log_content:
            connections_status.append('AMF: registered')
        elif 'Registration failed' in log_content:
            connections_status.append('AMF: failed')
        
        # Check PDU session establishment
        if 'PDU Session establishment is successful' in log_content:
            connections_status.append('PDU Session: established')
        elif 'PDU Session Establishment Reject' in log_content:
            connections_status.append('PDU Session: failed')
        
        # Check TUN interface (data connectivity)
        if 'TUN interface' in log_content and 'is up' in log_content:
            import re
            tun_match = re.search(r'TUN interface\[([^,]+), ([^\]]+)\]', log_content)
            if tun_match:
                connections_status.append(f'Data: {tun_match.group(2)}')
        
        if not connections_status:
            if 'PLMN-SEARCH' in log_content:
                return 'searching'
            else:
                return 'starting'
        else:
            return ', '.join(connections_status)

class ComponentStatusWidget(QFrame):
    """Widget to display status of a single component."""
    
    def __init__(self, component_name, component_type, parent=None):
        super().__init__(parent)
        self.component_name = component_name
        self.component_type = component_type
        
        self.setupUI()
        
    def setupUI(self):
        """Set up the component status widget UI."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 2px;
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)
        
        # Component icon and name
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_label)
        
        # Component name
        self.name_label = QLabel(self.component_name)
        self.name_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.name_label.setStyleSheet("border: none; background: transparent; color: #2c3e50;")
        layout.addWidget(self.name_label)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Segoe UI", 12))
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.status_indicator)
        
        # Status text
        self.status_label = QLabel("Checking...")
        self.status_label.setFont(QFont("Segoe UI", 8))
        self.status_label.setStyleSheet("border: none; background: transparent; color: #6c757d;")
        layout.addWidget(self.status_label)
        
        # Connection status indicator
        self.connection_indicator = QLabel("⚪")
        self.connection_indicator.setFont(QFont("Segoe UI", 10))
        self.connection_indicator.setAlignment(Qt.AlignCenter)
        self.connection_indicator.setFixedSize(16, 16)
        self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #007acc;")
        self.connection_indicator.setToolTip("Connection status: checking...")
        layout.addWidget(self.connection_indicator)
        
        layout.addStretch()
        
        # Set component icon
        self.setComponentIcon()
        
    def setComponentIcon(self):
        """Set the appropriate icon for the component type."""
        icon_map = {
            'AMF': '🌐', 'SMF': '📶', 'UPF': '🔀', 'NRF': '📋',
            'UDR': '💾', 'UDM': '👤', 'AUSF': '🔐', 'PCF': '⚙️',
            'NSSF': '🎯', 'BSF': '🔧', 'SCP': '🔗',
            'GNB': '📡', 'UE': '📱',
            'AP': '📶', 'STA': '💻', 'Host': '🖥️',
            'Controller': '🎮', 'Router': '🔀', 'Switch': '🔄'
        }
        
        icon_text = icon_map.get(self.component_type, '📦')
        self.icon_label.setText(icon_text)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
    def updateStatus(self, status_info):
        """Update the status display of this component."""
        status = status_info.get('status', 'unknown')
        details = status_info.get('details', '')
        health = status_info.get('health', 'unknown')
        connections = status_info.get('connections', 'unknown')
        
        debug_print(f"Updating status for {self.component_name}: status={status}, health={health}, connections={connections}")
        
        # Update status indicator color and text based on both container status and connections
        if status == 'running':
            if health == 'healthy':
                # Determine status text based on connection state
                status_text = self._getConnectionBasedStatus(connections, self.component_type)
                
                # Set color based on connection quality
                if connections and ('Connected' in status_text or 'Registered' in status_text or 'Active' in status_text):
                    self.status_indicator.setStyleSheet("color: #28a745; border: none; background: transparent;")
                    self.status_label.setStyleSheet("border: none; background: transparent; color: #28a745; font-weight: bold;")
                elif 'Connecting' in status_text or 'Searching' in status_text or 'Initializing' in status_text:
                    self.status_indicator.setStyleSheet("color: #ffc107; border: none; background: transparent;")
                    self.status_label.setStyleSheet("border: none; background: transparent; color: #ffc107; font-weight: bold;")
                elif 'Issues' in status_text or 'Disconnected' in status_text:
                    self.status_indicator.setStyleSheet("color: #fd7e14; border: none; background: transparent;")
                    self.status_label.setStyleSheet("border: none; background: transparent; color: #fd7e14; font-weight: bold;")
                else:
                    self.status_indicator.setStyleSheet("color: #17a2b8; border: none; background: transparent;")
                    self.status_label.setStyleSheet("border: none; background: transparent; color: #17a2b8; font-weight: bold;")
                
                self.status_label.setText(status_text)
            elif health == 'service_down':
                self.status_indicator.setStyleSheet("color: #ffc107; border: none; background: transparent;")
                self.status_label.setText("Service Down")
                self.status_label.setStyleSheet("border: none; background: transparent; color: #ffc107; font-weight: bold;")
            else:
                self.status_indicator.setStyleSheet("color: #17a2b8; border: none; background: transparent;")
                self.status_label.setText("Starting")
                self.status_label.setStyleSheet("border: none; background: transparent; color: #17a2b8; font-weight: bold;")
        elif status == 'stopped':
            self.status_indicator.setStyleSheet("color: #dc3545; border: none; background: transparent;")
            self.status_label.setText("Stopped")
            self.status_label.setStyleSheet("border: none; background: transparent; color: #dc3545; font-weight: bold;")
        elif status == 'not_found':
            self.status_indicator.setStyleSheet("color: #6c757d; border: none; background: transparent;")
            self.status_label.setText("Not Found")
            self.status_label.setStyleSheet("border: none; background: transparent; color: #6c757d; font-weight: bold;")
        else:  # error or unknown
            self.status_indicator.setStyleSheet("color: #dc3545; border: none; background: transparent;")
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("border: none; background: transparent; color: #dc3545; font-weight: bold;")
        
        # Update connection indicator
        self._updateConnectionIndicator(connections)
        
        # Set tooltip with detailed information
        tooltip_text = f"{self.component_name}\nType: {self.component_type}\nStatus: {status}\nDetails: {details}"
        if connections and connections != 'unknown':
            tooltip_text += f"\nConnections: {connections}"
        self.setToolTip(tooltip_text)
    
    def _updateConnectionIndicator(self, connections):
        """Update the connection status indicator."""
        if connections == 'unknown' or connections == 'not_applicable':
            self.connection_indicator.setText("⚪")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #6c757d;")
            self.connection_indicator.setToolTip("Connection status unknown")
        elif connections == 'log_not_found':
            self.connection_indicator.setText("�")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #ffc107;")
            self.connection_indicator.setToolTip("Log file not found")
        elif connections == 'disconnected' or connections == 'error':
            self.connection_indicator.setText("🔴")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #dc3545;")
            self.connection_indicator.setToolTip("Disconnected or error")
        elif connections in ['starting', 'searching', 'initialized']:
            self.connection_indicator.setText("🟡")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #ffc107;")
            self.connection_indicator.setToolTip(f"Status: {connections}")
        elif 'failed' in connections.lower() or 'reject' in connections.lower():
            self.connection_indicator.setText("🟠")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #ffc107;")
            self.connection_indicator.setToolTip(f"Connection issues: {connections}")
        else:
            # Has active connections
            self.connection_indicator.setText("🟢")
            self.connection_indicator.setStyleSheet("border: none; background: transparent; color: #28a745;")
            self.connection_indicator.setToolTip(f"Connected: {connections}")
    
    def _getConnectionBasedStatus(self, connections, component_type):
        """Get status text based on connection state and component type."""
        if connections == 'unknown' or connections == 'not_applicable':
            return "Running"
        elif connections == 'log_not_found':
            return "Running (No Logs)"
        elif connections == 'disconnected' or connections == 'error':
            return "Disconnected"
        elif connections in ['starting', 'searching', 'initialized']:
            if component_type == 'UE':
                return "Searching Network"
            elif component_type in ['AMF', 'SMF', 'UPF', 'NRF', 'UDR', 'UDM', 'AUSF', 'PCF', 'NSSF', 'BSF', 'SCP']:
                return "Initializing"
            elif component_type == 'GNB':
                return "Starting"
            else:
                return "Starting"
        elif 'failed' in connections.lower() or 'reject' in connections.lower():
            return "Connection Issues"
        else:
            # Has active connections - provide specific status based on component type
            if component_type == 'UE':
                if 'PDU Session: established' in connections:
                    return "Connected & Registered"
                elif 'AMF: registered' in connections:
                    return "Registered"
                elif 'gNB: connected' in connections:
                    return "Connected to gNB"
                else:
                    return "Connecting"
            elif component_type == 'GNB':
                if 'AMF: connected' in connections:
                    return "Connected to AMF"
                elif 'UE: connected' in connections:
                    return "UE Connected"
                else:
                    return "Connected"
            elif component_type == 'AMF':
                if 'UE: registered' in connections and 'gNB: connected' in connections:
                    return "Fully Connected"
                elif 'UE: registered' in connections:
                    return "UE Registered"
                elif 'gNB: connected' in connections:
                    return "gNB Connected"
                else:
                    return "Connected"
            elif component_type == 'UPF':
                if 'UE Sessions:' in connections:
                    import re
                    sessions = re.search(r'UE Sessions: (\d+)', connections)
                    if sessions:
                        count = sessions.group(1)
                        return f"Active ({count} UE sessions)"
                elif 'SMF: connected' in connections:
                    return "Connected to SMF"
                else:
                    return "Connected"
            elif component_type in ['UDR', 'UDM', 'AUSF']:
                if 'MongoDB: connected' in connections:
                    return "DB Connected"
                elif 'UDR: connected' in connections:
                    return "UDR Connected"
                else:
                    return "Connected"
            elif component_type == 'NRF':
                if 'NF registered' in connections:
                    return "NF Registry Active"
                else:
                    return "Connected"
            else:
                return "Connected"

class DeploymentMonitorPanel(QFrame):
    """Main deployment monitoring panel."""
    
    monitor_closed = pyqtSignal()
    
    def __init__(self, main_window, deployed_components, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.deployed_components = deployed_components
        self.component_widgets = {}
        self.monitor_worker = None
        
        # Movement and resize state
        self.dragging = False
        self.resizing = False
        self.drag_start_pos = None
        self.resize_start_pos = None
        self.resize_start_size = None
        self.resize_edge = None
        
        self.setupUI()
        self.startMonitoring()
        
        # Enable mouse tracking for cursor changes
        self.setMouseTracking(True)
        
    def setupUI(self):
        """Set up the monitoring panel UI."""
        # Make panel resizable (remove fixed size)
        self.setMinimumSize(280, 200)
        self.resize(320, 400)  # Initial size
        
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #007acc;
                border-radius: 12px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(3, 3)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with title and close button (this will be the drag handle)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #007acc;
                border: none;
                border-radius: 8px;
                margin-bottom: 4px;
            }
        """)
        self.header_frame.setFixedHeight(32)
        self.header_frame.setCursor(Qt.SizeAllCursor)  # Indicate draggable
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        title_label = QLabel("Deployment Status")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: white; border: none; background: transparent;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        close_button.clicked.connect(self.closePanel)
        header_layout.addWidget(close_button)
        
        layout.addWidget(self.header_frame)
        
        # Summary stats
        self.summary_label = QLabel("Checking components...")
        self.summary_label.setFont(QFont("Segoe UI", 9))
        self.summary_label.setStyleSheet("color: #6c757d; border: none; background: transparent; padding: 4px;")
        layout.addWidget(self.summary_label)
        
        # Scrollable area for components
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c757d;
            }
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for components
        self.components_widget = QWidget()
        self.components_layout = QVBoxLayout(self.components_widget)
        self.components_layout.setContentsMargins(4, 4, 4, 4)
        self.components_layout.setSpacing(3)
        
        scroll_area.setWidget(self.components_widget)
        layout.addWidget(scroll_area)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005ea3;
            }
            QPushButton:pressed {
                background-color: #004a82;
            }
        """)
        refresh_button.clicked.connect(self.refreshStatus)
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_button)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Create component widgets
        self.createComponentWidgets()
        
    def createComponentWidgets(self):
        """Create status widgets for each deployed component."""
        for component_name, component_info in self.deployed_components.items():
            component_type = component_info.get('type', 'unknown')
            widget = ComponentStatusWidget(component_name, component_type)
            self.component_widgets[component_name] = widget
            self.components_layout.addWidget(widget)
        
        # Add stretch to push components to top
        self.components_layout.addStretch()
        
    def startMonitoring(self):
        """Start the monitoring worker thread."""
        if self.monitor_worker:
            self.monitor_worker.stop()
            self.monitor_worker.wait()
        
        self.monitor_worker = ComponentStatusWorker(self.deployed_components)
        self.monitor_worker.status_updated.connect(self.updateComponentStatus)
        self.monitor_worker.start()
        
    def updateComponentStatus(self, status_dict):
        """Update the status of all components."""
        running_count = 0
        stopped_count = 0
        error_count = 0
        total_count = len(status_dict)
        
        for component_name, status_info in status_dict.items():
            if component_name in self.component_widgets:
                self.component_widgets[component_name].updateStatus(status_info)
                
                # Count statuses for summary
                status = status_info.get('status', 'unknown')
                if status == 'running':
                    running_count += 1
                elif status == 'stopped' or status == 'not_found':
                    stopped_count += 1
                else:
                    error_count += 1
        
        # Update summary
        summary_text = f"Total: {total_count} | "
        summary_text += f"✅ Running: {running_count} | "
        summary_text += f"🔴 Stopped: {stopped_count}"
        if error_count > 0:
            summary_text += f" | ❌ Errors: {error_count}"
        
        self.summary_label.setText(summary_text)
        
    def refreshStatus(self):
        """Manually refresh the status."""
        if self.monitor_worker:
            # Force an immediate status check
            self.summary_label.setText("Refreshing...")
            
    def closePanel(self):
        """Close the monitoring panel."""
        if self.monitor_worker:
            self.monitor_worker.stop()
            self.monitor_worker.wait()
        
        self.monitor_closed.emit()
        self.hide()
        self.deleteLater()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for dragging and resizing."""
        if event.button() == Qt.LeftButton:
            # Check if click is in header area (for dragging)
            header_rect = self.header_frame.geometry()
            if header_rect.contains(event.pos()):
                self.dragging = True
                self.drag_start_pos = event.globalPos() - self.pos()
                return
            
            # Check if click is near edges (for resizing)
            edge = self._getResizeEdge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.resize_start_pos = event.globalPos()
                self.resize_start_size = self.size()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging and resizing."""
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_pos)
            return
        
        if self.resizing and event.buttons() == Qt.LeftButton:
            self._handleResize(event.globalPos())
            return
        
        # Update cursor based on position
        edge = self._getResizeEdge(event.pos())
        if edge:
            if edge in ['top', 'bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif edge in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif edge in ['top-left', 'bottom-right']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge in ['top-right', 'bottom-left']:
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def _getResizeEdge(self, pos):
        """Determine which edge is being hovered for resizing."""
        margin = 8  # Resize handle margin
        rect = self.rect()
        
        left = pos.x() <= margin
        right = pos.x() >= rect.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= rect.height() - margin
        
        if top and left:
            return 'top-left'
        elif top and right:
            return 'top-right'
        elif bottom and left:
            return 'bottom-left'
        elif bottom and right:
            return 'bottom-right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        elif left:
            return 'left'
        elif right:
            return 'right'
        
        return None
    
    def _handleResize(self, global_pos):
        """Handle window resizing."""
        delta = global_pos - self.resize_start_pos
        new_size = self.resize_start_size
        new_pos = self.pos()
        
        if 'right' in self.resize_edge:
            new_size.setWidth(max(self.minimumWidth(), new_size.width() + delta.x()))
        elif 'left' in self.resize_edge:
            new_width = max(self.minimumWidth(), new_size.width() - delta.x())
            new_pos.setX(new_pos.x() + (new_size.width() - new_width))
            new_size.setWidth(new_width)
        
        if 'bottom' in self.resize_edge:
            new_size.setHeight(max(self.minimumHeight(), new_size.height() + delta.y()))
        elif 'top' in self.resize_edge:
            new_height = max(self.minimumHeight(), new_size.height() - delta.y())
            new_pos.setY(new_pos.y() + (new_size.height() - new_height))
            new_size.setHeight(new_height)
        
        self.resize(new_size)
        self.move(new_pos)
        
    def positionOnCanvas(self):
        """Position the panel in the upper right corner of the canvas."""
        if hasattr(self.main_window, 'canvas_view'):
            canvas_view = self.main_window.canvas_view
            canvas_rect = canvas_view.rect()
            
            # Position in upper right with some margin
            x = canvas_rect.width() - self.width() - 20
            y = 20
            
            # Make sure we're within bounds
            x = max(20, x)
            y = max(20, y)
            
            self.move(x, y)
            self.raise_()

class DeploymentMonitorManager:
    """Manager for the deployment monitoring functionality."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.monitor_panel = None
        
    def showMonitoringPanel(self):
        """Show the deployment monitoring panel after topology is running."""
        # Get deployed components from the topology
        deployed_components = self.extractDeployedComponents()
        
        if not deployed_components:
            debug_print("No deployed components found, not showing monitoring panel")
            return
        
        debug_print(f"Showing monitoring panel for {len(deployed_components)} components:")
        for name, info in deployed_components.items():
            debug_print(f"  - {name}: {info['container_name']} ({info['type']})")
        
        # Close existing panel if any
        if self.monitor_panel:
            self.monitor_panel.closePanel()
        
        # Create new monitoring panel
        self.monitor_panel = DeploymentMonitorPanel(
            self.main_window, 
            deployed_components, 
            self.main_window.canvas_view
        )
        
        # Position and show the panel
        self.monitor_panel.positionOnCanvas()
        self.monitor_panel.show()
        
        # Connect close signal
        self.monitor_panel.monitor_closed.connect(self.onMonitorPanelClosed)
        
        debug_print(f"Deployment monitoring panel shown with {len(deployed_components)} components")
        
    def extractDeployedComponents(self):
        """Extract deployed components from the exported Mininet script."""
        deployed_components = {}
        
        # Find the most recent exported Mininet script
        mininet_script_path = self._findLatestMininetScript()
        if not mininet_script_path:
            debug_print("No exported Mininet script found")
            return deployed_components
        
        debug_print(f"Reading deployed components from: {mininet_script_path}")
        
        try:
            with open(mininet_script_path, 'r') as f:
                script_content = f.read()
            
            # Parse Docker containers from the script
            deployed_components.update(self._parseDockerContainers(script_content))
            
            # Parse Docker stations (UE devices) from the script  
            deployed_components.update(self._parseDockerStations(script_content))
            
        except Exception as e:
            error_print(f"Error reading Mininet script: {e}")
            return deployed_components
        
        debug_print(f"Extracted {len(deployed_components)} deployed components from Mininet script:")
        for name, info in deployed_components.items():
            debug_print(f"  - {name}: {info['container_name']} ({info['type']})")
        
        return deployed_components
    
    def _findLatestMininetScript(self):
        """Find the most recent exported Mininet script."""
        try:
            # Get the export/mininet directory
            if hasattr(self.main_window, 'manager') and hasattr(self.main_window.manager, 'file_manager'):
                # Try to get the workspace path
                export_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'export', 'mininet')
            else:
                # Fallback to relative path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                export_base = os.path.join(os.path.dirname(current_dir), 'export', 'mininet')
            
            if not os.path.exists(export_base):
                debug_print(f"Export directory not found: {export_base}")
                return None
            
            # Find all export directories
            export_dirs = []
            for item in os.listdir(export_base):
                item_path = os.path.join(export_base, item)
                if os.path.isdir(item_path) and item.startswith('netflux5g_export_'):
                    export_dirs.append(item_path)
            
            if not export_dirs:
                debug_print("No export directories found")
                return None
            
            # Sort by modification time (newest first)
            export_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Look for the Python script in the most recent directory
            latest_dir = export_dirs[0]
            script_path = os.path.join(latest_dir, 'netflux5g_topology.py')
            
            if os.path.exists(script_path):
                debug_print(f"Found latest Mininet script: {script_path}")
                return script_path
            else:
                debug_print(f"No topology script found in: {latest_dir}")
                return None
                
        except Exception as e:
            error_print(f"Error finding Mininet script: {e}")
            return None
    
    def _parseDockerContainers(self, script_content):
        """Parse Docker containers from the Mininet script content."""
        components = {}
        
        import re
        
        # Parse Docker containers - look for net.addDocker() calls
        docker_pattern = r"(\w+)\s*=\s*net\.addDocker\(\s*['\"](\w+)['\"].*?dimage\s*=\s*['\"]([^'\"]+)['\"]"
        docker_matches = re.findall(docker_pattern, script_content, re.MULTILINE | re.DOTALL)
        
        for var_name, container_name, image in docker_matches:
            # Determine component type from image
            component_type = self._determineComponentTypeFromImage(image, container_name)
            
            components[container_name] = {
                'type': component_type,
                'container_name': f"mn.{container_name}",
                'parent_component': None,
                'base_name': container_name,
                'variable_name': var_name,
                'image': image
            }
            
        return components
    
    def _parseDockerStations(self, script_content):
        """Parse Docker stations (UE devices) from the Mininet script content."""
        components = {}
        
        import re
        
        # Parse Docker stations - look for net.addStation() calls with dimage parameter
        station_pattern = r"(\w+)\s*=\s*net\.addStation\(\s*['\"](\w+)['\"].*?dimage\s*=\s*['\"]([^'\"]+)['\"]"
        station_matches = re.findall(station_pattern, script_content, re.MULTILINE | re.DOTALL)
        
        for var_name, station_name, image in station_matches:
            # Determine component type from image
            component_type = self._determineComponentTypeFromImage(image, station_name)
            
            components[station_name] = {
                'type': component_type,
                'container_name': f"mn.{station_name}",
                'parent_component': None,
                'base_name': station_name,
                'variable_name': var_name,
                'image': image
            }
            
        return components
    
    def _determineComponentTypeFromImage(self, image, container_name):
        """Determine component type from Docker image and container name."""
        container_lower = container_name.lower()
        image_lower = image.lower()
        
        # Check for 5G Core components based on container name
        if any(x in container_lower for x in ['upf']):
            return 'UPF'
        elif any(x in container_lower for x in ['amf']):
            return 'AMF'
        elif any(x in container_lower for x in ['smf']):
            return 'SMF'
        elif any(x in container_lower for x in ['nrf']):
            return 'NRF'
        elif any(x in container_lower for x in ['scp']):
            return 'SCP'
        elif any(x in container_lower for x in ['ausf']):
            return 'AUSF'
        elif any(x in container_lower for x in ['bsf']):
            return 'BSF'
        elif any(x in container_lower for x in ['nssf']):
            return 'NSSF'
        elif any(x in container_lower for x in ['pcf']):
            return 'PCF'
        elif any(x in container_lower for x in ['udm']):
            return 'UDM'
        elif any(x in container_lower for x in ['udr']):
            return 'UDR'
        
        # Check for RAN components
        elif any(x in container_lower for x in ['gnb', 'enb']):
            return 'GNB'
        elif any(x in container_lower for x in ['ue']):
            return 'UE'
        
        # Check based on image
        elif 'open5gs' in image_lower:
            return '5GCore'
        elif 'ueransim' in image_lower:
            if 'gnb' in container_lower:
                return 'GNB'
            elif 'ue' in container_lower:
                return 'UE'
            else:
                return 'UERANSIM'
        
        # Default
        return 'Container'
        
    def hideMonitoringPanel(self):
        """Hide the deployment monitoring panel."""
        if self.monitor_panel:
            self.monitor_panel.closePanel()
            
    def onMonitorPanelClosed(self):
        """Handle when the monitoring panel is closed."""
        self.monitor_panel = None
        
    def isMonitoringActive(self):
        """Check if monitoring is currently active."""
        return self.monitor_panel is not None
