from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
import os

class HostPropertiesDialog(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        
        # Load the .ui file
        ui_file = os.path.join(os.path.dirname(__file__), "..", "ui", "HostDialog.ui")
        uic.loadUi(ui_file, self)