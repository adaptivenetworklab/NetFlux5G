import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton  # Added QGraphicsView
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5 import uic
from gui.canvas import Canvas
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions


# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "ui", "Main_Window.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)

        # Initialize the toolbar functions
        self.toolbar_functions = ToolbarFunctions(self)
        
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
        self.UE.pressed.connect(lambda: self.startDrag("UE"))
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
        self.actionTextBox.triggered.connect(self.addTextBox)
        self.actionDrawSquare.triggered.connect(self.addDrawSquare)
        self.actionShowGrid.triggered.connect(self.toggleGrid)
        self.actionZoomIn.triggered.connect(self.zoomIn)  # Connect Zoom In
        self.actionZoomOut.triggered.connect(self.zoomOut)  # Connect Zoom Out
        self.actionResetZoom.triggered.connect(self.resetZoom)  # Connect Reset Zoom
        self.actionDelete.triggered.connect(self.enableDeleteTool)
        # self.actionRunAll.triggered.connect(self.runAll)
        # self.actionStopAll.triggered.connect(self.stopAll)
                
        # Connect menu actions
        self.actionNew.triggered.connect(self.newTopology)
        self.actionSave.triggered.connect(self.saveTopology)
        self.actionOpen.triggered.connect(self.openTopology)
        self.actionSave_As.triggered.connect(self.saveTopologyAs)
        self.actionExport_to_Level_2_Script.triggered.connect(self.exportToScript)
        self.actionQuit.triggered.connect(self.close)
        
        # Set up the canvas_view for drag and drop
        self.canvas_view.setAcceptDrops(True)
        
        # Initialize attributes
        self.show_grid = False
        self.current_link_source = None
        self.current_file = None
        self.current_tool = "pick"  # Default tool
        self.selected_component = None  # Track the selected component for placement
        
        # Initialize component mapping for icons
        icon_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon")
        self.component_icon_map = {
            "Host": os.path.join(icon_base_path, "host.png"),
            "STA": os.path.join(icon_base_path, "sta.png"),
            "UE": os.path.join(icon_base_path, "ue.png"),
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
    
    def enableDeleteTool(self):
        """Enable the Delete Tool."""
        self.main_window.current_tool = "delete"
        self.main_window.statusbar.showMessage("Delete Tool selected. Click on items to delete them.")
        
    def addTextBox(self):
        self.current_tool = "text"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.current_tool = "square"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Square tool selected. Click and drag to draw a square.")

    def zoomIn(self):
        """Zoom in the canvas."""
        self.canvas_view.zoomIn()
        self.statusbar.showMessage("Zoomed in")

    def zoomOut(self):
        """Zoom out the canvas."""
        self.canvas_view.zoomOut()
        self.statusbar.showMessage("Zoomed out")

    def resetZoom(self):
        """Reset the zoom level of the canvas."""
        self.canvas_view.resetZoom()
        self.statusbar.showMessage("Zoom reset to default level")
        
    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas."""
        self.show_grid = not self.show_grid
        self.canvas_view.setShowGrid(self.show_grid)
        self.statusbar.showMessage(f"Grid {'shown' if self.show_grid else 'hidden'}")

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
    
    def togglePlacementMode(self, component_type):
        """Enable placement mode for the selected component."""
        if self.current_tool == "placement" and self.selected_component == component_type:
            # If already in placement mode for the same component, toggle off
            self.current_tool = "pick"
            self.selected_component = None
            self.statusbar.showMessage("Pick tool selected (placement mode canceled).")
        else:
            # Enable placement mode for the selected component
            self.current_tool = "placement"
            self.selected_component = component_type
            self.statusbar.showMessage(f"Placement mode enabled for {component_type}. Left-click to place. Press Esc to cancel.")

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            # Switch back to pick tool mode
            self.current_tool = "pick"
            self.selected_component = None
            self.statusbar.showMessage("Pick tool selected (placement mode canceled).")
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS file
    qss_file_path = os.path.join(os.path.dirname(__file__), "gui", "styles.qss")
    with open(qss_file_path, "r") as file:
        app.setStyleSheet(file.read())

    window = NetFlux5GApp()
    window.show()
    sys.exit(app.exec_())