import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton  # Added QGraphicsView
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QIcon
from PyQt5 import uic
from gui.canvas import Canvas
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from gui.links import NetworkLink  # Import NetworkLink


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

        # Initialize the toolbar functions
        self.toolbar_functions = ToolbarFunctions(self)
        
        # Initialize grid attribute
        self.show_grid = False  # Add this line
        
        # Set up the canvas as a QWidget
        self.canvas_view = Canvas(self, self)
        self.canvas_view.setMinimumSize(1828, 800)  # Ensure the canvas has a visible size
        
        # Replace the Canvas widget in the horizontal layout
        index = self.horizontalLayout.indexOf(self.Canvas)
        self.horizontalLayout.removeWidget(self.Canvas)
        self.Canvas.deleteLater()
        self.horizontalLayout.insertWidget(index, self.canvas_view)
        
        # Connect QPushButton objects in ObjectLayout to startDrag
        for button in self.ObjectLayout.findChildren(QPushButton):
            component_type = button.objectName()  # Use the button's objectName as the component type
            button.pressed.connect(lambda bt=component_type: self.startDrag(bt))
        
        # Connect button signals to add components
        self.Host.pressed.connect(lambda: self.startDrag("Host"))
        self.STA.pressed.connect(lambda: self.startDrag("STA"))
        self.UE.pressed.connect(lambda: self.startDrag("UE"))
        self.GNB.pressed.connect(lambda: self.startDrag("GNB"))
        self.DockerHost.pressed.connect(lambda: self.startDrag("DockerHost"))
        self.AP.pressed.connect(lambda: self.startDrag("AP"))
        self.VGcore.pressed.connect(lambda: self.startDrag("VGcore"))
        self.Router.pressed.connect(lambda: self.startDrag("Router"))
        self.Switch.pressed.connect(lambda: self.startDrag("Switch"))
        self.LinkCable.pressed.connect(lambda: self.startLinkMode("LinkCable"))
        self.Controller.pressed.connect(lambda: self.startDrag("Controller"))
        
        # Connect toolbar actions
        self.actionPickTool.triggered.connect(self.enablePickTool)
        self.actionTextBox.triggered.connect(self.addTextBox)
        self.actionDrawSquare.triggered.connect(self.addDrawSquare)
        self.actionShowGrid.triggered.connect(self.toggleGrid)
        self.actionZoomIn.triggered.connect(self.zoomIn)  # Connect Zoom In
        self.actionZoomOut.triggered.connect(self.zoomOut)  # Connect Zoom Out
        self.actionResetZoom.triggered.connect(self.resetZoom)  # Connect Reset Zoom
        self.actionDelete.triggered.connect(self.enableDeleteTool)
        # self.actionRunAll.triggered.connect(self.runAll)
        # self.actionStopAll.triggered.connect(self.stopAll)
                
        # Connect menu actions
        self.actionNew.triggered.connect(self.newTopology)
        self.actionSave.triggered.connect(self.saveTopology)
        self.actionOpen.triggered.connect(self.openTopology)
        self.actionSave_As.triggered.connect(self.saveTopologyAs)
        self.actionExport_to_Level_2_Script.triggered.connect(self.exportToMininet)
        self.actionQuit.triggered.connect(self.close)
        # Add export to Mininet menu action
        self.actionExport_to_Mininet = self.findChild(type(self.actionNew), "actionExport_to_Mininet")
        if self.actionExport_to_Mininet:
            self.actionExport_to_Mininet.triggered.connect(self.exportToMininet)
        
        # Set up the canvas_view for drag and drop
        self.canvas_view.setAcceptDrops(True)
        
        # Initialize attributes
        self.current_link_source = None
        self.current_file = None
        self.current_tool = "pick"  # Default tool
        self.selected_component = None  # Track the selected component for placement
        
        # Initialize component mapping for icons
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
        
        # Status message
        self.statusbar.showMessage("Ready")
        
    def startDrag(self, component_type):
        """Start drag action for components."""
        # Exit link mode if active
        self.exitLinkMode()
        
        print(f"Starting drag for component: {component_type}")  # Debug message

        # Create a drag object with component information
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(component_type)  # Pass the component type as text
        drag.setMimeData(mime_data)
        
        # Set a pixmap for the drag appearance
        icon_path = self.component_icon_map.get(component_type)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(20, 20))  # Set the drag hotspot to the center of the pixmap
        
        # Execute the drag
        drag.exec_(Qt.CopyAction)
        
    def startLinkMode(self, component_type):
        """Activate link mode."""
        # Reset any previous source selection
        self.current_link_source = None
        
        # Set current tool to link
        self.current_tool = "link"
        
        # Enable link mode in canvas
        self.canvas_view.setLinkMode(True)
        
        # Update cursor to indicate link mode
        self.canvas_view.setCursor(Qt.CrossCursor)
        
        # Update status bar
        self.statusbar.showMessage("Link mode activated. Click on source object, then destination object.")
        print("DEBUG: Link mode activated")
        
    def createLink(self, source, destination):
        """Create a link between two objects."""
        from gui.links import NetworkLink
        
        # Create a new NetworkLink with cable visualization
        link = NetworkLink(source, destination)
        
        # Add the link to the scene
        self.canvas_view.scene.addItem(link)
        
        # Update the status bar
        source_name = source.object_type if hasattr(source, 'object_type') else 'object'
        dest_name = destination.object_type if hasattr(destination, 'object_type') else 'object'
        self.statusbar.showMessage(f"LinkCable created between {source_name} and {dest_name}")
        
        # Update view
        self.canvas_view.viewport().update()
        
        return link

    def updateAllLinks(self):
        """Update all links in the scene."""
        for item in self.canvas_view.scene.items():
            if isinstance(item, NetworkLink):
                item.updatePosition()

    def exitLinkMode(self):
        """Exit link mode."""
        # Remove highlight from source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setHighlighted'):
            self.current_link_source.setHighlighted(False)
            print("DEBUG: Removing highlight from source object")
        
        # Re-enable dragging for source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setFlag'):
            from PyQt5.QtWidgets import QGraphicsItem
            self.current_link_source.setFlag(QGraphicsItem.ItemIsMovable, True)
            
        self.current_link_source = None
        self.canvas_view.setLinkMode(False)
        self.canvas_view.setCursor(Qt.ArrowCursor)
        self.statusbar.showMessage("Pick tool selected")

    def enablePickTool(self):
        """Restore the pick tool state."""
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "pick"
        self.selected_component = None  # Reset selected component
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.canvas_view.setCursor(Qt.ArrowCursor)  # Reset to arrow cursor
        self.statusbar.showMessage("Pick tool selected")
        print("DEBUG: Switched to pick tool")
    
    def enableDeleteTool(self):
        """Enable the Delete Tool."""
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "delete"
        self.canvas_view.setCursor(Qt.CrossCursor)  # Set a cross cursor for delete mode
        self.statusbar.showMessage("Delete Tool selected. Click on items to delete them.")
        
    def addTextBox(self):
        self.current_tool = "text"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.current_tool = "square"
        self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.statusbar.showMessage("Square tool selected. Click and drag to draw a square.")

    def zoomIn(self):
        """Zoom in the canvas."""
        self.canvas_view.zoomIn()
        self.statusbar.showMessage("Zoomed in")

    def zoomOut(self):
        """Zoom out the canvas."""
        self.canvas_view.zoomOut()
        self.statusbar.showMessage("Zoomed out")

    def resetZoom(self):
        """Reset the zoom level of the canvas."""
        self.canvas_view.resetZoom()
        self.statusbar.showMessage("Zoom reset to default level")
        
    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas."""
        self.show_grid = not self.show_grid
        self.canvas_view.setShowGrid(self.show_grid)
        status = "shown" if self.show_grid else "hidden"
        self.statusbar.showMessage(f"Grid {status}")

    def newTopology(self):
        self.scene.clear()
        self.current_file = None
        self.statusbar.showMessage("New topology created")
        
    def saveTopology(self):
        if self.current_file:
            self.saveTopologyToFile(self.current_file)
        else:
            self.saveTopologyAs()
            
    def saveTopologyToFile(self, filename):
        # Implement saving topology data to file
        self.statusbar.showMessage(f"Topology saved to {filename}")
        
    def saveTopologyAs(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Save Topology", "", "NetFlux5G Files (*.nf5g);;All Files (*)")
        if filename:
            self.current_file = filename
            self.saveTopologyToFile(filename)
            
    def openTopology(self):
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Open Topology", "", "NetFlux5G Files (*.nf5g);;All Files (*)")
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        # Implement loading topology from file
        self.current_file = filename
        self.statusbar.showMessage(f"Loaded topology from {filename}")
        
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
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            # Check current tool and switch back to pick tool mode
            if self.current_tool in ["delete", "link", "placement", "text", "square"]:
                print(f"DEBUG: ESC pressed, exiting {self.current_tool} mode")
                
                # Exit link mode if we're in it
                if self.current_tool == "link":
                    self.exitLinkMode()  # This already handles link mode cleanup
                
                # For all modes, switch to pick tool
                self.enablePickTool()  # Call this method instead of setting properties directly
            
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

    # # Load the QSS file
    # qss_file_path = os.path.join(os.path.dirname(__file__), "gui", "styles.qss")
    # with open(qss_file_path, "r") as file:
    #     app.setStyleSheet(file.read())

    window = NetFlux5GApp()
    window.show()
    sys.exit(app.exec_())