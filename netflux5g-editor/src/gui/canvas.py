from .components import NetworkComponent
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QPointF, QMimeData, QLineF
from PyQt5.QtGui import QDrag, QBrush, QPixmap, QPen, QColor

class NetworkCanvas(QGraphicsView):
    """Custom QGraphicsView for handling network components and connections"""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)
        self.parent_app = parent
        self.link_mode = False
        self.source_node = None
        self.show_grid = False
        self.grid_size = 20
        
    def setLinkMode(self, enabled):
        self.link_mode = enabled
        self.source_node = None
        
    def setShowGrid(self, show):
        self.show_grid = show
        self.viewport().update()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        if event.mimeData().hasText():
            component_type = event.mimeData().text()
            # Convert view coordinates to scene coordinates
            position = self.mapToScene(event.pos())
            # Add component to the scene
            self.addNetworkComponent(component_type, position)
            event.acceptProposedAction()
            
    def addNetworkComponent(self, component_type, position):
        # Create a network component and add it to the scene
        component = NetworkComponent(component_type, self.parent_app.component_icon_map)
        component.setPos(position)
        self.scene().addItem(component)
        self.parent_app.statusbar.showMessage(f"Added {component_type} at position {position.x():.0f}, {position.y():.0f}")
        
    def mousePressEvent(self, event):
        if self.link_mode:
            pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(pos, self.transform())
            
            if isinstance(item, NetworkComponent):
                if self.source_node is None:
                    self.source_node = item
                    self.parent_app.statusbar.showMessage(f"Selected {item.component_type} as source. Now select destination.")
                else:
                    # Create a link between source_node and this item
                    link = NetworkLink(self.source_node, item)
                    self.scene().addItem(link)
                    self.parent_app.statusbar.showMessage(f"Created link from {self.source_node.component_type} to {item.component_type}")
                    # Reset source node
                    self.source_node = None
        elif self.parent_app.current_tool == "delete":
            pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(pos, self.transform())
            if item:
                self.scene().removeItem(item)
                self.parent_app.statusbar.showMessage("Item deleted")
        else:
            super().mousePressEvent(event)
            
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        if self.show_grid:
            # Draw the grid
            left = int(rect.left()) - (int(rect.left()) % self.grid_size)
            top = int(rect.top()) - (int(rect.top()) % self.grid_size)
            
            # Create grid lines
            gridLines = []
            x = left
            while x < rect.right():
                gridLines.append(QLineF(x, rect.top(), x, rect.bottom()))
                x += self.grid_size
                
            y = top
            while y < rect.bottom():
                gridLines.append(QLineF(rect.left(), y, rect.right(), y))
                y += self.grid_size
                
            # Draw the grid lines
            painter.setPen(QPen(QColor(200, 200, 255, 125)))
            painter.drawLines(gridLines)