from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QKeyEvent
from PyQt5 import uic
import sys, os

actions = [
    "actionHost", "actionSTA", "actionGNB", "actionDockerHost",
    "actionAP", "action5GCore", "actionRouter", "actionSwitch",
    "actionLinkCable", "actionController"
]

class MovableLabel(QLabel):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setAttribute(Qt.WA_DeleteOnClose)

        if icon and not icon.isNull():
            pixmap = icon.pixmap(50, 50)
            self.setPixmap(pixmap)

        self.dragging = False
        self.offset = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()  
            self.setFocus()  # Set focus to receive key events

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        self.dragging = False  

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.close()  # Delete the object


class DraggableLabel(QLabel):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("qproperty-alignment: AlignCenter;")
        self.setFixedSize(50, 50)

        if icon and not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            self.setPixmap(pixmap)

        self.object_type = text  

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.object_type)  
            drag.setMimeData(mime_data)
            drag.exec_(Qt.MoveAction)


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        object_type = event.mimeData().text()
        action_attr = f"action{object_type}"  
        action = getattr(self.window(), action_attr, None)

        if action:
            label = MovableLabel(object_type, action.icon(), parent=self)
            label.move(event.pos())  
            label.show()
            label.setFocus()  
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "Main_Window.ui"), self)  
        
        self.canvas = Canvas()
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setup_draggable_objects()

    def setup_draggable_objects(self):
        for action_name in actions:
            action = getattr(self, action_name, None)
            if action:
                label = DraggableLabel(action_name.replace("action", ""), action.icon(), self)
                self.toolBar.addWidget(label)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()