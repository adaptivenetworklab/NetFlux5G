import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag, QPen, QBrush, QColor, QPainter, QPixmap
from PyQt5 import uic

# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "MainWindow.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)
        
        # Set up the canvas as a QGraphicsView
        self.scene = QGraphicsScene(self)
        self.canvas_view = QGraphicsView(self.scene)
        
        # Replace the Canvas widget with our QGraphicsView
        index = self.horizontalLayout.indexOf(self.Canvas)
        self.horizontalLayout.removeWidget(self.Canvas)
        self.Canvas.deleteLater()
        self.horizontalLayout.insertWidget(index, self.canvas_view)
        
        # Connect button signals to add components
        self.Host.pressed.connect(lambda: self.startDrag("Host"))
        self.STA.pressed.connect(lambda: self.startDrag("STA"))
        self.GNB.pressed.connect(lambda: self.startDrag("GNB"))
        self.DockerHost.pressed.connect(lambda: self.startDrag("DockerHost"))
        self.AP.pressed.connect(lambda: self.startDrag("AP"))
        self.VGcore.pressed.connect(lambda: self.startDrag("VGcore"))
        self.Router.pressed.connect(lambda: self.startDrag("Router"))
        self.Switch.pressed.connect(lambda: self.startDrag("Switch"))
        self.LinkCable.pressed.connect(lambda: self.startLinkMode("LinkCable"))
        self.Controller.pressed.connect(lambda: self.startDrag("Controller"))
        
        # Connect toolbar actions
        self.actionPickTool.triggered.connect(self.enablePickTool)
        self.actionHandTool.triggered.connect(self.enableHandTool)
        self.actionDelete.triggered.connect(self.enableDeleteTool)
        self.actionTextBox.triggered.connect(self.addTextBox)
        self.actionDrawSquare.triggered.connect(self.addDrawSquare)
        self.actionShowGrid.triggered.connect(self.toggleGrid)
        self.actionZoomIn.triggered.connect(self.zoomIn)
        self.actionZoomOut.triggered.connect(self.zoomOut)
        self.actionResetZoom.triggered.connect(self.resetZoom)
        
        # Connect menu actions
        self.actionNew.triggered.connect(self.newTopology)
        self.actionSave.triggered.connect(self.saveTopology)
        self.actionOpen.triggered.connect(self.openTopology)
        self.actionSave_As.triggered.connect(self.saveTopologyAs)
        self.actionExport_to_Level_2_Script.triggered.connect(self.exportToScript)
        self.actionQuit.triggered.connect(self.close)
        
        # Set up the canvas_view for drag and drop
        self.canvas_view.setAcceptDrops(True)
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.canvas_view.setRenderHint(QPainter.Antialiasing)
        
        # Set the current tool (pick by default)
        self.current_tool = "pick"
        self.actionPickTool.setChecked(True)
        
        # Initialize attributes
        self.show_grid = False
        self.current_link_source = None
        self.current_file = None
        
        # Custom canvas view with support for drag and drop
        self.canvas_view = NetworkCanvas(self.scene, self)
        index = self.horizontalLayout.indexOf(self.canvas_view)
        self.horizontalLayout.removeWidget(self.canvas_view)
        self.horizontalLayout.insertWidget(index, self.canvas_view)
        
        # Initialize the scene with white background
        self.scene.setBackgroundBrush(QBrush(Qt.white))
        
        # Initialize component mapping for icons
        self.component_icon_map = {
            "Host": "../Icon/host.png",
            "STA": "../Icon/sta.png",
            "GNB": "../Icon/gNB.png",
            "DockerHost": "../Icon/docker.png",
            "AP": "../Icon/AP.png",
            "VGcore": "../Icon/5G core.png",
            "Router": "../Icon/Router.png",
            "Switch": "../Icon/switch.png",
            "LinkCable": "../Icon/link cable.png",
            "Controller": "../Icon/controller.png"
        }
        
        # Status message
        self.statusbar.showMessage("Ready")
        
    def startDrag(self, component_type):
        # Create a drag object with component information
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(component_type)
        drag.setMimeData(mime_data)
        
        # Set a pixmap for the drag appearance
        icon_path = self.component_icon_map[component_type]
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPointF(20, 20))
        
        # Execute the drag
        drag.exec_(Qt.CopyAction)
        
    def startLinkMode(self, component_type):
        self.statusbar.showMessage(f"Link mode activated. Click on source node, then destination node.")
        self.current_tool = "link"
        self.canvas_view.setLinkMode(True)
        
    def enablePickTool(self):
        self.current_tool = "pick"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.canvas_view.setLinkMode(False)
        self.statusbar.showMessage("Pick tool selected")
        
    def enableHandTool(self):
        self.current_tool = "hand"
        self.canvas_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.canvas_view.setLinkMode(False)
        self.statusbar.showMessage("Hand tool selected")
        
    def enableDeleteTool(self):
        self.current_tool = "delete"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.canvas_view.setLinkMode(False)
        self.statusbar.showMessage("Delete tool selected. Click on items to delete them.")
        
    def addTextBox(self):
        self.current_tool = "text"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.current_tool = "square"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Square tool selected. Click and drag to draw a square.")
        
    def toggleGrid(self):
        self.show_grid = not self.show_grid
        self.canvas_view.setShowGrid(self.show_grid)
        self.statusbar.showMessage(f"Grid {'shown' if self.show_grid else 'hidden'}")
        
    def zoomIn(self):
        self.canvas_view.scale(1.2, 1.2)
        
    def zoomOut(self):
        self.canvas_view.scale(1/1.2, 1/1.2)
        
    def resetZoom(self):
        self.canvas_view.resetTransform()
        
    def newTopology(self):
        self.scene.clear()
        self.current_file = None
        self.statusbar.showMessage("New topology created")
        
    def saveTopology(self):
        if self.current_file:
            self.saveTopologyToFile(self.current_file)
        else:
            self.saveTopologyAs()
            
    def saveTopologyToFile(self, filename):
        # Implement saving topology data to file
        self.statusbar.showMessage(f"Topology saved to {filename}")
        
    def saveTopologyAs(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save Topology", "", "NetFlux5G Files (*.nf5g);;All Files (*)")
        if filename:
            self.current_file = filename
            self.saveTopologyToFile(filename)
            
    def openTopology(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Open Topology", "", "NetFlux5G Files (*.nf5g);;All Files (*)")
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        # Implement loading topology from file
        self.current_file = filename
        self.statusbar.showMessage(f"Loaded topology from {filename}")
        
    def exportToScript(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Level 2 Script", "", "Python Files (*.py);;All Files (*)")
        if filename:
            self.exportToScriptFile(filename)
            
    def exportToScriptFile(self, filename):
        # Implement exporting to a level 2 script
        self.statusbar.showMessage(f"Exported to script: {filename}")


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFlux5GApp()
    window.show()
    sys.exit(app.exec_())