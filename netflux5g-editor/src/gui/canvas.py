import os
from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPixmap
from .widgets.Dialog import *

class MovableLabel(QLabel):
    DIALOG_MAP = {
        "Host": HostPropertiesDialog,
        "STA": STAPropertiesDialog,
        "UE": UEPropertiesDialog,
        "GNB": GNBPropertiesDialog,
        "DockerHost": DockerHostPropertiesDialog,
        "AP": APPropertiesDialog,
        "VGcore": Core5GPropertiesDialog,
        "Controller": ControllerPropertiesDialog
    }

    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.ClickFocus)  # Allow the label to receive focus when clicked

        if icon and not icon.isNull():
            pixmap = icon.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
        else:
            self.setText(text)  # Fallback to text if no icon is provided

        self.dragging = False
        self.offset = QPoint()
        self.dialog = None  # Dialog for object properties
        self.object_type = text  # Store the object type (e.g., "Host", "STA")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.setFocus()  # Set focus to the label when clicked

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.close()  # Delete the label when the Delete key is pressed
    
    def contextMenuEvent(self, event):
        # Get the dialog class for the current object type
        dialog_class = self.DIALOG_MAP.get(self.object_type)
        if dialog_class:
            # Create a new dialog
            canvas = self.parent()
            self.dialog = dialog_class(self.text(), parent=canvas)

            # Move the dialog to the cursor position relative to the canvas
            self.dialog.move(event.globalPos() - canvas.mapToGlobal(QPoint(0, 0)))

            # Show the dialog
            self.dialog.show()

            # Notify the canvas about the currently open dialog
            if isinstance(canvas, Canvas):
                canvas.setCurrentDialog(self.dialog)
        else:
            print(f"No dialog found for object type: {self.object_type}")

class Canvas(QWidget):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: white;")
        self.current_dialog = None  # Track the currently open dialog

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
                print(f"DEBUG: Icon not found at path: {absolute_icon_path}")  # Debug message
        else:
            icon = None
            print(f"DEBUG: No icon path found for object type: {object_type}")  # Debug message

        # Create a label for the dropped object
        label = MovableLabel(object_type, icon=icon, parent=self)
        label.move(event.pos())
        label.show()
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        # Close the currently open dialog if it exists and the click is outside the dialog
        if self.current_dialog and not self.current_dialog.geometry().contains(event.globalPos()):
            self.current_dialog.close()
            self.current_dialog = None
        super().mousePressEvent(event)

    def setCurrentDialog(self, dialog):
        # Close the currently open dialog if it exists
        if self.current_dialog and self.current_dialog.isVisible():
            self.current_dialog.close()
        # Set the new dialog as the current dialog
        self.current_dialog = dialog