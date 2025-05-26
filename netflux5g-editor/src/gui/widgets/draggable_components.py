import os
from PyQt5.QtWidgets import QPushButton, QApplication, QLabel
from PyQt5.QtCore import Qt, QPoint, QSize, QMimeData
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QPainter


class DraggableButton(QPushButton):
    """Custom button that supports drag and drop operations for network components"""
    
    def __init__(self, text, component_type, icon_path, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path
        
        # Set up the button appearance - keep the text!
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(50, 50))
        
        # Don't hide the text - this was the issue!
        self.setText("")  # We'll handle text with labels separately
        self.setToolTip(f"Drag to canvas or click to start drag mode\n{component_type}")
        
        # Enable drag and drop
        self.setAcceptDrops(False)  # Buttons don't accept drops
        
        # Store reference to main window
        self.main_window = None
        
    def mousePressEvent(self, event):
        """Handle mouse press to initiate drag or show context menu"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Start drag operation when mouse is moved with button pressed"""
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not hasattr(self, 'drag_start_position'):
            return
            
        # Check if we've moved far enough to start a drag
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
            
        # Start the drag operation
        self.startDragOperation()
        
    def startDragOperation(self):
        """Create and execute a drag operation"""
        print(f"DEBUG: Starting drag operation for {self.component_type}")
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.component_type)
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        if self.icon_path and os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Make it semi-transparent
            transparent_pixmap = QPixmap(pixmap.size())
            transparent_pixmap.fill(Qt.transparent)
            
            painter = QPainter(transparent_pixmap)
            painter.setOpacity(0.7)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            drag.setPixmap(transparent_pixmap)
            drag.setHotSpot(QPoint(20, 20))
        
        # Notify main window about drag start
        if self.main_window:
            self.main_window.showCanvasStatus(f"Dragging {self.component_type}... Drop on canvas to place")
        
        # Execute drag
        drop_action = drag.exec_(Qt.CopyAction)
        
        # Notify main window about drag end
        if self.main_window:
            if drop_action == Qt.CopyAction:
                self.main_window.showCanvasStatus(f"{self.component_type} placed on canvas")
            else:
                self.main_window.showCanvasStatus("Drag cancelled")

    def setMainWindow(self, main_window):
        """Set reference to main window for status updates"""
        self.main_window = main_window


class ComponentButtonManager:
    """Manager class for handling component button creation and replacement"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.draggable_buttons = {}
        self.component_labels = {}
        
    def replaceButtonsWithDraggable(self, component_icon_map):
        """Replace existing component buttons with draggable versions while preserving labels"""
        try:
            print("DEBUG: Replacing buttons with draggable versions...")
            
            # Component button mappings with their display names
            button_mappings = [
                ("Host", "Host", "Host"),
                ("STA", "STA", "STA"), 
                ("UE", "UE", "UE"),
                ("GNB", "GNB", "gNB"),
                ("DockerHost", "DockerHost", "Docker"),
                ("AP", "AP", "AP"),
                ("VGcore", "VGcore", "5G Core"),
                ("Router", "Router", "Legacy Router"),
                ("Switch", "Switch", "Legacy Switch"),
                ("Controller", "Controller", "Controller")
            ]
            
            for button_name, component_type, display_name in button_mappings:
                if hasattr(self.main_window, button_name):
                    original_button = getattr(self.main_window, button_name)
                    
                    # Get the parent layout and position
                    parent_widget = original_button.parent()
                    button_geometry = original_button.geometry()
                    
                    # Create new draggable button
                    icon_path = component_icon_map.get(component_type)
                    draggable_button = DraggableButton(
                        display_name, 
                        component_type, 
                        icon_path, 
                        parent_widget
                    )
                    
                    # Set the same geometry and properties
                    draggable_button.setGeometry(button_geometry)
                    draggable_button.setStyleSheet(original_button.styleSheet())
                    draggable_button.setMainWindow(self.main_window)
                    
                    # Copy other properties
                    if hasattr(original_button, 'shortcut'):
                        draggable_button.setShortcut(original_button.shortcut())
                    
                    # Hide original and show new
                    original_button.hide()
                    draggable_button.show()
                    
                    # Store reference
                    self.draggable_buttons[component_type] = draggable_button
                    setattr(self.main_window, f"{button_name}_draggable", draggable_button)
                    
                    print(f"DEBUG: Replaced {button_name} with draggable version")
                    
            # Now preserve the existing labels - they should still be visible
            print("DEBUG: Checking for existing labels...")
            self.preserveComponentLabels()
                    
            print("DEBUG: All buttons replaced successfully")
            return self.draggable_buttons
            
        except Exception as e:
            print(f"ERROR: Failed to replace buttons: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def preserveComponentLabels(self):
        """Ensure component labels remain visible"""
        try:
            # Check if labels are already visible in the UI
            # Labels should be automatically preserved from the UI file
            label_names = [
                "label", "label_2", "label_3", "label_4", "label_5", 
                "label_6", "label_7", "label_8", "label_9", "label_10", "label_11"
            ]
            
            for label_name in label_names:
                if hasattr(self.main_window, label_name):
                    label = getattr(self.main_window, label_name)
                    if isinstance(label, QLabel):
                        # Ensure the label is visible
                        label.setVisible(True)
                        label.show()
                        print(f"DEBUG: Preserved label {label_name}: '{label.text()}'")
            
            # Also check for line separators
            line_names = [
                "line", "line_2", "line_3", "line_4", "line_5", 
                "line_6", "line_7", "line_8", "line_9", "line_10", "line_11"
            ]
            
            for line_name in line_names:
                if hasattr(self.main_window, line_name):
                    line = getattr(self.main_window, line_name)
                    line.setVisible(True)
                    line.show()
                    
        except Exception as e:
            print(f"ERROR: Failed to preserve labels: {e}")
            import traceback
            traceback.print_exc()
    
    def restoreComponentLabels(self):
        """Explicitly restore component labels if they were hidden"""
        try:
            # Map of label names to their text content based on your UI
            label_mapping = {
                "label": "Host",
                "label_2": "STA", 
                "label_3": "UE",
                "label_4": "gNB",
                "label_5": "Docker",
                "label_6": "AP",
                "label_7": "5G Core",
                "label_8": "Legacy Router",
                "label_9": "Legacy Switch",
                "label_10": "Link Cable",
                "label_11": "Controller"
            }
            
            for label_name, text_content in label_mapping.items():
                if hasattr(self.main_window, label_name):
                    label = getattr(self.main_window, label_name)
                    if isinstance(label, QLabel):
                        label.setText(text_content)
                        label.setVisible(True)
                        label.show()
                        print(f"DEBUG: Restored label {label_name}: '{text_content}'")
                        
        except Exception as e:
            print(f"ERROR: Failed to restore labels: {e}")
            import traceback
            traceback.print_exc()    

    def connectDraggableButtons(self, start_drag_callback):
        """Connect all draggable buttons to their respective callbacks"""
        try:
            for component_type, button in self.draggable_buttons.items():
                button.clicked.connect(lambda checked, ct=component_type: start_drag_callback(ct))
            print("DEBUG: All draggable buttons connected")
        except Exception as e:
            print(f"ERROR: Failed to connect draggable buttons: {e}")
            import traceback
            traceback.print_exc()
    
    def getDraggableButtons(self):
        """Get dictionary of all draggable buttons"""
        return self.draggable_buttons