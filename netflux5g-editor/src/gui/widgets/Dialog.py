import os
from PyQt5.QtWidgets import QMainWindow, QLineEdit, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import yaml
from gui.debug_manager import debug_print, error_print, warning_print

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

    def save5GComponentTableData(self, properties):
        """Save data from all 5G component tables."""
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'PCRF', 'UDM', 'UDR']
        
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
                        elif hasattr(config_item, 'config_file_path'):
                            row_data['config_file_path'] = config_item.config_file_path
                            row_data['imported'] = True
                            row_data['config_filename'] = os.path.basename(config_item.config_file_path)
                        else:
                            row_data['imported'] = False
                            row_data['config_filename'] = f"{component_type.lower()}.yaml"
                    else:
                        row_data['config_display'] = "(Double-click to import)"
                        row_data['imported'] = False
                        row_data['config_filename'] = f"{component_type.lower()}.yaml"
                    
                    # Settings (column 2, if exists)
                    if table.columnCount() > 2:
                        settings_item = table.item(row, 2)
                        if settings_item:
                            row_data['settings'] = settings_item.text()
                        else:
                            row_data['settings'] = ""
                    
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
                    widget.setValue(int(properties[name]))
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
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'PCRF', 'UDM', 'UDR']
        
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
                
                # Settings (column 2, if exists)
                if table.columnCount() > 2:
                    settings_item = QTableWidgetItem(row_data.get('settings', ''))
                    settings_item.setToolTip("Double-click to edit component settings")
                    table.setItem(i, 2, settings_item)
            
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
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"GNB Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.GNB_OKButton.clicked.connect(self.onOK)
        self.GNB_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class UEPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"UE Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        self.UE_OKButton.clicked.connect(self.onOK)
        self.UE_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class Component5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"5G Component Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        
        # Temporary debug - remove this after fixing the issue
        self.debug_ui_elements()
        
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        if hasattr(self, 'Component5G_OKButton'):
            self.Component5G_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'Component5G_CancelButton'):
            self.Component5G_CancelButton.clicked.connect(self.onCancel)
            
        # Connect add buttons for each component type - FIXED: Remove duplicate connections
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'PCRF', 'UDM', 'UDR']
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

    def onTableCellDoubleClicked(self, component_type, row, column):
        """Handle double-click on table cells, especially for Import YAML column."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table:
            return
            
        # Check if this is the "Import YAML" column (typically column 1)
        if column == 1:  # Import YAML column
            self.importYamlForComponent(component_type, row)
        elif column == 2 and table.columnCount() > 2:  # Settings column if it exists
            self.editComponentSettings(component_type, row)

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
        elif column == 2:  # Settings column
            menu.addAction("Edit Settings", lambda: self.editComponentSettings(component_type, row))
            menu.addAction("Clear Settings", lambda: self.clearComponentSettings(component_type, row))
        
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
            settings_item = QTableWidgetItem("")
            settings_item.setToolTip("Double-click to edit component settings")
            table.setItem(row_position, 2, settings_item)
        
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
        """Clear the settings for a component."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if table and row < table.rowCount() and table.columnCount() > 2:
            settings_item = table.item(row, 2)
            if settings_item:
                settings_item.setText("")

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
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "5g-configs"))
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
            'PCRF': 'pcrf',
            'UDM': 'udm',
            'UDR': 'udr'
        }
        
        expected_section = section_mapping.get(component_type, expected_section)
        
        # Check if the expected section exists in the YAML
        return expected_section in yaml_content

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
            
        # Update the specific component's configuration
        properties[config_key][row].update({
            'config_file_path': file_path,
            'config_content': yaml_content,
            'config_filename': os.path.basename(file_path),
            'imported': True
        })
        
        # Save back to component
        self.component.setProperties(properties)

    def editComponentSettings(self, component_type, row):
        """Edit component-specific settings."""
        table_name = f'Component5G_{component_type}table'
        table = getattr(self, table_name, None)
        
        if not table or table.columnCount() <= 2:
            return
            
        # Get current settings
        settings_item = table.item(row, 2)
        current_settings = settings_item.text() if settings_item else ""
        
        # Create a simple input dialog for settings
        from PyQt5.QtWidgets import QInputDialog
        
        settings, ok = QInputDialog.getMultiLineText(
            self,
            f"Edit Settings for {component_type}",
            "Enter component-specific settings (key=value, one per line):",
            current_settings
        )
        
        if ok:
            if not settings_item:
                settings_item = QTableWidgetItem()
                table.setItem(row, 2, settings_item)
            settings_item.setText(settings)

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
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()

class UPFCore5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None, component=None):
        super().__init__(label_text, parent, component)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UPF_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"UPF Properties - {label_text}")
        self.setWindowFlags(Qt.Window)
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons
        if hasattr(self, 'UPF_OKButton'):
            self.UPF_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'UPF_CancelButton'):
            self.UPF_CancelButton.clicked.connect(self.onCancel)
        
    def onOK(self):
        self.saveProperties()
        self.close()
        
    def onCancel(self):
        self.close()