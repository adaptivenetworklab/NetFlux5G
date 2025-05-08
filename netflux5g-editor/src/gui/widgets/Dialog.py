from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os

class HostPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Host_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        # Center the dialog on the parent widget
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class STAPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "STA_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"STA Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class APPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "AP_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"AP Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class ControllerPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Controller_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Controller Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class DockerHostPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "DockerHost_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Docker Host Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class GNBPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"gNB Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class UEPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"UE Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class Core5GPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Core5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"5G Core Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class Component5GPropertiesWindow(QMainWindow):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"5G Components Properties - {label_text}")
        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

# class UPFCore5GPropertiesWindow(QMainWindow):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UPF_properties.ui")
#         uic.loadUi(ui_file, self)
#         self.setWindowTitle("UPF Properties")

#         self.setWindowFlags(Qt.Window)

#         if parent:
#             parent_geometry = parent.geometry()
#             self.move(
#                 parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
#                 parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
#             )