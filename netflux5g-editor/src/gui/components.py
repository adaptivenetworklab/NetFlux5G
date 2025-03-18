import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPen


class NetworkComponent(QGraphicsItem):
    """Network component (node) that can be placed on the canvas"""
    
    def __init__(self, component_type, icon_map):
        super().__init__()
        
        self.component_type = component_type
        self.icon_path = icon_map.get(component_type)
        self.pixmap = QPixmap(self.icon_path) if os.path.exists(self.icon_path) else QPixmap(50, 50)
        
        # Make item draggable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Set properties
        self.name = f"{component_type}_{id(self) % 1000}"
        self.properties = {
            "name": self.name,
            "type": component_type
        }
        
    def boundingRect(self):
        return QRectF(-25, -25, 50, 50)
        
    def paint(self, painter, option, widget):
        # Draw the component icon
        painter.drawPixmap(-25, -25, 50, 50, self.pixmap)
        
        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())
            
        # Draw component name below the icon
        painter.setPen(Qt.black)
        painter.drawText(QRectF(-50, 25, 100, 20), Qt.AlignHCenter, self.name)
        
    def itemChange(self, change, value):
        # Update connected links when this item is moved
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            for item in self.scene().items():
                if isinstance(item, NetworkLink) and (item.source_node == self or item.dest_node == self):
                    item.updatePosition()
        return super().itemChange(change, value)