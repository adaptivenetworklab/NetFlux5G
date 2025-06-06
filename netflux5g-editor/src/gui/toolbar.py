from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

class ToolbarFunctions:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.setup_toolbar_actions()
        self.setup_tooltips()

    def setup_toolbar_actions(self):
        """Setup all toolbar action connections"""
        toolbar_actions = [
            (self.main_window.actionPickTool, self.enablePickTool),
            (self.main_window.actionLinkTool, self.enableLinkTool),  # Add this line
            (self.main_window.actionDelete, self.enableDeleteTool),
            (self.main_window.actionTextBox, self.addTextBox),
            (self.main_window.actionDrawSquare, self.addDrawSquare),
            (self.main_window.actionShowGrid, self.toggleGrid),
            (self.main_window.actionZoomIn, self.zoomIn),
            (self.main_window.actionZoomOut, self.zoomOut),
            (self.main_window.actionResetZoom, self.resetZoom),
        ]
        
        # Only connect actions that exist
        for action, method in toolbar_actions:
            if hasattr(self.main_window, action.objectName()):
                action.triggered.connect(method)
        
        # Connect run/stop actions if they exist
        if hasattr(self.main_window, 'actionRunAll'):
            self.main_window.actionRunAll.triggered.connect(self.runAll)
        if hasattr(self.main_window, 'actionStopAll'):
            self.main_window.actionStopAll.triggered.connect(self.stopAll)

    def setup_tooltips(self):
        """Set up helpful tooltips with keyboard shortcuts."""
        tooltips = {
            'actionPickTool': "Pick Tool (P)",
            'actionLinkTool': "Link Tool - Connect components (L)",  # Add this line
            'actionDelete': "Delete Tool (D)",
            'actionTextBox': "Text Box Tool (T)",
            'actionDrawSquare': "Draw Square Tool",
            'actionShowGrid': "Toggle Grid (G)",
            'actionZoomIn': "Zoom In (+)",
            'actionZoomOut': "Zoom Out (-)",
            'actionResetZoom': "Reset Zoom (0)",
            'actionRunAll': "Run All - Deploy and start all components",
            'actionStopAll': "Stop All - Stop all running services"
        }
        
        for action_name, tooltip in tooltips.items():
            if hasattr(self.main_window, action_name):
                getattr(self.main_window, action_name).setToolTip(tooltip)

    def enablePickTool(self):
        """Enable pick tool and reset cursor."""
        self.main_window.enablePickTool()

    def enableLinkTool(self): 
        """Enable link tool and set crosshair cursor."""
        self.main_window.enableLinkTool()

    def enableDeleteTool(self):
        """Enable delete tool and set appropriate cursor."""
        self.main_window.current_tool = "delete"
        
        # Set cursor for delete mode
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Update toolbar button states
        self.main_window.updateToolbarButtonStates()
        
        self.main_window.showCanvasStatus("Delete Tool selected. Click on items to delete them.")

    def addTextBox(self):
        self.main_window.addTextBox()

    def addDrawSquare(self):
        self.main_window.addDrawSquare()

    def toggleGrid(self):
        self.main_window.toggleGrid()

    def zoomIn(self):
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomIn()

    def zoomOut(self):
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomOut()

    def resetZoom(self):
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.resetZoom()

    def runAll(self):
        """Run All - Deploy and start all components"""
        self.main_window.runAllComponents()

    def stopAll(self):
        """Stop All - Stop all running services"""
        self.main_window.stopAllComponents()