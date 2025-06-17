import os
import math
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QPixmap, QTransform, QColor, QPainter
from manager.debug import debug_print, error_print

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
            "source": getattr(source_node, 'display_name', getattr(source_node, 'name', 'Unnamed Source')),
            "destination": getattr(dest_node, 'display_name', getattr(dest_node, 'name', 'Unnamed Destination'))
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
            debug_print(f"DEBUG: Cable image loaded from {cable_path}")
        else:
            error_print(f"ERROR: Cable image not found at {cable_path}")
            
        # Create cable segments
        self.cable_segments = []
        self.segment_count = 1  # Start with a single segment
        
        # Performance optimization: cache bounding rect
        self._cached_bounding_rect = None
        self._bounding_rect_dirty = True
        
        # Update position
        self.updatePosition()

    def get_center_point(self, node):
        """Get the center point of a network component."""
        if hasattr(node, 'pos') and hasattr(node, 'boundingRect'):
            # For NetworkComponent objects
            node_pos = node.pos()
            node_rect = node.boundingRect()
            center_x = node_pos.x() + node_rect.width() / 2
            center_y = node_pos.y() + node_rect.height() / 2
            return QPointF(center_x, center_y)
        elif hasattr(node, 'x') and hasattr(node, 'y'):
            # For legacy objects with x/y attributes
            return QPointF(node.x() + 25, node.y() + 25)  # Assume 50x50 size
        else:
            # Fallback
            return QPointF(0, 0)

    def get_object_radius(self, node):
        """Get the radius of a network component for connection points."""
        if hasattr(node, 'boundingRect'):
            rect = node.boundingRect()
            # Use the smaller dimension as the radius
            return min(rect.width(), rect.height()) / 2
        else:
            # Default radius for legacy objects
            return 25  # Half of 50px default size

    def get_intersection_point(self, center1, center2, radius):
        """Calculate the intersection point on the edge of a component."""
        # Calculate the direction vector from center1 to center2
        dx = center2.x() - center1.x()
        dy = center2.y() - center1.y()
        
        # Calculate distance
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return center1
        
        # Normalize the direction vector
        unit_x = dx / distance
        unit_y = dy / distance
        
        # Calculate the intersection point on the edge
        edge_x = center1.x() + unit_x * radius
        edge_y = center1.y() + unit_y * radius
        
        return QPointF(edge_x, edge_y)
            
    def updatePosition(self):
        """Update the link's position and trigger a redraw with optimized performance."""
        self._bounding_rect_dirty = True
        self._cached_bounding_rect = None
        self.prepareGeometryChange()
        
        # Only update if the link is visible in the current view
        if self.scene():
            views = self.scene().views()
            if views:
                view = views[0]
                visible_rect = view.mapToScene(view.viewport().rect()).boundingRect()
                if visible_rect.intersects(self.boundingRect()):
                    self.update()
            
    def boundingRect(self):
        """Define the bounding rectangle for the cable with caching."""
        if not self._bounding_rect_dirty and self._cached_bounding_rect:
            return self._cached_bounding_rect
            
        source_center = self.get_center_point(self.source_node)
        dest_center = self.get_center_point(self.dest_node)
        
        # Create a bounding rectangle that encompasses both points with some padding
        min_x = min(source_center.x(), dest_center.x()) - 20
        min_y = min(source_center.y(), dest_center.y()) - 20
        width = abs(source_center.x() - dest_center.x()) + 40
        height = abs(source_center.y() - dest_center.y()) + 40
        
        self._cached_bounding_rect = QRectF(min_x, min_y, width, height)
        self._bounding_rect_dirty = False
        return self._cached_bounding_rect
    
    def paint(self, painter, option, widget):
        """Draw the cable between components with performance optimizations."""
        # Skip drawing if not in visible area
        if not option.exposedRect.intersects(self.boundingRect()):
            return
            
        # Disable antialiasing for better performance
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # Get center positions of source and destination nodes
        source_center = self.get_center_point(self.source_node)
        dest_center = self.get_center_point(self.dest_node)
        
        # Get the appropriate radii for connection points
        source_radius = self.get_object_radius(self.source_node)
        dest_radius = self.get_object_radius(self.dest_node)
        
        # Calculate edge points where the link should start and end
        source_edge = self.get_intersection_point(source_center, dest_center, source_radius)
        dest_edge = self.get_intersection_point(dest_center, source_center, dest_radius)
        
        # Calculate angle and distance between edge points
        line = QLineF(source_edge, dest_edge)
        angle = line.angle()  # Angle in degrees
        length = line.length()
        
        # Always draw a line to ensure visibility and proper connection indication
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
        else:
            painter.setPen(QPen(QColor(0, 0, 128), 1, Qt.SolidLine))  # Thin dark blue line
            
        painter.drawLine(source_edge, dest_edge)
        
        # Simplified cable drawing for better performance
        if self.cable_pixmap and not self.cable_pixmap.isNull() and length > 20:
            # Only draw cable segments for longer connections to reduce overhead
            painter.save()
            
            # Reduce segment count for better performance
            if length > 100:
                self.segment_count = 2
            else:
                self.segment_count = 1
            
            # Calculate cable segment size (scale to fit connection length)
            segment_length = length / self.segment_count
            cable_width = max(8, min(16, int(segment_length / 6)))  # Smaller for performance
            cable_height = int(self.cable_pixmap.height() * (cable_width / self.cable_pixmap.width()))
            
            # Draw cable segments with reduced detail
            for i in range(self.segment_count):
                segment_pos = 0.5 if self.segment_count == 1 else i / (self.segment_count - 1)
                
                x = source_edge.x() + segment_pos * (dest_edge.x() - source_edge.x()) - cable_width / 2
                y = source_edge.y() + segment_pos * (dest_edge.y() - source_edge.y()) - cable_height / 2
                
                # Simplified transform for better performance
                painter.translate(x + cable_width / 2, y + cable_height / 2)
                painter.rotate(-angle)
                painter.translate(-cable_width / 2, -cable_height / 2)
                
                # Draw the scaled cable image
                painter.drawPixmap(0, 0, cable_width, cable_height, self.cable_pixmap)
                painter.resetTransform()
            
            painter.restore()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Check if we're in delete mode
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and view.app_instance.current_tool == "delete":
                # Remove this link from connected nodes
                if hasattr(self.source_node, 'connected_links') and self in self.source_node.connected_links:
                    self.source_node.connected_links.remove(self)
                if hasattr(self.dest_node, 'connected_links') and self in self.dest_node.connected_links:
                    self.dest_node.connected_links.remove(self)
                # Delete this link
                scene.removeItem(self)
                return
                
        # If not in delete mode, call the parent handler
        super().mousePressEvent(event)