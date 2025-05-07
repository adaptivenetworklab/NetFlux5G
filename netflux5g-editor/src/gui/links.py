from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QPixmap, QTransform, QColor
import os
import math

class NetworkLink(QGraphicsItem):
    """Link/connection between two network components using a cable image"""
    
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
            "source": getattr(source_node, 'name', 'Unnamed Source'),
            "destination": getattr(dest_node, 'name', 'Unnamed Destination')
        }
        
        # Make item selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Store source and destination in the nodes for updates
        if hasattr(source_node, 'connected_links'):
            source_node.connected_links.append(self)
        else:
            source_node.connected_links = [self]
            
        if hasattr(dest_node, 'connected_links'):
            dest_node.connected_links.append(self)
        else:
            dest_node.connected_links = [self]
            
        # Set Z-value below components
        self.setZValue(-1)
        
        # Load the cable image
        self.cable_pixmap = None
        icon_base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gui", "Icon")
        cable_path = os.path.join(icon_base_path, "link cable.png")
        
        if os.path.exists(cable_path):
            self.cable_pixmap = QPixmap(cable_path)
            print(f"DEBUG: Cable image loaded from {cable_path}")
        else:
            print(f"ERROR: Cable image not found at {cable_path}")
            
        # Create cable segments
        self.cable_segments = []
        self.segment_count = 1  # Start with a single segment
        
        # Update position
        self.updatePosition()
    
    def get_center_point(self, node):
        """Get the center point of a node"""
        if hasattr(node, 'boundingRect'):
            # For QGraphicsItem objects like NetworkComponent
            rect = node.boundingRect()
            pos = node.pos()
            return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        elif hasattr(node, 'rect'):
            # For QLabel-based objects like MovableLabel
            rect = node.rect()
            pos = node.pos()
            return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        elif hasattr(node, 'size'):
            # For other objects with size() method
            size = node.size()
            pos = node.pos()
            return QPointF(pos.x() + size.width()/2, pos.y() + size.height()/2)
        else:
            # Fallback to just the position
            return node.pos()
    
    def get_object_radius(self, node):
        """Get the approximate radius of an object"""
        if hasattr(node, 'boundingRect'):
            rect = node.boundingRect()
            return max(rect.width(), rect.height()) / 2
        elif hasattr(node, 'rect'):
            rect = node.rect()
            return max(rect.width(), rect.height()) / 2
        elif hasattr(node, 'size'):
            size = node.size()
            return max(size.width(), size.height()) / 2
        else:
            # Default radius if we can't determine
            return 25  # Assuming objects are about 50x50
    
    def get_intersection_point(self, center_point, target_point, radius):
        """Calculate the intersection point of a line with a circle"""
        # Create a line from center to target
        line = QLineF(center_point, target_point)
        
        # If the line is too short, just return the endpoint
        if line.length() < 1:
            return target_point
            
        # Calculate the unit vector in the direction of the line
        angle = line.angle() * math.pi / 180  # Convert to radians
        unit_x = math.cos(angle)
        unit_y = math.sin(angle)
        
        # Calculate intersection point (center + radius * unit_vector)
        # Note: Qt's angle is counter-clockwise from 3 o'clock position
        # We need to negate the y-component due to screen coordinates
        return QPointF(
            center_point.x() + radius * math.cos(-angle),
            center_point.y() + radius * math.sin(-angle)
        )
        
    def updatePosition(self):
        """Update the link's position and trigger a redraw"""
        self.prepareGeometryChange()
        if self.scene():
            self.update()
            
    def boundingRect(self):
        """Define the bounding rectangle for the cable"""
        source_center = self.get_center_point(self.source_node)
        dest_center = self.get_center_point(self.dest_node)
        
        # Create a bounding rectangle that encompasses both points with some padding
        return QRectF(min(source_center.x(), dest_center.x()) - 20,
                      min(source_center.y(), dest_center.y()) - 20,
                      abs(source_center.x() - dest_center.x()) + 40,
                      abs(source_center.y() - dest_center.y()) + 40)
    
    def paint(self, painter, option, widget):
        """Draw the cable between components"""
        # Get center positions of source and destination nodes
        source_center = self.get_center_point(self.source_node)
        dest_center = self.get_center_point(self.dest_node)
        
        # Get the approximate radii of the objects
        source_radius = self.get_object_radius(self.source_node)
        dest_radius = self.get_object_radius(self.dest_node)
        
        # Calculate edge points where the link should start and end
        source_edge = self.get_intersection_point(source_center, dest_center, source_radius)
        dest_edge = self.get_intersection_point(dest_center, source_center, dest_radius)
        
        # Print debug information
        print(f"DEBUG: Drawing link from {source_edge} to {dest_edge}")
        
        # Calculate angle and distance between edge points
        line = QLineF(source_edge, dest_edge)
        angle = line.angle()  # Angle in degrees
        length = line.length()
        
        # If we have a cable image and it's valid, use it
        if self.cable_pixmap and not self.cable_pixmap.isNull():
            # Save painter state
            painter.save()
            
            # Draw the cable image stretched between the two edge points
            segment_length = length / self.segment_count
            
            # Calculate cable segment size (scale to fit connection length)
            cable_width = int(min(20, segment_length / 3))  # Limit cable width and ensure it's an integer
            cable_height = int(self.cable_pixmap.height() * (cable_width / self.cable_pixmap.width()))  # Ensure height is an integer
            
            # Draw cable segments
            for i in range(self.segment_count):
                # Calculate segment position (evenly spaced)
                segment_pos = i / self.segment_count
                x = source_edge.x() + segment_pos * (dest_edge.x() - source_edge.x()) - cable_width / 2
                y = source_edge.y() + segment_pos * (dest_edge.y() - source_edge.y()) - cable_height / 2
                
                # Create transform to rotate around center
                transform = QTransform()
                transform.translate(x + cable_width / 2, y + cable_height / 2)
                transform.rotate(-angle)  # Negative angle to match Qt's coordinate system
                transform.translate(-cable_width / 2, -cable_height / 2)
                
                # Apply transform
                painter.setTransform(transform)
                
                # Draw the scaled cable image
                painter.drawPixmap(0, 0, cable_width, cable_height, self.cable_pixmap)
            
            # Additional cable segments for longer connections
            if length > 100:
                self.segment_count = 3  # Use 3 segments for long connections
            else:
                self.segment_count = 1  # Use 1 segment for short connections
                
            # Restore painter state
            painter.restore()
            
            # Always draw a line to ensure visibility
            if self.isSelected():
                painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            else:
                painter.setPen(QPen(QColor(0, 0, 128), 2, Qt.SolidLine))  # Dark blue line
                
            painter.drawLine(source_edge, dest_edge)
        else:
            print("DEBUG: Fallback to drawing line for link")
            # Fallback to simple line if no image
            if self.isSelected():
                painter.setPen(QPen(Qt.blue, 3, Qt.DashLine))
            else:
                # Use a more visible color (dark red) and thicker line
                painter.setPen(QPen(QColor(180, 0, 0), 3, Qt.SolidLine))
                
            painter.drawLine(source_edge, dest_edge)
