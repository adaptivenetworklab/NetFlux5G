import os
import math
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QPixmap, QTransform, QColor
from manager.debug import debug_print, error_print

class NetworkLink(QGraphicsItem):
    """Link/connection between two network components using a cable image"""
    
    def __init__(self, source_node, dest_node, main_window=None):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.main_window = main_window  # Store reference to main window for change notifications
        
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
        
        # Update position
        self.updatePosition()
        
        # Mark topology as modified when link is created
        if self.main_window and hasattr(self.main_window, 'onTopologyChanged'):
            self.main_window.onTopologyChanged()
    
    def get_center_point(self, node):
        """Get the center point of a node's icon (not including coverage circles or text)"""
        pos = node.pos()
        
        # For NetworkComponent objects, always use the icon area (50x50)
        if hasattr(node, 'component_type'):
            # All NetworkComponent icons are 50x50, so center is at (25, 25) from top-left
            return QPointF(pos.x() + 25, pos.y() + 25)
        
        # For other types of objects (legacy support)
        elif hasattr(node, 'boundingRect'):
            rect = node.boundingRect()
            # Use only the icon portion, not the full bounding rect which includes text
            if hasattr(node, 'component_type'):
                # For components, use fixed icon size
                return QPointF(pos.x() + 25, pos.y() + 25)
            else:
                # For other objects, use actual center
                return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        
        elif hasattr(node, 'rect'):
            rect = node.rect()
            return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        
        elif hasattr(node, 'size'):
            size = node.size()
            return QPointF(pos.x() + size.width()/2, pos.y() + size.height()/2)
        
        else:
            # Fallback: assume 50x50 icon
            return QPointF(pos.x() + 25, pos.y() + 25)

    def get_object_radius(self, node):
        """Get the radius for link connection point calculation (icon edge, not coverage)"""
        # For NetworkComponent objects, use the icon radius
        if hasattr(node, 'component_type'):
            # Icon is 50x50, so radius for connection should be about 25 (half the diagonal would be ~35)
            # Use 30 to give a small margin from the icon edge
            return 30
        
        # For legacy objects
        elif hasattr(node, 'boundingRect'):
            rect = node.boundingRect()
            # For components, don't use the full bounding rect as it includes coverage circles and text
            if hasattr(node, 'component_type'):
                return 30  # Fixed radius for component icons
            else:
                return min(rect.width(), rect.height()) / 2
        
        elif hasattr(node, 'rect'):
            rect = node.rect()
            return min(rect.width(), rect.height()) / 2
        
        elif hasattr(node, 'size'):
            size = node.size()
            return min(size.width(), size.height()) / 2
        
        else:
            return 30  # Default radius for 50x50 icons
    
    def get_intersection_point(self, center_point, target_point, radius):
        """Calculate the intersection point of a line with a circle (where link should start/end)"""
        # Create a line from center to target
        line = QLineF(center_point, target_point)
        
        # If the line is too short, just return the center point
        if line.length() < 1:
            return center_point
            
        # Calculate the angle of the line
        angle_rad = math.atan2(target_point.y() - center_point.y(), target_point.x() - center_point.x())
        
        # Calculate intersection point (center + radius * unit_vector)
        intersection_x = center_point.x() + radius * math.cos(angle_rad)
        intersection_y = center_point.y() + radius * math.sin(angle_rad)
        
        return QPointF(intersection_x, intersection_y)
        
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
        min_x = min(source_center.x(), dest_center.x()) - 20
        min_y = min(source_center.y(), dest_center.y()) - 20
        width = abs(source_center.x() - dest_center.x()) + 40
        height = abs(source_center.y() - dest_center.y()) + 40
        
        return QRectF(min_x, min_y, width, height)
    
    def paint(self, painter, option, widget):
        """Draw the cable between components"""
        # Determine if this is a Controller link
        is_controller_link = False
        for node in (self.source_node, self.dest_node):
            # Check for both QGraphicsPixmapItem and QLabel based nodes
            if hasattr(node, 'component_type') and node.component_type == 'Controller':
                is_controller_link = True
                break
            if hasattr(node, 'object_type') and node.object_type == 'Controller':
                is_controller_link = True
                break
        
        # Draw a red, dotted line for Controller links
        if is_controller_link:
            pen = QPen(QColor(220, 0, 0), 3, Qt.DotLine)
        else:
            pen = QPen(Qt.black, 3, Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        # Draw the cable as a line between the centers
        src = self.get_center_point(self.source_node)
        dst = self.get_center_point(self.dest_node)
        painter.drawLine(QLineF(src, dst))

        # Optionally, draw the cable image for non-controller links
        if not is_controller_link and self.cable_pixmap:
            # Get center positions of source and destination nodes
            source_center = self.get_center_point(self.source_node)
            dest_center = self.get_center_point(self.dest_node)
            
            # Get the appropriate radii for connection points
            source_radius = self.get_object_radius(self.source_node)
            dest_radius = self.get_object_radius(self.dest_node)
            
            # Calculate edge points where the link should start and end
            source_edge = self.get_intersection_point(source_center, dest_center, source_radius)
            dest_edge = self.get_intersection_point(dest_center, source_center, dest_radius)
            
            # Debug output
            debug_print(f"DEBUG: Link from {source_edge.x():.1f},{source_edge.y():.1f} to {dest_edge.x():.1f},{dest_edge.y():.1f}")
            
            # Calculate angle and distance between edge points
            line = QLineF(source_edge, dest_edge)
            angle = line.angle()  # Angle in degrees
            length = line.length()
            
            # Save painter state
            painter.save()
            
            # Determine number of segments based on length
            if length > 150:
                self.segment_count = 3  # Use 3 segments for long connections
            elif length > 75:
                self.segment_count = 2  # Use 2 segments for medium connections
            else:
                self.segment_count = 1  # Use 1 segment for short connections
            
            # Calculate cable segment size (scale to fit connection length)
            segment_length = length / self.segment_count
            cable_width = max(12, min(20, int(segment_length / 4)))  # Adaptive width
            cable_height = int(self.cable_pixmap.height() * (cable_width / self.cable_pixmap.width()))
            
            # Draw cable segments
            for i in range(self.segment_count):
                # Calculate segment position (evenly spaced)
                if self.segment_count == 1:
                    segment_pos = 0.5  # Center the single segment
                else:
                    segment_pos = i / (self.segment_count - 1)  # Distribute segments
                
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
            
            # Restore painter state
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