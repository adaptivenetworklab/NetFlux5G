"""
Log Viewer Widget for NetFlux5G Components

This module provides a log viewer window that displays real-time logs
from deployed components including 5G Core, gNBs, UEs, and other network components.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QComboBox, QCheckBox, 
                           QSpinBox, QGroupBox, QSplitter, QFileDialog,
                           QMessageBox, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QTextCursor, QIcon
import subprocess
import os
import re
from utils.debug import debug_print, error_print, warning_print


class DeployedComponentsExtractor:
    """Extract deployed components from the exported Mininet script."""
    
    @staticmethod
    def extractDeployedComponents():
        """Extract deployed components from the exported Mininet script."""
        deployed_components = {}
        
        # Find the most recent exported Mininet script
        mininet_script_path = DeployedComponentsExtractor._findLatestMininetScript()
        if not mininet_script_path:
            debug_print("No exported Mininet script found")
            return deployed_components
        
        debug_print(f"Reading deployed components from: {mininet_script_path}")
        
        try:
            with open(mininet_script_path, 'r') as f:
                script_content = f.read()
            
            # Parse Docker containers from the script
            deployed_components.update(DeployedComponentsExtractor._parseDockerContainers(script_content))
            
            # Parse Docker stations (UE devices) from the script  
            deployed_components.update(DeployedComponentsExtractor._parseDockerStations(script_content))
            
        except Exception as e:
            error_print(f"Error reading Mininet script: {e}")
            return deployed_components
        
        debug_print(f"Extracted {len(deployed_components)} deployed components from Mininet script:")
        for name, info in deployed_components.items():
            debug_print(f"  - {name}: {info['container_name']} ({info['type']})")
        
        return deployed_components
    
    @staticmethod
    def _findLatestMininetScript():
        """Find the most recent exported Mininet script."""
        try:
            # Get the export/mininet directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            export_base = os.path.join(current_dir, 'export', 'mininet')
            
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
    
    @staticmethod
    def _parseDockerContainers(script_content):
        """Parse Docker containers from the Mininet script content."""
        components = {}
        
        # Parse Docker containers - look for net.addDocker() calls
        docker_pattern = r"(\w+)\s*=\s*net\.addDocker\(\s*['\"](\w+)['\"].*?dimage\s*=\s*['\"]([^'\"]+)['\"]"
        docker_matches = re.findall(docker_pattern, script_content, re.MULTILINE | re.DOTALL)
        
        for var_name, container_name, image in docker_matches:
            # Determine component type from image
            component_type = DeployedComponentsExtractor._determineComponentTypeFromImage(image, container_name)
            
            components[container_name] = {
                'type': component_type,
                'container_name': f"mn.{container_name}",
                'parent_component': None,
                'base_name': container_name,
                'variable_name': var_name,
                'image': image
            }
            
        return components
    
    @staticmethod
    def _parseDockerStations(script_content):
        """Parse Docker stations (UE devices) from the Mininet script content."""
        components = {}
        
        # Parse Docker stations - look for net.addStation() calls with dimage parameter
        station_pattern = r"(\w+)\s*=\s*net\.addStation\(\s*['\"](\w+)['\"].*?dimage\s*=\s*['\"]([^'\"]+)['\"]"
        station_matches = re.findall(station_pattern, script_content, re.MULTILINE | re.DOTALL)
        
        for var_name, station_name, image in station_matches:
            # Determine component type from image
            component_type = DeployedComponentsExtractor._determineComponentTypeFromImage(image, station_name)
            
            components[station_name] = {
                'type': component_type,
                'container_name': f"mn.{station_name}",
                'parent_component': None,
                'base_name': station_name,
                'variable_name': var_name,
                'image': image
            }
            
        return components
    
    @staticmethod
    def _determineComponentTypeFromImage(image, container_name):
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


class LogReaderWorker(QThread):
    """Worker thread to read logs without blocking the UI."""
    
    new_log_data = pyqtSignal(str)  # Signal to emit new log data
    log_error = pyqtSignal(str)     # Signal to emit error messages
    
    def __init__(self, container_name, component_type, follow=True, lines=100):
        super().__init__()
        self.container_name = container_name
        self.component_type = component_type
        self.follow = follow
        self.lines = lines
        self.running = True
        self.log_file_path = None
        self.process = None
        
        # Determine log file path based on component type
        self._determine_log_file_path()
        
    def _determine_log_file_path(self):
        """Determine the log file path based on component type."""
        # Remove 'mn.' prefix to get the actual component name
        actual_component_name = self.container_name.replace('mn.', '')
        
        # For all components, use the simple pattern: /logging/{component_name}.log
        # This matches the pattern where mn.upf1 -> /logging/upf1.log
        self.log_file_path = f"/logging/{actual_component_name}.log"
        
        debug_print(f"Determined log file path for {self.container_name}: {self.log_file_path}")
    
    def stop(self):
        """Stop the log reading thread."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.quit()
        
    def run(self):
        """Main log reading loop."""
        try:
            # Always try to read from the single log file path first
            # If it fails, fallback to docker logs
            self._read_from_single_path()
        except Exception as e:
            self.log_error.emit(f"Error reading logs: {str(e)}")
    
    def _read_docker_logs(self):
        """Read logs using docker logs command."""
        try:
            if self.follow:
                cmd = ['docker', 'logs', '-f', '--tail', str(self.lines), self.container_name]
            else:
                cmd = ['docker', 'logs', '--tail', str(self.lines), self.container_name]
            
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                          universal_newlines=True, bufsize=1)
            
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                if line:
                    timestamp = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
                    formatted_line = f"[{timestamp}] {line.rstrip()}\n"
                    self.new_log_data.emit(formatted_line)
                    
        except Exception as e:
            self.log_error.emit(f"Error reading docker logs: {str(e)}")
    
    def _read_from_single_path(self):
        """Read logs from a single file path inside the container."""
        try:
            # First, check if the log file exists
            cmd = ['docker', 'exec', self.container_name, 'test', '-f', self.log_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                # Log file doesn't exist, fallback to docker logs
                debug_print(f"Log file {self.log_file_path} not found in {self.container_name}, falling back to docker logs")
                self.log_error.emit(f"Log file {self.log_file_path} not found, using docker logs as fallback")
                self._read_docker_logs()
                return
            
            # Try to get existing logs
            cmd = ['docker', 'exec', self.container_name, 'tail', f'-{self.lines}', self.log_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    # Log file has content
                    for line in result.stdout.splitlines():
                        if not self.running:
                            break
                        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
                        formatted_line = f"[{timestamp}] {line}\n"
                        self.new_log_data.emit(formatted_line)
                else:
                    # Log file exists but is empty
                    self.new_log_data.emit(f"[INFO] Log file {self.log_file_path} is empty or has no recent entries\n")
            else:
                # Error reading log file
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                debug_print(f"Error reading log file: {error_msg}")
                self.log_error.emit(f"Error reading {self.log_file_path}: {error_msg}")
                # Fallback to docker logs
                self._read_docker_logs()
                return
            
            # If follow is enabled, continue monitoring
            if self.follow and self.running:
                cmd = ['docker', 'exec', self.container_name, 'tail', '-f', self.log_file_path]
                self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                              universal_newlines=True, bufsize=1)
                
                for line in iter(self.process.stdout.readline, ''):
                    if not self.running:
                        break
                    if line:
                        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
                        formatted_line = f"[{timestamp}] {line.rstrip()}\n"
                        self.new_log_data.emit(formatted_line)
                        
        except Exception as e:
            debug_print(f"Exception in _read_from_single_path: {e}")
            self.log_error.emit(f"Error accessing {self.log_file_path}: {str(e)}")
            # Fallback to docker logs
            self._read_docker_logs()
    

class LogViewerDialog(QDialog):
    """Dialog window for viewing component logs."""
    
    def __init__(self, component_name, component_type, container_name, parent=None, available_containers=None):
        super().__init__(parent)
        self.component_name = component_name
        self.component_type = component_type
        self.container_name = container_name
        self.available_containers = available_containers or [container_name]
        self.log_worker = None
        self.auto_scroll = True
        
        self.setupUI()
        self.setupConnections()
        self.startLogReading()
        
    def setupUI(self):
        """Setup the user interface."""
        self.setWindowTitle(f"Log Viewer - {self.component_name} ({self.component_type})")
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "gui", "Icon", "logoSquare.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass  # Icon not critical
            
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Header with component info
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header)
        
        info_label = QLabel(f"<b>Component:</b> {self.component_name} | <b>Type:</b> {self.component_type}")
        header_layout.addWidget(info_label)
        
        # If multiple containers available, add selector
        if len(self.available_containers) > 1:
            header_layout.addWidget(QLabel(" | <b>Container:</b>"))
            self.container_selector = QComboBox()
            self.container_selector.addItems(self.available_containers)
            self.container_selector.setCurrentText(self.container_name)
            header_layout.addWidget(self.container_selector)
        else:
            header_layout.addWidget(QLabel(f" | <b>Container:</b> {self.container_name}"))
            self.container_selector = None
        
        layout.addWidget(header)
        
        # Control panel
        control_panel = QGroupBox("Log Controls")
        control_layout = QHBoxLayout(control_panel)
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        control_layout.addWidget(self.auto_scroll_cb)
        
        # Lines to show
        control_layout.addWidget(QLabel("Lines:"))
        self.lines_spinbox = QSpinBox()
        self.lines_spinbox.setRange(10, 10000)
        self.lines_spinbox.setValue(100)
        control_layout.addWidget(self.lines_spinbox)
        
        # Follow logs checkbox
        self.follow_logs_cb = QCheckBox("Follow logs")
        self.follow_logs_cb.setChecked(True)
        control_layout.addWidget(self.follow_logs_cb)
        
        control_layout.addStretch()
        
        # Control buttons
        self.refresh_btn = QPushButton("Refresh")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save to File")
        self.stop_btn = QPushButton("Stop Following")
        
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.stop_btn)
        
        layout.addWidget(control_panel)
        
        # Log display area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        font = QFont("Courier", 9)  # Monospace font for better log readability
        self.log_text.setFont(font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def setupConnections(self):
        """Setup signal connections."""
        self.auto_scroll_cb.toggled.connect(self.onAutoScrollToggled)
        self.follow_logs_cb.toggled.connect(self.onFollowLogsToggled)
        self.refresh_btn.clicked.connect(self.refreshLogs)
        self.clear_btn.clicked.connect(self.clearLogs)
        self.save_btn.clicked.connect(self.saveLogs)
        self.stop_btn.clicked.connect(self.stopFollowing)
        
        # Connect container selector if available
        if self.container_selector:
            self.container_selector.currentTextChanged.connect(self.onContainerChanged)
        
    def startLogReading(self):
        """Start reading logs from the container."""
        if self.log_worker:
            self.log_worker.stop()
            self.log_worker.wait()
        
        lines = self.lines_spinbox.value()
        follow = self.follow_logs_cb.isChecked()
        
        # For VGCore components, determine the actual component type from container name
        actual_component_type = self.component_type
        if self.component_type == "VGcore":
            # Extract the component type from container name (mn.upf1 -> UPF)
            container_base = self.container_name.replace('mn.', '').lower()
            if 'upf' in container_base:
                actual_component_type = 'UPF'
            elif 'amf' in container_base:
                actual_component_type = 'AMF'
            elif 'smf' in container_base:
                actual_component_type = 'SMF'
            elif 'nrf' in container_base:
                actual_component_type = 'NRF'
            elif 'udr' in container_base:
                actual_component_type = 'UDR'
            elif 'udm' in container_base:
                actual_component_type = 'UDM'
            elif 'ausf' in container_base:
                actual_component_type = 'AUSF'
            elif 'pcf' in container_base:
                actual_component_type = 'PCF'
            elif 'nssf' in container_base:
                actual_component_type = 'NSSF'
            elif 'bsf' in container_base:
                actual_component_type = 'BSF'
            elif 'scp' in container_base:
                actual_component_type = 'SCP'
        
        debug_print(f"Starting log reader for {self.container_name} with component type: {actual_component_type}")
        
        self.log_worker = LogReaderWorker(self.container_name, actual_component_type, follow, lines)
        self.log_worker.new_log_data.connect(self.appendLogData)
        self.log_worker.log_error.connect(self.showLogError)
        self.log_worker.start()
        
        self.status_label.setText(f"Reading logs from {self.container_name}...")
        
    def appendLogData(self, data):
        """Append new log data to the text widget."""
        self.log_text.insertPlainText(data)
        
        if self.auto_scroll:
            # Scroll to the bottom
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_text.setTextCursor(cursor)
    
    def showLogError(self, error_msg):
        """Show log reading error."""
        self.log_text.insertPlainText(f"\n[ERROR] {error_msg}\n")
        self.status_label.setText(f"Error: {error_msg}")
        
    def onAutoScrollToggled(self, enabled):
        """Handle auto-scroll toggle."""
        self.auto_scroll = enabled
        
    def onFollowLogsToggled(self, enabled):
        """Handle follow logs toggle."""
        if not enabled and self.log_worker:
            self.log_worker.stop()
            self.status_label.setText("Stopped following logs")
        elif enabled:
            self.refreshLogs()
    
    def onContainerChanged(self, new_container):
        """Handle container selection change."""
        self.container_name = new_container
        self.log_text.clear()
        self.startLogReading()
    
    def refreshLogs(self):
        """Refresh the logs."""
        self.log_text.clear()
        self.startLogReading()
        
    def clearLogs(self):
        """Clear the log display."""
        self.log_text.clear()
        
    def saveLogs(self):
        """Save logs to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log File",
            f"{self.component_name}_{self.component_type}_logs.txt",
            "Text Files (*.txt);;Log Files (*.log);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Success", f"Logs saved to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save logs: {str(e)}")
    
    def stopFollowing(self):
        """Stop following logs."""
        if self.log_worker:
            self.log_worker.stop()
            self.status_label.setText("Stopped following logs")
        self.follow_logs_cb.setChecked(False)
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.log_worker:
            self.log_worker.stop()
            self.log_worker.wait()
        event.accept()
