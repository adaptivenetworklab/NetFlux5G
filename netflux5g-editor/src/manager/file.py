import os
import json
import traceback
import yaml
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QDateTime
from manager.debug import debug_print, error_print, warning_print

class FileManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def newTopology(self):
        """Create a new topology."""
        if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
            self.main_window.canvas_view.scene.clear()
        self.main_window.current_file = None
        self.main_window.status_manager.showCanvasStatus("New topology created")
            
    def saveTopology(self):
        """Save the current topology. If no file is set, prompt for save location."""
        if self.main_window.current_file:
            self.saveTopologyToFile(self.main_window.current_file)
        else:
            self.saveTopologyAs()
    
    def saveTopologyToFile(self, filename):
        """Save topology data to file with enhanced configuration preservation."""
        try:
            nodes, links = self.extractTopology()
            
            topology_data = {
                "version": "1.1",  # Updated version for enhanced features
                "type": "NetFlux5G_Topology",
                "metadata": {
                    "created_with": "NetFlux5G Editor",
                    "created_date": QDateTime.currentDateTime().toString(),
                    "saved_date": QDateTime.currentDateTime().toString(),
                    "canvas_size": {
                        "width": self.main_window.canvas_view.size().width() if hasattr(self.main_window, 'canvas_view') else 1161,
                        "height": self.main_window.canvas_view.size().height() if hasattr(self.main_window, 'canvas_view') else 1151
                    },
                    "component_counts": getattr(self.main_window, 'component_counts', {}),
                    "editor_version": "2.0"
                },
                "nodes": nodes,
                "links": links,
                "canvas_properties": {
                    "zoom_level": getattr(self.main_window.canvas_view, 'zoom_level', 1.0) if hasattr(self.main_window, 'canvas_view') else 1.0,
                    "show_grid": getattr(self.main_window, 'show_grid', False)
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=2)
                
            self.main_window.current_file = filename
            self.main_window.status_manager.showCanvasStatus(f"Topology saved to {os.path.basename(filename)}")
            debug_print(f"DEBUG: Topology saved successfully to {filename}")
            debug_print(f"DEBUG: Saved {len(nodes)} nodes and {len(links)} links")
            
        except Exception as e:
            error_msg = f"Error saving topology: {str(e)}"
            self.main_window.status_manager.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()
    
    def saveTopologyAs(self):
        """Prompt user to save topology with a new filename."""
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window, 
            "Save Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            self.saveTopologyToFile(filename)
            
    def openTopology(self):
        """Open a topology file with enhanced file type support."""
        filename, _ = QFileDialog.getOpenFileName(
            self.main_window, 
            "Open Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        """Enhanced topology loading with comprehensive configuration restoration."""
        try:
            # Load the file based on extension
            with open(filename, 'r') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    topology_data = yaml.safe_load(f)
                else:
                    topology_data = json.load(f)
            
            # Clear current topology
            if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
                self.main_window.canvas_view.scene.clear()
            
            # Load nodes
            if 'nodes' in topology_data:
                self.loadNodes(topology_data['nodes'])
            
            # Load links
            if 'links' in topology_data:
                self.loadLinks(topology_data['links'])
            
            # Restore canvas properties
            if 'canvas_properties' in topology_data:
                self.restoreCanvasProperties(topology_data['canvas_properties'])
            
            self.main_window.current_file = filename
            self.main_window.status_manager.showCanvasStatus(f"Topology loaded from {os.path.basename(filename)}")
            debug_print(f"DEBUG: Topology loaded successfully from {filename}")
            
        except Exception as e:
            error_msg = f"Error loading topology: {str(e)}"
            self.main_window.status_manager.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def extractTopology(self):
        """Extract current topology data."""
        nodes = []
        links = []
        
        if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
            from gui.components import NetworkComponent
            from gui.links import NetworkLink
            
            for item in self.main_window.canvas_view.scene.items():
                if isinstance(item, NetworkComponent):
                    node_data = {
                        'name': item.display_name,
                        'type': item.component_type,
                        'x': item.pos().x(),
                        'y': item.pos().y(),
                        'properties': item.getProperties()
                    }
                    nodes.append(node_data)
                elif isinstance(item, NetworkLink):
                    link_data = {
                        'source': getattr(item.source_node, 'display_name', 'Unknown'),
                        'destination': getattr(item.dest_node, 'display_name', 'Unknown'),
                        'type': getattr(item, 'link_type', 'ethernet'),
                        'properties': getattr(item, 'properties', {})
                    }
                    links.append(link_data)
        
        return nodes, links

    def loadNodes(self, nodes_data):
        """Load nodes from topology data."""
        from gui.components import NetworkComponent
        
        for node_data in nodes_data:
            component_type = node_data.get('type', 'Host')
            icon_path = self.main_window.component_icon_map.get(component_type)
            
            if icon_path and os.path.exists(icon_path):
                component = NetworkComponent(component_type, icon_path)
                component.setPosition(node_data.get('x', 0), node_data.get('y', 0))
                component.setProperties(node_data.get('properties', {}))
                component.display_name = node_data.get('name', component.display_name)
                
                self.main_window.canvas_view.scene.addItem(component)

    def loadLinks(self, links_data):
        """Load links from topology data."""
        from gui.links import NetworkLink
        
        # Find components by name
        components = {}
        for item in self.main_window.canvas_view.scene.items():
            if hasattr(item, 'display_name'):
                components[item.display_name] = item
        
        for link_data in links_data:
            source_name = link_data.get('source')
            dest_name = link_data.get('destination')
            
            if source_name in components and dest_name in components:
                source = components[source_name]
                dest = components[dest_name]
                link = NetworkLink(source, dest)
                self.main_window.canvas_view.scene.addItem(link)

    def restoreCanvasProperties(self, canvas_props):
        """Restore canvas properties."""
        if hasattr(self.main_window, 'canvas_view'):
            zoom_level = canvas_props.get('zoom_level', 1.0)
            if zoom_level != 1.0:
                self.main_window.canvas_view.zoom_level = zoom_level
                
            show_grid = canvas_props.get('show_grid', False)
            self.main_window.show_grid = show_grid
            if hasattr(self.main_window.canvas_view, 'setShowGrid'):
                self.main_window.canvas_view.setShowGrid(show_grid)

    def loadExampleTemplate(self, template_name):
        """Load an example template topology."""
        try:
            # Get the examples directory path
            examples_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "examples"
            )
            
            # Construct the template file path
            template_file = os.path.join(examples_dir, f"{template_name}.nf5g")
            
            if not os.path.exists(template_file):
                error_print(f"Template file not found: {template_file}")
                return False
            
            # Load the template file
            self.loadTopologyFromFile(template_file)
            
            # Don't set current_file for templates (they should be saved as new files)
            self.main_window.current_file = None
            
            debug_print(f"Example template loaded successfully: {template_name}")
            return True
            
        except Exception as e:
            error_print(f"Failed to load example template '{template_name}': {e}")
            return False