from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen

class NetworkLink(QGraphicsItem):
    """Link/connection between two network components."""
    
    def __init__(self, source_node, dest_node):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node

        # Make the link selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        # Connect to the moved signal of the source and destination nodes
        self.source_node.moved.connect(self.updatePosition)
        self.dest_node.moved.connect(self.updatePosition)

    def updatePosition(self):
        """Update the position of the link."""
        self.prepareGeometryChange()  # Notify the scene that the geometry is changing
        self.update()  # Trigger a repaint of the link

    def boundingRect(self):
        """Return the bounding rectangle of the link."""
        source_center = self.source_node.boundingRect().center() + self.source_node.pos()
        dest_center = self.dest_node.boundingRect().center() + self.dest_node.pos()
        return QRectF(
            min(source_center.x(), dest_center.x()) - 5,
            min(source_center.y(), dest_center.y()) - 5,
            abs(source_center.x() - dest_center.x()) + 10,
            abs(source_center.y() - dest_center.y()) + 10
        )

    def paint(self, painter, option, widget):
        """Draw the link."""
        # Calculate the center points of the source and destination nodes
        source_center = self.source_node.boundingRect().center() + self.source_node.pos()
        dest_center = self.dest_node.boundingRect().center() + self.dest_node.pos()

        # Set the pen for the line
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        if self.isSelected():
            pen.setColor(Qt.blue)
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Draw the line between the center points
        painter.drawLine(source_center, dest_center)