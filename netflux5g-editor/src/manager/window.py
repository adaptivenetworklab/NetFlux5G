from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
from manager.debug import debug_print, error_print, warning_print
import os

class WindowManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setupWindow(self):
        """Set up the main window with proper sizing and positioning."""
        # Set application icon for window and taskbar
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "gui", "Icon", "logoSquare.png")
        self.main_window.setWindowIcon(QIcon(icon_path))

        # Get screen geometry for better initial sizing
        screen = QDesktopWidget().screenGeometry()
        
        # Set initial size to 80% of screen size
        initial_width = int(screen.width() * 0.8)
        initial_height = int(screen.height() * 0.8)
        self.main_window.resize(initial_width, initial_height)
        
        # Set window properties for better responsiveness
        self.main_window.setMinimumSize(1000, 700)
        
        # Center the window on the screen
        self.main_window.move(
            (screen.width() - initial_width) // 2,
            (screen.height() - initial_height) // 2
        )
        
    def updateCanvasGeometry(self):
        """Let the splitter/layout manage the canvas size. Only update scene size if needed."""
        try:
            if not hasattr(self.main_window, 'canvas_view'):
                warning_print("Canvas view not found during geometry update")
                return
            if hasattr(self.main_window.canvas_view, 'updateSceneSize'):
                self.main_window.canvas_view.updateSceneSize()
            debug_print("Canvas geometry update: only updateSceneSize called (no manual geometry)")
        except Exception as e:
            error_print(f"Failed to update canvas geometry: {e}")