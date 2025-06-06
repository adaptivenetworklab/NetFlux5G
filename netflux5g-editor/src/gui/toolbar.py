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

        # Connect run/stop actions if they exist
        run_action = getattr(self.main_window, 'actionRunAll', None)
        if run_action is not None:
            run_action.triggered.connect(self.runAll)
        stop_action = getattr(self.main_window, 'actionStopAll', None)
        if stop_action is not None:
            stop_action.triggered.connect(self.stopAll)

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
            'actionStopAll': "Stop All - Stop all running services"
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

    def runAll(self):
        if hasattr(self.main_window, 'runAllComponents'):
            self.main_window.runAllComponents()

    def stopAll(self):
        if hasattr(self.main_window, 'stopAllComponents'):
            self.main_window.stopAllComponents()