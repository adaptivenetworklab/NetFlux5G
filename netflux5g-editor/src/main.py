import sys
import os
import json
import re
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QIcon
from PyQt5 import uic
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from gui.links import NetworkLink

# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "ui", "Main_Window.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)

        # Set application icon for window and taskbar
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon", "logoSquare.png")
        self.setWindowIcon(QIcon(icon_path))

        # IMPORTANT: Resize the main window to fit the screen better
        self.resize(1200, 800)  # Start with a reasonable size
        
        # Set window properties for better responsiveness
        self.setMinimumSize(1000, 700)
        
        # Center the window on the screen
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

        # Initialize the toolbar functions
        self.toolbar_functions = ToolbarFunctions(self)
        
        # Initialize grid attribute
        self.show_grid = False
        
        # Initialize component mapping for icons FIRST
        icon_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon")
        self.component_icon_map = {
            "Host": os.path.join(icon_base_path, "host.png"),
            "STA": os.path.join(icon_base_path, "sta.png"),
            "UE": os.path.join(icon_base_path, "ue.png"),
            "GNB": os.path.join(icon_base_path, "gNB.png"),
            "DockerHost": os.path.join(icon_base_path, "docker.png"),
            "AP": os.path.join(icon_base_path, "AP.png"),
            "VGcore": os.path.join(icon_base_path, "5G core.png"),
            "Router": os.path.join(icon_base_path, "Router.png"),
            "Switch": os.path.join(icon_base_path, "switch.png"),
            "LinkCable": os.path.join(icon_base_path, "link cable.png"),
            "Controller": os.path.join(icon_base_path, "controller.png")
        }
        
        # Set up the canvas first
        self.setupCanvas()
        
        # Make the component panel scrollable AFTER canvas setup
        # self.makeComponentPanelScrollable()
        
        # Initialize attributes
        self.current_link_source = None
        self.current_file = None
        self.current_tool = "pick"
        self.selected_component = None
        
        # Setup all connections
        self.setupConnections()
        
        # Status message
        self.statusbar.showMessage("Ready - Application resized for better usability")
        
        # Show helpful shortcut information
        self.showShortcutHelp()
        
        # Debug canvas setup
        self.debugCanvasSetup()

    # def makeComponentPanelScrollable(self):
    #     """Make the component panel scrollable if there are too many components."""
    #     try:
    #         from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout
    #         from PyQt5.QtCore import QSize
            
    #         if hasattr(self, 'verticalLayoutWidget') and hasattr(self, 'ObjectLayout'):
    #             # Get the current component layout
    #             original_layout = self.ObjectLayout
                
    #             # Calculate the available height based on window size
    #             window_height = self.size().height()
    #             available_height = window_height - 80  # Leave space for menubar, toolbar, statusbar
                
    #             # Create a scroll area that fills the available height
    #             scroll_area = QScrollArea(self.ObjectFrame)
    #             scroll_area.setGeometry(10, 10, 93, available_height)  # Use calculated height
    #             scroll_area.setWidgetResizable(True)
    #             scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    #             scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                
    #             # Create a widget to hold the components
    #             scroll_widget = QWidget()
    #             scroll_layout = QVBoxLayout(scroll_widget)
    #             scroll_layout.setSpacing(3)  # Small spacing between components
    #             scroll_layout.setContentsMargins(2, 2, 2, 2)
                
    #             # Move all items from the original layout to the scroll layout
    #             while original_layout.count():
    #                 item = original_layout.takeAt(0)
    #                 if item.widget():
    #                     widget = item.widget()
                        
    #                     # Handle component buttons
    #                     if isinstance(widget, QPushButton):
    #                         # Set appropriate size for buttons to maintain icon quality
    #                         widget.setFixedSize(85, 70)  # Slightly larger for better icon display
                            
    #                         # Maintain icon aspect ratio but make it fit well
    #                         current_icon_size = widget.iconSize()
    #                         new_icon_size = QSize(45, 45)  # Good balance between size and clarity
    #                         widget.setIconSize(new_icon_size)
                            
    #                         print(f"DEBUG: Resized button {widget.objectName()} - Size: 85x70, Icon: 45x45")
                        
    #                     # Handle labels (component names)
    #                     elif hasattr(widget, 'setText') and hasattr(widget, 'text'):
    #                         # Make labels more compact
    #                         font = widget.font()
    #                         font.setPointSize(7)  # Smaller font
    #                         widget.setFont(font)
    #                         widget.setFixedHeight(15)  # Fixed height for consistency
    #                         widget.setAlignment(Qt.AlignCenter)  # Center align text
                            
    #                         print(f"DEBUG: Resized label: {widget.text()}")
                        
    #                     # Handle line separators
    #                     elif hasattr(widget, 'orientation'):
    #                         widget.setFixedHeight(2)  # Very thin separators
                        
    #                     scroll_layout.addWidget(widget)
                
    #             # Add stretch at the end to push components to the top
    #             scroll_layout.addStretch()
                
    #             # Set the scroll widget
    #             scroll_area.setWidget(scroll_widget)
                
    #             # Hide the original layout widget
    #             self.verticalLayoutWidget.hide()
                
    #             # Store the scroll area reference for resizing
    #             self.component_scroll_area = scroll_area
                
    #             print(f"DEBUG: Component panel made scrollable with height: {available_height}")
                
    #     except Exception as e:
    #         print(f"ERROR: Failed to make component panel scrollable: {e}")
    #         import traceback
    #         traceback.print_exc()

    def showShortcutHelp(self):
        """Show a brief help message about shortcuts."""
        help_message = (
            "Mouse Navigation: Middle-click + drag to pan | Ctrl + Mouse wheel to zoom | "
            "Keyboard: P=Pick, D=Delete, L=Link, G=Grid, +/-=Zoom, 0=Reset Zoom, ESC=Pick Tool"
        )
        # Show for 5 seconds, then return to ready state
        self.showCanvasStatus(help_message, 5000)

    def setupCanvas(self):
        """Set up the canvas with proper error handling and dynamic sizing."""
        try:
            print("DEBUG: Setting up canvas...")
            
            # Create the canvas
            self.canvas_view = Canvas(self, self)
            
            # Make sure it accepts drops
            self.canvas_view.setAcceptDrops(True)
            
            # Find and replace the original Canvas widget
            if hasattr(self, 'Canvas'):
                print("DEBUG: Found original Canvas widget")
                
                # Get the original canvas properties
                original_geometry = self.Canvas.geometry()
                original_parent = self.Canvas.parent()
                original_style = self.Canvas.styleSheet()
                
                print(f"DEBUG: Original canvas geometry: {original_geometry}")
                
                # Set the new canvas properties but with responsive sizing
                self.canvas_view.setParent(original_parent)
                self.canvas_view.setStyleSheet(original_style)
                
                # Make the canvas responsive instead of fixed size
                self.canvas_view.setGeometry(105, 1, 800, 600)  # Start with reasonable size
                
                # Hide and delete the original canvas
                self.Canvas.hide()
                self.Canvas.deleteLater()
                
                # Replace the reference
                self.Canvas = self.canvas_view
                
                # Show the new canvas
                self.canvas_view.show()
                
            else:
                print("ERROR: Canvas widget not found in UI")
                # Fallback: try to place it in the ObjectFrame
                if hasattr(self, 'ObjectFrame'):
                    self.canvas_view.setParent(self.ObjectFrame)
                    self.canvas_view.setGeometry(105, 1, 800, 600)
                    self.canvas_view.setStyleSheet("background-color: rgb(255, 255, 255);")
                    self.canvas_view.show()
                    self.Canvas = self.canvas_view
                    print("DEBUG: Canvas placed in ObjectFrame as fallback")
            
            # Create a custom status bar that only covers the canvas area
            self.setupCanvasStatusBar()
            
            # Add scene reference for compatibility
            self.scene = self.canvas_view.scene
            
            print("DEBUG: Canvas setup completed successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to setup canvas: {e}")
            import traceback
            traceback.print_exc()

    def setupCanvasStatusBar(self):
        """Create a custom status bar that only appears over the canvas area."""
        try:
            from PyQt5.QtWidgets import QLabel, QFrame
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QFont
            
            # Create a custom status label that will float over the canvas
            self.canvas_status_label = QLabel(self.canvas_view)
            
            # Style the canvas status label
            self.canvas_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(240, 240, 240, 220);
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    padding: 4px 8px;
                    color: #333333;
                    font-size: 11px;
                }
            """)
            
            # Set font
            font = QFont()
            font.setPointSize(9)
            self.canvas_status_label.setFont(font)
            
            # Set initial text
            self.canvas_status_label.setText("Ready")
            
            # Position it at the bottom of the canvas area
            self.updateCanvasStatusBarPosition()
            
            # Make it stay on top but not interfere with canvas interaction
            self.canvas_status_label.setWindowFlags(Qt.Widget)
            self.canvas_status_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            
            # Show the canvas status bar
            self.canvas_status_label.show()
            
            # Hide the main status bar or keep it for other purposes
            if hasattr(self, 'statusbar'):
                self.statusbar.hide()  # Hide the main status bar
            
            print("DEBUG: Canvas status bar created successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas status bar: {e}")
            import traceback
            traceback.print_exc()

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar."""
        if hasattr(self, 'canvas_status_label') and hasattr(self, 'canvas_view'):
            try:
                # Get canvas dimensions
                canvas_rect = self.canvas_view.geometry()
                
                # Calculate status label size
                self.canvas_status_label.adjustSize()
                label_width = self.canvas_status_label.width()
                label_height = self.canvas_status_label.height()
                
                # Position at bottom-left of canvas with some margin
                x = 10  # Left margin from canvas edge
                y = canvas_rect.height() - label_height - 10  # Bottom margin
                
                # Set the position relative to the canvas
                self.canvas_status_label.setGeometry(x, y, label_width, label_height)
                
                # Ensure it stays visible
                self.canvas_status_label.raise_()
                
            except Exception as e:
                print(f"ERROR: Failed to update canvas status bar position: {e}")

    def showCanvasStatus(self, message, timeout=0):
        """Show a status message on the canvas status bar."""
        if hasattr(self, 'canvas_status_label'):
            self.canvas_status_label.setText(message)
            self.canvas_status_label.adjustSize()
            self.updateCanvasStatusBarPosition()
            
            # If timeout is specified, clear the message after the timeout
            if timeout > 0:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(timeout, lambda: self.showCanvasStatus("Ready"))
        else:
            # Fallback to main status bar if canvas status bar doesn't exist
            if hasattr(self, 'statusbar'):
                if timeout > 0:
                    self.statusbar.showMessage(message, timeout) 
                else:
                    self.statusbar.showMessage(message)
                    
    def resizeEvent(self, event):
        """Handle window resize events to update canvas and component layout size."""
        super().resizeEvent(event)
        
        try:
            # Get the current window size
            window_size = self.size()
            
            # Resize ObjectFrame to fit the window better
            if hasattr(self, 'ObjectFrame'):
                # Make ObjectFrame fill most of the window
                new_frame_width = window_size.width() - 20
                new_frame_height = window_size.height() - 60  # Leave space for menubar and statusbar
                
                self.ObjectFrame.setGeometry(10, 0, new_frame_width, new_frame_height)
                
                # Resize component panel scroll area to fill the frame height
                if hasattr(self, 'component_scroll_area'):
                    # Calculate new height for component panel
                    component_panel_height = new_frame_height - 20  # Small margin from top/bottom
                    self.component_scroll_area.setGeometry(10, 10, 93, component_panel_height)
                    print(f"DEBUG: Component scroll area resized to height: {component_panel_height}")
                    # ADD THESE LINES
                elif hasattr(self, 'verticalLayoutWidget'):
                    component_panel_height = new_frame_height - 20
                    self.verticalLayoutWidget.setGeometry(10, 10, 93, component_panel_height)
                    print(f"DEBUG: Original layout widget resized to height: {component_panel_height}")
                    # ADD THESE LINES
            
            # Update canvas size
            if hasattr(self, 'canvas_view') and hasattr(self, 'ObjectFrame'):
                frame_rect = self.ObjectFrame.geometry()
                
                # Calculate new canvas dimensions
                component_panel_width = 105
                margin = 1
                
                new_width = max(frame_rect.width() - component_panel_width - margin, 400)
                new_height = max(frame_rect.height() - margin, 300)
                
                # Update canvas geometry
                self.canvas_view.setGeometry(component_panel_width, margin, new_width, new_height)
                
                # Update canvas status bar position after canvas resize
                self.updateCanvasStatusBarPosition()
                
                print(f"DEBUG: Window resized - Canvas: {new_width}x{new_height}, Frame: {frame_rect}")
                
                # Update status
                self.showCanvasStatus(f"Window: {window_size.width()}x{window_size.height()}, Canvas: {new_width}x{new_height}")
                
        except Exception as e:
            print(f"ERROR: Failed to resize window: {e}")

    def setupConnections(self):
        """Set up all signal connections."""
        try:
            print("DEBUG: Setting up connections...")
            
            # Connect component buttons
            button_connections = [
                (self.Host, "Host"),
                (self.STA, "STA"),
                (self.UE, "UE"),
                (self.GNB, "GNB"),
                (self.DockerHost, "DockerHost"),
                (self.AP, "AP"),
                (self.VGcore, "VGcore"),
                (self.Router, "Router"),
                (self.Switch, "Switch"),
                (self.Controller, "Controller")
            ]
            
            for button, comp_type in button_connections:
                if button:
                    button.pressed.connect(lambda checked, ct=comp_type: self.startDrag(ct))
                    print(f"DEBUG: Connected {comp_type} button")
                    # ADD THESE LINES
                else:
                    print(f"WARNING: {comp_type} button not found")
                    # ADD THESE LINES
            
            # Connect LinkCable separately
            if hasattr(self, 'LinkCable'):
                self.LinkCable.pressed.connect(lambda: self.startLinkMode("LinkCable"))
                print("DEBUG: Connected LinkCable button")
            
            # Connect toolbar actions with explicit disconnect first
            toolbar_connections = [
                (self.actionPickTool, self.enablePickTool),
                (self.actionTextBox, self.addTextBox),
                (self.actionDrawSquare, self.addDrawSquare),
                (self.actionShowGrid, self.toggleGrid),  # This is the problematic one
                (self.actionZoomIn, self.zoomIn),
                (self.actionZoomOut, self.zoomOut),
                (self.actionResetZoom, self.resetZoom),
                (self.actionDelete, self.enableDeleteTool)
            ]
            
            for action, method in toolbar_connections:
                if action:
                    action.triggered.disconnect()  # Clear any existing connections
                    action.triggered.connect(method)
                    print(f"DEBUG: Connected {action.objectName()}")
                    # ADD THESE LINES
            
            # Connect menu actions - FIXED
            menu_connections = [
                (self.actionNew, self.newTopology),
                (self.actionSave, self.saveTopology),
                (self.actionOpen, self.openTopology),
                (self.actionSave_As, self.saveTopologyAs),
                (self.actionExport_to_Level_2_Script, self.exportToMininet),
                (self.actionQuit, self.close)
            ]
            
            for action, method in menu_connections:
                if action:
                    action.triggered.connect(method)
                    print(f"DEBUG: Connected menu action {action.objectName()}")
                    # ADD THESE LINES
            
            print("DEBUG: All connections setup completed")
            
        except Exception as e:
            print(f"ERROR: Failed to setup connections: {e}")
            import traceback
            traceback.print_exc()

    def debugCanvasSetup(self):
        """Debug method to verify canvas setup."""
        print("=== CANVAS DEBUG INFO ===")
        print(f"Canvas view exists: {hasattr(self, 'canvas_view')}")
        if hasattr(self, 'canvas_view'):
            print(f"Canvas view size: {self.canvas_view.size()}")
            print(f"Canvas view geometry: {self.canvas_view.geometry()}")
            print(f"Canvas view visible: {self.canvas_view.isVisible()}")
            print(f"Canvas accepts drops: {self.canvas_view.acceptDrops()}")
            print(f"Scene exists: {hasattr(self.canvas_view, 'scene')}")
            if hasattr(self.canvas_view, 'scene'):
                print(f"Scene rect: {self.canvas_view.scene.sceneRect()}")
                print(f"Scene items count: {len(self.canvas_view.scene.items())}")
        print("=== END CANVAS DEBUG ===")

    def startDrag(self, component_type):
        """Start drag action for components with enhanced debugging."""
        print(f"DEBUG: Starting drag for component: {component_type}")
        
        # Exit link mode if active
        self.exitLinkMode()
        
        # Verify canvas exists and is ready
        if not hasattr(self, 'canvas_view'):
            print("ERROR: canvas_view not found!")
            self.showCanvasStatus("ERROR: Canvas not initialized")
            return
            
        if not self.canvas_view.acceptDrops():
            print("WARNING: Canvas does not accept drops, enabling...")
            self.canvas_view.setAcceptDrops(True)

        # Create a drag object with component information
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(component_type)  # Pass the component type as text
        drag.setMimeData(mime_data)
        
        print(f"DEBUG: Created drag with mime data: '{component_type}'")
        
        # Set a pixmap for the drag appearance
        icon_path = self.component_icon_map.get(component_type)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(20, 20))  # Set the drag hotspot to the center
            print(f"DEBUG: Set drag pixmap from {icon_path}")
        else:
            print(f"ERROR: Icon not found for {component_type} at {icon_path}")
            # Create a simple text pixmap as fallback
            fallback_pixmap = QPixmap(40, 40)
            fallback_pixmap.fill(Qt.lightGray)
            drag.setPixmap(fallback_pixmap)
        
        # Update status
        self.showCanvasStatus(f"Dragging {component_type}... Drop on canvas to place")
        
        # Execute the drag
        result = drag.exec_(Qt.CopyAction)
        print(f"DEBUG: Drag operation completed with result: {result}")
        
        # Reset status
        self.showCanvasStatus("Ready")
        
    def startLinkMode(self, component_type):
        """Activate link mode."""
        print("DEBUG: Starting link mode")
        
        # Reset any previous source selection
        self.current_link_source = None
        
        # Set current tool to link
        self.current_tool = "link"
        
        # Enable link mode in canvas
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(True)
            self.canvas_view.setCursor(Qt.CrossCursor)
        
        # Update status bar
        self.showCanvasStatus("Link mode activated. Click on source object, then destination object.")

    def createLink(self, source, destination):
        """Create a link between two objects."""
        from gui.links import NetworkLink
        
        print(f"DEBUG: Creating link between {source} and {destination}")
        
        # Create a new NetworkLink with cable visualization
        link = NetworkLink(source, destination)
        
        # Add the link to the scene
        self.canvas_view.scene.addItem(link)
        
        # Update the status bar
        source_name = getattr(source, 'object_type', getattr(source, 'component_type', 'object'))
        dest_name = getattr(destination, 'object_type', getattr(destination, 'component_type', 'object'))
        self.showCanvasStatus(f"Link created between {source_name} and {dest_name}")
        
        # Update view
        self.canvas_view.viewport().update()
        
        return link

    def exitLinkMode(self):
        """Exit link mode."""
        print("DEBUG: Exiting link mode")
        
        # Remove highlight from source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setHighlighted'):
            self.current_link_source.setHighlighted(False)
        
        # Re-enable dragging for source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setFlag'):
            from PyQt5.QtWidgets import QGraphicsItem
            self.current_link_source.setFlag(QGraphicsItem.ItemIsMovable, True)
            
        self.current_link_source = None
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(False)
            self.canvas_view.setCursor(Qt.ArrowCursor)
            
        self.showCanvasStatus("Pick tool selected")

    def updateAllLinks(self):
        """Update all links in the scene."""
        if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
            for item in self.canvas_view.scene.items():
                if isinstance(item, NetworkLink):
                    item.updatePosition()

    def enablePickTool(self):
        """Restore the pick tool state."""
        print("DEBUG: Enabling pick tool")
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "pick"
        self.selected_component = None  # Reset selected component
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setDragMode(QGraphicsView.NoDrag)
            self.canvas_view.setCursor(Qt.ArrowCursor)  # Reset to arrow cursor
            
        self.showCanvasStatus("Pick tool selected")

    def enableDeleteTool(self):
        """Enable the Delete Tool."""
        print("DEBUG: Enabling delete tool")
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "delete"
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setCursor(Qt.CrossCursor)  # Set a cross cursor for delete mode
            
        self.showCanvasStatus("Delete Tool selected. Click on items to delete them.")

    def addTextBox(self):
        self.current_tool = "text"
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.showCanvasStatus("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.current_tool = "square"
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.showCanvasStatus("Square tool selected. Click and drag to draw a square.")

    def zoomIn(self):
        """Zoom in the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.zoomIn()
            self.showCanvasStatus(f"Zoomed in (Level: {self.canvas_view.zoom_level:.1f}x)")

    def zoomOut(self):
        """Zoom out the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.zoomOut()
            self.showCanvasStatus(f"Zoomed out (Level: {self.canvas_view.zoom_level:.1f}x)")

    def resetZoom(self):
        """Reset the zoom level of the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.resetZoom()
            self.showCanvasStatus("Zoom reset to default level")
        
    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas with debouncing."""
        print(f"DEBUG: toggleGrid called, current state: {self.show_grid}")
        
        # Add a small delay to prevent double-triggering
        if hasattr(self, '_grid_toggle_timer'):
            if self._grid_toggle_timer.isActive():
                print("DEBUG: Grid toggle debounced - timer still active")
                return
        
        from PyQt5.QtCore import QTimer
        if not hasattr(self, '_grid_toggle_timer'):
            self._grid_toggle_timer = QTimer()
            self._grid_toggle_timer.setSingleShot(True)
            self._grid_toggle_timer.timeout.connect(self._performGridToggle)
        
        # Start timer with 100ms delay
        self._grid_toggle_timer.start(100)

    def _performGridToggle(self):
        """Actually perform the grid toggle after debouncing."""
        self.show_grid = not self.show_grid
        print(f"DEBUG: Grid state changed to: {self.show_grid}")
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setShowGrid(self.show_grid)
            print(f"DEBUG: Canvas setShowGrid called with: {self.show_grid}")
        
        status = "shown" if self.show_grid else "hidden"
        self.showCanvasStatus(f"Grid {status}")
        
        # Update the action's checked state to match
        if hasattr(self, 'actionShowGrid'):
            self.actionShowGrid.setChecked(self.show_grid)

    def newTopology(self):
        if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
            self.canvas_view.scene.clear()
        self.current_file = None
        self.showCanvasStatus("New topology created")
            
    def saveTopology(self):
        """Save the current topology. If no file is set, prompt for save location."""
        if self.current_file:
            # Save to existing file
            self.saveTopologyToFile(self.current_file)
        else:
            # Prompt for save location
            self.saveTopologyAs()
    
    def saveTopologyToFile(self, filename):
        """Save topology data to file."""
        try:
            import json
            
            # Extract current topology
            nodes, links = self.extractTopology()
            
            # Create topology data structure
            topology_data = {
                "version": "1.0",
                "type": "NetFlux5G_Topology",
                "metadata": {
                    "created_with": "NetFlux5G Editor",
                    "canvas_size": {
                        "width": self.canvas_view.size().width() if hasattr(self, 'canvas_view') else 1161,
                        "height": self.canvas_view.size().height() if hasattr(self, 'canvas_view') else 1151
                    }
                },
                "nodes": nodes,
                "links": links
            }
            
            # Save to JSON file
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=2)
                
            self.current_file = filename
            self.showCanvasStatus(f"Topology saved to {os.path.basename(filename)}")
            print(f"DEBUG: Topology saved successfully to {filename}")
            
        except Exception as e:
            error_msg = f"Error saving topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        
    def saveTopologyAs(self):
        """Prompt user to save topology with a new filename."""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            # Add .nf5g extension if no extension provided
            if not os.path.splitext(filename)[1]:
                filename += ".nf5g"
            self.saveTopologyToFile(filename)
            
    def openTopology(self):
        """Open a topology file."""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        """Load topology from file."""
        try:
            import json
            from gui.components import NetworkComponent
            from gui.links import NetworkLink
            
            # Clear current topology
            if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
                self.canvas_view.scene.clear()
            
            # Load topology data
            with open(filename, 'r') as f:
                topology_data = json.load(f)
            
            nodes = topology_data.get("nodes", [])
            links = topology_data.get("links", [])
            
            # Dictionary to store created components for linking
            created_components = {}
            
            # Create nodes
            for node_data in nodes:
                component_type = node_data.get("type")
                node_name = node_data.get("name")
                pos = node_data.get("pos", (0, 0))
                properties = node_data.get("properties", {})
                
                # Get icon path
                icon_path = self.component_icon_map.get(component_type)
                if icon_path and os.path.exists(icon_path):
                    # Create component
                    component = NetworkComponent(component_type, icon_path)
                    component.setPosition(pos[0], pos[1])
                    component.setProperties(properties)
                    
                    # Add to scene
                    self.canvas_view.scene.addItem(component)
                    
                    # Store for linking
                    created_components[node_name] = component
                    
                    print(f"DEBUG: Loaded {component_type} '{node_name}' at ({pos[0]}, {pos[1]})")
                    # ADD THESE LINES
                else:
                    print(f"WARNING: Could not load {component_type} - icon not found")
                    # ADD THESE LINES
            
            # Create links
            for link_data in links:
                if len(link_data) >= 2:
                    src_name, dst_name = link_data[0], link_data[1]
                    
                    if src_name in created_components and dst_name in created_components:
                        link = NetworkLink(created_components[src_name], created_components[dst_name])
                        self.canvas_view.scene.addItem(link)
                    else:
                        print(f"WARNING: Could not create link between {src_name} and {dst_name} - components not found")
                    # ADD THESE LINES
            
            # Update canvas
            self.canvas_view.scene.update()
            self.canvas_view.viewport().update()
            
            # Set current file
            self.current_file = filename
            self.showCanvasStatus(f"Loaded topology from {os.path.basename(filename)}")
            print(f"DEBUG: Topology loaded successfully from {filename}")
            
        except Exception as e:
            error_msg = f"Error loading topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        
    def exportToScript(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Level 2 Script", "", "Python Files (*.py);;All Files (*)")
        if filename:
            self.exportToScriptFile(filename)
            
    def exportToScriptFile(self, filename):
        # Implement exporting to a level 2 script
        self.statusbar.showMessage(f"Exported to script: {filename}")
    
    def togglePlacementMode(self, component_type):
        """Enable placement mode for the selected component."""
        if self.current_tool == "placement" and self.selected_component == component_type:
            # If already in placement mode for the same component, toggle off
            self.current_tool = "pick"
            self.selected_component = None
            self.statusbar.showMessage("Pick tool selected (placement mode canceled).")
        else:
            # Enable placement mode for the selected component
            self.current_tool = "placement"
            self.selected_component = component_type
            self.statusbar.showMessage(f"Placement mode enabled for {component_type}. Left-click to place. Press Esc to cancel.")

    def keyPressEvent(self, event):
        """Handle key press events with improved shortcuts."""
        
        # ESC key - return to pick tool
        if event.key() == Qt.Key_Escape:
            if self.current_tool in ["delete", "link", "placement", "text", "square"]:
                print(f"DEBUG: ESC pressed, exiting {self.current_tool} mode")
                
                # Exit link mode if we're in it
                if self.current_tool == "link":
                    self.exitLinkMode()
                
                # For all modes, switch to pick tool
                self.enablePickTool()
                
        # Zoom shortcuts
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            # + or = key for zoom in
            if hasattr(self, 'canvas_view'):
                self.canvas_view.zoomIn()
                self.statusbar.showMessage(f"Zoomed in (Level: {self.canvas_view.zoom_level:.1f}x)")
                
        elif event.key() == Qt.Key_Minus:
            # - key for zoom out
            if hasattr(self, 'canvas_view'):
                self.canvas_view.zoomOut()
                self.statusbar.showMessage(f"Zoomed out (Level: {self.canvas_view.zoom_level:.1f}x)")
                
        elif event.key() == Qt.Key_0:
            # 0 key for reset zoom
            if hasattr(self, 'canvas_view'):
                self.canvas_view.resetZoom()
                self.statusbar.showMessage("Zoom reset to default level")
                
        # Grid toggle
        elif event.key() == Qt.Key_G:
            self.toggleGrid()
            
        # Tool shortcuts
        elif event.key() == Qt.Key_P:
            # P for Pick tool
            self.enablePickTool()
            
        elif event.key() == Qt.Key_D:
            # D for Delete tool
            self.enableDeleteTool()
            
        elif event.key() == Qt.Key_L:
            # L for Link tool
            self.startLinkMode("LinkCable")
            
        elif event.key() == Qt.Key_T:
            # T for Text tool
            self.addTextBox()
            
        # File shortcuts (if not already handled by menu)
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_N:
                # Ctrl+N for New
                self.newTopology()
            elif event.key() == Qt.Key_S:
                # Ctrl+S for Save
                if self.current_file:
                    self.saveTopologyToFile(self.current_file)
                else:
                    self.saveTopologyAs()
            elif event.key() == Qt.Key_O:
                # Ctrl+O for Open
                self.openTopology()
                
        # Call parent implementation for other keys
        super().keyPressEvent(event)
        
    def extractTopology(self):
        """Extract all nodes and links from the canvas, including properties and positions."""
        nodes = []
        links = []
        for item in self.canvas_view.scene.items():
            # Nodes
            if hasattr(item, "component_type"):
                # Get updated properties including current position
                properties = item.getProperties() if hasattr(item, 'getProperties') else {}
                
                nodes.append({
                    "type": item.component_type,
                    "name": getattr(item, "display_name", item.component_type),
                    "pos": (item.pos().x(), item.pos().y()),
                    "properties": properties
                })
            # Links
            elif isinstance(item, NetworkLink):
                src = getattr(item.source_node, "display_name", None)
                dst = getattr(item.dest_node, "display_name", None)
                if src and dst:
                    links.append((src, dst))
        return nodes, links

    def exportToMininetScript(self, filename):
        """Export the current topology to a Mininet Python script with component configurations."""
        nodes, links = self.extractTopology()
        with open(filename, "w") as f:
            f.write("#!/usr/bin/env python\n")
            f.write('"""\n')
            f.write("NetFlux5G Generated Mininet Script\n")
            f.write("Generated topology with component configurations\n")
            f.write('"""\n\n')
            f.write("from mininet.net import Mininet\n")
            f.write("from mininet.node import Controller, OVSKernelSwitch, Host\n")
            f.write("from mininet.link import TCLink\n")
            f.write("from mininet.cli import CLI\n")
            f.write("from mininet.log import setLogLevel\n")
            f.write("import os\n\n")
            
            f.write("def customTopo():\n")
            f.write('    """Create a custom topology with NetFlux5G configurations"""\n')
            f.write("    net = Mininet(controller=Controller, switch=OVSKernelSwitch, link=TCLink)\n\n")
            
            # Add controller if present
            controllers = [node for node in nodes if node["type"] == "Controller"]
            if controllers:
                f.write("    # Add controllers\n")
                for node in controllers:
                    var_name = self.sanitizeVariableName(node['name'])
                    pos_x, pos_y = node["pos"]
                    properties = node.get("properties", {})
                    
                    f.write(f"    # {node['name']} - Position: ({pos_x:.1f}, {pos_y:.1f})\n")
                    
                    # Controller configuration
                    ip = properties.get("Controller_IPAddress", "127.0.0.1")
                    port = properties.get("Controller_Port", "6633")
                    f.write(f"    {var_name} = net.addController('{node['name']}', ip='{ip}', port={port})\n")
                f.write("\n")
            
            # Add hosts with detailed configurations
            f.write("    # Add hosts with configurations\n")
            for node in nodes:
                if node["type"] in ["Host", "STA", "UE", "DockerHost"]:
                    var_name = self.sanitizeVariableName(node['name'])
                    pos_x, pos_y = node["pos"]
                    properties = node.get("properties", {})
                    
                    f.write(f"    # {node['name']} - Position: ({pos_x:.1f}, {pos_y:.1f})\n")
                    
                    # Build host options based on component type and properties
                    opts = []
                    
                    # Common host properties
                    if properties.get("STA_IPAddress") or properties.get("Host_IPAddress"):
                        ip = properties.get("STA_IPAddress") or properties.get("Host_IPAddress")
                        if ip and ip.strip():
                            opts.append(f"ip='{ip}'")
                    
                    # Default route
                    if properties.get("STA_DefaultRoute") or properties.get("Host_DefaultRoute"):
                        route = properties.get("STA_DefaultRoute") or properties.get("Host_DefaultRoute")
                        if route and route.strip():
                            opts.append(f"defaultRoute='via {route}'")
                    
                    # CPU configuration
                    if properties.get("STA_AmountCPU") or properties.get("Host_AmountCPU"):
                        cpu = properties.get("STA_AmountCPU") or properties.get("Host_AmountCPU")
                        if cpu and cpu.strip():
                            opts.append(f"cpu={cpu}")
                    
                    # Memory configuration
                    if properties.get("STA_Memory") or properties.get("Host_Memory"):
                        memory = properties.get("STA_Memory") or properties.get("Host_Memory")
                        if memory and memory.strip():
                            opts.append(f"mem='{memory}m'")
                    
                    # Docker-specific configurations
                    if node["type"] == "DockerHost":
                        if properties.get("DockerHost_ContainerImage"):
                            image = properties.get("DockerHost_ContainerImage")
                            opts.append(f"image='{image}'")
                        if properties.get("DockerHost_PortForward"):
                            ports = properties.get("DockerHost_PortForward")
                            opts.append(f"ports=['{ports}']")
                    
                    opts_str = ", " + ", ".join(opts) if opts else ""
                    f.write(f"    {var_name} = net.addHost('{node['name']}'{opts_str})\n")
                    
                    # Add post-configuration commands
                    self.writeHostPostConfig(f, var_name, node, properties)
                    f.write("\n")
            
            # Add switches and APs
            f.write("    # Add switches and access points\n")
            for node in nodes:
                if node["type"] in ["Switch", "Router", "AP"]:
                    var_name = self.sanitizeVariableName(node['name'])
                    pos_x, pos_y = node["pos"]
                    properties = node.get("properties", {})
                    
                    f.write(f"    # {node['name']} - Position: ({pos_x:.1f}, {pos_y:.1f})\n")
                    
                    if node["type"] == "AP":
                        # Access Point configuration
                        opts = []
                        if properties.get("AP_SSID"):
                            opts.append(f"ssid='{properties['AP_SSID']}'")
                        if properties.get("AP_Channel"):
                            opts.append(f"channel={properties['AP_Channel']}")
                        if properties.get("AP_Mode"):
                            opts.append(f"mode='{properties['AP_Mode']}'")
                        
                        opts_str = ", " + ", ".join(opts) if opts else ""
                        f.write(f"    {var_name} = net.addAccessPoint('{node['name']}'{opts_str})\n")
                    else:
                        # Regular switch
                        opts = []
                        if properties.get("Switch_DPID") or properties.get("Router_DPID"):
                            dpid = properties.get("Switch_DPID") or properties.get("Router_DPID")
                            if dpid:
                                opts.append(f"dpid='{dpid}'")
                        
                        opts_str = ", " + ", ".join(opts) if opts else ""
                        f.write(f"    {var_name} = net.addSwitch('{node['name']}'{opts_str})\n")
                    f.write("\n")
            
            # Add 5G components as special hosts
            f.write("    # Add 5G network components\n")
            for node in nodes:
                if node["type"] in ["GNB", "VGcore", "UE"]:
                    var_name = self.sanitizeVariableName(node['name'])
                    pos_x, pos_y = node["pos"]
                    properties = node.get("properties", {})
                    
                    f.write(f"    # {node['name']} - Position: ({pos_x:.1f}, {pos_y:.1f})\n")
                    f.write(f"    # 5G Component: {node['type']}\n")
                    
                    opts = ["cls=Host"]  # 5G components are special hosts
                    
                    # Add 5G specific configurations as comments for manual implementation
                    if node["type"] == "GNB":
                        f.write(f"    # GNB Configuration:\n")
                        if properties.get("GNB_AMFHostName"):
                            f.write(f"    #   AMF Hostname: {properties['GNB_AMFHostName']}\n")
                        if properties.get("GNB_TAC"):
                            f.write(f"    #   TAC: {properties['GNB_TAC']}\n")
                        if properties.get("GNB_MCC"):
                            f.write(f"    #   MCC: {properties['GNB_MCC']}\n")
                        if properties.get("GNB_MNC"):
                            f.write(f"    #   MNC: {properties['GNB_MNC']}\n")
                    
                    elif node["type"] == "UE":
                        f.write(f"    # UE Configuration:\n")
                        if properties.get("UE_GNBHostName"):
                            f.write(f"    #   GNB Hostname: {properties['UE_GNBHostName']}\n")
                        if properties.get("UE_APN"):
                            f.write(f"    #   APN: {properties['UE_APN']}\n")
                        if properties.get("UE_MSISDN"):
                            f.write(f"    #   MSISDN: {properties['UE_MSISDN']}\n")
                    
                    opts_str = ", " + ", ".join(opts)
                    f.write(f"    {var_name} = net.addHost('{node['name']}'{opts_str})\n")
                    f.write("\n")
            
            # Add links with configurations
            f.write("    # Add links with configurations\n")
            for src, dst in links:
                src_var = self.sanitizeVariableName(src)
                dst_var = self.sanitizeVariableName(dst)
                f.write(f"    net.addLink({src_var}, {dst_var}, cls=TCLink)\n")
            
            f.write("\n    # Start the network\n")
            f.write("    net.start()\n")
            f.write("\n    # Configure wireless if needed\n")
            f.write("    # net.plotGraph(max_x=1000, max_y=1000)\n")
            f.write("\n    # Start CLI\n")
            f.write("    CLI(net)\n")
            f.write("\n    # Stop the network\n")
            f.write("    net.stop()\n\n")
            
            f.write("if __name__ == '__main__':\n")
            f.write("    setLogLevel('info')\n")
            f.write("    customTopo()\n")
            
        self.statusbar.showMessage(f"Exported topology with configurations to {filename}")

    def sanitizeVariableName(self, name):
        """Convert component name to valid Python variable name."""
        # Replace spaces and special characters with underscores
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())

    def writeHostPostConfig(self, file, var_name, node, properties):
        """Write post-configuration commands for hosts."""
        commands = []
        
        # Start commands
        if properties.get("STA_StartCommand") or properties.get("Host_StartCommand"):
            cmd = properties.get("STA_StartCommand") or properties.get("Host_StartCommand")
            if cmd and cmd.strip():
                commands.append(f"    {var_name}.cmd('{cmd}')")
        
        # Network interface configurations
        if properties.get("STA_IPAddress") or properties.get("Host_IPAddress"):
            ip = properties.get("STA_IPAddress") or properties.get("Host_IPAddress")
            if ip and ip.strip() and "/" not in ip:  # Add subnet if not present
                commands.append(f"    {var_name}.cmd('ifconfig {var_name}-eth0 {ip}/24')")
        
        # Authentication for wireless
        if node["type"] == "STA" and properties.get("STA_AuthenticationType"):
            auth_type = properties.get("STA_AuthenticationType")
            if auth_type and auth_type != "none":
                commands.append(f"    # Wireless authentication: {auth_type}")
                if properties.get("STA_Username"):
                    commands.append(f"    # Username: {properties['STA_Username']}")
                if properties.get("STA_Password"):
                    commands.append(f"    # Password: [configured]")
        
        if commands:
            file.write("\n    # Post-configuration for " + node['name'] + "\n")
            for cmd in commands:
                file.write(cmd + "\n")

    def printTopologyPositions(self):
        """Debug method to print all component positions."""
        print("=== Current Topology Positions ===")
        for item in self.canvas_view.scene.items():
            if hasattr(item, "component_type"):
                pos = item.pos()
                properties = item.getProperties() if hasattr(item, 'getProperties') else {}
                print(f"{item.display_name}: Canvas({pos.x():.1f}, {pos.y():.1f}) Properties({properties.get('x', 'N/A')}, {properties.get('y', 'N/A')})")
        print("=== End Topology Positions ===")

    def exportToMininet(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Mininet Script", "", "Python Files (*.py);;All Files (*)")
        if filename:
            self.exportToMininetScript(filename)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application-wide icon
    icon_path = os.path.join(os.path.dirname(__file__), "gui", "Icon", "logoSquare.png")
    app.setWindowIcon(QIcon(icon_path))

    window = NetFlux5GApp()
    window.show()
    
    # Debug window after showing
    print("=== WINDOW SHOWN DEBUG ===")
    window.debugCanvasSetup()
    print("=== END WINDOW DEBUG ===")
    
    sys.exit(app.exec_())