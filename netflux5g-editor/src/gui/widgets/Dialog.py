from PyQt5.QtWidgets import QMainWindow, QLineEdit, QComboBox, QCheckBox, QTableWidget, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import os

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
        """Save all UI values to the component's properties"""
        if not self.component:
            print("Warning: No component reference to save properties to")
            return
            
        properties = {}
        
        # Automatically collect all QLineEdit, QComboBox, QCheckBox values
        for widget in self.findChildren(QLineEdit):
            name = widget.objectName()
            if name:  # Only save if the widget has a name
                properties[name] = widget.text()
                
        for widget in self.findChildren(QComboBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.currentText()
                
        for widget in self.findChildren(QCheckBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.isChecked()

        for widget in self.findChildren(QSpinBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.value()

        for widget in self.findChildren(QDoubleSpinBox):
            name = widget.objectName()
            if name:
                properties[name] = widget.value()
        
        # Save to component
        self.component.setProperties(properties)
        print(f"DEBUG: Saved properties for {self.component_name}: {properties}")

    def loadProperties(self):
        """Load component properties into UI widgets"""
        if not self.component:
            return
            
        properties = self.component.getProperties()
        
        # Load values into widgets
        for widget in self.findChildren(QLineEdit):
            name = widget.objectName()
            if name in properties:
                widget.setText(str(properties[name]))
                
        for widget in self.findChildren(QComboBox):
            name = widget.objectName()
            if name in properties:
                text = str(properties[name])
                index = widget.findText(text)
                if index >= 0:
                    widget.setCurrentIndex(index)
                    
        for widget in self.findChildren(QCheckBox):
            name = widget.objectName()
            if name in properties:
                widget.setChecked(bool(properties[name]))

        for widget in self.findChildren(QSpinBox):
            name = widget.objectName()
            if name in properties:
                widget.setValue(int(properties[name]))

        for widget in self.findChildren(QDoubleSpinBox):
            name = widget.objectName()
            if name in properties:
                widget.setValue(float(properties[name]))

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
        self.setupConnections()
        self.loadProperties()

    def setupConnections(self):
        # Connect OK and Cancel buttons (adjust based on actual UI)
        if hasattr(self, 'Component5G_OKButton'):
            self.Component5G_OKButton.clicked.connect(self.onOK)
        if hasattr(self, 'Component5G_CancelButton'):
            self.Component5G_CancelButton.clicked.connect(self.onCancel)
        
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