import os
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QGraphicsSceneContextMenuEvent, QMenu, QGraphicsItem
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
            # Move the label
            new_pos = self.mapToParent(event.pos() - self.offset)
            self.move(new_pos)
            
            # Update connected links
            if hasattr(self, 'connected_links'):
                for link in self.connected_links:
                    link.updatePosition()

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
            
    def setHighlighted(self, highlight=True):
        """Set the highlight state of this component"""
        self.highlighted = highlight
        
        # Force redraw
        self.update()

    def paintEvent(self, event):
        """Override paint event to draw highlight if needed"""
        super().paintEvent(event)
        if hasattr(self, 'highlighted') and self.highlighted:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 3))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))  # Draw inside the border

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
        
        # Link mode support
        self.link_mode = False

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

    def setLinkMode(self, enabled):
        """Enable or disable link mode."""
        self.link_mode = enabled
        print(f"DEBUG: Link mode set to {self.link_mode}")
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Handle link mode first
        if self.link_mode and event.button() == Qt.LeftButton:
            # Get item under the cursor
            item = self.itemAt(event.pos())
            
            # Check if it's a component we can link
            if item is not None and (
                (isinstance(item, NetworkComponent)) or 
                (hasattr(item, 'object_type'))
            ):
                # Process link creation
                if self.app_instance.current_link_source is None:
                    # First click - set source and highlight it
                    self.app_instance.current_link_source = item
                    
                    # Highlight the source object
                    if hasattr(item, 'setHighlighted'):
                        item.setHighlighted(True)
                        print("DEBUG: Highlighting source object")
                    
                    self.app_instance.statusbar.showMessage(
                        f"Source selected: {item.object_type if hasattr(item, 'object_type') else 'component'} (highlighted in red) - now select destination"
                    )
                    print(f"DEBUG: Source selected: {item}")
                    
                    # Prevent dragging when in link mode
                    if hasattr(item, 'setFlag'):
                        item.setFlag(QGraphicsItem.ItemIsMovable, False)
                        
                    # Force update to ensure highlight is visible
                    if hasattr(item, 'update'):
                        item.update()
                    
                    return
                else:
                    # Second click - create link
                    source = self.app_instance.current_link_source
                    destination = item
                    
                    # Don't link to the same object
                    if source != destination:
                        # Remove highlight from source
                        if hasattr(source, 'setHighlighted'):
                            source.setHighlighted(False)
                        
                        self.app_instance.createLink(source, destination)
                        print(f"DEBUG: Link created between {source} and {destination}")
                    else:
                        print("DEBUG: Cannot link an object to itself")
                    
                    # Re-enable dragging for source
                    if hasattr(source, 'setFlag'):
                        source.setFlag(QGraphicsItem.ItemIsMovable, True)
                    
                    # Reset source for next link operation
                    self.app_instance.current_link_source = None
                    self.app_instance.statusbar.showMessage("Link created. Select next source or change tool.")
                    return
                    
        # Handle dialog closing
        if self.current_dialog:
            print("DEBUG: Closing dialog because canvas was clicked.")
            self.current_dialog.close()
            self.current_dialog = None

        # Handle normal mouse press
        super().mousePressEvent(event)