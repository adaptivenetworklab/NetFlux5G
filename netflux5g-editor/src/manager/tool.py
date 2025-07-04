from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt, QPoint, QMimeData, QTimer
from PyQt5.QtGui import QDrag, QPixmap, QCursor
from gui.links import NetworkLink
from manager.debug import debug_print, error_print, warning_print
import os

class ToolManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def startDrag(self, component_type):
        """Start drag action for components with enhanced debugging."""
        debug_print(f"DEBUG: Starting drag for component: {component_type}")
        
        # Exit link mode if active
        self.exitLinkMode()
        
        # Verify canvas exists and is ready
        if not hasattr(self.main_window, 'canvas_view'):
            error_print("ERROR: canvas_view not found!")
            self.main_window.status_manager.showCanvasStatus("ERROR: Canvas not initialized")
            return
            
        if not self.main_window.canvas_view.acceptDrops():
            warning_print("WARNING: Canvas does not accept drops, enabling...")
            self.main_window.canvas_view.setAcceptDrops(True)

        # Create a drag object with component information
        drag = QDrag(self.main_window)
        mime_data = QMimeData()
        mime_data.setText(component_type)  # Pass the component type as text
        drag.setMimeData(mime_data)
        
        debug_print(f"DEBUG: Created drag with mime data: '{component_type}'")
        
        # Set a pixmap for the drag appearance
        icon_path = self.main_window.component_icon_map.get(component_type)
        if icon_path and os.path.exists(icon_path):
            # Always scale the pixmap to a small size for smooth dragging
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            drag.setPixmap(pixmap)
        else:
            # Use a default small pixmap if icon not found
            drag.setPixmap(QPixmap(48, 48))
        
        # Update status
        self.main_window.status_manager.showCanvasStatus(f"Dragging {component_type}... Drop on canvas to place")
        
        # Execute the drag
        result = drag.exec_(Qt.CopyAction)
        debug_print(f"DEBUG: Drag operation completed with result: {result}")
        
        # Reset status
        self.main_window.status_manager.showCanvasStatus("Ready")
        
    def startLinkMode(self, component_type):
        """Activate link mode."""
        debug_print("DEBUG: Starting link mode")
        
        # Reset any previous source selection
        self.main_window.current_link_source = None
        
        # Set current tool to link
        self.main_window.current_tool = "link"
        
        # Enable link mode in canvas
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setLinkMode(True)
            self.main_window.canvas_view.setCursor(Qt.CrossCursor)
        
        # Update status bar
        self.main_window.status_manager.showCanvasStatus("Link mode activated. Click on source object, then destination object.")

    def createLink(self, source, destination):
        """Create a link between two objects."""
        debug_print(f"DEBUG: Creating link between {source} and {destination}")
        
        # Create a new NetworkLink with cable visualization
        link = NetworkLink(source, destination, main_window=self.main_window)
        
        # Add the link to the scene
        self.main_window.canvas_view.scene.addItem(link)
        
        # Update the status bar
        source_name = getattr(source, 'object_type', getattr(source, 'component_type', 'object'))
        dest_name = getattr(destination, 'object_type', getattr(destination, 'component_type', 'object'))
        self.main_window.status_manager.showCanvasStatus(f"Link created between {source_name} and {dest_name}")
        
        # Update view
        self.main_window.canvas_view.viewport().update()
        
        return link

    def exitLinkMode(self):
        """Exit link mode."""
        debug_print("DEBUG: Exiting link mode")
        
        # Remove highlight from source if one was selected
        if self.main_window.current_link_source and hasattr(self.main_window.current_link_source, 'setHighlighted'):
            self.main_window.current_link_source.setHighlighted(False)
        
        # Re-enable dragging for source if one was selected
        if self.main_window.current_link_source and hasattr(self.main_window.current_link_source, 'setFlag'):
            from PyQt5.QtWidgets import QGraphicsItem
            self.main_window.current_link_source.setFlag(QGraphicsItem.ItemIsMovable, True)
            
        self.main_window.current_link_source = None
        
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setLinkMode(False)
            # Reset cursor to default
            self.main_window.canvas_view.setCursor(QCursor(Qt.ArrowCursor))
            
        self.main_window.status_manager.showCanvasStatus("Pick tool selected")

    def updateAllLinks(self):
        """Update all links in the scene."""
        if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
            for item in self.main_window.canvas_view.scene.items():
                if isinstance(item, NetworkLink):
                    item.updatePosition()

    def enablePickTool(self):
        """Restore the pick tool state."""
        debug_print("DEBUG: Enabling pick tool")
        self.exitLinkMode()  # Exit link mode if active
        self.main_window.current_tool = "pick"
        self.main_window.selected_component = None  # Reset selected component
        
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setLinkMode(False)
            # Reset cursor to default arrow
            self.main_window.canvas_view.setCursor(QCursor(Qt.ArrowCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        self.main_window.status_manager.showCanvasStatus("Pick tool selected")

    def enableLinkTool(self):
        """Enable the Link Tool from toolbar."""
        debug_print("DEBUG: Enabling link tool from toolbar")
        
        # Exit other modes
        self.main_window.current_tool = "link"
        
        # Reset any previous source selection
        self.main_window.current_link_source = None
        
        # Enable link mode in canvas
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setLinkMode(True)
            # Set cursor to plus sign for link mode
            self.main_window.canvas_view.setCursor(QCursor(Qt.CrossCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        # Update status bar
        self.main_window.status_manager.showCanvasStatus("Link Tool active. Click on source component, then destination component.")

    def enableDeleteTool(self):
        """Enable the Delete Tool."""
        debug_print("DEBUG: Enabling delete tool")
        self.exitLinkMode()  # Exit link mode if active
        self.main_window.current_tool = "delete"
        
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setLinkMode(False)
            # Set cursor to a different cursor for delete mode (optional)
            self.main_window.canvas_view.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        self.main_window.status_manager.showCanvasStatus("Delete Tool selected. Click on items to delete them.")

    def updateToolbarButtonStates(self):
        """Update the checked state of toolbar buttons based on current tool."""
        if hasattr(self.main_window, 'actionPickTool'):
            self.main_window.actionPickTool.setChecked(self.main_window.current_tool == "pick")
        if hasattr(self.main_window, 'actionLinkTool'):
            self.main_window.actionLinkTool.setChecked(self.main_window.current_tool == "link")
        if hasattr(self.main_window, 'actionDelete'):
            self.main_window.actionDelete.setChecked(self.main_window.current_tool == "delete")

    def addTextBox(self):
        self.main_window.current_tool = "text"
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.main_window.status_manager.showCanvasStatus("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.main_window.current_tool = "square"
        if hasattr(self.main_window, 'canvas_view'):
            self.main_window.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.main_window.status_manager.showCanvasStatus("Square tool selected. Click and drag to draw a square.")