import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget, QPushButton  # Added QGraphicsView
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QBrush, QPixmap, QPainter
from PyQt5 import uic
from gui.canvas import Canvas
from gui.canvas import Canvas, MovableLabel


# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "ui", "MainWindow.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)
        
        # Set up the canvas as a QWidget
        self.canvas_view = Canvas(self, self)
        self.canvas_view.setMinimumSize(1828, 800)  # Ensure the canvas has a visible size
        
        # Replace the Canvas widget in the horizontal layout
        index = self.horizontalLayout.indexOf(self.Canvas)
        self.horizontalLayout.removeWidget(self.Canvas)
        self.Canvas.deleteLater()
        self.horizontalLayout.insertWidget(index, self.canvas_view)
        
        # Connect QPushButton objects in ObjectLayout to startDrag
        for button in self.ObjectLayout.findChildren(QPushButton):
            component_type = button.objectName()  # Use the button's objectName as the component type
            button.pressed.connect(lambda bt=component_type: self.startDrag(bt))
        
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
        
        # Set the current tool (pick by default)
        self.current_tool = "pick"
        self.actionPickTool.setChecked(True)
        
        # Initialize attributes
        self.show_grid = False
        self.current_link_source = None
        self.current_file = None
        
        # Initialize component mapping for icons
        icon_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon")
        self.component_icon_map = {
            "Host": os.path.join(icon_base_path, "host.png"),
            "STA": os.path.join(icon_base_path, "sta.png"),
            "GNB": os.path.join(icon_base_path, "gNB.png"),
            "DockerHost": os.path.join(icon_base_path, "docker.png"),
            "AP": os.path.join(icon_base_path, "AP.png"),
            "VGcore": os.path.join(icon_base_path, "5G core.png"),
            "Router": os.path.join(icon_base_path, "Router.png"),
            "Switch": os.path.join(icon_base_path, "switch.png"),
            "LinkCable": os.path.join(icon_base_path, "link cable.png"),
            "Controller": os.path.join(icon_base_path, "controller.png")
        }
        
        # Status message
        self.statusbar.showMessage("Ready")
        
    def startDrag(self, component_type):
        print(f"Starting drag for component: {component_type}")  # Debug message

        # Create a drag object with component information
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(component_type)  # Pass the component type as text
        drag.setMimeData(mime_data)
        
        # Set a pixmap for the drag appearance
        icon_path = self.component_icon_map.get(component_type)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(20, 20))  # Set the drag hotspot to the center of the pixmap
        
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

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS file
    qss_file_path = os.path.join(os.path.dirname(__file__), "gui", "styles.qss")
    with open(qss_file_path, "r") as file:
        app.setStyleSheet(file.read())

    
    window = NetFlux5GApp()
    window.show()
    sys.exit(app.exec_())