import os
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QGraphicsSceneContextMenuEvent, QMenu
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRect 
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen
from .widgets.Dialog import *
from .components import NetworkComponent

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
        self.current_dialog = None

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

        # Track the currently open dialog
        self.current_dialog = False

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
        print(f"DEBUG: Grid visibility set to {self.show_grid}")  # Debug message
        self.viewport().update()  # Trigger a repaint of the canvas

    def drawBackground(self, painter, rect):
        """Draw the grid if enabled."""
        super().drawBackground(painter, rect)
        if self.show_grid:
            pen = QPen(Qt.lightGray)
            pen.setWidth(0)
            painter.setPen(pen)

            # Draw grid lines
            grid_size = 35  # Size of each grid cell
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            right = int(rect.right())
            bottom = int(rect.bottom())

            for x in range(left, right, grid_size):
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            for y in range(top, bottom, grid_size):
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            component_type = event.mimeData().text()
            print(f"DEBUG: Dropped component type: {component_type}")  # Debug message

            # Get the icon for the dropped component
            icon_path = self.app_instance.component_icon_map.get(component_type)
            if icon_path and os.path.exists(icon_path):
                # Create a NetworkComponent and add it to the scene
                position = self.mapToScene(event.pos())
                component = NetworkComponent(component_type, icon_path)
                component.setPos(position)
                self.scene.addItem(component)
                print(f"DEBUG: Component {component_type} added at position {position}")  # Debug message
            else:
                print(f"ERROR: Icon for component type '{component_type}' not found.")
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if self.current_dialog:
            # Close the currently open dialog
            print("DEBUG: Closing dialog because canvas was clicked.")  # Debug message
            self.current_dialog.close()
            self.current_dialog = None

        super().mousePressEvent(event)

    def setCurrentDialog(self, dialog):
        """Close the currently open dialog and set the new dialog."""
        if self.current_dialog and self.current_dialog.isVisible():
            self.current_dialog.close()
        self.current_dialog = dialog

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            # Get all selected items in the scene
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    print(f"DEBUG: Deleting item {item}")  # Debug message
                    self.scene.removeItem(item)  # Remove the item from the scene
            else:
                print("DEBUG: No items selected to delete.")  # Debug message
        else:
            # Pass other key events to the parent class
            super().keyPressEvent(event)