from PyQt5.QtCore import Qt
from manager.debug import debug_print, error_print, warning_print, set_debug_enabled, is_debug_enabled

class KeyboardManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def handleKeyPress(self, event):
        """Handle key press events with improved shortcuts."""
        
        # ESC key - return to pick tool
        if event.key() == Qt.Key_Escape:
            self.main_window.tool_manager.enablePickTool()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.main_window.canvas_manager.zoomIn()
        elif event.key() == Qt.Key_Minus:
            self.main_window.canvas_manager.zoomOut()
        elif event.key() == Qt.Key_0:
            self.main_window.canvas_manager.resetZoom()
        elif event.key() == Qt.Key_G:
            self.main_window.canvas_manager.toggleGrid()
        elif event.key() == Qt.Key_P:
            self.main_window.tool_manager.enablePickTool()
        elif event.key() == Qt.Key_D:
            if event.modifiers() & Qt.ShiftModifier and event.modifiers() & Qt.ControlModifier:
                # Ctrl+Shift+D for debug toggle
                current_debug = is_debug_enabled()
                set_debug_enabled(not current_debug)
                self.main_window.showCanvasStatus(f"Debug mode {'enabled' if not current_debug else 'disabled'}")
            else:
                self.main_window.tool_manager.enableDeleteTool()
        elif event.key() == Qt.Key_L: 
            self.main_window.tool_manager.enableLinkTool()
        elif event.key() == Qt.Key_T:
            self.main_window.tool_manager.enableTextTool()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_N:
                self.main_window.file_manager.newTopology()
            elif event.key() == Qt.Key_O:
                self.main_window.file_manager.openTopology()
            elif event.key() == Qt.Key_S:
                if event.modifiers() & Qt.ShiftModifier:
                    self.main_window.file_manager.saveTopologyAs()
                else:
                    self.main_window.file_manager.saveTopology()
        elif event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            self.main_window.automation_manager.runAllComponents()
        else:
            return False  # Key not handled
        
        return True  # Key was handled