import os
import json
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QDateTime
from manager.debug import debug_print, error_print, warning_print
import traceback

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
        """Save topology data to file."""
        try:
            nodes, links = self.extractTopology()
            
            topology_data = {
                "version": "1.0",
                "type": "NetFlux5G_Topology",
                "metadata": {
                    "created_with": "NetFlux5G Editor",
                    "created_date": QDateTime.currentDateTime().toString(),
                    "canvas_size": {
                        "width": self.main_window.canvas_view.size().width() if hasattr(self.main_window, 'canvas_view') else 1161,
                        "height": self.main_window.canvas_view.size().height() if hasattr(self.main_window, 'canvas_view') else 1151
                    }
                },
                "nodes": nodes,
                "links": links
            }
            
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=2, ensure_ascii=False)
                
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
        """Open a topology file."""
        filename, _ = QFileDialog.getOpenFileName(
            self.main_window, 
            "Open Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        """Load topology from file."""
        try:
            with open(filename, 'r') as f:
                topology_data = json.load(f)
            
            if not isinstance(topology_data, dict) or 'nodes' not in topology_data:
                raise ValueError("Invalid topology file format")
            
            # Clear current canvas
            if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
                self.main_window.canvas_view.scene.clear()
            
            # Load nodes
            nodes = topology_data.get('nodes', [])
            node_map = {}
            
            for node_data in nodes:
                component = self.createComponentFromData(node_data)
                if component:
                    node_map[node_data['name']] = component
            
            # Load links
            links = topology_data.get('links', [])
            for link_data in links:
                self.createLinkFromData(link_data, node_map)
            
            # Update canvas
            if hasattr(self.main_window, 'canvas_view'):
                self.main_window.canvas_view.scene.update()
                self.main_window.canvas_view.viewport().update()
            
            self.main_window.current_file = filename
            self.main_window.status_manager.showCanvasStatus(f"Topology loaded: {len(nodes)} components, {len(links)} links")
            debug_print(f"DEBUG: Topology loaded successfully from {filename}")
            
        except Exception as e:
            error_msg = f"Error loading topology: {str(e)}"
            self.main_window.status_manager.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def createComponentFromData(self, node_data):
        """Create a component from saved node data."""
        try:
            component_type = node_data.get('type')
            name = node_data.get('name')
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            properties = node_data.get('properties', {})
            
            icon_path = self.main_window.component_icon_map.get(component_type)
            if not icon_path or not os.path.exists(icon_path):
                warning_print(f"WARNING: Icon not found for {component_type}")
                return None
            
            from gui.components import NetworkComponent
            component = NetworkComponent(component_type, icon_path)
            component.setPosition(x, y)
            component.display_name = name
            component.setProperties(properties)
            
            self.main_window.canvas_view.scene.addItem(component)
            debug_print(f"DEBUG: Created component {name} of type {component_type} at ({x}, {y})")
            return component
            
        except Exception as e:
            error_print(f"ERROR: Failed to create component from data: {e}")
            return None

    def createLinkFromData(self, link_data, node_map):
        """Create a link from saved link data."""
        try:
            source_name = link_data.get('source')
            dest_name = link_data.get('destination')
            link_type = link_data.get('type', 'ethernet')
            properties = link_data.get('properties', {})
            
            source_component = node_map.get(source_name)
            dest_component = node_map.get(dest_name)
            
            if not source_component or not dest_component:
                warning_print(f"WARNING: Could not find components for link {source_name} -> {dest_name}")
                return None
            
            from gui.links import NetworkLink
            link = NetworkLink(source_component, dest_component)
            link.link_type = link_type
            link.properties = properties
            
            self.main_window.canvas_view.scene.addItem(link)
            debug_print(f"DEBUG: Created link from {source_name} to {dest_name}")
            return link
            
        except Exception as e:
            error_print(f"ERROR: Failed to create link from data: {e}")
            return None

    def extractTopology(self):
        """Extract all nodes and links from the canvas."""
        nodes = []
        links = []
        
        if not hasattr(self.main_window, 'canvas_view') or not hasattr(self.main_window.canvas_view, 'scene'):
            return nodes, links
        
        from gui.links import NetworkLink
        
        for item in self.main_window.canvas_view.scene.items():
            if hasattr(item, 'component_type'):  # NetworkComponent
                node_data = {
                    'name': getattr(item, 'display_name', item.component_type),
                    'type': item.component_type,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'properties': item.getProperties() if hasattr(item, 'getProperties') else {}
                }
                nodes.append(node_data)
                
            elif isinstance(item, NetworkLink):  # NetworkLink
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
        
        debug_print(f"DEBUG: Total extracted - {len(nodes)} nodes, {len(links)} links")
        return nodes, links