from PyQt5.QtCore import Qt

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
                self.main_window.toggleDebugMode()
            else:
                # Just D for delete tool
                self.main_window.tool_manager.enableDeleteTool()
        elif event.key() == Qt.Key_L: 
            self.main_window.tool_manager.enableLinkTool()
        elif event.key() == Qt.Key_T:
            self.main_window.tool_manager.addTextBox()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.main_window.file_manager.saveTopology()
            elif event.key() == Qt.Key_N:
                self.main_window.file_manager.newTopology()
            elif event.key() == Qt.Key_O:
                self.main_window.file_manager.openTopology()
            elif event.key() == Qt.Key_X:
                # Ctrl+X for cut component
                if hasattr(self.main_window, 'component_operations_manager'):
                    self.main_window.component_operations_manager.cutComponent()
            elif event.key() == Qt.Key_C:
                # Ctrl+C for copy component
                if hasattr(self.main_window, 'component_operations_manager'):
                    self.main_window.component_operations_manager.copyComponent()
            elif event.key() == Qt.Key_V:
                # Ctrl+V for paste component
                if hasattr(self.main_window, 'component_operations_manager'):
                    self.main_window.component_operations_manager.pasteComponent()
        # Add shortcuts for RunAll and StopAll
        elif event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            # Ctrl+R for RunAll 
            self.main_window.automation_manager.runAllComponents()
        elif event.key() == Qt.Key_F5:
            # F5 for Run topology
            self.main_window.automation_manager.runTopology()
        elif event.key() == Qt.Key_F6:
            # F6 for Stop topology
            self.main_window.automation_manager.stopTopology()
        # Add shortcuts for Docker network operations
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+C for create Docker network
            if hasattr(self.main_window, 'docker_network_manager'):
                self.main_window.docker_network_manager.create_docker_network()
        elif event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+X for delete Docker network
            if hasattr(self.main_window, 'docker_network_manager'):
                self.main_window.docker_network_manager.delete_docker_network()
        # Add shortcuts for Database operations
        elif event.key() == Qt.Key_B and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+B for deploy database
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.deployDatabase()
        elif event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+D for stop database
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.stopDatabase()
        # Add shortcuts for Web UI operations
        elif event.key() == Qt.Key_U and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+U for deploy Web UI
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.deployWebUI()
        elif event.key() == Qt.Key_W and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+W for stop Web UI
            if hasattr(self.main_window, 'database_manager'):
                self.main_window.database_manager.stopWebUI()
        # Add shortcuts for Monitoring operations
        elif event.key() == Qt.Key_M and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+M for deploy monitoring
            if hasattr(self.main_window, 'monitoring_manager'):
                self.main_window.monitoring_manager.deployMonitoring()
        elif event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            # Ctrl+Shift+N for stop monitoring
            if hasattr(self.main_window, 'monitoring_manager'):
                self.main_window.monitoring_manager.stopMonitoring()
        else:
            return False
        
        return True