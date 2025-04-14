import os
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRect 
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen
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
        self.setAttribute(Qt.WA_DeleteOnClose)

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
            # Prevent dragging in Delete Mode
            if self.parent().app_instance.current_tool == "delete":
                return  # Let the parent handle the delete logic
            self.dragging = True
            self.offset = event.pos()
            self.setFocus()  # Set focus to the label when clicked
            print(f"DEBUG: MovableLabel mousePressEvent at {event.pos()}, current_tool: {self.parent().app_instance.current_tool}")

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.close()  # Delete the label when the Delete key is pressed
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu events."""
        # Get the dialog class for the current object type
        dialog_class = self.DIALOG_MAP.get(self.object_type)
        if dialog_class:
            # Close the existing dialog if it is already open
            canvas = self.parent()
            if canvas.current_dialog:
                canvas.current_dialog.close()

            # Create a new dialog
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

class Canvas(QGraphicsView):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        # Create a QGraphicsScene for the canvas
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Set a larger scene size
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)  # A large virtual canvas

        # Enable drag mode for panning
        self.setDragMode(QGraphicsView.NoDrag)

        # Set the background color
        self.setStyleSheet("background-color: white;")

        # Enable drag-and-drop
        self.setAcceptDrops(True)

        # Track whether the grid is shown
        self.show_grid = False

        # Initialize zoom level
        self.zoom_level = 1.0

    def zoomIn(self):
        """Zoom in the canvas."""
        self.zoom_level *= 1.2  # Increase zoom level by 20%
        self.scale(1.2, 1.2)
        print(f"DEBUG: Zoomed in, current zoom level: {self.zoom_level}")

    def zoomOut(self):
        """Zoom out the canvas."""
        self.zoom_level /= 1.2  # Decrease zoom level by 20%
        self.scale(1 / 1.2, 1 / 1.2)
        print(f"DEBUG: Zoomed out, current zoom level: {self.zoom_level}")

    def resetZoom(self):
        """Reset the zoom level to the default."""
        self.resetTransform()  # Reset the transformation matrix
        self.zoom_level = 1.0
        print("DEBUG: Zoom reset to default level")

    def setShowGrid(self, show):
        """Enable or disable the grid."""
        self.show_grid = show
        self.update()  # Trigger a repaint of the canvas

    def drawBackground(self, painter, rect):
        """Draw the grid if enabled."""
        super().drawBackground(painter, rect)
        if self.show_grid:
            pen = QPen(Qt.lightGray)
            pen.setWidth(1)
            painter.setPen(pen)

            # Draw grid lines
            grid_size = 20  # Size of each grid cell
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            for x in range(left, int(rect.right()), grid_size):
                painter.drawLine(x, rect.top(), x, rect.bottom())
            for y in range(top, int(rect.bottom()), grid_size):
                painter.drawLine(rect.left(), y, rect.right(), y)

    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            component_type = event.mimeData().text()
            print(f"DEBUG: Dropped component type: {component_type}")  # Debug message

            # Get the icon for the dropped component
            icon_path = self.app_instance.component_icon_map.get(component_type)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path).scaled(50, 50)
                item = QGraphicsPixmapItem(pixmap)
                item.setPos(self.mapToScene(event.pos()))
                self.scene.addItem(item)
                print(f"DEBUG: Component {component_type} added at position {event.pos()}")  # Debug message
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Check if the click is outside any MovableLabel
            clicked_on_label = False
            for child in self.children():
                if isinstance(child, MovableLabel) and child.geometry().contains(event.pos()):
                    clicked_on_label = True
                    break

            if not clicked_on_label and self.current_dialog:
                print("DEBUG: Closing dialog because canvas was clicked.")  # Debug message
                self.current_dialog.close()
                self.current_dialog = None

            # Handle delete tool or other tools
            if self.app_instance.current_tool == "delete":
                for child in self.children():
                    if isinstance(child, MovableLabel) and child.geometry().contains(event.pos()):
                        print(f"DEBUG: Deleting component {child.object_type}")  # Debug message
                        child.deleteLater()  # Delete the component
                        return  # Exit after deleting the component
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def setCurrentDialog(self, dialog):
        """Close the currently open dialog and set the new dialog."""
        if self.current_dialog and self.current_dialog.isVisible():
            self.current_dialog.close()
        self.current_dialog = dialog