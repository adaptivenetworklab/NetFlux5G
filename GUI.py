from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFrame, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag
from PyQt5 import uic
import os
import sys

class DraggableButton(QPushButton):
    """ Buttons inside ObjectLayout that can be dragged onto the canvas """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setText(text)

    def mouseMoveEvent(self, event):
        """ Initiates drag event when button is moved """
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())  # Send button text as data
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)


class Canvas(QWidget):
    """ The canvas where dragged objects will be placed """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: white; border: 1px solid black;")  # Ensure visibility

    def dragEnterEvent(self, event):
        """ Accepts dragged items """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """ Handles placing dropped objects onto the canvas """
        object_type = event.mimeData().text()
        print(f"Dropped: {object_type} at {event.pos()}")  # Debugging

        # Create a new button at the dropped position
        new_button = QPushButton(object_type, self)  # Use QPushButton for simplicity
        new_button.move(event.pos())  # Position where dropped
        new_button.show()

        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "MainWindow.ui"), self)

        self.objectFrame = self.findChild(QFrame, "ObjectFrame")  # Reference to ObjectFrame
        self.objectLayout = self.findChild(QVBoxLayout, "ObjectLayout")  # Layout inside ObjectFrame
        self.canvas = self.findChild(QWidget, "Canvas")  # Reference to Canvas

        # Ensure Canvas accepts drops
        if self.canvas:
            self.canvas.setAcceptDrops(True)

        self.makeObjectsDraggable()

    def makeObjectsDraggable(self):
        """ Makes buttons inside ObjectLayout draggable """
        if self.objectLayout:
            for i in range(self.objectLayout.count()):
                widget = self.objectLayout.itemAt(i).widget()
                if isinstance(widget, QPushButton):  # Ensure it's a button
                    widget.mouseMoveEvent = lambda event, btn=widget: self.startDrag(event, btn)

    def startDrag(self, event, button):
        """ Starts drag operation when a button is moved """
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(button)
            mime_data = QMimeData()
            mime_data.setText(button.text())  
            drag.setMimeData(mime_data)

            drag.exec_(Qt.MoveAction)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
