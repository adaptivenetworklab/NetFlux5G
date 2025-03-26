from PyQt5.QtWidgets import QMainWindow

class ToolbarFunctions:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.setup_toolbar_actions()

    def setup_toolbar_actions(self):
        self.main_window.actionPickTool.triggered.connect(self.enablePickTool)
        self.main_window.actionHandTool.triggered.connect(self.enableHandTool)
        self.main_window.actionDelete.triggered.connect(self.enableDeleteTool)
        self.main_window.actionTextBox.triggered.connect(self.addTextBox)
        self.main_window.actionDrawSquare.triggered.connect(self.addDrawSquare)
        self.main_window.actionShowGrid.triggered.connect(self.toggleGrid)
        self.main_window.actionZoomIn.triggered.connect(self.zoomIn)
        self.main_window.actionZoomOut.triggered.connect(self.zoomOut)
        self.main_window.actionResetZoom.triggered.connect(self.resetZoom)
        self.main_window.actionRunAll.triggered.connect(self.runAll)
        self.main_window.actionStopAll.triggered.connect(self.stopAll)

    def enablePickTool(self):
        self.main_window.statusbar.showMessage("Pick Tool selected")
        # Add logic for Pick Tool

    def enableHandTool(self):
        self.main_window.statusbar.showMessage("Hand Tool selected")
        # Add logic for Hand Tool

    def enableDeleteTool(self):
        self.main_window.statusbar.showMessage("Delete Tool selected")
        # Add logic for Delete Tool

    def addTextBox(self):
        self.main_window.statusbar.showMessage("Text Box Tool selected")
        # Add logic for adding a text box

    def addDrawSquare(self):
        self.main_window.statusbar.showMessage("Draw Square Tool selected")
        # Add logic for drawing a square

    def toggleGrid(self):
        self.main_window.show_grid = not self.main_window.show_grid
        self.main_window.statusbar.showMessage(f"Grid {'shown' if self.main_window.show_grid else 'hidden'}")
        # Add logic for toggling the grid

    def zoomIn(self):
        self.main_window.statusbar.showMessage("Zoom In triggered")
        # Add logic for zooming in

    def zoomOut(self):
        self.main_window.statusbar.showMessage("Zoom Out triggered")
        # Add logic for zooming out

    def resetZoom(self):
        self.main_window.statusbar.showMessage("Reset Zoom triggered")
        # Add logic for resetting zoom

    def runAll(self):
        self.main_window.statusbar.showMessage("Run All triggered")
        # Add logic for running all components

    def stopAll(self):
        self.main_window.statusbar.showMessage("Stop All triggered")
        # Add logic for stopping all components