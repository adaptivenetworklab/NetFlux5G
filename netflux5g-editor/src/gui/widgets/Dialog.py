import os
from PyQt5.QtWidgets import QMainWindow, QLineEdit, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import yaml
from manager.debug import debug_print, error_print, warning_print

class BasePropertiesWindow(QMainWindow):
    """Base class for all properties windows that automatically sets the icon."""
    
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(parent)
        # Store the component name and reference
        self.component_name = label_text
        self.component = component  # Reference to the actual component object

        # Set the window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Icon", "logoSquare.png")
        self.setWindowIcon(QIcon(icon_path))
        
        # Center the dialog on the parent widget
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

    def setupConnections(self):
        """Setup connections for OK and Cancel buttons - to be implemented by subclasses"""
        pass

    def saveProperties(self):
        """Save all UI values to the component's properties, including 5G component tables."""
        if not self.component:
            warning_print("WARNING: No component reference to save properties to")
            return
            
        properties = {}
        
        # Automatically collect all QLineEdit values
        for widget in self.findChildren(QLineEdit):
            name = widget.objectName()
            if name:  # Only save if the widget has a name
                properties[name] = widget.text()
                
        # Collect all QComboBox values
        for widget in self.findChildren(QComboBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.currentText()
                
        # Collect all QCheckBox values
        for widget in self.findChildren(QCheckBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.isChecked()

        # Collect all QSpinBox values
        for widget in self.findChildren(QSpinBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.value()

        # Collect all QDoubleSpinBox values
        for widget in self.findChildren(QDoubleSpinBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.value()
                
        # Collect all QTextEdit values
        for widget in self.findChildren(QTextEdit):
            name = widget.objectName()
            if name:
                properties[name] = widget.toPlainText()
                
        # Collect all QPlainTextEdit values
        for widget in self.findChildren(QPlainTextEdit):
            name = widget.objectName()
            if name:
                properties[name] = widget.toPlainText()
        
        # For Component5GPropertiesWindow, also save table data
        if isinstance(self, Component5GPropertiesWindow):
            self.save5GComponentTableData(properties)
        
        # Save to component
        self.component.setProperties(properties)
        debug_print(f"DEBUG: Saved properties for {self.component_name}: {len(properties)} properties")
        
        # Mark topology as modified when component properties are changed
        scene = self.component.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and hasattr(view.app_instance, 'onTopologyChanged'):
                view.app_instance.onTopologyChanged()

    def save5GComponentTableData(self, properties):
        """Save data from all 5G component tables."""
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        
        for component_type in component_types:
            # Try different possible table name patterns
            possible_table_names = [
                f'Component5G_{component_type}table',
                f'{component_type}table',
                f'{component_type}Table',
                f'Component5G_{component_type}Table',
                f'{component_type}_table'
            ]
            
            table = None
            for name in possible_table_names:
                if hasattr(self, name):
                    table = getattr(self, name)
                    break
            
            if table and hasattr(table, 'rowCount'):
                # Extract table data
                table_data = []
                for row in range(table.rowCount()):
                    row_data = {}
                    
                    # Name (column 0)
                    name_item = table.item(row, 0)
                    if name_item:
                        row_data['name'] = name_item.text()
                    else:
                        row_data['name'] = f"{component_type.lower()}{row + 1}"
                    
                    # Config file info (column 1)
                    config_item = table.item(row, 1)
                    if config_item:
                        config_text = config_item.text()
                        row_data['config_display'] = config_text
                        
                        # Check if this row has imported configuration data
                        if hasattr(config_item, 'config_data'):
                            row_data['config_content'] = config_item.config_data
                            row_data['imported'] = True
                            row_data['config_filename'] = getattr(config_item, 'config_filename', 'imported.yaml')
                            # Store the file path if available
                            if hasattr(config_item, 'config_file_path'):
                                row_data['config_file_path'] = config_item.config_file_path
                            else:
                                row_data['config_file_path'] = ''
                        elif hasattr(config_item, 'config_file_path'):
                            row_data['config_file_path'] = config_item.config_file_path
                            row_data['imported'] = True
                            row_data['config_filename'] = os.path.basename(config_item.config_file_path)
                            # Also try to get config content if available
                            if hasattr(config_item, 'config_data'):
                                row_data['config_content'] = config_item.config_data
                        else:
                            row_data['imported'] = False
                            row_data['config_filename'] = f"{component_type.lower()}.yaml"
                            row_data['config_file_path'] = ''
                    else:
                        row_data['config_display'] = "(Double-click to import)"
                        row_data['imported'] = False
                        row_data['config_filename'] = f"{component_type.lower()}.yaml"
                        row_data['config_file_path'] = ''
                    
                    # Config Path (column 2, if exists)
                    if table.columnCount() > 2:
                        config_path_item = table.item(row, 2)
                        if config_path_item:
                            row_data['config_path'] = config_path_item.text()
                        else:
                            row_data['config_path'] = ""
                    else:
                        row_data['config_path'] = ""
                    
                    # Add default values
                    row_data['image'] = 'adaptive/open5gs:1.0'
                    row_data['component_type'] = component_type
                    row_data['volumes'] = []
                    
                    table_data.append(row_data)
                
                # Store in properties with a key specific to this component type
                config_key = f"{component_type}_configs"
                properties[config_key] = table_data
                
                debug_print(f"DEBUG: Saved {len(table_data)} {component_type} configurations")

    def loadProperties(self):
        """Load component properties into UI widgets, including 5G component tables."""
        if not self.component:
            return
            
        properties = self.component.getProperties()
        
        # Load values into QLineEdit widgets
        for widget in self.findChildren(QLineEdit):
            name = widget.objectName()
            if name in properties:
                widget.setText(str(properties[name]))
                
        # Load values into QComboBox widgets
        for widget in self.findChildren(QComboBox):
            name = widget.objectName()
            if name in properties:
                text = str(properties[name])
                index = widget.findText(text)
                if index >= 0:
                    widget.setCurrentIndex(index)
                    
        # Load values into QCheckBox widgets
        for widget in self.findChildren(QCheckBox):
            name = widget.objectName()
            if name in properties:
                widget.setChecked(bool(properties[name]))

        # Load values into QSpinBox widgets
        for widget in self.findChildren(QSpinBox):
            name = widget.objectName()
            if name in properties:
                try:
                    # Accept float strings by converting to float first, then int
                    value = properties[name]
                    if isinstance(value, str):
                        value = int(float(value))
                    else:
                        value = int(value)
                    widget.setValue(value)
                except (ValueError, TypeError):
                    pass

        # Load values into QDoubleSpinBox widgets
        for widget in self.findChildren(QDoubleSpinBox):
            name = widget.objectName()
            if name in properties:
                try:
                    widget.setValue(float(properties[name]))
                except (ValueError, TypeError):
                    pass
                    
        # Load values into QTextEdit widgets
        for widget in self.findChildren(QTextEdit):
            name = widget.objectName()
            if name in properties:
                widget.setPlainText(str(properties[name]))
                
        # Load values into QPlainTextEdit widgets
        for widget in self.findChildren(QPlainTextEdit):
            name = widget.objectName()
            if name in properties:
                widget.setPlainText(str(properties[name]))
        
        # For Component5GPropertiesWindow, also load table data
        self.load5GComponentTableData(properties)
        
    def load5GComponentTableData(self, properties):
        """Load data into all 5G component tables."""
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        
        for component_type in component_types:
            config_key = f"{component_type}_configs"
            if config_key not in properties:
                continue
                
            table_data = properties[config_key]
            if not isinstance(table_data, list):
                continue
                
            # Find the table
            possible_table_names = [
                f'Component5G_{component_type}table',
                f'{component_type}table',
                f'{component_type}Table',
                f'Component5G_{component_type}Table',
                f'{component_type}_table'
            ]
            
            table = None
            for name in possible_table_names:
                if hasattr(self, name):
                    table = getattr(self, name)
                    break
            
            if not table or not hasattr(table, 'setRowCount'):
                continue
                
            # Clear existing rows
            table.setRowCount(0)
            
            # Load each row
            for i, row_data in enumerate(table_data):
                table.insertRow(i)
                
                # Name (column 0)
                name_item = QTableWidgetItem(row_data.get('name', f"{component_type.lower()}{i + 1}"))
                table.setItem(i, 0, name_item)
                
                # Config file info (column 1)
                config_item = QTableWidgetItem(row_data.get('config_display', '(Double-click to import)'))
                config_item.setToolTip("Double-click to import YAML configuration file")
                
                # Restore imported configuration data to the item
                if row_data.get('imported', False):
                    if 'config_content' in row_data:
                        config_item.config_data = row_data['config_content']
                        config_item.config_filename = row_data.get('config_filename', 'imported.yaml')
                    if 'config_file_path' in row_data:
                        config_item.config_file_path = row_data['config_file_path']
                        
                table.setItem(i, 1, config_item)
                
                # Config Path (column 2, if exists)
                if table.columnCount() > 2:
                    config_path_item = QTableWidgetItem(row_data.get('config_path', ''))
                    config_path_item.setToolTip("Path to imported configuration file")
                    table.setItem(i, 2, config_path_item)
            
            debug_print(f"DEBUG: Loaded {len(table_data)} {component_type} configurations into table")

class HostPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Host_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.pushButton.clicked.connect(self.onOK)  # OK button
        self.pushButton_5.clicked.connect(self.onCancel)  # Cancel button
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class STAPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "STA_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"STA Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.STA_OKButton.clicked.connect(self.onOK)
        self.STA_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class APPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "AP_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"AP Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons (adjust these based on actual button names in UI)
        if hasattr(self, 'AP_OKButton'):
            self.AP_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'AP_CancelButton'):
            self.AP_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class ControllerPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Controller_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Controller Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.Controller_OKButton.clicked.connect(self.onOK)
        self.Controller_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class DockerHostPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "DockerHost_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Docker Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        if hasattr(self, 'DockerHost_OKButton'):
            self.DockerHost_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'DockerHost_CancelButton'):
            self.DockerHost_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class GNBPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        # Try to load enhanced UI first, fall back to basic UI if not found
        enhanced_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties_enhanced.ui")
        basic_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties.ui")
        
        if os.path.exists(enhanced_ui_file):
            uic.loadUi(enhanced_ui_file, self)
            debug_print("DEBUG: Loaded enhanced gNB UI with AP functionality")
        else:
            uic.loadUi(basic_ui_file, self)
            debug_print("DEBUG: Loaded basic gNB UI (enhanced UI not found)")
            
        self.setWindowTitle(f"gNB Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.setupDefaultValues()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.GNB_OKButton.clicked.connect(self.onOK)
        self.GNB_CancelButton.clicked.connect(self.onCancel)
        
        # Connect AP enable checkbox to enable/disable AP configuration widgets
        if hasattr(self, 'GNB_AP_Enabled'):
            self.GNB_AP_Enabled.toggled.connect(self.onAPEnabledToggled)
            
        # Connect OVS enable checkbox to enable/disable OVS configuration widgets
        if hasattr(self, 'GNB_OVS_Enabled'):
            self.GNB_OVS_Enabled.toggled.connect(self.onOVSEnabledToggled)
    
    def setupDefaultValues(self):
        """Setup default values for the enhanced gNB configuration"""
        # Set default 5G configuration values
        if hasattr(self, 'GNB_AMFHostName'):
            self.GNB_AMFHostName.setText("amf1")
        if hasattr(self, 'GNB_AMF_IP'):
            self.GNB_AMF_IP.setText("")  # Empty by default, optional field
        if hasattr(self, 'GNB_GNBHostName'):
            self.GNB_GNBHostName.setText("GNB__1")
        if hasattr(self, 'GNB_TAC'):
            self.GNB_TAC.setText("1")
        if hasattr(self, 'GNB_MCC'):
            self.GNB_MCC.setText("999")
        if hasattr(self, 'GNB_MNC'):
            self.GNB_MNC.setText("70")
        if hasattr(self, 'GNB_SST'):
            self.GNB_SST.setText("1")
        if hasattr(self, 'GNB_SD'):
            self.GNB_SD.setText("0xffffff")
        
        # Set default AP configuration values
        if hasattr(self, 'GNB_AP_SSID'):
            self.GNB_AP_SSID.setText("gnb-hotspot")
        
        # Set default OpenFlow/OVS values
        if hasattr(self, 'GNB_OVS_BridgeName'):
            self.GNB_OVS_BridgeName.setText("br-gnb")
        if hasattr(self, 'GNB_OVS_FailMode'):
            self.GNB_OVS_FailMode.setCurrentText("secure")
        if hasattr(self, 'GNB_OVS_Protocols'):
            self.GNB_OVS_Protocols.setCurrentText("OpenFlow14")
        if hasattr(self, 'GNB_OVS_Datapath'):
            self.GNB_OVS_Datapath.setCurrentText("kernel")
            
        # Set default network interface values
        if hasattr(self, 'GNB_N2_Interface'):
            self.GNB_N2_Interface.setText("eth0")
        if hasattr(self, 'GNB_N3_Interface'):
            self.GNB_N3_Interface.setText("eth0")
        if hasattr(self, 'GNB_Radio_Interface'):
            self.GNB_Radio_Interface.setText("eth0")
        if hasattr(self, 'GNB_Bridge_Priority'):
            self.GNB_Bridge_Priority.setValue(32768)
    
    def onAPEnabledToggled(self, enabled):
        """Handle AP functionality enable/disable"""
        debug_print(f"DEBUG: gNB AP functionality {'enabled' if enabled else 'disabled'}")
        # The UI connection should handle enabling/disabling the widget_ap_config automatically
        # Additional logic can be added here if needed
        
    def onOVSEnabledToggled(self, enabled):
        """Handle OVS functionality enable/disable"""
        debug_print(f"DEBUG: gNB OVS functionality {'enabled' if enabled else 'disabled'}")
        # The UI connection should handle enabling/disabling the OVS widgets automatically
    
    def getAPConfiguration(self):
        """Get AP configuration as environment variables for Docker"""
        ap_config = {}
        
        if hasattr(self, 'GNB_AP_Enabled') and self.GNB_AP_Enabled.isChecked():
            ap_config['AP_ENABLED'] = 'true'
            
            if hasattr(self, 'GNB_AP_SSID'):
                ap_config['AP_SSID'] = self.GNB_AP_SSID.text() or 'gnb-hotspot'
            if hasattr(self, 'GNB_AP_Channel'):
                ap_config['AP_CHANNEL'] = str(self.GNB_AP_Channel.value())
            if hasattr(self, 'GNB_AP_Mode'):
                ap_config['AP_MODE'] = self.GNB_AP_Mode.currentText() or 'g'
            if hasattr(self, 'GNB_AP_Password'):
                ap_config['AP_PASSWD'] = self.GNB_AP_Password.text()
            
            # Add OpenFlow configuration for AP (from Dockerfile)
            if hasattr(self, 'GNB_OVS_Controller'):
                ap_config['OVS_CONTROLLER'] = self.GNB_OVS_Controller.text()
            if hasattr(self, 'GNB_OVS_FailMode'):
                ap_config['AP_FAILMODE'] = self.GNB_OVS_FailMode.currentText() or 'secure'
            if hasattr(self, 'GNB_OVS_Protocols'):
                ap_config['OPENFLOW_PROTOCOLS'] = self.GNB_OVS_Protocols.currentText() or 'OpenFlow14'
        else:
            ap_config['AP_ENABLED'] = 'false'
            
        return ap_config
    
    def getOVSConfiguration(self):
        """Get OVS/OpenFlow configuration as environment variables for Docker"""
        ovs_config = {}
        
        if hasattr(self, 'GNB_OVS_Enabled') and self.GNB_OVS_Enabled.isChecked():
            ovs_config['OVS_ENABLED'] = 'true'
            
            if hasattr(self, 'GNB_OVS_Controller') and self.GNB_OVS_Controller.text():
                ovs_config['OVS_CONTROLLER'] = self.GNB_OVS_Controller.text()
            if hasattr(self, 'GNB_OVS_BridgeName'):
                ovs_config['OVS_BRIDGE_NAME'] = self.GNB_OVS_BridgeName.text() or 'br-gnb'
            if hasattr(self, 'GNB_OVS_FailMode'):
                ovs_config['OVS_FAIL_MODE'] = self.GNB_OVS_FailMode.currentText() or 'secure'
            if hasattr(self, 'GNB_OVS_Protocols'):
                ovs_config['OPENFLOW_PROTOCOLS'] = self.GNB_OVS_Protocols.currentText() or 'OpenFlow14'
            if hasattr(self, 'GNB_OVS_Datapath'):
                ovs_config['OVS_DATAPATH'] = self.GNB_OVS_Datapath.currentText() or 'kernel'
        else:
            ovs_config['OVS_ENABLED'] = 'false'
            
        return ovs_config
    
    def get5GConfiguration(self):
        """Get 5G configuration parameters matching UERANSIM Docker environment"""
        config = {}
        
        # Core 5G configuration - must match Dockerfile defaults
        if hasattr(self, 'GNB_AMFHostName'):
            config['AMF_HOSTNAME'] = self.GNB_AMFHostName.text() or 'amf'
        if hasattr(self, 'GNB_AMF_IP'):
            amf_ip = self.GNB_AMF_IP.text().strip()
            if amf_ip:  # Only add if not empty
                config['AMF_IP'] = amf_ip
        if hasattr(self, 'GNB_GNBHostName'):
            config['GNB_HOSTNAME'] = self.GNB_GNBHostName.text() or 'localhost'
        if hasattr(self, 'GNB_TAC'):
            config['TAC'] = self.GNB_TAC.text() or '1'
        if hasattr(self, 'GNB_MCC'):
            config['MCC'] = self.GNB_MCC.text() or '999'
        if hasattr(self, 'GNB_MNC'):
            config['MNC'] = self.GNB_MNC.text() or '70'
        if hasattr(self, 'GNB_SST'):
            config['SST'] = self.GNB_SST.text() or '1'
        if hasattr(self, 'GNB_SD'):
            config['SD'] = self.GNB_SD.text() or '0xffffff'
            
        return config
    
    def getNetworkConfiguration(self):
        """Get network interface configuration parameters"""
        config = {}
        
        # Network interfaces - must match Dockerfile environment variables
        if hasattr(self, 'GNB_N2_Interface'):
            config['N2_IFACE'] = self.GNB_N2_Interface.text() or 'eth0'
        if hasattr(self, 'GNB_N3_Interface'):
            config['N3_IFACE'] = self.GNB_N3_Interface.text() or 'eth0'
        if hasattr(self, 'GNB_Radio_Interface'):
            config['RADIO_IFACE'] = self.GNB_Radio_Interface.text() or 'eth0'
            
        # Bridge configuration
        if hasattr(self, 'GNB_Bridge_Priority'):
            config['BRIDGE_PRIORITY'] = str(self.GNB_Bridge_Priority.value())
        if hasattr(self, 'GNB_STP_Enabled') and self.GNB_STP_Enabled.isChecked():
            config['STP_ENABLED'] = 'true'
        else:
            config['STP_ENABLED'] = 'false'
            
        # Add UERANSIM component type
        config['UERANSIM_COMPONENT'] = 'gnb'
            
        return config
    
    def getWirelessConfiguration(self):
        """Get wireless configuration for mininet-wifi"""
        config = {}
        
        if hasattr(self, 'GNB_Power'):
            config['txpower'] = self.GNB_Power.value()
        if hasattr(self, 'GNB_Range'):
            config['range'] = self.GNB_Range.value()
            
        return config
        
    def onOK(self):
        """Enhanced save that includes all new configuration options"""
        self.saveProperties()
        
        # Store additional configurations in the component
        if self.component:
            # Store AP configuration
            ap_config = self.getAPConfiguration()
            self.component.properties.update({f"ap_{k.lower()}": v for k, v in ap_config.items()})
            
            # Store OVS configuration
            ovs_config = self.getOVSConfiguration()
            self.component.properties.update({f"ovs_{k.lower()}": v for k, v in ovs_config.items()})
            
            # Store 5G configuration
            config_5g = self.get5GConfiguration()
            self.component.properties.update({f"5g_{k.lower()}": v for k, v in config_5g.items()})
            
            # Store network configuration
            network_config = self.getNetworkConfiguration()
            self.component.properties.update({f"network_{k.lower()}": v for k, v in network_config.items()})
            
            # Store wireless configuration
            wireless_config = self.getWirelessConfiguration()
            self.component.properties.update({f"wireless_{k}": v for k, v in wireless_config.items()})
            
            # Set component type for UERANSIM
            self.component.properties['ueransim_component'] = 'gnb'
            
            debug_print(f"DEBUG: Saved enhanced gNB configuration for {self.component_name}")
            
        self.close()
        
    def onCancel(self):
        self.close()

class UEPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        # Try to load enhanced UI first, fall back to basic UI if not found
        enhanced_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties_enhanced.ui")
        basic_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties.ui")
        
        if os.path.exists(enhanced_ui_file):
            uic.loadUi(enhanced_ui_file, self)
            debug_print("DEBUG: Loaded enhanced UE UI with wireless and network functionality")
        else:
            uic.loadUi(basic_ui_file, self)
            debug_print("DEBUG: Loaded basic UE UI (enhanced UI not found)")
            
        self.setWindowTitle(f"UE Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.setupDefaultValues()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.UE_OKButton.clicked.connect(self.onOK)
        self.UE_CancelButton.clicked.connect(self.onCancel)
    
    def setupDefaultValues(self):
        """Setup default values for the UE configuration"""
        # Set default UE configuration values
        if hasattr(self, 'UE_GNBHostName'):
            self.UE_GNBHostName.setText("gnb")
        if hasattr(self, 'UE_APN'):
            self.UE_APN.setText("internet")
        if hasattr(self, 'UE_MSISDN'):
            self.UE_MSISDN.setText("0000000001")
        if hasattr(self, 'UE_MCC'):
            self.UE_MCC.setText("999")
        if hasattr(self, 'UE_MNC'):
            self.UE_MNC.setText("70")
        if hasattr(self, 'UE_KEY'):
            self.UE_KEY.setText("465B5CE8B199B49FAA5F0A2EE238A6BC")
        if hasattr(self, 'UE_OPType'):
            self.UE_OPType.setCurrentText("OPC")
        if hasattr(self, 'UE_OP'):
            self.UE_OP.setText("E8ED289DEBA952E4283B54E88E6183CA")
        if hasattr(self, 'UE_SST'):
            self.UE_SST.setText("1")
        if hasattr(self, 'UE_SD'):
            self.UE_SD.setText("0xffffff")
        if hasattr(self, 'UE_IMEI'):
            self.UE_IMEI.setText("356938035643803")
        if hasattr(self, 'UE_IMEISV'):
            self.UE_IMEISV.setText("4370816125816151")
            
        # Set default network configuration values
        if hasattr(self, 'UE_TunnelInterface'):
            self.UE_TunnelInterface.setText("uesimtun0")
        if hasattr(self, 'UE_RadioInterface'):
            self.UE_RadioInterface.setText("eth0")
        if hasattr(self, 'UE_SessionType'):
            self.UE_SessionType.setCurrentText("IPv4")
        if hasattr(self, 'UE_PDUSessions'):
            self.UE_PDUSessions.setValue(1)
            
        # Set default wireless configuration values
        if hasattr(self, 'UE_AssociationMode'):
            self.UE_AssociationMode.setCurrentText("auto")
        if hasattr(self, 'UE_Power'):
            self.UE_Power.setValue(20)
        if hasattr(self, 'UE_Range'):
            self.UE_Range.setValue(116)
            
    def get5GConfiguration(self):
        """Get 5G configuration parameters matching UERANSIM Docker environment"""
        config = {}
        
        # Core 5G configuration - must match UERANSIM Dockerfile defaults
        if hasattr(self, 'UE_GNBHostName'):
            config['GNB_HOSTNAME'] = self.UE_GNBHostName.text() or 'gnb'
        if hasattr(self, 'UE_APN'):
            config['APN'] = self.UE_APN.text() or 'internet'
        if hasattr(self, 'UE_MSISDN'):
            config['MSISDN'] = self.UE_MSISDN.text() or '0000000001'
        if hasattr(self, 'UE_MCC'):
            config['MCC'] = self.UE_MCC.text() or '999'
        if hasattr(self, 'UE_MNC'):
            config['MNC'] = self.UE_MNC.text() or '70'
        if hasattr(self, 'UE_SST'):
            config['SST'] = self.UE_SST.text() or '1'
        if hasattr(self, 'UE_SD'):
            config['SD'] = self.UE_SD.text() or '0xffffff'
            
        # Authentication configuration
        if hasattr(self, 'UE_KEY'):
            config['KEY'] = self.UE_KEY.text() or '465B5CE8B199B49FAA5F0A2EE238A6BC'
        if hasattr(self, 'UE_OPType'):
            config['OP_TYPE'] = self.UE_OPType.currentText() or 'OPC'
        if hasattr(self, 'UE_OP'):
            config['OP'] = self.UE_OP.text() or 'E8ED289DEBA952E4283B54E88E6183CA'
            
        # Device identifiers
        if hasattr(self, 'UE_IMEI'):
            config['IMEI'] = self.UE_IMEI.text() or '356938035643803'
        if hasattr(self, 'UE_IMEISV'):
            config['IMEISV'] = self.UE_IMEISV.text() or '4370816125816151'
            
        return config
    
    def getNetworkConfiguration(self):
        """Get network interface configuration parameters"""
        config = {}
        
        # Network interfaces - must match Dockerfile environment variables
        if hasattr(self, 'UE_GNB_IP'):
            gnb_ip = self.UE_GNB_IP.text()
            if gnb_ip and gnb_ip.strip():
                config['GNB_IP'] = gnb_ip.strip()
        if hasattr(self, 'UE_TunnelInterface'):
            config['TUNNEL_IFACE'] = self.UE_TunnelInterface.text() or 'uesimtun0'
        if hasattr(self, 'UE_RadioInterface'):
            config['RADIO_IFACE'] = self.UE_RadioInterface.text() or 'eth0'
        if hasattr(self, 'UE_SessionType'):
            config['SESSION_TYPE'] = self.UE_SessionType.currentText() or 'IPv4'
        if hasattr(self, 'UE_PDUSessions'):
            config['PDU_SESSIONS'] = str(self.UE_PDUSessions.value()) if hasattr(self.UE_PDUSessions, 'value') else '1'
            
        # Add UERANSIM component type
        config['UERANSIM_COMPONENT'] = 'ue'
            
        return config
    
    def getWirelessConfiguration(self):
        """Get wireless configuration for mininet-wifi"""
        config = {}
        
        if hasattr(self, 'UE_AssociationMode'):
            config['association'] = self.UE_AssociationMode.currentText() or 'auto'
        if hasattr(self, 'UE_Power'):
            config['txpower'] = self.UE_Power.value() if hasattr(self.UE_Power, 'value') else 20
        if hasattr(self, 'UE_Range'):
            config['range'] = self.UE_Range.value() if hasattr(self.UE_Range, 'value') else 300
            
        return config
    
    def onOK(self):
        """Enhanced save that includes all new configuration options"""
        self.saveProperties()
        
        # Store additional configurations in the component
        if self.component:
            # Store 5G configuration
            config_5g = self.get5GConfiguration()
            self.component.properties.update({f"5g_{k.lower()}": v for k, v in config_5g.items()})
            
            # Store network configuration
            network_config = self.getNetworkConfiguration()
            self.component.properties.update({f"network_{k.lower()}": v for k, v in network_config.items()})
            
            # Store wireless configuration
            wireless_config = self.getWirelessConfiguration()
            self.component.properties.update({f"wireless_{k}": v for k, v in wireless_config.items()})
            
            # Set component type for UERANSIM
            self.component.properties['ueransim_component'] = 'ue'
            
            debug_print(f"DEBUG: Saved enhanced UE configuration for {self.component_name}")
            
        self.close()
        
    def onCancel(self):
        self.close()
    
    def get5GConfiguration(self):
        """Get 5G/UE configuration parameters"""
        config = {}
        
        if hasattr(self, 'UE_GNBHostName'):
            config['GNB_HOSTNAME'] = self.UE_GNBHostName.text()
        if hasattr(self, 'UE_APN'):
            config['APN'] = self.UE_APN.text()
        if hasattr(self, 'UE_MSISDN'):
            config['MSISDN'] = self.UE_MSISDN.text()
        if hasattr(self, 'UE_MCC'):
            config['MCC'] = self.UE_MCC.text()
        if hasattr(self, 'UE_MNC'):
            config['MNC'] = self.UE_MNC.text()
        if hasattr(self, 'UE_KEY'):
            config['KEY'] = self.UE_KEY.text()
        if hasattr(self, 'UE_OPType'):
            config['OP_TYPE'] = self.UE_OPType.currentText()
        if hasattr(self, 'UE_OP'):
            config['OP'] = self.UE_OP.text()
        if hasattr(self, 'UE_SST'):
            config['SST'] = self.UE_SST.text()
        if hasattr(self, 'UE_SD'):
            config['SD'] = self.UE_SD.text()
        if hasattr(self, 'UE_IMEI'):
            config['IMEI'] = self.UE_IMEI.text()
        if hasattr(self, 'UE_IMEISV'):
            config['IMEISV'] = self.UE_IMEISV.text()
            
        return config
    
    def onOK(self):
        """Enhanced save that includes all new configuration options"""
        self.saveProperties()
        
        # Store additional configurations in the component
        if self.component:
            # Store 5G configuration
            config_5g = self.get5GConfiguration()
            self.component.properties.update({f"5g_{k.lower()}": v for k, v in config_5g.items()})
            
            # Store network configuration
            network_config = self.getNetworkConfiguration()
            self.component.properties.update({f"network_{k.lower()}": v for k, v in network_config.items()})
            
            # Store wireless configuration
            wireless_config = self.getWirelessConfiguration()
            self.component.properties.update({f"wireless_{k}": v for k, v in wireless_config.items()})
            
            # Set component type for UERANSIM
            self.component.properties['ueransim_component'] = 'ue'
            
            debug_print(f"DEBUG: Saved enhanced UE configuration for {self.component_name}")
            
        self.close()
        
    def onCancel(self):
        self.close()

class Component5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        # Try to load enhanced UI first, fall back to basic UI if not found
        enhanced_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties_enhanced.ui")
        basic_ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties.ui")
        
        if os.path.exists(enhanced_ui_file):
            uic.loadUi(enhanced_ui_file, self)
            debug_print("DEBUG: Loaded enhanced 5G Core UI with Open5GS configuration")
        else:
            uic.loadUi(basic_ui_file, self)
            debug_print("DEBUG: Loaded basic 5G Core UI (enhanced UI not found)")
            
        self.setWindowTitle(f"5G Core Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        
        self.setupConnections()
        self.setupDefaultValues()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        if hasattr(self, 'Component5G_OKButton'):
            self.Component5G_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'Component5G_CancelButton'):
            self.Component5G_CancelButton.clicked.connect(self.onCancel)
            
        # Connect Docker configuration toggles if they exist
        if hasattr(self, 'VGCore_DockerEnabled'):
            self.VGCore_DockerEnabled.toggled.connect(self.onDockerToggled)
        if hasattr(self, 'VGCore_OVSEnabled'):
            self.VGCore_OVSEnabled.toggled.connect(self.onOVSToggled)
            
        # Connect add buttons for each component type - FIXED: Remove duplicate connections
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        for comp_type in component_types:
            add_button = getattr(self, f'Component5G_Add{comp_type}Button', None)
            if add_button:
                # Disconnect any existing connections first
                try:
                    add_button.clicked.disconnect()
                except TypeError:
                    pass  # No connections to disconnect
                # Use functools.partial to properly capture the component type
                from functools import partial
                add_button.clicked.connect(partial(self.addComponentType, comp_type))
                
            # Connect remove buttons if they exist
            remove_button = getattr(self, f'Component5G_Remove{comp_type}Button', None)
            if remove_button:
                # Disconnect any existing connections first
                try:
                    remove_button.clicked.disconnect()
                except TypeError:
                    pass  # No connections to disconnect
                # Use functools.partial to properly capture the component type
                remove_button.clicked.connect(partial(self.removeComponentType, comp_type))
                
            # Setup table cell click events for import functionality
            table_name = f'Component5G_{comp_type}table'
            table = getattr(self, table_name, None)
            if table:
                # Disconnect existing connections first
                try:
                    table.cellDoubleClicked.disconnect()
                except TypeError:
                    pass  # No connections to disconnect
                    
                # Use functools.partial to properly capture the component type
                table.cellDoubleClicked.connect(partial(self.onTableCellDoubleClicked, comp_type))
                
                # Add context menu for right-click import
                table.setContextMenuPolicy(Qt.CustomContextMenu)
                try:
                    table.customContextMenuRequested.disconnect()
                except TypeError:
                    pass  # No connections to disconnect
                    
                # Use functools.partial to properly capture the component type
                table.customContextMenuRequested.connect(partial(self.showTableContextMenu, comp_type))
    
    def setupDefaultValues(self):
        """Setup default values for the enhanced 5G Core configuration"""
        # Set default Docker configuration values
        if hasattr(self, 'VGCore_DockerImage'):
            self.VGCore_DockerImage.setText("adaptive/open5gs:1.0")
        if hasattr(self, 'VGCore_DockerNetwork'):
            self.VGCore_DockerNetwork.setText("netflux5g")
        if hasattr(self, 'VGCore_DatabaseURI'):
            self.VGCore_DatabaseURI.setText("mongodb://mongo/open5gs")
        if hasattr(self, 'VGCore_DockerEnabled'):
            self.VGCore_DockerEnabled.setChecked(True)
            
        # Set default Open5GS configuration values
        if hasattr(self, 'VGCore_NetworkInterface'):
            self.VGCore_NetworkInterface.setText("eth0")
        if hasattr(self, 'VGCore_MCC'):
            self.VGCore_MCC.setText("999")
        if hasattr(self, 'VGCore_MNC'):
            self.VGCore_MNC.setText("70")
        if hasattr(self, 'VGCore_TAC'):
            self.VGCore_TAC.setText("1")
        if hasattr(self, 'VGCore_SST'):
            self.VGCore_SST.setText("1")
        if hasattr(self, 'VGCore_SD'):
            self.VGCore_SD.setText("0xffffff")
            
        # Set default OVS/OpenFlow configuration values
        if hasattr(self, 'VGCore_OVSEnabled'):
            self.VGCore_OVSEnabled.setChecked(False)
        if hasattr(self, 'VGCore_OVSBridgeName'):
            self.VGCore_OVSBridgeName.setText("br-open5gs")
        if hasattr(self, 'VGCore_OVSFailMode'):
            self.VGCore_OVSFailMode.setCurrentText("standalone")
        if hasattr(self, 'VGCore_OpenFlowProtocols'):
            self.VGCore_OpenFlowProtocols.setText("OpenFlow14")
        if hasattr(self, 'VGCore_OVSDatapath'):
            self.VGCore_OVSDatapath.setCurrentText("kernel")
            
        # Set default network configuration
        if hasattr(self, 'VGCore_EnableNAT'):
            self.VGCore_EnableNAT.setChecked(True)
        if hasattr(self, 'VGCore_BridgePriority'):
            self.VGCore_BridgePriority.setText("32768")
        if hasattr(self, 'VGCore_STPEnabled'):
            self.VGCore_STPEnabled.setChecked(False)
    
    def onDockerToggled(self, enabled):
        """Handle Docker functionality enable/disable"""
        debug_print(f"DEBUG: VGCore Docker {'enabled' if enabled else 'disabled'}")
        # Enable/disable docker-related fields
        docker_widgets = ['VGCore_DockerImage', 'VGCore_DockerNetwork', 'VGCore_DatabaseURI']
        for widget_name in docker_widgets:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.setEnabled(enabled)
    
    def onOVSToggled(self, enabled):
        """Handle OVS functionality enable/disable"""
        debug_print(f"DEBUG: VGCore OVS {'enabled' if enabled else 'disabled'}")
        # Enable/disable OVS-related fields
        ovs_widgets = ['VGCore_OVSController', 'VGCore_OVSBridgeName', 'VGCore_OVSFailMode', 
                      'VGCore_OpenFlowProtocols', 'VGCore_OVSDatapath', 'VGCore_ControllerPort']
        for widget_name in ovs_widgets:
            widget = getattr(self, widget_name, None)
            if widget:
                widget.setEnabled(enabled)
    
    def getDockerConfiguration(self):
        """Get Docker configuration parameters - fallback implementation for backward compatibility"""
        config = {}
        
        # If enhanced UI fields are not available, use defaults
        if hasattr(self, 'VGCore_DockerEnabled'):
            config['DOCKER_ENABLED'] = self.VGCore_DockerEnabled.isChecked()
        else:
            config['DOCKER_ENABLED'] = True
            
        if hasattr(self, 'VGCore_DockerImage'):
            config['DOCKER_IMAGE'] = self.VGCore_DockerImage.text()
        else:
            config['DOCKER_IMAGE'] = 'adaptive/open5gs:1.0'
            
        if hasattr(self, 'VGCore_DockerNetwork'):
            config['DOCKER_NETWORK'] = self.VGCore_DockerNetwork.text()
        else:
            config['DOCKER_NETWORK'] = 'netflux5g'
            
        if hasattr(self, 'VGCore_DatabaseURI'):
            config['DATABASE_URI'] = self.VGCore_DatabaseURI.text()
        else:
            config['DATABASE_URI'] = 'mongodb://mongo/open5gs'
            
        return config
    
    def get5GCoreConfiguration(self):
        """Get 5G Core configuration parameters - fallback implementation for backward compatibility"""
        config = {}
        
        # Network configuration with fallbacks
        config['NETWORK_INTERFACE'] = getattr(self, 'VGCore_NetworkInterface', None)
        if hasattr(config['NETWORK_INTERFACE'], 'text'):
            config['NETWORK_INTERFACE'] = config['NETWORK_INTERFACE'].text()
        else:
            config['NETWORK_INTERFACE'] = 'eth0'
            
        config['MCC'] = getattr(self, 'VGCore_MCC', None)
        if hasattr(config['MCC'], 'text'):
            config['MCC'] = config['MCC'].text()
        else:
            config['MCC'] = '999'
            
        config['MNC'] = getattr(self, 'VGCore_MNC', None)
        if hasattr(config['MNC'], 'text'):
            config['MNC'] = config['MNC'].text()
        else:
            config['MNC'] = '70'
            
        config['TAC'] = getattr(self, 'VGCore_TAC', None)
        if hasattr(config['TAC'], 'text'):
            config['TAC'] = config['TAC'].text()
        else:
            config['TAC'] = '1'
            
        config['SST'] = getattr(self, 'VGCore_SST', None)
        if hasattr(config['SST'], 'text'):
            config['SST'] = config['SST'].text()
        else:
            config['SST'] = '1'
            
        config['SD'] = getattr(self, 'VGCore_SD', None)
        if hasattr(config['SD'], 'text'):
            config['SD'] = config['SD'].text()
        else:
            config['SD'] = '0xffffff'
            
        config['ENABLE_NAT'] = getattr(self, 'VGCore_EnableNAT', None)
        if hasattr(config['ENABLE_NAT'], 'isChecked'):
            config['ENABLE_NAT'] = config['ENABLE_NAT'].isChecked()
        else:
            config['ENABLE_NAT'] = True
            
        return config
    
    def getOVSConfiguration(self):
        """Get OVS/OpenFlow configuration parameters - fallback implementation for backward compatibility"""
        config = {}
        
        # OVS configuration with fallbacks
        config['OVS_ENABLED'] = getattr(self, 'VGCore_OVSEnabled', None)
        if hasattr(config['OVS_ENABLED'], 'isChecked'):
            config['OVS_ENABLED'] = config['OVS_ENABLED'].isChecked()
        else:
            config['OVS_ENABLED'] = False
            
        config['OVS_CONTROLLER'] = getattr(self, 'VGCore_OVSController', None)
        if hasattr(config['OVS_CONTROLLER'], 'text'):
            config['OVS_CONTROLLER'] = config['OVS_CONTROLLER'].text()
        else:
            config['OVS_CONTROLLER'] = ''
            
        config['OVS_BRIDGE_NAME'] = getattr(self, 'VGCore_OVSBridgeName', None)
        if hasattr(config['OVS_BRIDGE_NAME'], 'text'):
            config['OVS_BRIDGE_NAME'] = config['OVS_BRIDGE_NAME'].text()
        else:
            config['OVS_BRIDGE_NAME'] = 'br-open5gs'
            
        config['OVS_FAIL_MODE'] = getattr(self, 'VGCore_OVSFailMode', None)
        if hasattr(config['OVS_FAIL_MODE'], 'currentText'):
            config['OVS_FAIL_MODE'] = config['OVS_FAIL_MODE'].currentText()
        else:
            config['OVS_FAIL_MODE'] = 'standalone'
            
        config['OPENFLOW_PROTOCOLS'] = getattr(self, 'VGCore_OpenFlowProtocols', None)
        if hasattr(config['OPENFLOW_PROTOCOLS'], 'text'):
            config['OPENFLOW_PROTOCOLS'] = config['OPENFLOW_PROTOCOLS'].text()
        else:
            config['OPENFLOW_PROTOCOLS'] = 'OpenFlow14'
            
        config['OVS_DATAPATH'] = getattr(self, 'VGCore_OVSDatapath', None)
        if hasattr(config['OVS_DATAPATH'], 'currentText'):
            config['OVS_DATAPATH'] = config['OVS_DATAPATH'].currentText()
        else:
            config['OVS_DATAPATH'] = 'kernel'
            
        config['CONTROLLER_PORT'] = getattr(self, 'VGCore_ControllerPort', None)
        if hasattr(config['CONTROLLER_PORT'], 'text'):
            config['CONTROLLER_PORT'] = config['CONTROLLER_PORT'].text()
        else:
            config['CONTROLLER_PORT'] = '6633'
            
        config['BRIDGE_PRIORITY'] = getattr(self, 'VGCore_BridgePriority', None)
        if hasattr(config['BRIDGE_PRIORITY'], 'text'):
            config['BRIDGE_PRIORITY'] = config['BRIDGE_PRIORITY'].text()
        else:
            config['BRIDGE_PRIORITY'] = '32768'
            
        config['STP_ENABLED'] = getattr(self, 'VGCore_STPEnabled', None)
        if hasattr(config['STP_ENABLED'], 'isChecked'):
            config['STP_ENABLED'] = config['STP_ENABLED'].isChecked()
        else:
            config['STP_ENABLED'] = False
            
        return config

    def onTableCellDoubleClicked(self, component_type, row, column):
        """Handle double-click on table cells, especially for Import YAML column."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            return
            
        # Check if this is the "Import YAML" column (column 1)
        if column == 1:  # Import YAML column
            self.importYamlForComponent(component_type, row)
        elif column == 2 and table.columnCount() > 2:  # Config Path column - allow browsing to file
            self.browseConfigPath(component_type, row)

    def showTableContextMenu(self, component_type, position):
        """Show context menu for table operations."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            return
            
        item = table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        column = item.column()
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        if column == 1:  # Import YAML column
            menu.addAction("Import YAML Configuration", lambda: self.importYamlForComponent(component_type, row))
            menu.addAction("Clear Configuration", lambda: self.clearComponentConfiguration(component_type, row))
        elif column == 2:  # Config Path column
            menu.addAction("Browse Config Path", lambda: self.browseConfigPath(component_type, row))
            menu.addAction("Clear Config Path", lambda: self.clearComponentSettings(component_type, row))
        
        menu.addSeparator()
        menu.addAction("Remove Component", lambda: self.removeSpecificComponent(component_type, row))
        
        menu.exec_(table.mapToGlobal(position))

    def addComponentType(self, component_type):
        """Add a new component instance to the corresponding table."""
        debug_print(f"DEBUG: Adding {component_type} component...")
        
        # Try different possible table name patterns
        possible_table_names = [
            f'Component5G_{component_type}table',
            f'{component_type}table',
            f'{component_type}Table',
            f'Component5G_{component_type}Table',
            f'{component_type}_table'
        ]
        
        table = None
        table_name = None
        
        # Find the table using any of the possible naming patterns
        for name in possible_table_names:
            if hasattr(self, name):
                table = getattr(self, name)
                table_name = name
                debug_print(f"DEBUG: Found table with name: {name}")
                break
        
        if not table:
            # Debug: # print all available attributes that contain 'table' or the component type
            debug_print(f"DEBUG: Could not find table for {component_type}. Available attributes:")
            for attr_name in dir(self):
                if 'table' in attr_name.lower() or component_type.lower() in attr_name.lower():
                    debug_print(f"  - {attr_name}")
            return
        
        # Verify it's actually a QTableWidget
        from PyQt5.QtWidgets import QTableWidget
        if not isinstance(table, QTableWidget):
            error_print(f"ERROR: Found object {table_name} but it's not a QTableWidget: {type(table)}")
            return
        
        row_position = table.rowCount()
        table.insertRow(row_position)
        
        # Set default name
        default_name = f"{component_type.lower()}{row_position + 1}"
        name_item = QTableWidgetItem(default_name)
        table.setItem(row_position, 0, name_item)
        
        # Set default config file entry with import instruction
        config_item = QTableWidgetItem("(Double-click to import)")
        config_item.setToolTip("Double-click to import YAML configuration file")
        table.setItem(row_position, 1, config_item)
        
        # Add additional default columns if table has more columns
        if table.columnCount() > 2:
            # Column 2 should be Config Path (based on UI definition)
            config_path_item = QTableWidgetItem("")
            config_path_item.setToolTip("Path to imported configuration file")
            table.setItem(row_position, 2, config_path_item)
            debug_print(f"DEBUG: Initialized Config Path column for {component_type} at row {row_position}")
        
        debug_print(f"DEBUG: Successfully added {component_type} component: {default_name} at row {row_position}")

    def removeComponentType(self, component_type):
        """Remove selected component instance from the corresponding table."""
        # Try different possible table name patterns
        possible_table_names = [
            f'Component5G_{component_type}table',
            f'{component_type}table',
            f'{component_type}Table',
            f'Component5G_{component_type}Table',
            f'{component_type}_table'
        ]
        
        table = None
        
        # Find the table using any of the possible naming patterns
        for name in possible_table_names:
            if hasattr(self, name):
                table = getattr(self, name)
                break
        
        if table:
            from PyQt5.QtWidgets import QTableWidget
            if isinstance(table, QTableWidget):
                current_row = table.currentRow()
                if current_row >= 0:
                    # Also remove from stored configurations
                    if self.component:
                        config_key = f"{component_type}_configs"
                        properties = self.component.getProperties()
                        if config_key in properties and isinstance(properties[config_key], list):
                            if current_row < len(properties[config_key]):
                                properties[config_key].pop(current_row)
                                self.component.setProperties(properties)
                    
                    table.removeRow(current_row)
                    debug_print(f"DEBUG: Removed {component_type} component at row {current_row}")
                else:
                    debug_print(f"DEBUG: No row selected for {component_type} table")
            else:
                error_print(f"ERROR: Found object but it's not a QTableWidget: {type(table)}")
        else:
            debug_print(f"DEBUG: Could not find table for {component_type}")

    def clearComponentConfiguration(self, component_type, row):
        """Clear the imported configuration for a component."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if table and row < table.rowCount():
            config_item = table.item(row, 1)
            if config_item:
                config_item.setText("(Double-click to import)")
                config_item.setToolTip("Double-click to import YAML configuration file")
                config_item.setData(Qt.UserRole, None)
                
            # Clear the Config Path column (column 2) as well
            if table.columnCount() > 2:
                config_path_item = table.item(row, 2)
                if config_path_item:
                    config_path_item.setText("")
                    config_path_item.setToolTip("")
                    debug_print(f"DEBUG: Cleared Config Path column for {component_type} row {row}")
                
            # Update stored configurations
            if self.component:
                properties = self.component.getProperties()
                config_key = f"{component_type}_configs"
                if config_key in properties and row < len(properties[config_key]):
                    config = properties[config_key][row]
                    config['imported'] = False
                    config['config_content'] = {}
                    config['config_file_path'] = ''
                    config['config_file'] = f"{config.get('name', component_type.lower())}.yaml"
                    self.component.setProperties(properties)

    def clearComponentSettings(self, component_type, row):
        """Clear the config path for a component (column 2 is Config Path, not settings)."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if table and row < table.rowCount() and table.columnCount() > 2:
            config_path_item = table.item(row, 2)
            if config_path_item:
                config_path_item.setText("")
                config_path_item.setToolTip("Path to imported configuration file")
                debug_print(f"DEBUG: Cleared Config Path for {component_type} row {row}")

    def removeSpecificComponent(self, component_type, row):
        """Remove a specific component row."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if table and row < table.rowCount():
            # Get component name for confirmation
            name_item = table.item(row, 0)
            component_name = name_item.text() if name_item else f"Row {row + 1}"
            
            reply = QMessageBox.question(
                self,
                "Remove Component",
                f"Are you sure you want to remove {component_type} component '{component_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove from stored configurations
                if self.component:
                    properties = self.component.getProperties()
                    config_key = f"{component_type}_configs"
                    if config_key in properties and row < len(properties[config_key]):
                        properties[config_key].pop(row)
                        self.component.setProperties(properties)
                
                # Remove from table
                table.removeRow(row)
                debug_print(f"DEBUG: Removed {component_type} component '{component_name}' at row {row}")

    def importYamlForComponent(self, component_type, row):
        """Import YAML configuration file for a specific component."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            # Try alternative table names
            possible_names = [f'{component_type}table', f'{component_type}Table', f'Component5G_{component_type}Table']
            for name in possible_names:
                if hasattr(self, name):
                    table = getattr(self, name)
                    break
        
        if not table:
            error_print(f"ERROR: Could not find table for {component_type}")
            return
            
        # Get the component name from the first column
        name_item = table.item(row, 0)
        if not name_item:
            QMessageBox.warning(self, "No Component Name", "Please enter a component name first.")
            return
            
        component_name = name_item.text().strip()
        if not component_name:
            QMessageBox.warning(self, "No Component Name", "Please enter a component name first.")
            return
        
        # Open file dialog to select YAML file
        # Dynamically find the 5g-configs directory relative to this script
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "export", "5g-configs"))
        initial_dir = config_dir if os.path.exists(config_dir) else ""
        
        # Suggest a default filename based on component type
        default_filename = f"{component_type.lower()}.yaml"
        initial_file = os.path.join(initial_dir, default_filename) if initial_dir else default_filename
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import YAML Configuration for {component_name} ({component_type})",
            initial_file,
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            try:
                import yaml
                
                # Load and validate the YAML file
                with open(file_path, 'r') as f:
                    yaml_content = yaml.safe_load(f)
                
                # Validate the configuration
                if not self.validate_yaml_for_component_type(yaml_content, component_type):
                    reply = QMessageBox.question(
                        self,
                        "Configuration Validation",
                        f"The selected YAML file may not be appropriate for {component_type} component.\n"
                        f"Do you want to import it anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                # Update the table item to show the imported file
                config_item = table.item(row, 1)
                if not config_item:
                    config_item = QTableWidgetItem()
                    table.setItem(row, 1, config_item)
                
                # Store the configuration data in the table item
                config_item.setText(f"✓ {os.path.basename(file_path)}")
                config_item.setToolTip(f"Imported from: {file_path}")
                config_item.config_data = yaml_content
                config_item.config_file_path = file_path
                config_item.config_filename = os.path.basename(file_path)
                
                # Update the Config Path column (column 2) to show the file path
                if table.columnCount() > 2:  # Ensure Config Path column exists
                    config_path_item = table.item(row, 2)
                    if not config_path_item:
                        config_path_item = QTableWidgetItem()
                        table.setItem(row, 2, config_path_item)
                    
                    config_path_item.setText(file_path)
                    config_path_item.setToolTip(f"Configuration file: {file_path}")
                    debug_print(f"DEBUG: Updated Config Path column for {component_type} row {row}: {file_path}")
                
                # Also store the configuration in component properties
                self.storeComponentConfiguration(component_type, row, file_path, yaml_content)
                
                debug_print(f"DEBUG: Successfully imported {file_path} for {component_name}")
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Configuration imported successfully for {component_name}!\n\n"
                    f"File: {os.path.basename(file_path)}\n"
                    f"Remember to click 'OK' to save all changes."
                )
                
            except yaml.YAMLError as e:
                QMessageBox.critical(
                    self,
                    "YAML Error",
                    f"Error parsing YAML file:\n{str(e)}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Error importing configuration file:\n{str(e)}"
                )

    def validate_yaml_for_component_type(self, yaml_content, component_type):
        """Validate that a YAML configuration is appropriate for the component type."""
        if not isinstance(yaml_content, dict):
            return False
            
        # Check if the YAML contains a section matching the component type
        expected_section = component_type.lower()
        
        # Some components might have different section names
        section_mapping = {
            'UPF': 'upf',
            'AMF': 'amf',
            'SMF': 'smf',
            'NRF': 'nrf',
            'SCP': 'scp',
            'AUSF': 'ausf',
            'BSF': 'bsf',
            'NSSF': 'nssf',
            'PCF': 'pcf',
            'UDM': 'udm',
            'UDR': 'udr'
        }
        
        expected_section = section_mapping.get(component_type, expected_section)
        
        # Check if the expected section exists in the YAML
        return expected_section in yaml_content

    def browseConfigPath(self, component_type, row):
        """Browse and select a configuration file path for the Config Path column."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            # Try alternative table names
            possible_names = [f'{component_type}table', f'{component_type}Table', f'Component5G_{component_type}Table']
            for name in possible_names:
                if hasattr(self, name):
                    table = getattr(self, name)
                    break
        
        if not table:
            error_print(f"ERROR: Could not find table for {component_type}")
            return
            
        # Get the component name from the first column
        name_item = table.item(row, 0)
        if not name_item:
            QMessageBox.warning(self, "No Component Name", "Please enter a component name first.")
            return
            
        component_name = name_item.text().strip()
        if not component_name:
            QMessageBox.warning(self, "No Component Name", "Please enter a component name first.")
            return
        
        # Open file dialog to select YAML file
        # Dynamically find the 5g-configs directory relative to this script
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "export", "5g-configs"))
        initial_dir = config_dir if os.path.exists(config_dir) else ""
        
        # Suggest a default filename based on component type
        default_filename = f"{component_type.lower()}.yaml"
        initial_file = os.path.join(initial_dir, default_filename) if initial_dir else default_filename
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Configuration File Path for {component_name} ({component_type})",
            initial_file,
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            # Update the Config Path column (column 2) to show the file path
            if table.columnCount() > 2:
                config_path_item = table.item(row, 2)
                if not config_path_item:
                    config_path_item = QTableWidgetItem()
                    table.setItem(row, 2, config_path_item)
                
                config_path_item.setText(file_path)
                config_path_item.setToolTip(f"Configuration file: {file_path}")
                debug_print(f"DEBUG: Set Config Path for {component_type} row {row}: {file_path}")
                
                QMessageBox.information(
                    self,
                    "Config Path Updated",
                    f"Configuration path set for {component_name}!\n\n"
                    f"Path: {file_path}\n"
                    f"Remember to click 'OK' to save all changes."
                )

    def storeComponentConfiguration(self, component_type, row, file_path, yaml_content):
        """Store the component configuration in the component's properties."""
        if not self.component:
            return
            
        # Get current properties
        properties = self.component.getProperties()
        
        # Initialize configurations storage if it doesn't exist
        config_key = f"{component_type}_configs"
        if config_key not in properties:
            properties[config_key] = []
            
        # Ensure we have enough entries in the config list
        while len(properties[config_key]) <= row:
            properties[config_key].append({})
            
        # Get component name from the table
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        component_name = f"{component_type.lower()}{row + 1}"  # Default name
        
        if table:
            name_item = table.item(row, 0)
            if name_item and name_item.text().strip():
                component_name = name_item.text().strip()
        
        # Update the specific component's configuration
        properties[config_key][row].update({
            'name': component_name,
            'config_file_path': file_path,
            'config_content': yaml_content,
            'config_filename': os.path.basename(file_path),
            'imported': True
        })
        
        # Save back to component
        self.component.setProperties(properties)

    def editComponentSettings(self, component_type, row):
        """Edit component config path manually (deprecated - use browseConfigPath instead)."""
        warning_print("WARNING: editComponentSettings is deprecated. Use browseConfigPath instead.")
        self.browseConfigPath(component_type, row)

    def extractTableData(self, component_type):
        """Extract data from a component type table including imported configurations."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            return []
            
        table_data = []
        for row in range(table.rowCount()):
            row_data = {}
            
            # Extract name (column 0)
            name_item = table.item(row, 0)
            if name_item and name_item.text().strip():
                row_data['name'] = name_item.text().strip()
            else:
                continue  # Skip rows without names
            
            # Extract config file info (column 1)
            config_item = table.item(row, 1)
            if config_item:
                config_data = config_item.data(Qt.UserRole)
                if config_data and isinstance(config_data, dict):
                    # Has imported configuration
                    row_data['config_file'] = config_data.get('config_filename', f"{row_data['name']}.yaml")
                    row_data['config_file_path'] = config_data.get('file_path', '')
                    row_data['config_content'] = config_data.get('config_content', {})
                    row_data['imported'] = config_data.get('imported', False)
                else:
                    # Use text value or default
                    config_text = config_item.text().strip()
                    if config_text and config_text != "(Double-click to import)":
                        row_data['config_file'] = config_text
                    else:
                        row_data['config_file'] = f"{row_data['name']}.yaml"
                    row_data['imported'] = False
            else:
                row_data['config_file'] = f"{row_data['name']}.yaml"
                row_data['imported'] = False
                
            # Extract additional columns if they exist
            if table.columnCount() > 2:
                settings_item = table.item(row, 2)
                if settings_item:
                    row_data['settings'] = settings_item.text().strip()
            
            # Add default values
            row_data['image'] = 'adaptive/open5gs:1.0'
            row_data['component_type'] = component_type
            row_data['volumes'] = []
            
            table_data.append(row_data)
        
        return table_data

    def loadTableData(self, component_type, table_data):
        """Load data into a component type table including imported configurations."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table or not table_data:
            return
            
        # Clear existing data
        table.setRowCount(0)
        
        # Load data
        for row_data in table_data:
            row_position = table.rowCount()
            table.insertRow(row_position)
            
            # Set name (column 0)
            if 'name' in row_data:
                name_item = QTableWidgetItem(row_data['name'])
                table.setItem(row_position, 0, name_item)
            
            # Set config file (column 1)
            config_item = QTableWidgetItem()
            if row_data.get('imported', False):
                # Has imported configuration
                config_filename = row_data.get('config_file', f"{row_data['name']}.yaml")
                config_item.setText(config_filename)
                config_item.setToolTip(f"Imported from: {row_data.get('config_file_path', 'Unknown')}")
                
                # Store the configuration data
                config_data = {
                    'file_path': row_data.get('config_file_path', ''),
                    'config_content': row_data.get('config_content', {}),
                    'config_filename': config_filename,
                    'imported': True
                }
                config_item.setData(Qt.UserRole, config_data)
            else:
                # No imported configuration
                config_filename = row_data.get('config_file', f"{row_data['name']}.yaml")
                config_item.setText(config_filename if config_filename != f"{row_data['name']}.yaml" else "(Double-click to import)")
                config_item.setToolTip("Double-click to import YAML configuration file")
                
            table.setItem(row_position, 1, config_item)
                
            # Set additional columns if they exist
            if table.columnCount() > 2 and 'settings' in row_data:
                settings_item = QTableWidgetItem(row_data['settings'])
                settings_item.setToolTip("Double-click to edit component settings")
                table.setItem(row_position, 2, settings_item)
        
        debug_print(f"DEBUG: Loaded {len(table_data)} items into {component_type} table")
        
    def debug_ui_elements(self):
        """Debug method to # print all UI elements - call this in __init__ to see what's available"""
        debug_print("=== DEBUG: All UI elements ===")
        from PyQt5.QtWidgets import QTableWidget, QPushButton
        
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                try:
                    attr_obj = getattr(self, attr_name)
                    if isinstance(attr_obj, QTableWidget):
                        debug_print(f"TABLE: {attr_name} (rows: {attr_obj.rowCount()}, cols: {attr_obj.columnCount()})")
                    elif isinstance(attr_obj, QPushButton):
                        debug_print(f"BUTTON: {attr_name} (text: '{attr_obj.text()}')")
                except:
                    pass
        debug_print("=== END DEBUG ===")
        
    def onOK(self):
        """Enhanced save that includes all new configuration options"""
        self.saveProperties()
        
        # Store additional configurations in the component
        if self.component:
            # Store Docker configuration
            docker_config = self.getDockerConfiguration()
            self.component.properties.update({f"docker_{k.lower()}": v for k, v in docker_config.items()})
            
            # Store 5G Core configuration
            core_config = self.get5GCoreConfiguration()
            self.component.properties.update({f"5gcore_{k.lower()}": v for k, v in core_config.items()})
            
            # Store OVS configuration
            ovs_config = self.getOVSConfiguration()
            self.component.properties.update({f"ovs_{k.lower()}": v for k, v in ovs_config.items()})
            
            debug_print(f"DEBUG: Enhanced 5G Core configuration saved for {self.component_name}")
            
        self.close()
        
    def onCancel(self):
        self.close()

class LinkPropertiesWindow(BasePropertiesWindow):
    """Properties window for network links with bandwidth, delay, and loss settings."""
    
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        
        # Load the UI file
        ui_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "Link_properties.ui")
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
            debug_print(f"DEBUG: Loaded Link properties UI from {ui_file}")
        else:
            error_print(f"ERROR: Link properties UI file not found: {ui_file}")
            return
            
        # Set window properties
        self.setWindowTitle(f"Link Properties - {label_text}")
        self.setFixedSize(450, 300)
        
        # Load existing properties
        self.loadProperties()
        
        # Setup connections
        self.setupConnections()
        
    def setupConnections(self):
        """Setup button connections"""
        self.pushButton_ok.clicked.connect(self.onOK)
        self.pushButton_cancel.clicked.connect(self.onCancel)
        
    def loadProperties(self):
        """Load current link properties into the UI"""
        if not self.component:
            return
            
        properties = self.component.properties
        
        # Basic information
        self.lineEdit_name.setText(properties.get('name', ''))
        
        # Set type combo box
        link_type = properties.get('type', 'ethernet')
        index = self.comboBox_type.findText(link_type)
        if index >= 0:
            self.comboBox_type.setCurrentIndex(index)
            
        self.lineEdit_source.setText(properties.get('source', ''))
        self.lineEdit_destination.setText(properties.get('destination', ''))
        
        # Network parameters
        bandwidth = properties.get('bandwidth', '')
        if bandwidth:
            try:
                # Remove 'Mbps' suffix if present and convert to int (via float for float strings)
                if isinstance(bandwidth, str) and bandwidth.endswith('Mbps'):
                    bandwidth = int(bandwidth.replace('Mbps', '').strip())
                else:
                    bandwidth = int(bandwidth)
                self.spinBox_bandwidth.setValue(bandwidth)
            except (ValueError, TypeError):
                self.spinBox_bandwidth.setValue(0)
        else:
            self.spinBox_bandwidth.setValue(0)
            
        self.lineEdit_delay.setText(properties.get('delay', ''))
        
        loss = properties.get('loss', 0.0)
        if loss:
            try:
                # Remove '%' suffix if present and convert to float
                if isinstance(loss, str) and loss.endswith('%'):
                    loss = int(loss.replace('%', '').strip())
                else:
                    loss = int(loss)
                self.spinBox_loss.setValue(loss)
            except (ValueError, TypeError):
                self.spinBox_loss.setValue(0)
        else:
            self.spinBox_loss.setValue(0)
            
    def saveProperties(self):
        """Save the link properties from UI to component"""
        if not self.component:
            warning_print("WARNING: No component reference to save properties to")
            return
            
        # Update basic properties
        self.component.properties['name'] = self.lineEdit_name.text()
        self.component.properties['type'] = self.comboBox_type.currentText()
        
        # Update network parameters
        bandwidth = self.spinBox_bandwidth.value()
        if bandwidth > 0:
            self.component.properties['bandwidth'] = str(bandwidth)
        else:
            self.component.properties.pop('bandwidth', None)
            
        delay = self.lineEdit_delay.text().strip()
        if delay:
            self.component.properties['delay'] = delay
        else:
            self.component.properties.pop('delay', None)
            
        loss = self.spinBox_loss.value()
        if loss > 0:
            self.component.properties['loss'] = str(loss)
        else:
            self.component.properties.pop('loss', None)
            
        # Update display name if name was changed
        if self.lineEdit_name.text():
            self.component.name = self.lineEdit_name.text()
        
        # Update tooltip and visual appearance
        if hasattr(self.component, 'updateTooltip'):
            self.component.updateTooltip()
        if hasattr(self.component, 'update'):
            self.component.update()  # Refresh visual appearance
            
        # Mark topology as modified
        if hasattr(self.component, 'main_window') and self.component.main_window:
            if hasattr(self.component.main_window, 'onTopologyChanged'):
                self.component.main_window.onTopologyChanged()
                
        debug_print(f"DEBUG: Link properties saved - bandwidth: {self.component.properties.get('bandwidth', 'Auto')}, delay: {self.component.properties.get('delay', 'None')}, loss: {self.component.properties.get('loss', '0')}")
        
    def onOK(self):
        """Save properties and close dialog"""
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        """Close dialog without saving"""
        self.close()