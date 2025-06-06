from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer
from manager.debug import debug_print, error_print
import traceback

class StatusManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.canvas_status_label = None
        self._status_timer = None
        
    def setupCanvasStatusBar(self):
        """Create a custom status bar that only appears over the canvas area."""
        try:
            # Remove existing status label if it exists
            if hasattr(self, 'canvas_status_label') and self.canvas_status_label:
                try:
                    if not self.canvas_status_label.isHidden():
                        self.canvas_status_label.hide()
                    self.canvas_status_label.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self.canvas_status_label = None
            
            # Cancel any pending status timers
            if self._status_timer:
                self._status_timer.stop()
                self._status_timer = None
            
            # Create new status label
            if hasattr(self.main_window, 'canvas_view') and self.main_window.canvas_view:
                self.canvas_status_label = QLabel(self.main_window.canvas_view)
                self.canvas_status_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 200);
                        border: 1px solid gray;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 11px;
                        color: black;
                    }
                """)
                self.canvas_status_label.hide()
                self.updateCanvasStatusBarPosition()
                debug_print("Canvas status bar created successfully")
            
        except Exception as e:
            error_print(f"Failed to setup canvas status bar: {e}")

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar."""
        try:
            if (self.canvas_status_label and 
                hasattr(self.main_window, 'canvas_view') and 
                self.main_window.canvas_view):
                
                try:
                    _ = self.canvas_status_label.isVisible()
                except RuntimeError:
                    self.setupCanvasStatusBar()
                    return
                
                canvas_rect = self.main_window.canvas_view.geometry()
                x = 10
                y = canvas_rect.height() - 30
                self.canvas_status_label.move(x, y)
                
        except Exception as e:
            error_print(f"Failed to update canvas status bar position: {e}")

    def showCanvasStatus(self, message, timeout=0):
        """Show a status message on the canvas status bar."""
        try:
            if not self.canvas_status_label:
                self.setupCanvasStatusBar()
            
            if self.canvas_status_label:
                try:
                    _ = self.canvas_status_label.isVisible()
                    self.canvas_status_label.setText(message)
                    self.canvas_status_label.adjustSize()
                    self.canvas_status_label.show()
                    
                    if self._status_timer:
                        self._status_timer.stop()
                    
                    if timeout > 0:
                        self._status_timer = QTimer()
                        self._status_timer.setSingleShot(True)
                        self._status_timer.timeout.connect(self._hideCanvasStatus)
                        self._status_timer.start(timeout)
                    
                    debug_print(f"Canvas status updated: {message}")
                    
                except RuntimeError:
                    self.setupCanvasStatusBar()
                    if self.canvas_status_label:
                        self.canvas_status_label.setText(message)
                        self.canvas_status_label.adjustSize()
                        self.canvas_status_label.show()
            
        except Exception as e:
            error_print(f"Failed to show canvas status: {e}")
            debug_print(f"STATUS: {message}", force=True)

    def _hideCanvasStatus(self):
        """Hide the canvas status label safely."""
        try:
            if self.canvas_status_label:
                try:
                    self.canvas_status_label.hide()
                    self.canvas_status_label.setText("Ready")
                except RuntimeError:
                    pass
        except Exception as e:
            error_print(f"Failed to hide canvas status: {e}")