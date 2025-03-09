from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
import sys, os

class Ui(QMainWindow):  # Use QMainWindow directly
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "Main_Window.ui"), self)
        
        self.show()

app = QApplication(sys.argv)
window = Ui()  # Fix class name
window.show()
app.exec()
