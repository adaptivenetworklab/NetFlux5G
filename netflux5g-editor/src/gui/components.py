import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPixmap, QPen, QColor, QPainter
from .widgets.Dialog import *
from manager.debug import debug_print, error_print, warning_print


class NetworkComponent(QGraphicsPixmapItem):
    """Network component (node) that can be placed on the canvas"""

    # Map component types to their respective dialog classes
    PROPERTIES_MAP = {
        "Host": HostPropertiesWindow,
        "STA": STAPropertiesWindow,
        "UE": UEPropertiesWindow,
        "GNB": GNBPropertiesWindow,
        "DockerHost": DockerHostPropertiesWindow,
        "AP": APPropertiesWindow,
        "VGcore": Component5GPropertiesWindow,
        "Controller": ControllerPropertiesWindow,
    }

    # Track the count of each component type
    component_counts = {
        "Host": 0, "STA": 0, "UE": 0, "GNB": 0, "DockerHost": 0,
        "AP": 0, "VGcore": 0, "Controller": 0, "Router": 0, "Switch": 0,
    }
    
    def __init__(self, component_type, icon_path, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path
    
        # Increment the component count and assign a unique number
        NetworkComponent.component_counts[component_type] = NetworkComponent.component_counts.get(component_type, 0) + 1
        self.component_number = NetworkComponent.component_counts[component_type]
        
        # Set the display name (e.g., "Host #1")
        self.display_name = f"{component_type} #{self.component_number}"
    
        # Initialize properties dictionary to store configuration
        self.properties = {
            "name": self.display_name,
            "type": self.component_type,
            "x": 0,  # Initial x position
            "y": 0,  # Initial y position
        }
    
        # Set the pixmap for the item
        pixmap = QPixmap(self.icon_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
    
        # Make the item draggable and selectable
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        self.setFlag(QGraphicsPixmapItem.ItemSendsGeometryChanges)
        
        # Enable handling context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        # Coverage radius for wireless components - always visible
        self.coverage_radius = 340.0 if component_type in ["AP", "GNB"] else 0
        
        # Set appropriate Z-value
        if self.component_type in ["AP", "GNB"]:
            self.setZValue(5)  # Components with coverage circles slightly higher
        else:
            self.setZValue(10)  # Regular components on top

    def setPosition(self, x, y):
        """Set the component's position and update properties."""
        self.setPos(x, y)
        self.updatePositionProperties()

    def updatePositionProperties(self):
        """Update the position properties based on current position."""
        current_pos = self.pos()
        self.properties["x"] = current_pos.x()
        self.properties["y"] = current_pos.y()

    def setProperties(self, properties_dict):
        """Update the component's properties dictionary"""
        self.properties.update(properties_dict)
        
        # Update the component's name if it exists in properties
        if "name" in properties_dict:
            self.display_name = properties_dict["name"]
        
        # Update position if provided in properties
        if "x" in properties_dict and "y" in properties_dict:
            self.setPos(properties_dict["x"], properties_dict["y"])

    def getProperties(self):
        """Get the current properties including updated position."""
        self.updatePositionProperties()  # Ensure position is current
        return self.properties.copy()

    def boundingRect(self):
        """Define the bounding rectangle for the component including text."""
        if self.component_type in ["AP", "GNB"]:
            # For wireless components with coverage circles
            radius = self.coverage_radius
            # Ensure the bounding rect includes both the coverage circle and the text
            return QRectF(-radius, -radius, radius * 2 + 50, radius * 2 + 50 + 20)
        else:
            # For all other components (including DockerHost and Controller)
            # Use consistent dimensions: icon + text + extra padding
            return QRectF(-10, -10, 70, 90)  # Extra padding and height for text with margins
    
    def paint(self, painter, option, widget):
        """Draw the component with optimized performance."""
        # Enable performance optimizations
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # Save the painter state
        painter.save()
        
        # Draw coverage circle for wireless components first (so it's behind the icon)
        if self.component_type in ["AP", "GNB"]:
            # Only draw coverage circle if it's within visible area
            if option.exposedRect.intersects(QRectF(
                25 - self.coverage_radius, 25 - self.coverage_radius,
                self.coverage_radius * 2, self.coverage_radius * 2
            )):
                # Set up a semi-transparent fill for the coverage area
                painter.setBrush(QColor(0, 128, 255, 40))
                
                # Use a thin border for the coverage area
                painter.setPen(QPen(QColor(0, 0, 0, 80), 1, Qt.DashLine))
                
                # Draw the coverage circle using QRectF to handle float values
                circle_rect = QRectF(
                    25 - self.coverage_radius,  # x (float)
                    25 - self.coverage_radius,  # y (float)
                    self.coverage_radius * 2,   # width (float)
                    self.coverage_radius * 2    # height (float)
                )
                painter.drawEllipse(circle_rect)
        
        # Reset painter for icon drawing
        painter.restore()
        painter.save()
        
        # Draw the component icon only if visible
        if option.exposedRect.intersects(QRectF(0, 0, 50, 50)):
            if not self.pixmap().isNull():
                painter.drawPixmap(0, 0, 50, 50, self.pixmap())
    
        # Draw the component name below the icon with proper background clearing
        text_rect = QRectF(0, 55, 50, 20)
        if option.exposedRect.intersects(text_rect):
            painter.setPen(Qt.black)
            font = painter.font()
            font.setPointSize(8)  # Smaller font size
            painter.setFont(font)
            
            # Calculate text metrics
            text_width = painter.fontMetrics().width(self.display_name)
            text_height = painter.fontMetrics().height()
            
            # Clear the text area with white background to prevent traces
            clear_rect = QRectF(
                (50 - text_width) / 2 - 2,  # x position with padding
                55,  # y position
                text_width + 4,  # width with padding
                text_height + 4  # height with padding
            )
            
            # Fill text background with white to clear any traces
            painter.fillRect(clear_rect, Qt.white)
            
            # Draw the text
            painter.drawText(
                int((50 - text_width) / 2),  # Center horizontally (ensure integer)
                65,  # Position below the icon
                self.display_name
            )
    
        # Restore painter state
        painter.restore()
        painter.save()
        
        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(QRectF(-2, -2, 54, 75))  # Selection rectangle around icon and text
            
        # If highlighted, draw a red border
        if hasattr(self, 'highlighted') and self.highlighted:
            painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            painter.drawRect(QRectF(-2, -2, 54, 75))  # Highlight rectangle around icon and text
            
        # Restore painter state
        painter.restore()

    def shape(self):
        """Return the shape of the item for collision detection and repainting."""
        from PyQt5.QtGui import QPainterPath
        
        path = QPainterPath()
        if self.component_type in ["AP", "GNB"]:
            # For wireless components, include the coverage circle
            radius = self.coverage_radius
            path.addEllipse(-radius, -radius, radius * 2 + 50, radius * 2 + 50)
        else:
            # For regular components, use just the icon area + text
            path.addRect(0, 0, 50, 65)
        
        return path

    def itemChange(self, change, value):
        """Handle position changes and update connected links with optimized updates."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Update position properties when position changes
            if hasattr(value, 'x') and hasattr(value, 'y'):
                self.properties["x"] = value.x()
                self.properties["y"] = value.y()
            
            # If we have connected links, update them (but don't force immediate scene update)
            if hasattr(self, 'connected_links'):
                for link in self.connected_links:
                    link.prepareGeometryChange()
        
        # For position changes, update the coverage area for AP/GNB components
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Final position update after the move is complete
            self.updatePositionProperties()
            
            # Use minimal update instead of full scene update
            if self.scene():
                # Update only the necessary area
                update_rect = self.sceneBoundingRect().adjusted(-10, -10, 10, 10)
                self.scene.update(update_rect)
        
        return super().itemChange(change, value)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """Handle right-click context menu events."""
        menu = QMenu()
        if self.component_type in ["Switch", "Router"]:
            menu.addAction("Delete", lambda: self.scene().removeItem(self))
        else:
            menu.addAction("Properties", self.openPropertiesDialog)
            menu.addSeparator()
            menu.addAction("Delete", lambda: self.scene().removeItem(self))
        menu.exec_(event.screenPos())

    def openPropertiesDialog(self):
        """Open the properties dialog for the component."""
        dialog_class = self.PROPERTIES_MAP.get(self.component_type)
        if dialog_class:
            # Pass the component reference to the dialog
            dialog = dialog_class(label_text=self.display_name, parent=self.scene().views()[0], component=self)
            dialog.show()

    def setHighlighted(self, highlight=True):
        """Set the highlight state of this component"""
        self.highlighted = highlight
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Check if we're in delete mode
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and view.app_instance.current_tool == "delete":
                # Remove any connected links first
                if hasattr(self, 'connected_links') and self.connected_links:
                    # Copy the list to avoid modification during iteration
                    links_to_remove = self.connected_links.copy()
                    for link in links_to_remove:
                        # Remove the link from both connected nodes
                        if hasattr(link, 'source_node') and hasattr(link.source_node, 'connected_links'):
                            if link in link.source_node.connected_links:
                                link.source_node.connected_links.remove(link)
                        if hasattr(link, 'dest_node') and hasattr(link.dest_node, 'connected_links'):
                            if link in link.dest_node.connected_links:
                                link.dest_node.connected_links.remove(link)
                        # Remove the link from the scene
                        if link.scene():
                            scene.removeItem(link)
                
                # Now remove this component
                scene.removeItem(self)
                
                # Show status message
                if hasattr(view, 'app_instance'):
                    num_links = len(self.connected_links) if hasattr(self, 'connected_links') and self.connected_links else 0
                    view.app_instance.showCanvasStatus(f"Deleted component and {num_links} connected link(s)")
                return
                
        # If not in delete mode, call the parent handler for other functionality
        super().mousePressEvent(event)