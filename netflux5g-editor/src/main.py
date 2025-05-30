from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton, QDesktopWidget, QFileDialog, QFrame
from PyQt5.QtCore import Qt, QPoint, QMimeData, QTimer, QDateTime
from PyQt5.QtGui import QDrag, QPixmap, QIcon, QFont
from PyQt5 import uic
import os
import sys
import json
import traceback
import re
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from gui.links import NetworkLink
from gui.compose_export import DockerComposeExporter
from gui.mininet_export import MininetExporter

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
        
        # Initialize exporters
        self.docker_compose_exporter = DockerComposeExporter(self)
        self.mininet_exporter = MininetExporter(self)
        
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

        # Debug menu actions
        self.debugMenuActions()

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

            window_size = self.size()

            # Get ObjectFrame width from the actual widget
            object_frame_width = self.ObjectFrame.width() if hasattr(self, 'ObjectFrame') else 71

            menubar_height = self.menubar.height() if hasattr(self, 'menubar') else 26
            toolbar_height = self.toolBar.height() if hasattr(self, 'toolBar') else 30
            statusbar_height = self.statusbar.height() if hasattr(self, 'statusbar') else 23

            available_width = window_size.width() - object_frame_width - 10
            available_height = window_size.height() - menubar_height - toolbar_height - statusbar_height - 10

            available_width = max(available_width, 400)
            available_height = max(available_height, 300)

            canvas_x = object_frame_width + 5
            canvas_y = 5

            self.canvas_view.setGeometry(canvas_x, canvas_y, available_width, available_height)
            self.canvas_view.setVisible(True)
            self.canvas_view.show()

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
            self.canvas_status_label = QLabel(self.centralwidget)  # Parent to centralwidget instead of canvas_view
            
            # Style the canvas status label with better appearance
            self.canvas_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(50, 50, 50, 200);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 100);
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            
            # Set font
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            self.canvas_status_label.setFont(font)
            
            # Set initial text and size
            self.canvas_status_label.setText("Ready")
            self.canvas_status_label.adjustSize()
            
            # Position it at the bottom-center of the canvas area
            self.updateCanvasStatusBarPosition()
            
            # Make it stay on top but not interfere with canvas interaction
            self.canvas_status_label.setWindowFlags(Qt.Widget)
            self.canvas_status_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Allow clicks to pass through
            
            # Show the canvas status bar
            self.canvas_status_label.show()
            self.canvas_status_label.raise_()  # Bring to front
            
            print("DEBUG: Canvas status bar created successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to create canvas status bar: {e}")
            import traceback
            traceback.print_exc()

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar."""
        if hasattr(self, 'canvas_status_label') and hasattr(self, 'canvas_view'):
            try:
                canvas_rect = self.canvas_view.geometry()
                label_width = self.canvas_status_label.width()
                label_height = self.canvas_status_label.height()
                
                # Position at bottom-center of canvas, slightly up from the bottom
                center_x = canvas_rect.x() + (canvas_rect.width() - label_width) // 2
                bottom_y = canvas_rect.y() + canvas_rect.height() - label_height - 30  # 30px up from bottom
                
                self.canvas_status_label.move(center_x, bottom_y)
                
                print(f"DEBUG: Status bar positioned at ({center_x}, {bottom_y})")
                print(f"DEBUG: Canvas rect: {canvas_rect}")
                print(f"DEBUG: Label size: {label_width}x{label_height}")
                
            except Exception as e:
                print(f"ERROR: Failed to update canvas status bar position: {e}")

    def showCanvasStatus(self, message, timeout=0):
        """Show a status message on the canvas status bar."""
        if hasattr(self, 'canvas_status_label'):
            self.canvas_status_label.setText(message)
            self.canvas_status_label.adjustSize()  # Resize label to fit content
            self.updateCanvasStatusBarPosition()   # Reposition after resizing
            
            # Ensure the label is visible
            self.canvas_status_label.show()
            self.canvas_status_label.raise_()  # Bring to front
            
            # If timeout is specified, clear the message after the timeout
            if timeout > 0:
                QTimer.singleShot(timeout, lambda: self.showCanvasStatus("Ready"))
        else:
            print(f"DEBUG: Canvas status message: {message}") 
                    
    def resizeEvent(self, event):
        """Handle window resize events to update canvas and component layout size."""
        super().resizeEvent(event)
        try:
            window_size = self.size()
            # Update ObjectFrame to be fixed width but full height
            if hasattr(self, 'ObjectFrame'):
                self.ObjectFrame.setGeometry(0, 0, 71, window_size.height() - 26 - 30 - 23)  # Account for menu, toolbar, status
            
            self.updateCanvasGeometry()
            
            # Update status bar position after canvas geometry changes
            QTimer.singleShot(100, self.updateCanvasStatusBarPosition)  # Small delay to ensure canvas is positioned
            
            print(f"DEBUG: Window resized to {window_size.width()}x{window_size.height()}")
            if hasattr(self, 'canvas_view'):
                print(f"DEBUG: Canvas size after resize: {self.canvas_view.size()}")
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
                button.clicked.connect(lambda checked, t=comp_type: self.startDrag(t))
            
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
                action.triggered.disconnect()
                action.triggered.connect(method)
            
            # Connect menu actions - use the new exporter methods
            menu_connections = [
                ('actionNew', self.newTopology),
                ('actionSave', self.saveTopology),
                ('actionOpen', self.openTopology),
                ('actionSave_As', self.saveTopologyAs),
                ('actionExport_to_Level_2_Script', self.exportToMininet),
                ('actionExport_to_Docker_Compose', self.exportToDockerCompose),
                ('actionQuit', self.close)
            ]
            
            for action_name, method in menu_connections:
                if hasattr(self, action_name):
                    action = getattr(self, action_name)
                    action.triggered.disconnect()
                    action.triggered.connect(method)
            
            # Add export to docker-compose action if it doesn't exist
            if not hasattr(self, 'actionExport_to_Docker_Compose'):
                print("WARNING: actionExport_to_Docker_Compose not found in UI")
            
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
                    "created_date": QDateTime.currentDateTime().toString(),
                    "canvas_size": {
                        "width": self.canvas_view.size().width() if hasattr(self, 'canvas_view') else 1161,
                        "height": self.canvas_view.size().height() if hasattr(self, 'canvas_view') else 1151
                    }
                },
                "nodes": nodes,
                "links": links
            }
            
            # Save to JSON file
            import json
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=2, ensure_ascii=False)
                
            self.current_file = filename
            self.showCanvasStatus(f"Topology saved to {os.path.basename(filename)}")
            print(f"DEBUG: Topology saved successfully to {filename}")
            print(f"DEBUG: Saved {len(nodes)} nodes and {len(links)} links")
            
        except Exception as e:
            error_msg = f"Error saving topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
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
            import json
            
            with open(filename, 'r') as f:
                topology_data = json.load(f)
            
            # Validate the file format
            if not isinstance(topology_data, dict) or 'nodes' not in topology_data:
                raise ValueError("Invalid topology file format")
            
            # Clear current canvas
            if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
                self.canvas_view.scene.clear()
            
            # Load nodes
            nodes = topology_data.get('nodes', [])
            node_map = {}  # Map to store created components for linking
            
            for node_data in nodes:
                component = self.createComponentFromData(node_data)
                if component:
                    node_map[node_data['name']] = component
            
            # Load links
            links = topology_data.get('links', [])
            for link_data in links:
                self.createLinkFromData(link_data, node_map)
            
            # Update canvas
            if hasattr(self, 'canvas_view'):
                self.canvas_view.scene.update()
                self.canvas_view.viewport().update()
            
            # Set current file
            self.current_file = filename
            
            self.showCanvasStatus(f"Topology loaded: {len(nodes)} components, {len(links)} links")
            print(f"DEBUG: Topology loaded successfully from {filename}")
            
        except Exception as e:
            error_msg = f"Error loading topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def createComponentFromData(self, node_data):
        """Create a component from saved node data."""
        try:
            component_type = node_data.get('type')
            name = node_data.get('name')
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            properties = node_data.get('properties', {})
            
            # Get the icon path for this component type
            icon_path = self.component_icon_map.get(component_type)
            if not icon_path or not os.path.exists(icon_path):
                print(f"WARNING: Icon not found for {component_type}")
                return None
            
            # Create the component
            from .gui.components import NetworkComponent
            component = NetworkComponent(component_type, icon_path)
            
            # Set position
            component.setPosition(x, y)
            
            # Set display name
            component.display_name = name
            
            # Set properties (this will include all 5G configurations)
            component.setProperties(properties)
            
            # Add to scene
            self.canvas_view.scene.addItem(component)
            
            print(f"DEBUG: Created component {name} of type {component_type} at ({x}, {y})")
            return component
            
        except Exception as e:
            print(f"ERROR: Failed to create component from data: {e}")
            return None

    def createLinkFromData(self, link_data, node_map):
        """Create a link from saved link data."""
        try:
            source_name = link_data.get('source')
            dest_name = link_data.get('destination')
            link_type = link_data.get('type', 'ethernet')
            properties = link_data.get('properties', {})
            
            # Find source and destination components
            source_component = node_map.get(source_name)
            dest_component = node_map.get(dest_name)
            
            if not source_component or not dest_component:
                print(f"WARNING: Could not find components for link {source_name} -> {dest_name}")
                return None
            
            # Create the link
            from gui.links import NetworkLink
            link = NetworkLink(source_component, dest_component)
            link.link_type = link_type
            link.properties = properties
            
            # Add to scene
            self.canvas_view.scene.addItem(link)
            
            print(f"DEBUG: Created link from {source_name} to {dest_name}")
            return link
            
        except Exception as e:
            print(f"ERROR: Failed to create link from data: {e}")
            return None

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

    def exportToDockerCompose(self):
        """Export 5G Core components to docker-compose.yaml and configuration files."""
        self.docker_compose_exporter.export_to_docker_compose()

    def exportToMininet(self):
        """Export the current topology to a Mininet script."""
        self.mininet_exporter.export_to_mininet()

    def extractTopology(self):
        """Extract all nodes and links from the canvas, including properties and positions."""
        nodes = []
        links = []
        
        if not hasattr(self, 'canvas_view') or not hasattr(self.canvas_view, 'scene'):
            return nodes, links
        
        for item in self.canvas_view.scene.items():
            if hasattr(item, 'component_type'):  # NetworkComponent
                # Extract component information including properties
                node_data = {
                    'name': getattr(item, 'display_name', item.component_type),
                    'type': item.component_type,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'properties': item.getProperties() if hasattr(item, 'getProperties') else {}
                }
                nodes.append(node_data)
                
            elif isinstance(item, NetworkLink):  # NetworkLink
                # Extract link information
                source_name = getattr(item.source_node, 'display_name', 
                                    getattr(item.source_node, 'component_type', 'Unknown'))
                dest_name = getattr(item.dest_node, 'display_name', 
                                  getattr(item.dest_node, 'component_type', 'Unknown'))
                
                link_data = {
                    'source': source_name,
                    'destination': dest_name,
                    'type': getattr(item, 'link_type', 'ethernet')
                }
                links.append(link_data)
        
        print(f"DEBUG: Total extracted - {len(nodes)} nodes, {len(links)} links")
        return nodes, links
    
    def debugMenuActions(self):
        """Debug method to check available menu actions."""
        print("=== DEBUG: Menu Actions ===")
        
        # Check if File menu exists
        if hasattr(self, 'menuFile'):
            print(f"menuFile found: {self.menuFile}")
            print("Actions in File menu:")
            for action in self.menuFile.actions():
                print(f"  - {action.objectName()}: {action.text()}")
        
        # Check specific actions
        menu_actions = ['actionNew', 'actionSave', 'actionOpen', 'actionSave_As', 'actionQuit']
        for action_name in menu_actions:
            if hasattr(self, action_name):
                action = getattr(self, action_name)
                print(f"{action_name}: Found - {action.text()}")
            else:
                print(f"{action_name}: NOT FOUND")
        
        print("=== END DEBUG ===")

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