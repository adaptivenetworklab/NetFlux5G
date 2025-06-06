from PyQt5.QtCore import QTimer
from manager.debug import debug_print

class CanvasManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def zoomIn(self):
        """Zoom in the canvas."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomIn()
            self.main_window.status_manager.showCanvasStatus(f"Zoomed in (Level: {self.main_window.canvas_view.zoom_level:.1f}x)")

    def zoomOut(self):
        """Zoom out the canvas."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.zoomOut()
            self.main_window.status_manager.showCanvasStatus(f"Zoomed out (Level: {self.main_window.canvas_view.zoom_level:.1f}x)")

    def resetZoom(self):
        """Reset the zoom level of the canvas."""
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.resetZoom()
            self.main_window.status_manager.showCanvasStatus("Zoom reset to default level")
        
    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas with debouncing."""
        debug_print(f"DEBUG: toggleGrid called, current state: {self.main_window.show_grid}")
        
        # Add a small delay to prevent double-triggering
        if hasattr(self.main_window, '_grid_toggle_timer'):
            if self.main_window._grid_toggle_timer.isActive():
                return
        
        if not hasattr(self.main_window, '_grid_toggle_timer'):
            self.main_window._grid_toggle_timer = QTimer()
            self.main_window._grid_toggle_timer.setSingleShot(True)
            self.main_window._grid_toggle_timer.timeout.connect(self._performGridToggle)
        
        # Start timer with 100ms delay
        self.main_window._grid_toggle_timer.start(100)

    def _performGridToggle(self):
        """Actually perform the grid toggle after debouncing."""
        self.main_window.show_grid = not self.main_window.show_grid
        debug_print(f"DEBUG: Grid state changed to: {self.main_window.show_grid}")
        
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setShowGrid(self.main_window.show_grid)
            debug_print(f"DEBUG: Canvas setShowGrid called with: {self.main_window.show_grid}")
        
        status = "shown" if self.main_window.show_grid else "hidden"
        self.main_window.status_manager.showCanvasStatus(f"Grid {status}")
        
        # Update the action's checked state to match
        if hasattr(self.main_window, 'actionShowGrid'):
            self.main_window.actionShowGrid.setChecked(self.main_window.show_grid)