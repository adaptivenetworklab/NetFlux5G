from PyQt5.QtWidgets import QWidget, QMainWindow, QPushButton
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os

class HostPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "HostDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle(f"Host Properties - {label_text}")

        # Connect the button to open the HostPropertiesWindow
        self.Host_PropertiesButton.clicked.connect(self.openDetailProperties)  # Replace 'pushButton' with the actual objectName of the button

    def openDetailProperties(self):
        # Open the HostPropertiesWindow
        detail_properties_window = HostPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        # Close the current dialog
        self.close()

class HostPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Host_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Host Properties")

        # Make the QWidget behave like a standalone window
        self.setWindowFlags(Qt.Window)

        # Center the dialog on the parent widget
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class STAPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "STADialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("STA Properties")

        self.STA_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = STAPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class STAPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "STA_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("STA Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class APPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "APDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("AP Properties")

        self.AP_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = APPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class APPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "AP_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("AP Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class ControllerPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "ControllerDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Controller Properties")

        self.Controller_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = ControllerPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class ControllerPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Controller_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Controller Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class DockerHostPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "DockerHostDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Docker Host Properties")

        self.DockerHost_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = DockerHostPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class DockerHostPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "DockerHost_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("Docker Host  Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class GNBPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNBDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("gNB Properties")

        self.GNB_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = GNBPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class GNBPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "GNB_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("gNB Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class UEPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UEDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("UE Properties")

        self.UE_PropertiesButton.clicked.connect(self.openDetailProperties) 

    def openDetailProperties(self):
        detail_properties_window = UEPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class UEPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "UE_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("UE Properties")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class Core5GPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Core5GDialog.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("5G Core Properties")

        self.Core5G_GeneralSettingsButton.clicked.connect(self.openDetailProperties)
        self.Core5G_Component5GPropertiesButton.clicked.connect(self.Component5GopenDetailProperties)

    def openDetailProperties(self):
        detail_properties_window = Core5GPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

    def Component5GopenDetailProperties(self):
        detail_properties_window = Component5GPropertiesWindow(parent=self.parent())
        detail_properties_window.show()

        self.close()

class Core5GPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Core5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("5G Core General Setting")

        self.setWindowFlags(Qt.Window)

        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )

class Component5GPropertiesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "Component5G_properties.ui")
        uic.loadUi(ui_file, self)
        self.setWindowTitle("5G Components Properties")

        self.setWindowFlags(Qt.Window)

        # if parent:
        #     parent_geometry = parent.geometry()
        #     self.move(
        #         parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
        #         parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
        #     )

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