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
        """Update canvas geometry based on current window size and ObjectFrame position."""
        try:
            if not hasattr(self.main_window, 'canvas_view'):
                warning_print("Canvas view not found during geometry update")
                return

            window_size = self.main_window.size()

            # Get ObjectFrame width from the actual widget
            object_frame_width = self.main_window.ObjectFrame.width() if hasattr(self.main_window, 'ObjectFrame') else 71

            menubar_height = self.main_window.menubar.height() if hasattr(self.main_window, 'menubar') else 26
            toolbar_height = self.main_window.toolBar.height() if hasattr(self.main_window, 'toolBar') else 30
            statusbar_height = self.main_window.statusbar.height() if hasattr(self.main_window, 'statusbar') else 23

            available_width = window_size.width() - object_frame_width - 10
            available_height = window_size.height() - menubar_height - toolbar_height - statusbar_height - 10

            available_width = max(available_width, 400)
            available_height = max(available_height, 300)

            canvas_x = object_frame_width + 5
            canvas_y = 5

            self.main_window.canvas_view.setGeometry(canvas_x, canvas_y, available_width, available_height)
            self.main_window.canvas_view.setVisible(True)
            self.main_window.canvas_view.show()

            if hasattr(self.main_window.canvas_view, 'updateSceneSize'):
                self.main_window.canvas_view.updateSceneSize()

            debug_print(f"Canvas geometry updated - x:{canvas_x}, y:{canvas_y}, w:{available_width}, h:{available_height}")

        except Exception as e:
            error_print(f"Failed to update canvas geometry: {e}")