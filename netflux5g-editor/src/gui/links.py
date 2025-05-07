from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen

class NetworkLink(QGraphicsItem):
    """Link/connection between two network components"""
    
    def __init__(self, source_node, dest_node):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        
        # Set properties
        self.link_type = "ethernet"
        self.name = f"link_{id(self) % 1000}"
        self.properties = {
            "name": self.name,
            "type": self.link_type,
            "source": source_node.name,
            "destination": dest_node.name
        }
        
        # Make item selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Update position
        self.updatePosition()
        
    def updatePosition(self):
        self.prepareGeometryChange()
        
    def boundingRect(self):
        # Get positions of source and destination nodes
        source_pos = self.source_node.pos()
        dest_pos = self.dest_node.pos()
        
        # Create a bounding rectangle that encompasses both points
        return QRectF(min(source_pos.x(), dest_pos.x()) - 5,
                      min(source_pos.y(), dest_pos.y()) - 5,
                      abs(source_pos.x() - dest_pos.x()) + 10,
                      abs(source_pos.y() - dest_pos.y()) + 10)
    
    def paint(self, painter, option, widget):
        # Draw line between components
        source_pos = self.source_node.pos()
        dest_pos = self.dest_node.pos()
        
        # Set line style based on selection state
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
        else:
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
            
        # Draw the line
        painter.drawLine(source_pos, dest_pos)