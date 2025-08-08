"""
Packet Capture Viewer Widget for NetFlux5G Components

This module provides a packet capture viewer window that displays network packets
from deployed components using tshark to parse pcapng files. It supports:

- Real-time packet capture viewing
- Component-specific capture files
- Filtering and search capabilities
- Export functionality
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                           QPushButton, QLabel, QComboBox, QCheckBox, 
                           QSpinBox, QGroupBox, QSplitter, QFileDialog,
                           QMessageBox, QProgressBar, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QTextCursor, QIcon
import subprocess
import os
import re
import time
from utils.debug import debug_print, error_print, warning_print


class DeployedComponentsExtractor:
    """Extract deployed components from the exported Mininet script (reused from LogViewer)."""
    
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


class PacketReaderWorker(QThread):
    """Worker thread to read packet captures without blocking the UI."""
    
    new_packet_data = pyqtSignal(str)  # Signal to emit new packet data
    capture_error = pyqtSignal(str)    # Signal to emit error messages
    
    def __init__(self, container_name, component_type, follow=True, packet_count=100, display_filter=""):
        super().__init__()
        self.container_name = container_name
        self.component_type = component_type
        self.follow = follow
        self.packet_count = packet_count
        self.display_filter = display_filter
        self.running = True
        self.capture_file_path = None
        self.process = None
        self.last_packet_count = 0
        
        # Determine capture file path based on component
        self._determine_capture_file_path()
        
    def _determine_capture_file_path(self):
        """Determine the capture file path based on component."""
        # Extract the actual component name from container name (remove mn. prefix)
        actual_component_name = self.container_name.replace('mn.', '')
        
        # Standard capture file path: /captures/{component_name}.pcapng
        self.capture_file_path = f"/captures/{actual_component_name}.pcapng"
        
        debug_print(f"Capture file path for {self.container_name}: {self.capture_file_path}")
    
    def stop(self):
        """Stop the packet reading thread."""
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
        """Main packet reading loop."""
        try:
            if self.follow:
                self._follow_capture_file()
            else:
                self._read_static_capture()
        except Exception as e:
            self.capture_error.emit(f"Error reading packet capture: {str(e)}")
    
    def _read_static_capture(self):
        """Read a static capture file (non-follow mode)."""
        try:
            # Check if capture file exists first
            check_cmd = ['docker', 'exec', self.container_name, 'test', '-f', self.capture_file_path]
            result = subprocess.run(check_cmd, capture_output=True, timeout=5)
            
            if result.returncode != 0:
                self.capture_error.emit(f"Capture file {self.capture_file_path} not found in container {self.container_name}")
                return
            
            # Build tshark command
            tshark_cmd = [
                'docker', 'exec', self.container_name, 
                'tshark', '-r', self.capture_file_path,
                '-c', str(self.packet_count),  # Limit packet count
                '-T', 'text',  # Text output format
                '-V'  # Verbose output (packet details)
            ]
            
            # Add display filter if specified
            if self.display_filter.strip():
                tshark_cmd.extend(['-Y', self.display_filter.strip()])
            
            debug_print(f"Running tshark command: {' '.join(tshark_cmd)}")
            
            # Execute tshark
            result = subprocess.run(tshark_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                if result.stdout:
                    self.new_packet_data.emit(result.stdout)
                else:
                    self.capture_error.emit("No packets found matching the criteria")
            else:
                error_msg = f"tshark error: {result.stderr}" if result.stderr else "tshark command failed"
                self.capture_error.emit(error_msg)
                
        except subprocess.TimeoutExpired:
            self.capture_error.emit("tshark command timed out")
        except Exception as e:
            self.capture_error.emit(f"Error running tshark: {str(e)}")
    
    def _follow_capture_file(self):
        """Follow a capture file for real-time updates."""
        try:
            # In follow mode, we periodically check for new packets
            while self.running:
                # Check if capture file exists
                check_cmd = ['docker', 'exec', self.container_name, 'test', '-f', self.capture_file_path]
                result = subprocess.run(check_cmd, capture_output=True, timeout=5)
                
                if result.returncode != 0:
                    # File doesn't exist yet, wait a bit
                    time.sleep(2)
                    continue
                
                # Get current packet count
                count_cmd = [
                    'docker', 'exec', self.container_name,
                    'tshark', '-r', self.capture_file_path, '-T', 'fields', '-e', 'frame.number'
                ]
                
                try:
                    count_result = subprocess.run(count_cmd, capture_output=True, text=True, timeout=10)
                    if count_result.returncode == 0:
                        lines = count_result.stdout.strip().split('\n')
                        current_packet_count = len([line for line in lines if line.strip()])
                        
                        # Check if there are new packets
                        if current_packet_count > self.last_packet_count:
                            # Read new packets
                            new_packets_to_read = min(10, current_packet_count - self.last_packet_count)  # Read max 10 new packets at a time
                            
                            # Read the new packets
                            tshark_cmd = [
                                'docker', 'exec', self.container_name,
                                'tshark', '-r', self.capture_file_path,
                                '-T', 'text', '-V',
                                '-c', str(new_packets_to_read),
                                '-o', f'frame.offset:{self.last_packet_count}'
                            ]
                            
                            # Add display filter if specified
                            if self.display_filter.strip():
                                tshark_cmd.extend(['-Y', self.display_filter.strip()])
                            
                            packet_result = subprocess.run(tshark_cmd, capture_output=True, text=True, timeout=15)
                            
                            if packet_result.returncode == 0 and packet_result.stdout:
                                timestamp = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
                                formatted_output = f"\n[{timestamp}] === New packets detected ===\n{packet_result.stdout}\n"
                                self.new_packet_data.emit(formatted_output)
                            
                            self.last_packet_count = current_packet_count
                
                except subprocess.TimeoutExpired:
                    pass  # Continue monitoring
                except Exception as e:
                    debug_print(f"Error checking for new packets: {e}")
                
                # Wait before checking again
                if self.running:
                    time.sleep(5)  # Check every 5 seconds
                    
        except Exception as e:
            self.capture_error.emit(f"Error following capture file: {str(e)}")


class PacketCaptureViewerDialog(QDialog):
    """Dialog window for viewing packet captures."""
    
    def __init__(self, component_name, component_type, container_name, parent=None, available_containers=None):
        super().__init__(parent)
        self.component_name = component_name
        self.component_type = component_type
        self.container_name = container_name
        self.available_containers = available_containers or [container_name]
        self.packet_worker = None
        self.auto_scroll = True
        
        self.setupUI()
        self.setupConnections()
        self.startPacketReading()
        
    def setupUI(self):
        """Setup the user interface."""
        self.setWindowTitle(f"Packet Capture Viewer - {self.component_name} ({self.component_type})")
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "gui", "Icon", "logoSquare.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass  # Icon not critical
            
        self.resize(1000, 700)
        
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
        control_panel = QGroupBox("Capture Controls")
        control_layout = QVBoxLayout(control_panel)
        
        # First row of controls
        control_row1 = QHBoxLayout()
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        control_row1.addWidget(self.auto_scroll_cb)
        
        # Packet count
        control_row1.addWidget(QLabel("Packets:"))
        self.packet_count_spinbox = QSpinBox()
        self.packet_count_spinbox.setRange(10, 10000)
        self.packet_count_spinbox.setValue(100)
        control_row1.addWidget(self.packet_count_spinbox)
        
        # Follow captures checkbox
        self.follow_capture_cb = QCheckBox("Follow capture")
        self.follow_capture_cb.setChecked(False)  # Default to false for better performance
        control_row1.addWidget(self.follow_capture_cb)
        
        control_row1.addStretch()
        control_layout.addLayout(control_row1)
        
        # Second row - Display filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Display Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("e.g., tcp.port == 80 or ip.addr == 192.168.1.1")
        filter_row.addWidget(self.filter_input)
        control_layout.addLayout(filter_row)
        
        # Third row - Control buttons
        button_row = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save to File")
        self.stop_btn = QPushButton("Stop Following")
        
        button_row.addWidget(self.refresh_btn)
        button_row.addWidget(self.clear_btn)
        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.stop_btn)
        button_row.addStretch()
        
        control_layout.addLayout(button_row)
        layout.addWidget(control_panel)
        
        # Packet display area
        self.packet_text = QTextEdit()
        self.packet_text.setReadOnly(True)
        font = QFont("Courier", 8)  # Smaller monospace font for packet data
        self.packet_text.setFont(font)
        self.packet_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.packet_text)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def setupConnections(self):
        """Setup signal connections."""
        self.auto_scroll_cb.toggled.connect(self.onAutoScrollToggled)
        self.follow_capture_cb.toggled.connect(self.onFollowCaptureToggled)
        self.refresh_btn.clicked.connect(self.refreshCapture)
        self.clear_btn.clicked.connect(self.clearCapture)
        self.save_btn.clicked.connect(self.saveCapture)
        self.stop_btn.clicked.connect(self.stopFollowing)
        self.filter_input.returnPressed.connect(self.refreshCapture)
        
        # Connect container selector if available
        if self.container_selector:
            self.container_selector.currentTextChanged.connect(self.onContainerChanged)
        
    def startPacketReading(self):
        """Start reading packets from the container."""
        if self.packet_worker:
            self.packet_worker.stop()
            self.packet_worker.wait()
        
        packet_count = self.packet_count_spinbox.value()
        follow = self.follow_capture_cb.isChecked()
        display_filter = self.filter_input.text()
        
        self.packet_worker = PacketReaderWorker(
            self.container_name, 
            self.component_type, 
            follow, 
            packet_count,
            display_filter
        )
        self.packet_worker.new_packet_data.connect(self.appendPacketData)
        self.packet_worker.capture_error.connect(self.showCaptureError)
        self.packet_worker.start()
        
        self.status_label.setText(f"Reading packet capture from {self.container_name}...")
        
    def appendPacketData(self, data):
        """Append new packet data to the text widget."""
        self.packet_text.insertPlainText(data)
        
        if self.auto_scroll:
            # Scroll to the bottom
            cursor = self.packet_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.packet_text.setTextCursor(cursor)
    
    def showCaptureError(self, error_msg):
        """Show capture reading error."""
        self.packet_text.insertPlainText(f"\n[ERROR] {error_msg}\n")
        self.status_label.setText(f"Error: {error_msg}")
        
    def onAutoScrollToggled(self, enabled):
        """Handle auto-scroll toggle."""
        self.auto_scroll = enabled
        
    def onFollowCaptureToggled(self, enabled):
        """Handle follow capture toggle."""
        if not enabled and self.packet_worker:
            self.packet_worker.stop()
            self.status_label.setText("Stopped following capture")
        elif enabled:
            self.refreshCapture()
    
    def onContainerChanged(self, new_container):
        """Handle container selection change."""
        self.container_name = new_container
        self.packet_text.clear()
        self.startPacketReading()
    
    def refreshCapture(self):
        """Refresh the packet capture."""
        self.packet_text.clear()
        self.startPacketReading()
        
    def clearCapture(self):
        """Clear the packet display."""
        self.packet_text.clear()
        
    def saveCapture(self):
        """Save packet capture to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Packet Capture",
            f"{self.component_name}_{self.component_type}_capture.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.packet_text.toPlainText())
                QMessageBox.information(self, "Success", f"Packet capture saved to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save capture: {str(e)}")
    
    def stopFollowing(self):
        """Stop following packet capture."""
        if self.packet_worker:
            self.packet_worker.stop()
            self.status_label.setText("Stopped following capture")
        self.follow_capture_cb.setChecked(False)
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.packet_worker:
            self.packet_worker.stop()
            self.packet_worker.wait()
        event.accept()
