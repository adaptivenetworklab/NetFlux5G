import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPixmap, QPen
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
    
    def __init__(self, component_type, icon_path, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path

        # Set the pixmap for the item
        pixmap = QPixmap(self.icon_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)

        # Make the item draggable and selectable
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        self.setFlag(QGraphicsPixmapItem.ItemSendsGeometryChanges)
        
        # Enable handling context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

        
    def boundingRect(self):
        return QRectF(0, 0, 50, 50)
        
    def paint(self, painter, option, widget):
        """Draw the component."""
        # Draw the component icon
        if not self.pixmap().isNull():
            painter.drawPixmap(0, 0, 50, 50, self.pixmap())

        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())
            
        # If highlighted, draw a red border
        if hasattr(self, 'highlighted') and self.highlighted:
            painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            painter.drawRect(self.boundingRect())

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
            dialog = dialog_class(label_text=self.component_type, parent=self.scene().views()[0])
            dialog.show()

    def itemChange(self, change, value):
        """Handle position changes and update connected links."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # If we have connected links, update them
            if hasattr(self, 'connected_links'):
                for link in self.connected_links:
                    link.updatePosition()
        
        return super().itemChange(change, value)
    
    def setHighlighted(self, highlight=True):
        """Set the highlight state of this component"""
        self.highlighted = highlight
        self.update()