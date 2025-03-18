import os
from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPixmap
from .widgets.Dialog import HostPropertiesDialog

class MovableLabel(QLabel):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setAttribute(Qt.WA_DeleteOnClose)

        if icon and not icon.isNull():
            pixmap = icon.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
            print("DEBUG: Pixmap set for MovableLabel")  # Debug message
        else:
            self.setText(text)  # Fallback to text if no icon is provided
            print("DEBUG: No icon provided, fallback to text")  # Debug message

        self.dragging = False
        self.offset = QPoint()
        self.dialog = None # Dialog for object properties

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
    
    def contextMenuEvent(self, event):
        # Close the existing dialog if it is already open
        if self.dialog and self.dialog.isVisible():
            self.dialog.close()

        # Create a new dialog
        canvas = self.parent()
        self.dialog = HostPropertiesDialog(self.text(), parent=canvas)

        # Move the dialog to the cursor position relative to the canvas
        self.dialog.move(event.globalPos() - canvas.mapToGlobal(QPoint(0, 0)))

        # Show the dialog
        self.dialog.show()

class Canvas(QWidget):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance  # Store a reference to the NetFlux5GApp instance
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: white;")  # Set a visible background color for the canvas

    def dragEnterEvent(self, event):
        print("DEBUG: Drag entered canvas")  # Debug message
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        print("DEBUG: Drop event on canvas")  # Debug message
        object_type = event.mimeData().text()
        print(f"Dropped object type: {object_type}")  # Debug message

        # Get the icon for the dropped object
        icon_path = self.app_instance.component_icon_map.get(object_type)
        if icon_path:
            absolute_icon_path = os.path.abspath(icon_path)
            print(f"DEBUG: Absolute icon path: {absolute_icon_path}")  # Debug message
            if os.path.exists(absolute_icon_path):
                icon = QPixmap(absolute_icon_path)
                print("DEBUG: Icon loaded successfully")  # Debug message
            else:
                icon = None
                print("DEBUG: Icon not found at path: {absolute_icon_path}")  # Debug message
        else:
            icon = None
            print("DEBUG: No icon path found for object type: {object_type}")  # Debug message

        # Create a label for the dropped object
        label = MovableLabel(object_type, icon=icon, parent=self)
        label.move(event.pos())
        label.show()
        event.acceptProposedAction()