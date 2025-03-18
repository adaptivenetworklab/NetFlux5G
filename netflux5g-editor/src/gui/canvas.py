from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPixmap

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
            self.setFocus()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.close()


class Canvas(QWidget):
    def __init__(self, parent=None):  # Accept a parent argument
        super().__init__(parent)  # Pass the parent to the QWidget constructor
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        object_type = event.mimeData().text()
        print(f"Dropped object type: {object_type}")  # Debug message
        # Handle the drop event (e.g., create a new widget or object)