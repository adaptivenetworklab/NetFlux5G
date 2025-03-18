from .components import NetworkComponent
from .links import NetworkLink
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QMimeData
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor

class Canvas(QWidget):  # Canvas now inherits from QWidget
    """Custom QWidget for handling network components and connections"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.parent_app = parent
        self.link_mode = False
        self.source_node = None
        self.show_grid = False
        self.grid_size = 20
        self.scene_items = []  # Store items manually since we're not using QGraphicsScene
        
    def setLinkMode(self, enabled):
        self.link_mode = enabled
        self.source_node = None
        
    def setShowGrid(self, show):
        self.show_grid = show
        self.update()  # Trigger a repaint
        
    def dragEnterEvent(self, event):
        print("DEBUG: Drag entered canvas")  # Debug message
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
        
    def dragMoveEvent(self, event):
        print("DEBUG: Drag moved over canvas")  # Debug message
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        print("DEBUG: Drop event on canvas")  # Debug message
        if event.mimeData().hasText():
            component_type = event.mimeData().text()
            print(f"DEBUG: Dropped component type: {component_type}")  # Debug message
            # Get the drop position
            position = event.pos()
            print(f"DEBUG: Drop position: {position}")  # Debug message
            # Add component to the canvas
            self.addNetworkComponent(component_type, position)
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def addNetworkComponent(self, component_type, position):
        print(f"DEBUG: Adding component: {component_type} at position: {position}")  # Debug message
        # Create a network component and add it to the canvas
        component = NetworkComponent(component_type, self.parent_app.component_icon_map)
        component.position = position  # Store position manually
        self.scene_items.append(component)  # Add to the list of items
        self.update()  # Trigger a repaint
        self.parent_app.statusbar.showMessage(f"Added {component_type} at position {position.x()}, {position.y()}")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw grid if enabled
        if self.show_grid:
            self.drawGrid(painter)
        
        # Draw all components
        for component in self.scene_items:
            painter.drawPixmap(component.position, component.pixmap)
        
    def drawGrid(self, painter):
        # Draw the grid
        rect = self.rect()
        left = rect.left() - (rect.left() % self.grid_size)
        top = rect.top() - (rect.top() % self.grid_size)
        
        # Create grid lines
        grid_lines = []
        x = left
        while x < rect.right():
            grid_lines.append((x, rect.top(), x, rect.bottom()))
            x += self.grid_size
            
        y = top
        while y < rect.bottom():
            grid_lines.append((rect.left(), y, rect.right(), y))
            y += self.grid_size
            
        # Draw the grid lines
        pen = QPen(QColor(200, 200, 255, 125))
        painter.setPen(pen)
        for line in grid_lines:
            painter.drawLine(*line)