from PyQt5.QtWidgets import QMainWindow

class ToolbarFunctions:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.setup_toolbar_actions()
        self.setup_tooltips()

    def setup_toolbar_actions(self):
        self.main_window.actionPickTool.triggered.connect(self.enablePickTool)
        self.main_window.actionDelete.triggered.connect(self.enableDeleteTool)
        self.main_window.actionTextBox.triggered.connect(self.addTextBox)
        self.main_window.actionDrawSquare.triggered.connect(self.addDrawSquare)
        self.main_window.actionShowGrid.triggered.connect(self.toggleGrid)
        self.main_window.actionZoomIn.triggered.connect(self.zoomIn)
        self.main_window.actionZoomOut.triggered.connect(self.zoomOut)
        self.main_window.actionResetZoom.triggered.connect(self.resetZoom)
        self.main_window.actionRunAll.triggered.connect(self.runAll)
        self.main_window.actionStopAll.triggered.connect(self.stopAll)

    def setup_tooltips(self):
        """Set up helpful tooltips with keyboard shortcuts."""
        self.main_window.actionPickTool.setToolTip("Pick Tool (P)")
        self.main_window.actionDelete.setToolTip("Delete Tool (D)")
        self.main_window.actionTextBox.setToolTip("Text Box Tool (T)")
        self.main_window.actionDrawSquare.setToolTip("Draw Square Tool")
        self.main_window.actionShowGrid.setToolTip("Toggle Grid (G)")
        self.main_window.actionZoomIn.setToolTip("Zoom In (+)")
        self.main_window.actionZoomOut.setToolTip("Zoom Out (-)")
        self.main_window.actionResetZoom.setToolTip("Reset Zoom (0)")
        self.main_window.actionRunAll.setToolTip("Run All Components")
        self.main_window.actionStopAll.setToolTip("Stop All Components")

    def enablePickTool(self):
        self.main_window.statusbar.showMessage("Pick Tool selected (P)")
        self.main_window.enablePickTool()

    def enableDeleteTool(self):
        self.main_window.statusbar.showMessage("Delete Tool selected (D). Click on items to delete them.")
        self.main_window.current_tool = "delete"

    def addTextBox(self):
        self.main_window.statusbar.showMessage("Text Box Tool selected (T)")
        self.main_window.addTextBox()

    def addDrawSquare(self):
        self.main_window.statusbar.showMessage("Draw Square Tool selected")
        self.main_window.addDrawSquare()

    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas."""
        self.main_window.toggleGrid()

    def zoomIn(self):
        """Zoom in using toolbar button."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomIn()
            self.main_window.statusbar.showMessage(f"Zoomed in (Level: {self.main_window.canvas_view.zoom_level:.1f}x)")

    def zoomOut(self):
        """Zoom out using toolbar button."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomOut()
            self.main_window.statusbar.showMessage(f"Zoomed out (Level: {self.main_window.canvas_view.zoom_level:.1f}x)")

    def resetZoom(self):
        """Reset zoom using toolbar button."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.resetZoom()
            self.main_window.statusbar.showMessage("Zoom reset to default level")

    def runAll(self):
        self.main_window.statusbar.showMessage("Run All triggered")
        # Add logic for running all components

    def stopAll(self):
        self.main_window.statusbar.showMessage("Stop All triggered")
        # Add logic for stopping all components