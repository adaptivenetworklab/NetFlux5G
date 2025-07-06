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
        action_methods = {
            'actionPickTool': self.enablePickTool,
            'actionLinkTool': self.enableLinkTool,
            'actionDelete': self.enableDeleteTool,
            'actionTextBox': self.addTextBox,
            'actionDrawSquare': self.addDrawSquare,
            'actionShowGrid': self.toggleGrid,
            'actionZoomIn': self.zoomIn,
            'actionZoomOut': self.zoomOut,
            'actionResetZoom': self.resetZoom,
        }

        for action_name, method in action_methods.items():
            action = getattr(self.main_window, action_name, None)
            if action is not None:
                action.triggered.connect(method)

        # Note: RunAll/StopAll actions are connected directly in main.py to avoid duplicate connections
        # Note: Database actions are connected directly in main.py to avoid duplicate connections
        # Note: Docker network actions are connected directly in main.py to avoid duplicate connections

        # Note: Database actions are connected directly in main.py to avoid duplicate connections

    def setup_tooltips(self):
        """Set up helpful tooltips with keyboard shortcuts."""
        tooltips = {
            'actionPickTool': "Pick Tool (P)",
            'actionLinkTool': "Link Tool - Connect components (L)",
            'actionDelete': "Delete Tool (D)",
            'actionTextBox': "Text Box Tool (T)",
            'actionDrawSquare': "Draw Square Tool",
            'actionShowGrid': "Toggle Grid (G)",
            'actionZoomIn': "Zoom In (+)",
            'actionZoomOut': "Zoom Out (-)",
            'actionResetZoom': "Reset Zoom (0)",
            'actionRunAll': "Run All - Deploy and start all components",
            'actionStopAll': "Stop All - Stop all running services",
            'actionCreate_Docker_Network': "Create Docker Network - Create network for current topology",
            'actionDelete_Docker_Network': "Delete Docker Network - Delete network for current topology",
            'actionDeploy_Database': "Deploy Database - Deploy MongoDB container (Ctrl+Shift+B)",
            'actionStop_Database': "Stop Database - Stop MongoDB container (Ctrl+Shift+D)",
            'actionDeploy_User_Manager': "Deploy Web UI - Deploy Open5GS WebUI container (Ctrl+Shift+U)",
            'actionStop_User_Manager': "Stop Web UI - Stop Open5GS WebUI container (Ctrl+Shift+W)",
            'actionDeploy_Monitoring': "Deploy Monitoring - Deploy Prometheus, Grafana monitoring stack (Ctrl+Shift+M)",
            'actionStop_Monitoring': "Stop Monitoring - Stop monitoring stack (Ctrl+Shift+N)"
        }

        for action_name, tooltip in tooltips.items():
            action = getattr(self.main_window, action_name, None)
            if action is not None:
                action.setToolTip(tooltip)

    def enablePickTool(self):
        if hasattr(self.main_window, 'enablePickTool'):
            self.main_window.enablePickTool()

    def enableLinkTool(self):
        if hasattr(self.main_window, 'enableLinkTool'):
            self.main_window.enableLinkTool()

    def enableDeleteTool(self):
        if hasattr(self.main_window, 'current_tool'):
            self.main_window.current_tool = "delete"
        canvas_view = getattr(self.main_window, 'canvas_view', None)
        if canvas_view is not None:
            canvas_view.setCursor(QCursor(Qt.PointingHandCursor))
        if hasattr(self.main_window, 'updateToolbarButtonStates'):
            self.main_window.updateToolbarButtonStates()
        if hasattr(self.main_window, 'showCanvasStatus'):
            self.main_window.showCanvasStatus("Delete Tool selected. Click on items to delete them.")

    def addTextBox(self):
        if hasattr(self.main_window, 'addTextBox'):
            self.main_window.addTextBox()

    def addDrawSquare(self):
        if hasattr(self.main_window, 'addDrawSquare'):
            self.main_window.addDrawSquare()

    def toggleGrid(self):
        if hasattr(self.main_window, 'toggleGrid'):
            self.main_window.toggleGrid()

    def zoomIn(self):
        canvas_view = getattr(self.main_window, 'canvas_view', None)
        if canvas_view is not None and hasattr(canvas_view, 'zoomIn'):
            canvas_view.zoomIn()

    def zoomOut(self):
        canvas_view = getattr(self.main_window, 'canvas_view', None)
        if canvas_view is not None and hasattr(canvas_view, 'zoomOut'):
            canvas_view.zoomOut()

    def resetZoom(self):
        canvas_view = getattr(self.main_window, 'canvas_view', None)
        if canvas_view is not None and hasattr(canvas_view, 'resetZoom'):
            canvas_view.resetZoom()

    # Note: RunAll/StopAll methods are handled directly in main.py via automation_manager
    # Note: Docker network methods are handled directly in main.py via docker_network_manager
    # Note: Database methods are handled directly in main.py via database_manager