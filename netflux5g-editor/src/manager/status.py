from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from manager.debug import debug_print, error_print

class StatusManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.canvas_status_label = None
        self._status_timer = None
        
    def setupCanvasStatusBar(self):
        """Set up the canvas status bar."""
        try:
            if not hasattr(self.main_window, 'canvas_view'):
                error_print("ERROR: Canvas view not found when setting up status bar")
                return
                
            if self.canvas_status_label:
                self.canvas_status_label.deleteLater()
                self.canvas_status_label = None
            
            self.canvas_status_label = QLabel(self.main_window.canvas_view)
            self.canvas_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 0, 0, 180);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 50);
                }
            """)
            
            font = QFont("Segoe UI", 9)
            self.canvas_status_label.setFont(font)
            self.canvas_status_label.setAlignment(Qt.AlignCenter)
            self.canvas_status_label.hide()
            
            # Position at bottom middle of canvas
            self.updateCanvasStatusBarPosition()
            
            debug_print("DEBUG: Canvas status bar setup complete - positioned at bottom middle")
            
        except Exception as e:
            error_print(f"ERROR: Failed to setup canvas status bar: {e}")

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar to bottom middle with slight upward offset."""
        try:
            if not self.canvas_status_label or not hasattr(self.main_window, 'canvas_view'):
                return
                
            canvas = self.main_window.canvas_view
            canvas_rect = canvas.geometry()
            
            # Get the current text to calculate proper size
            text = self.canvas_status_label.text()
            if not text:
                text = "Ready"  # Default text for sizing
            
            # Calculate text metrics
            font_metrics = self.canvas_status_label.fontMetrics()
            text_width = font_metrics.width(text)
            text_height = font_metrics.height()
            
            # Add padding (matching the stylesheet padding: 8px 16px)
            label_width = text_width + 32  # 16px padding on each side
            label_height = text_height + 16  # 8px padding on top and bottom
            
            # Calculate bottom middle position with upward offset
            center_x = (canvas.width() - label_width) // 2
            # Position near bottom but with 40px offset from the very bottom
            bottom_y = canvas.height() - label_height - 40
            
            # Ensure the label doesn't go outside canvas bounds
            center_x = max(10, min(center_x, canvas.width() - label_width - 10))
            bottom_y = max(10, min(bottom_y, canvas.height() - label_height - 10))
            
            self.canvas_status_label.setGeometry(center_x, bottom_y, label_width, label_height)
            
            debug_print(f"DEBUG: Status bar positioned at bottom middle: ({center_x}, {bottom_y}), size: ({label_width}, {label_height})")
            
        except Exception as e:
            error_print(f"ERROR: Failed to update canvas status bar position: {e}")

    def showCanvasStatus(self, message, timeout=2000):
        """Show a status message on the canvas at the bottom middle."""
        try:
            if not self.canvas_status_label:
                self.setupCanvasStatusBar()
            
            if not self.canvas_status_label:
                debug_print(f"Status (fallback): {message}")
                return
            
            self.canvas_status_label.setText(message)
            
            # Update position based on new text content
            self.updateCanvasStatusBarPosition()
            
            self.canvas_status_label.show()
            self.canvas_status_label.raise_()  # Bring to front
            
            # Stop existing timer
            if self._status_timer and self._status_timer.isActive():
                self._status_timer.stop()
            
            # Set up auto-hide timer if timeout is specified
            if timeout > 0:
                if not self._status_timer:
                    self._status_timer = QTimer()
                    self._status_timer.setSingleShot(True)
                    self._status_timer.timeout.connect(self._hideCanvasStatus)
                
                self._status_timer.start(timeout)
            
            debug_print(f"DEBUG: Canvas status shown at bottom middle: {message}")
            
        except Exception as e:
            error_print(f"ERROR: Failed to show canvas status: {e}")

    def _hideCanvasStatus(self):
        """Hide the canvas status label."""
        try:
            if self.canvas_status_label:
                self.canvas_status_label.hide()
                debug_print("DEBUG: Canvas status hidden")
        except Exception as e:
            error_print(f"ERROR: Failed to hide canvas status: {e}")

    def hideCanvasStatus(self):
        """Manually hide the canvas status."""
        self._hideCanvasStatus()