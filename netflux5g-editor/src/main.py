import os
import sys
import json
import re
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton, QDesktopWidget, QFileDialog, QFrame
from PyQt5.QtCore import Qt, QPoint, QMimeData, QTimer
from PyQt5.QtGui import QDrag, QPixmap, QIcon, QFont
from PyQt5 import uic
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from gui.links import NetworkLink
from gui.config_mapping import ConfigurationMapper
from gui.compose_export import DockerComposeExporter

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
        
        # Initialize Docker Compose exporter
        self.docker_compose_exporter = DockerComposeExporter(self)
        
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
        self.canvas_status_label.setText(message)
        self.canvas_status_label.adjustSize()
        self.updateCanvasStatusBarPosition()
        
        # If timeout is specified, clear the message after the timeout
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.canvas_status_label.setText("Ready"))
                    
    def resizeEvent(self, event):
        """Handle window resize events to update canvas and component layout size."""
        super().resizeEvent(event)
        try:
            window_size = self.size()
            # Update ObjectFrame to be fixed width but full height
            if hasattr(self, 'ObjectFrame'):
                self.ObjectFrame.setGeometry(
                    0, 0,
                    self.ObjectFrame.width(),
                    window_size.height()
                )
            self.updateCanvasGeometry()
            self.updateCanvasStatusBarPosition()
            print(f"DEBUG: Window resized to {window_size.width()}x{window_size.height()}")
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
                action.disconnect()
                action.triggered.connect(method)
            
            # Connect menu actions
            menu_connections = [
                (self.actionNew, self.newTopology),
                (self.actionSave, self.saveTopology),
                (self.actionOpen, self.openTopology),
                (self.actionSave_As, self.saveTopologyAs),
                (self.actionExport_to_Level_2_Script, self.exportToMininet),
                (self.actionExport_to_Docker_Compose, self.exportToDockerCompose),
                (self.actionQuit, self.close)
            ]
            
            for action, method in menu_connections:
                if hasattr(self, action.objectName()):
                    action.disconnect()
                    action.triggered.connect(method)
            
            # Add export to docker-compose action if it doesn't exist
            if not hasattr(self, 'actionExport_to_Docker_Compose'):
                from PyQt5.QtWidgets import QAction
                self.actionExport_to_Docker_Compose = QAction('Export to Docker Compose', self)
                self.actionExport_to_Docker_Compose.setShortcut('Ctrl+Shift+D')
                
                # Add to File menu
                if hasattr(self, 'menuFile'):
                    # Find the position after "Export to Level 2 Script"
                    actions = self.menuFile.actions()
                    insert_pos = len(actions)
                    for i, action in enumerate(actions):
                        if hasattr(action, 'objectName') and 'Export_to_Level_2_Script' in action.objectName():
                            insert_pos = i + 1
                            break
                    
                    if insert_pos < len(actions):
                        self.menuFile.insertAction(actions[insert_pos], self.actionExport_to_Docker_Compose)
                    else:
                        self.menuFile.addAction(self.actionExport_to_Docker_Compose)
                
                # Connect the new action
                self.actionExport_to_Docker_Compose.triggered.connect(self.exportToDockerCompose)
            
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

    def exportToDockerCompose(self):
        """Export 5G Core components to docker-compose.yaml and configuration files."""
        self.docker_compose_exporter.export_to_docker_compose()

    def extractTopology(self):
        """Extract all nodes and links from the canvas, including properties and positions."""
        nodes = []
        links = []
        
        if not hasattr(self, 'canvas_view') or not hasattr(self.canvas_view, 'scene'):
            return nodes, links
        
        for item in self.canvas_view.scene.items():
            if hasattr(item, 'component_type'):  # This is a NetworkComponent
                # Get all properties from the component
                properties = item.getProperties()
                
                # Create node data structure
                node_data = {
                    'name': properties.get('name', item.display_name),
                    'type': item.component_type,
                    'x': properties.get('x', item.pos().x()),
                    'y': properties.get('y', item.pos().y()),
                    'properties': properties
                }
                nodes.append(node_data)
                print(f"DEBUG: Extracted node: {node_data['name']} ({node_data['type']}) at ({node_data['x']}, {node_data['y']})")
                
            elif hasattr(item, 'source_node') and hasattr(item, 'dest_node'):  # This is a NetworkLink
                # Get source and destination names
                source_name = getattr(item.source_node, 'display_name', 'Unknown')
                dest_name = getattr(item.dest_node, 'display_name', 'Unknown')
                
                link_data = {
                    'source': source_name,
                    'destination': dest_name,
                    'type': getattr(item, 'link_type', 'ethernet')
                }
                links.append(link_data)
                print(f"DEBUG: Extracted link: {source_name} -> {dest_name}")
        
        print(f"DEBUG: Total extracted - {len(nodes)} nodes, {len(links)} links")
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
        
        if not nodes:
            self.showCanvasStatus("No components to export!")
            return
        
        # Separate nodes by type
        hosts = [n for n in nodes if n['type'] in ['Host', 'STA']]
        ues = [n for n in nodes if n['type'] == 'UE']
        gnbs = [n for n in nodes if n['type'] == 'GNB']
        aps = [n for n in nodes if n['type'] == 'AP']
        switches = [n for n in nodes if n['type'] in ['Switch', 'Router']]
        controllers = [n for n in nodes if n['type'] == 'Controller']
        docker_hosts = [n for n in nodes if n['type'] == 'DockerHost']
        core5g = [n for n in nodes if n['type'] == 'VGcore']
        
        with open(filename, "w") as f:
            # Write script header
            f.write("#!/usr/bin/python\n")
            f.write("import sys\n")
            f.write("import os\n")
            f.write("from mininet.net import Mininet\n")
            f.write("from mininet.link import TCLink, Link, Intf\n")
            f.write("from mininet.node import RemoteController, OVSKernelSwitch, Host, Node\n")
            f.write("from mininet.log import setLogLevel, info\n")
            f.write("from mn_wifi.net import Mininet_wifi\n")
            f.write("from mn_wifi.node import Station, OVSKernelAP\n")
            f.write("from mn_wifi.link import wmediumd, Intf\n")
            f.write("from mn_wifi.wmediumdConnector import interference\n")
            
            # Add containernet imports if Docker hosts or 5G components exist
            if docker_hosts or ues or gnbs or core5g:
                f.write("from containernet.cli import CLI\n")
                f.write("from containernet.node import DockerSta\n")
                f.write("from containernet.term import makeTerm as makeTerm2\n")
            else:
                f.write("from mn_wifi.cli import CLI\n")
                
            f.write("from subprocess import call\n\n\n")
            
            # Write topology function
            f.write("def topology(args):\n")
            f.write("    \n")
            
            # Initialize network
            if aps or ues or gnbs:
                f.write("    net = Mininet_wifi(topo=None,\n")
                f.write("                       build=False,\n")
                f.write("                       link=wmediumd, wmediumd_mode=interference,\n")
                f.write("                       ipBase='10.0.0.0/8')\n")
            else:
                f.write("    net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8')\n")
            f.write("    \n")
            
            # Add controllers
            if controllers:
                f.write("    info( '\\n*** Adding controller\\n' )\n")
                for i, controller in enumerate(controllers):
                    props = controller.get('properties', {})
                    ctrl_name = self.sanitizeVariableName(controller['name'])
                    ctrl_ip = props.get('Controller_IPAddress', '127.0.0.1')
                    ctrl_port = props.get('Controller_Port', 6633)
                    
                    f.write(f"    {ctrl_name} = net.addController(name='{ctrl_name}',\n")
                    f.write(f"                           controller=RemoteController,\n")
                    f.write(f"                           ip='{ctrl_ip}',\n")
                    f.write(f"                           port={ctrl_port})\n")
                f.write("\n")
            else:
                f.write("    info( '\\n*** Adding controller\\n' )\n")
                f.write("    c0 = net.addController(name='c0',\n")
                f.write("                           controller=RemoteController)\n\n")
            
            # Add APs and Switches
            if aps or switches:
                f.write("    info( '\\n*** Add APs & Switches\\n')\n")
                
                # Add APs
                for ap in aps:
                    props = ap.get('properties', {})
                    ap_name = self.sanitizeVariableName(ap['name'])
                    ssid = props.get('AP_SSID', f'{ap_name}-ssid')
                    channel = props.get('AP_Channel', '36')
                    mode = props.get('AP_Mode', 'a')
                    position = f"{ap['x']:.1f},{ap['y']:.1f},0"
                    
                    f.write(f"    {ap_name} = net.addAccessPoint('{ap_name}', cls=OVSKernelAP, ssid='{ssid}', failMode='standalone', datapath='user',\n")
                    f.write(f"                             channel='{channel}', mode='{mode}', position='{position}', protocols=\"OpenFlow14\")\n")
                
                # Add switches
                for switch in switches:
                    switch_name = self.sanitizeVariableName(switch['name'])
                    f.write(f"    {switch_name} = net.addSwitch('{switch_name}', cls=OVSKernelSwitch, protocols=\"OpenFlow14\")\n")
                
                f.write("\n")
            
            # Get current working directory
            f.write("    cwd = os.getcwd() # Current Working Directory\n\n")
            
            # Add UPF (from 5G Core components)
            upf_components = [c for c in core5g if c.get('properties', {}).get('Component5G_Type') == 'UPF']
            if upf_components:
                f.write("    info( '\\n *** Add UPF\\n')\n")
                for i, upf in enumerate(upf_components, 1):
                    upf_name = self.sanitizeVariableName(upf['name'])
                    position = f"{upf['x']:.1f},{upf['y']:.1f},0"
                    config_file = f"{upf_name}.yaml"
                    
                    f.write(f"    {upf_name} = net.addStation('{upf_name}', cap_add=[\"net_admin\"], network_mode=\"open5gs-ueransim_default\", privileged=True, publish_all_ports=True,\n")
                    f.write(f"                          dcmd=\"/bin/bash\",cls=DockerSta, dimage=\"adaptive/open5gs:1.0\", position='{position}', range=116,\n")
                    f.write(f"                          volumes=[cwd + \"/config/{config_file}:/opt/open5gs/etc/open5gs/upf.yaml\"])\n")
                f.write("\n")
            
            # Add AMF (from 5G Core components)
            amf_components = [c for c in core5g if c.get('properties', {}).get('Component5G_Type') == 'AMF']
            if amf_components:
                f.write("    info( '\\n *** Add AMF\\n')\n")
                for amf in amf_components:
                    amf_name = self.sanitizeVariableName(amf['name'])
                    position = f"{amf['x']:.1f},{amf['y']:.1f},0"
                    config_file = f"{amf_name}.yaml"
                    
                    f.write(f"    {amf_name} = net.addStation('{amf_name}', network_mode=\"open5gs-ueransim_default\", cap_add=[\"net_admin\"],  publish_all_ports=True,\n")
                    f.write(f"                          dcmd=\"/bin/bash\",cls=DockerSta, dimage=\"adaptive/open5gs:1.0\", position='{position}', range=116,\n")
                    f.write(f"                          volumes=[cwd + \"/config/{config_file}:/opt/open5gs/etc/open5gs/amf.yaml\"])\n")
                f.write("\n")
            
            # Add gNBs
            if gnbs:
                f.write("    info( '\\n *** Add gNB\\n')\n")
                for gnb in gnbs:
                    props = gnb.get('properties', {})
                    gnb_name = self.sanitizeVariableName(gnb['name'])
                    position = f"{gnb['x']:.1f},{gnb['y']:.1f},0"
                    amf_ip = props.get('GNB_AMF_IP', '10.0.0.3')
                    hostname = props.get('GNB_Hostname', f'mn.{gnb_name}')
                    mcc = props.get('GNB_MCC', '999')
                    mnc = props.get('GNB_MNC', '70')
                    sst = props.get('GNB_SST', '1')
                    sd = props.get('GNB_SD', '0xffffff')
                    tac = props.get('GNB_TAC', '1')
                    
                    f.write(f"    {gnb_name} = net.addStation('{gnb_name}', cap_add=[\"net_admin\"], network_mode=\"open5gs-ueransim_default\", publish_all_ports=True, \n")
                    f.write(f"                          dcmd=\"/bin/bash\",cls=DockerSta, dimage=\"adaptive/ueransim:1.0\", position='{position}', range=116,\n")
                    f.write(f"                          environment={{\"AMF_IP\": \"{amf_ip}\", \"GNB_HOSTNAME\": \"{hostname}\", \"N2_IFACE\":\"{gnb_name}-wlan0\", \"N3_IFACE\":\"{gnb_name}-wlan0\", \"RADIO_IFACE\":\"{gnb_name}-wlan0\",\n")
                    f.write(f"                                        \"MCC\": \"{mcc}\", \"MNC\": \"{mnc}\", \"SST\": \"{sst}\", \"SD\": \"{sd}\", \"TAC\": \"{tac}\"}})\n")
                f.write("\n")
            
            # Add UEs
            if ues:
                f.write("    info('\\n*** Adding docker UE hosts\\n')\n")
                for ue in ues:
                    props = ue.get('properties', {})
                    ue_name = self.sanitizeVariableName(ue['name'])
                    position = f"{ue['x']:.1f},{ue['y']:.1f},0"
                    gnb_ip = props.get('UE_GNB_IP', '10.0.0.4')
                    apn = props.get('UE_APN', 'internet')
                    msisdn = props.get('UE_MSISDN', f'000000000{len(ues)}')
                    mcc = props.get('UE_MCC', '999')
                    mnc = props.get('UE_MNC', '70')
                    sst = props.get('UE_SST', '1')
                    sd = props.get('UE_SD', '0xffffff')
                    tac = props.get('UE_TAC', '1')
                    key = props.get('UE_Key', '465B5CE8B199B49FAA5F0A2EE238A6BC')
                    op_type = props.get('UE_OP_Type', 'OPC')
                    op = props.get('UE_OP', 'E8ED289DEBA952E4283B54E88E6183CA')
                    
                    f.write(f"    {ue_name} = net.addStation('{ue_name}', devices=[\"/dev/net/tun\"], cap_add=[\"net_admin\"], range=116, network_mode=\"open5gs-ueransim_default\",\n")
                    f.write(f"                          dcmd=\"/bin/bash\",cls=DockerSta, dimage=\"adaptive/ueransim:1.0\", position='{position}', \n")
                    f.write(f"                          environment={{\"GNB_IP\": \"{gnb_ip}\", \"APN\": \"{apn}\", \"MSISDN\": '{msisdn}',\n")
                    f.write(f"                                        \"MCC\": \"{mcc}\", \"MNC\": \"{mnc}\", \"SST\": \"{sst}\", \"SD\": \"{sd}\", \"TAC\": \"{tac}\", \n")
                    f.write(f"                                        \"KEY\": \"{key}\", \"OP_TYPE\": \"{op_type}\", \"OP\": \"{op}\"}})\n")
                f.write("\n")
            
            # Add Docker hosts
            for docker_host in docker_hosts:
                props = docker_host.get('properties', {})
                host_name = self.sanitizeVariableName(docker_host['name'])
                position = f"{docker_host['x']:.1f},{docker_host['y']:.1f},0"
                image = props.get('DockerHost_ContainerImage', 'ubuntu:latest')
                
                f.write(f"    {host_name} = net.addStation('{host_name}', dcmd=\"/bin/bash\", cls=DockerSta, dimage=\"{image}\", position='{position}')\n")
            
            # Add regular hosts and STAs
            for host in hosts:
                props = host.get('properties', {})
                host_name = self.sanitizeVariableName(host['name'])
                position = f"{host['x']:.1f},{host['y']:.1f},0"
                ip = props.get('Host_IPAddress') or props.get('STA_IPAddress', '')
                
                if host['type'] == 'STA':
                    f.write(f"    {host_name} = net.addStation('{host_name}', position='{position}'")
                    if ip:
                        f.write(f", ip='{ip}'")
                    f.write(")\n")
                else:
                    f.write(f"    {host_name} = net.addHost('{host_name}'")
                    if ip:
                        f.write(f", ip='{ip}'")
                    f.write(")\n")
            
            # Add WiFi connections if needed
            if ues or any(host['type'] == 'STA' for host in hosts):
                f.write("\n    info( '\\n*** Connecting Docker nodes to APs\\n')\n")
                for ue in ues:
                    ue_name = self.sanitizeVariableName(ue['name'])
                    # Find closest AP (simplified - you might want to improve this logic)
                    if aps:
                        closest_ap = min(aps, key=lambda ap: ((ap['x'] - ue['x'])**2 + (ap['y'] - ue['y'])**2)**0.5)
                        ap_name = self.sanitizeVariableName(closest_ap['name'])
                        ap_ssid = closest_ap.get('properties', {}).get('AP_SSID', f'{ap_name}-ssid')
                        f.write(f"    {ue_name}.cmd('iw dev {ue_name}-wlan0 connect {ap_ssid}')\n")
                f.write("\n")
            
            # Configure propagation model if wireless components exist
            if aps or gnbs:
                f.write("    info(\"\\n*** Configuring Propagation Model\\n\")\n")
                f.write("    net.setPropagationModel(model=\"logDistance\", exp=3)\n\n")
                f.write("    info('\\n*** Configuring WiFi nodes\\n')\n")
                f.write("    net.configureWifiNodes()\n\n")
            
            # Add links
            if links:
                f.write("    info( '\\n*** Add links\\n')\n")
                for link in links:
                    source_name = self.sanitizeVariableName(link['source'])
                    dest_name = self.sanitizeVariableName(link['destination'])
                    
                    # Determine link type based on connected components
                    source_node = next((n for n in nodes if self.sanitizeVariableName(n['name']) == source_name), None)
                    dest_node = next((n for n in nodes if self.sanitizeVariableName(n['name']) == dest_name), None)
                    
                    if source_node and dest_node:
                        # Use TCLink for connections involving wireless components
                        if (source_node['type'] in ['AP', 'GNB', 'UE', 'STA'] or 
                            dest_node['type'] in ['AP', 'GNB', 'UE', 'STA']):
                            f.write(f"    net.addLink({source_name}, {dest_name}, cls=TCLink)\n")
                        else:
                            f.write(f"    net.addLink({source_name}, {dest_name})\n")
                f.write("\n")
            
            # Add plot graph if wireless components exist
            if aps or gnbs or ues:
                f.write("    net.plotGraph(max_x=1000, max_y=1000)\n\n")
            
            # Start network
            f.write("    info('\\n*** Starting network\\n')\n")
            f.write("    net.build()\n\n")
            
            # Start controllers
            if controllers:
                f.write("    info( '\\n*** Starting controllers\\n')\n")
                for controller in controllers:
                    ctrl_name = self.sanitizeVariableName(controller['name'])
                    f.write(f"    {ctrl_name}.start()\n")
            else:
                f.write("    info( '\\n*** Starting controllers\\n')\n")
                f.write("    c0.start()\n")
            f.write("\n")
            
            # Start APs and switches
            if aps or switches:
                f.write("    info( '\\n*** Starting APs\\n')\n")
                controller_name = 'c0'
                if controllers:
                    controller_name = self.sanitizeVariableName(controllers[0]['name'])
                    
                for ap in aps:
                    ap_name = self.sanitizeVariableName(ap['name'])
                    f.write(f"    net.get('{ap_name}').start([{controller_name}])\n")
                    
                for switch in switches:
                    switch_name = self.sanitizeVariableName(switch['name'])
                    f.write(f"    net.get('{switch_name}').start([{controller_name}])\n")
                f.write("\n")
            
            # Add 5G specific startup sequences if 5G components exist
            if upf_components or amf_components or gnbs or ues:
                f.write("    info( '\\n *** Capture all initialization flow and slice packet\\n')\n")
                f.write("    Capture1 = cwd + \"/capture-initialization-fixed.sh\"\n")
                f.write("    CLI(net, script=Capture1)\n\n")
                f.write("    CLI.do_sh(net, 'sleep 20')\n\n")
                f.write("    info( '\\n *** pingall for testing and flow tables update\\n')\n")
                f.write("    net.pingAll()\n\n")
                f.write("    CLI.do_sh(net, 'sleep 10')\n\n")
                
                # Start UPF
                if upf_components:
                    f.write("    info( '\\n *** Post configure Docker UPF connection to Core\\n')\n")
                    for upf in upf_components:
                        upf_name = self.sanitizeVariableName(upf['name'])
                        f.write(f"    makeTerm2({upf_name}, cmd=\"/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/{upf_name}.log\")\n")
                    f.write("\n")
                
                # Start AMF
                if amf_components:
                    f.write("    info( '\\n *** Post configure Docker AMF connection to Core\\n')\n")
                    for amf in amf_components:
                        amf_name = self.sanitizeVariableName(amf['name'])
                        f.write(f"    makeTerm2({amf_name}, cmd=\"open5gs-amfd 2>&1 | tee -a /logging/{amf_name}.log\")\n")
                    f.write("\n    CLI.do_sh(net, 'sleep 10')\n\n")
                
                # Start gNBs
                if gnbs:
                    f.write("    info( '\\n*** Post configure Docker gNB connection to AMF\\n')\n")
                    for gnb in gnbs:
                        gnb_name = self.sanitizeVariableName(gnb['name'])
                        f.write(f"    makeTerm2({gnb_name}, cmd=\"/entrypoint.sh gnb 2>&1 | tee -a /logging/{gnb_name}.log\")\n")
                    f.write("\n    CLI.do_sh(net, 'sleep 10')\n\n")
                
                # Start UEs
                if ues:
                    f.write("    info( '\\n*** Post configure Docker UE nodes\\n')\n")
                    for ue in ues:
                        ue_name = self.sanitizeVariableName(ue['name'])
                        f.write(f"    makeTerm2({ue_name}, cmd=\"/entrypoint.sh ue 2>&1 | tee -a /logging/{ue_name}.log\")\n")
                    f.write("\n    CLI.do_sh(net, 'sleep 20')\n\n")
                    
                    # Add routing for UEs
                    f.write("    info( '\\n ***Route traffic on UE for End-to-End and End-to-Edge Connection\\n')\n")
                    for ue in ues:
                        ue_name = self.sanitizeVariableName(ue['name'])
                        props = ue.get('properties', {})
                        apn = props.get('UE_APN', 'internet')
                        if apn == 'internet':
                            f.write(f"    {ue_name}.cmd('ip route add 10.45.0.0/16 dev uesimtun0')\n")
                        elif apn == 'internet2':
                            f.write(f"    {ue_name}.cmd('ip route add 10.46.0.0/16 dev uesimtun0')\n")
                    f.write("\n")
            
            # Add CLI and cleanup
            f.write("    info('*** Running CLI\\n')\n")
            f.write("    CLI(net)\n\n")
            f.write("    info('*** Stopping network\\n')\n")
            f.write("    net.stop()\n\n")
            
            # Add main execution block
            f.write("if __name__ == '__main__':\n")
            f.write("    setLogLevel('info')\n")
            f.write("    topology(sys.argv)\n")
        
        self.showCanvasStatus(f"Exported topology with configurations to {os.path.basename(filename)}")
        print(f"DEBUG: Exported {len(nodes)} nodes and {len(links)} links with configurations to {filename}")

    def sanitizeVariableName(self, name):
        """Convert component name to valid Python variable name."""
        import re
        # Replace spaces and special characters with underscores
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    
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