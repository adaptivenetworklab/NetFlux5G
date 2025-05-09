import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPixmap, QPen, QColor
from .widgets.Dialog import *


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
        "VGcore": Core5GPropertiesWindow,
        "Controller": ControllerPropertiesWindow,
    }

    # Track the count of each component type
    component_counts = {
        "Host": 0,
        "STA": 0,
        "UE": 0,
        "GNB": 0,
        "DockerHost": 0,
        "AP": 0,
        "VGcore": 0,
        "Controller": 0,
        "Router": 0,
        "Switch": 0,
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
    
    def boundingRect(self):
        # If this is an AP or GNB, make the bounding rectangle include the coverage area
        if self.component_type in ["AP", "GNB"]:
            radius = self.coverage_radius
            return QRectF(-radius, -radius, radius * 2 + 50, radius * 2 + 50)
        else:
            # Make the bounding rectangle taller to include the text label
            return QRectF(0, 0, 50, 65)  # Height increased to accommodate text
    
    def paint(self, painter, option, widget):
        """Draw the component."""
        # Draw coverage circle for wireless components
        if self.component_type in ["AP", "GNB"]:
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
        
        # Draw the component icon
        if not self.pixmap().isNull():
            painter.drawPixmap(0, 0, 50, 50, self.pixmap())
    
        # Draw the component name below the icon
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(8)  # Smaller font size
        painter.setFont(font)
        
        # Calculate text width to center it
        text_width = painter.fontMetrics().width(self.display_name)
        painter.drawText(
            (50 - text_width) // 2,  # Center horizontally
            60,  # Position below the icon
            self.display_name
        )
    
        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(QRectF(0, 0, 50, 65))  # Selection rectangle only around the icon
            
        # If highlighted, draw a red border
        if hasattr(self, 'highlighted') and self.highlighted:
            painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            painter.drawRect(QRectF(0, 0, 50, 65))  # Highlight rectangle only around the icon
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """Handle right-click context menu events."""
        menu = QMenu()
        menu.addAction("Properties", self.openPropertiesDialog)
        menu.addSeparator()
        menu.addAction("Delete", lambda: self.scene().removeItem(self))
        menu.exec_(event.screenPos())

    def openPropertiesDialog(self):
        """Open the properties dialog for the component."""
        dialog_class = self.PROPERTIES_MAP.get(self.component_type)
        if dialog_class:
            dialog = dialog_class(label_text=self.display_name, parent=self.scene().views()[0])
            dialog.show()

    def itemChange(self, change, value):
        """Handle position changes and update connected links."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # If we have connected links, update them
            if hasattr(self, 'connected_links'):
                for link in self.connected_links:
                    link.updatePosition()
        
        # For position changes, update the coverage area for AP/GNB components
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            if self.component_type in ["AP", "GNB"]:
                self.update()  # Redraw with updated position
        
        return super().itemChange(change, value)
    
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
                # Delete this component
                if hasattr(self, 'connected_links'):
                    # Remove any connected links first
                    links_to_remove = self.connected_links.copy() if hasattr(self, 'connected_links') else []
                    for link in links_to_remove:
                        scene.removeItem(link)
                
                # Now remove this component
                scene.removeItem(self)
                return
                
        # If not in delete mode, call the parent handler
        super().mousePressEvent(event)