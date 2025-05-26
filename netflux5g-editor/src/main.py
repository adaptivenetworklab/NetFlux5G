import sys
import os
import json
import re
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton, QDesktopWidget, QFileDialog
from PyQt5.QtCore import Qt, QPoint, QMimeData, QTimer
from PyQt5.QtGui import QDrag, QPixmap, QIcon, QFont
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

        # Get screen geometry for better initial sizing
        screen = QDesktopWidget().screenGeometry()
        
        # Set initial size to 80% of screen size
        initial_width = int(screen.width() * 0.8)
        initial_height = int(screen.height() * 0.8)
        self.resize(initial_width, initial_height)
        
        # Set window properties for better responsiveness
        self.setMinimumSize(1000, 700)
        
        # Center the window on the screen
        self.move(
            (screen.width() - initial_width) // 2,
            (screen.height() - initial_height) // 2
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
        
        # Initialize attributes
        self.current_link_source = None
        self.current_file = None
        self.current_tool = "pick"
        self.selected_component = None
        
        # Setup all connections
        self.setupConnections()
        
        # Status message
        self.statusbar.showMessage("Ready - Dynamic canvas sizing enabled")
        
        # Show helpful shortcut information
        self.showShortcutHelp()
        
        # Debug canvas setup
        self.debugCanvasSetup()
        
        # Force initial geometry update
        QTimer.singleShot(100, self.updateCanvasGeometry)

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
            
            # Set parent to centralwidget instead of trying to replace existing Canvas
            self.canvas_view.setParent(self.centralwidget)
            self.canvas_view.setObjectName("CanvasView")
            
            # Set initial size and position
            self.updateCanvasGeometry()
            
            # Ensure canvas is visible
            self.canvas_view.setVisible(True)
            self.canvas_view.show()
            
            # Create a custom status bar that only covers the canvas area
            self.setupCanvasStatusBar()
            
            # Add scene reference for compatibility
            self.scene = self.canvas_view.scene
            
            # Set focus policy so canvas can receive keyboard events
            self.canvas_view.setFocusPolicy(Qt.StrongFocus)
            
            print("DEBUG: Canvas setup completed successfully")
            print(f"DEBUG: Canvas geometry after setup: {self.canvas_view.geometry()}")
            print(f"DEBUG: Canvas parent: {self.canvas_view.parent()}")
            print(f"DEBUG: Canvas visible: {self.canvas_view.isVisible()}")
            
        except Exception as e:
            print(f"ERROR: Failed to setup canvas: {e}")
            traceback.print_exc()

    def updateCanvasGeometry(self):
        """Update canvas geometry based on current window size and ObjectFrame position."""
        try:
            if not hasattr(self, 'canvas_view'):
                return
                
            # Get current window size
            window_size = self.size()
            
            # Get ObjectFrame actual width from the UI
            object_frame_width = 115  # Fixed width from the UI file
            
            # Account for menubar, toolbar, and statusbar heights
            menubar_height = self.menubar.height() if hasattr(self, 'menubar') else 26
            toolbar_height = self.toolBar.height() if hasattr(self, 'toolBar') else 30
            statusbar_height = self.statusbar.height() if hasattr(self, 'statusbar') else 23
            
            # Calculate available space (be more conservative with padding)
            available_width = window_size.width() - object_frame_width - 10  # 10px total padding
            available_height = window_size.height() - menubar_height - toolbar_height - statusbar_height - 10  # 10px total padding
            
            # Ensure minimum size
            available_width = max(available_width, 400)
            available_height = max(available_height, 300)
            
            # Set canvas geometry - position it right after the ObjectFrame
            canvas_x = object_frame_width + 5  # 5px offset from ObjectFrame
            canvas_y = 5  # 5px offset from top
            
            # Set the geometry
            self.canvas_view.setGeometry(canvas_x, canvas_y, available_width, available_height)
            
            # Ensure canvas is visible and properly configured
            self.canvas_view.setVisible(True)
            self.canvas_view.show()
            
            # Update the scene to match the new canvas size
            if hasattr(self.canvas_view, 'updateSceneSize'):
                self.canvas_view.updateSceneSize()
            
            print(f"DEBUG: Canvas geometry updated - x:{canvas_x}, y:{canvas_y}, w:{available_width}, h:{available_height}")
            print(f"DEBUG: Canvas visible: {self.canvas_view.isVisible()}")
            print(f"DEBUG: Canvas accepts drops: {self.canvas_view.acceptDrops()}")
            
        except Exception as e:
            print(f"ERROR: Failed to update canvas geometry: {e}")
            traceback.print_exc()

    def setupCanvasStatusBar(self):
        """Create a custom status bar that only appears over the canvas area."""
        try:
            from PyQt5.QtWidgets import QLabel
            
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
            
            print("DEBUG: Canvas status bar created successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas status bar: {e}")
            traceback.print_exc()

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar."""
        if hasattr(self, 'canvas_status_label') and hasattr(self, 'canvas_view'):
            try:
                canvas_rect = self.canvas_view.geometry()
                label_width = self.canvas_status_label.sizeHint().width()
                
                # Position relative to canvas
                x = (canvas_rect.width() - label_width) // 2
                y = canvas_rect.height() - 35  # 35px from bottom
                
                # Ensure label stays within canvas bounds
                if x < 10:
                    x = 10
                if x + label_width > canvas_rect.width() - 10:
                    x = canvas_rect.width() - label_width - 10
                    
                self.canvas_status_label.move(x, y)
                
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
                QTimer.singleShot(timeout, lambda: self.canvas_status_label.setText("Ready"))
        else:
            # Fallback to main status bar if canvas status bar doesn't exist
            if hasattr(self, 'statusbar'):
                self.statusbar.showMessage(message, timeout)
                    
    def resizeEvent(self, event):
        """Handle window resize events to update canvas and component layout size."""
        super().resizeEvent(event)
        
        try:
            # Get the current window size
            window_size = self.size()
            
            # Update ObjectFrame to be fixed width but full height
            if hasattr(self, 'ObjectFrame'):
                # Keep ObjectFrame at fixed width but adjust height
                self.ObjectFrame.setGeometry(0, 0, 115, window_size.height())
            
            # Update canvas size dynamically
            self.updateCanvasGeometry()
            
            # Update canvas status bar position
            self.updateCanvasStatusBarPosition()
            
            print(f"DEBUG: Window resized to {window_size.width()}x{window_size.height()}")
            
            # Force canvas to update and redraw
            if hasattr(self, 'canvas_view'):
                self.canvas_view.update()
                self.canvas_view.viewport().update()
            
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
                button.clicked.connect(lambda checked, ct=comp_type: self.startDrag(ct))
            
            # Connect LinkCable separately
            if hasattr(self, 'LinkCable'):
                self.LinkCable.clicked.connect(lambda: self.startLinkMode("LinkCable"))
            
            # Connect toolbar actions with explicit disconnect first
            toolbar_connections = [
                (self.actionPickTool, self.enablePickTool),
                (self.actionTextBox, self.addTextBox),
                (self.actionDrawSquare, self.addDrawSquare),
                (self.actionShowGrid, self.toggleGrid),
                (self.actionZoomIn, self.zoomIn),
                (self.actionZoomOut, self.zoomOut),
                (self.actionResetZoom, self.resetZoom),
                (self.actionDelete, self.enableDeleteTool)
            ]
            
            for action, method in toolbar_connections:
                action.triggered.connect(method)
            
            # Connect menu actions
            menu_connections = [
                (self.actionNew, self.newTopology),
                (self.actionSave, self.saveTopology),
                (self.actionOpen, self.openTopology),
                (self.actionSave_As, self.saveTopologyAs),
                (self.actionExport_to_Level_2_Script, self.exportToMininet),
                (self.actionQuit, self.close)
            ]
            
            for action, method in menu_connections:
                action.triggered.connect(method)
            
            print("DEBUG: All connections setup completed")
            
        except Exception as e:
            print(f"ERROR: Failed to setup connections: {e}")
            traceback.print_exc()

    def debugCanvasSetup(self):
        """Debug method to verify canvas setup."""
        print("=== CANVAS DEBUG INFO ===")
        print(f"Canvas view exists: {hasattr(self, 'canvas_view')}")
        if hasattr(self, 'canvas_view'):
            print(f"Canvas view size: {self.canvas_view.size()}")
            print(f"Canvas view geometry: {self.canvas_view.geometry()}")
            print(f"Canvas view visible: {self.canvas_view.isVisible()}")
            print(f"Canvas view parent: {self.canvas_view.parent()}")
            print(f"Canvas accepts drops: {self.canvas_view.acceptDrops()}")
            print(f"Canvas viewport size: {self.canvas_view.viewport().size()}")
            print(f"Scene exists: {hasattr(self.canvas_view, 'scene')}")
            if hasattr(self.canvas_view, 'scene'):
                print(f"Scene rect: {self.canvas_view.scene.sceneRect()}")
                print(f"Scene items count: {len(self.canvas_view.scene.items())}")
            
            # Check if ObjectFrame overlaps with canvas
            if hasattr(self, 'ObjectFrame'):
                obj_frame_geom = self.ObjectFrame.geometry()
                canvas_geom = self.canvas_view.geometry()
                print(f"ObjectFrame geometry: {obj_frame_geom}")
                print(f"Canvas geometry: {canvas_geom}")
                overlap = obj_frame_geom.intersects(canvas_geom)
                print(f"ObjectFrame and Canvas overlap: {overlap}")
                
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
                return
        
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
            traceback.print_exc()
        
    def saveTopologyAs(self):
        """Prompt user to save topology with a new filename."""
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
            from gui.components import NetworkComponent
            
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
                component_type = node_data["type"]
                icon_path = self.component_icon_map.get(component_type)
                if icon_path and os.path.exists(icon_path):
                    component = NetworkComponent(component_type, icon_path)
                    component.setPosition(node_data["x"], node_data["y"])
                    component.setProperties(node_data.get("properties", {}))
                    self.canvas_view.scene.addItem(component)
                    created_components[node_data["id"]] = component
            
            # Create links
            for link_data in links:
                source_id = link_data["source"]
                dest_id = link_data["destination"]
                if source_id in created_components and dest_id in created_components:
                    source = created_components[source_id]
                    dest = created_components[dest_id]
                    link = NetworkLink(source, dest)
                    self.canvas_view.scene.addItem(link)
            
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
            traceback.print_exc()
    
    def keyPressEvent(self, event):
        """Handle key press events with improved shortcuts."""
        
        # ESC key - return to pick tool
        if event.key() == Qt.Key_Escape:
            if self.current_tool in ["delete", "link", "placement", "text", "square"]:
                self.enablePickTool()
                
        # Zoom shortcuts
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            # + or = key for zoom in
            if hasattr(self, 'canvas_view'):
                self.zoomIn()
                
        elif event.key() == Qt.Key_Minus:
            # - key for zoom out
            if hasattr(self, 'canvas_view'):
                self.zoomOut()
                
        elif event.key() == Qt.Key_0:
            # 0 key for reset zoom
            if hasattr(self, 'canvas_view'):
                self.resetZoom()
                
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
                self.newTopology()
            elif event.key() == Qt.Key_S:
                self.saveTopology()
            elif event.key() == Qt.Key_O:
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
                node_data = {
                    "id": str(id(item)),
                    "type": item.component_type,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "properties": item.getProperties()
                }
                nodes.append(node_data)
                
            elif isinstance(item, NetworkLink):
                link_data = {
                    "source": str(id(item.source_node)),
                    "destination": str(id(item.dest_node)),
                    "type": "ethernet"
                }
                links.append(link_data)
                
        return nodes, links

    def exportToMininet(self):
        """Export the current topology to a Mininet script."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Export to Mininet Script", 
            "", 
            "Python Files (*.py);;All Files (*)"
        )
        if filename:
            self.exportToMininetScript(filename)

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
                f.write("    # Add controller\n")
                for node in controllers:
                    var_name = self.sanitizeVariableName(node["properties"].get("name", "controller"))
                    f.write(f"    {var_name} = net.addController('{var_name}')\n")
                f.write("\n")
            
            # Add hosts with detailed configurations
            f.write("    # Add hosts with configurations\n")
            for node in nodes:
                if node["type"] in ["Host", "STA", "UE"]:
                    var_name = self.sanitizeVariableName(node["properties"].get("name", node["type"]))
                    f.write(f"    {var_name} = net.addHost('{var_name}')\n")
            f.write("\n")
            
            # Add switches and APs
            f.write("    # Add switches and access points\n")
            for node in nodes:
                if node["type"] in ["Switch", "AP"]:
                    var_name = self.sanitizeVariableName(node["properties"].get("name", node["type"]))
                    f.write(f"    {var_name} = net.addSwitch('{var_name}')\n")
            f.write("\n")
            
            # Add 5G components as special hosts
            f.write("    # Add 5G network components\n")
            for node in nodes:
                if node["type"] in ["GNB", "VGcore"]:
                    var_name = self.sanitizeVariableName(node["properties"].get("name", node["type"]))
                    f.write(f"    {var_name} = net.addHost('{var_name}')  # 5G {node['type']}\n")
            f.write("\n")
            
            # Add links with configurations
            f.write("    # Add links with configurations\n")
            link_count = 0
            for link_data in links:
                link_count += 1
                f.write(f"    # Link {link_count}\n")
                f.write(f"    net.addLink(source, dest)  # Configure based on topology\n")
            f.write("\n")
            
            f.write("    # Start the network\n")
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
            
        self.showCanvasStatus(f"Exported topology to {os.path.basename(filename)}")

    def sanitizeVariableName(self, name):
        """Convert component name to valid Python variable name."""
        # Replace spaces and special characters with underscores
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())

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