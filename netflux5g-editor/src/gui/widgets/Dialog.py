from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import os

class BasePropertiesWindow(QMainWindow):
    """Base class for all properties windows that automatically sets the icon."""
    
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        # Store the component name
        self.component_name = label_text

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

class HostPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Host_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class STAPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "STA_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"STA Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class APPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "AP_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"AP Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class ControllerPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Controller_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Controller Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class DockerHostPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "DockerHost_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Docker Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class GNBPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"GNB Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class UEPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"UE Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class Core5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Core5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"5G Core Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class Component5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"5G Component Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

class UPFCore5GPropertiesWindow(BasePropertiesWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(label_text, parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UPF_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"UPF Properties - {label_text}")
        self.setWindowFlags(Qt.Window)