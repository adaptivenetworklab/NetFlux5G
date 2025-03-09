from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QToolBar, QAction
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QIcon, QPixmap, QKeyEvent
from PyQt5 import uic
import sys, os

class MovableLabel(QLabel):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
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
        super().__init__(text, parent)
        self.setStyleSheet("qproperty-alignment: AlignCenter;")
        self.setFixedSize(50, 50)

        if icon and not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())  
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
        label = MovableLabel("Host", self.window().actionHost.icon(), parent=self)
        label.move(event.pos())  
        label.show()
        label.setFocus()  # Ensure the dropped object can receive key events
        event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "Main_Window.ui"), self)  
        
        self.actionHost = self.findChild(QAction, "actionHost")
        if self.actionHost:
            self.actionHost.triggered.connect(self.add_host_to_canvas)  

        self.canvas = Canvas()
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.make_host_draggable()

    def make_host_draggable(self):
        host_label = DraggableLabel("Host", self.actionHost.icon(), self.toolBar)
        self.toolBar.addWidget(host_label)

    def add_host_to_canvas(self):
        print("Adding Host to Canvas")  
        host_label = MovableLabel("Host", self.actionHost.icon(), self.canvas)
        host_label.move(50, 50)
        host_label.show()
        host_label.setFocus()  


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()