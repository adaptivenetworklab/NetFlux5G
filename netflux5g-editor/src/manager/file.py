import os
import json
import yaml
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QDateTime, Qt
from manager.debug import debug_print, error_print, warning_print
import traceback

class FileManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def newTopology(self):
        """Create a new topology."""
        if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
            self.main_window.canvas_view.scene.clear()
        
        # Reset component numbering system
        from gui.components import NetworkComponent
        NetworkComponent.component_counts = {
            "Host": 0, "STA": 0, "UE": 0, "GNB": 0, "DockerHost": 0,
            "AP": 0, "VGcore": 0, "Controller": 0, "Router": 0, "Switch": 0,
        }
        NetworkComponent.available_numbers = {
            "Host": set(), "STA": set(), "UE": set(), "GNB": set(), "DockerHost": set(),
            "AP": set(), "VGcore": set(), "Controller": set(), "Router": set(), "Switch": set(),
        }
        
        # Clear component operations clipboard
        if hasattr(self.main_window, 'component_operations_manager'):
            self.main_window.component_operations_manager.clearClipboard()
            
        self.main_window.current_file = None
        # Clear template flags
        self.main_window.is_template_loaded = False
        if hasattr(self.main_window, 'template_name'):
            del self.main_window.template_name
        # Mark as saved since new topology is clean
        if hasattr(self.main_window, 'markAsSaved'):
            self.main_window.markAsSaved()
        else:
            # Fallback for older versions
            if hasattr(self.main_window, 'setWindowTitle'):
                self.main_window.setWindowTitle("NetFlux5G Editor - New Topology")
        self.main_window.status_manager.showCanvasStatus("New topology created")
            
    def saveTopology(self):
        """Save the current topology. If no file is set or a template is loaded, prompt for save location."""
        # If a template is loaded, always use Save As behavior
        if (self.main_window.current_file and 
            not getattr(self.main_window, 'is_template_loaded', False)):
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
                json.dump(topology_data, f, indent=2, ensure_ascii=False)
            self.main_window.current_file = filename
            # Clear template flags when saving as a new file
            if hasattr(self.main_window, 'is_template_loaded'):
                self.main_window.is_template_loaded = False
            if hasattr(self.main_window, 'template_name'):
                del self.main_window.template_name
            # Mark as saved
            if hasattr(self.main_window, 'markAsSaved'):
                self.main_window.markAsSaved()
            else:
                # Fallback for older versions
                if hasattr(self.main_window, 'setWindowTitle'):
                    self.main_window.setWindowTitle(f"NetFlux5G Editor - {os.path.basename(filename)}")
            self.main_window.status_manager.showCanvasStatus(f"Topology saved as {os.path.basename(filename)}")
            debug_print(f"DEBUG: Topology saved successfully to {filename}")
            debug_print(f"DEBUG: Saved {len(nodes)} nodes and {len(links)} links")
        except Exception as e:
            error_msg = f"Error saving topology: {str(e)}"
            self.main_window.status_manager.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()
        
    def saveTopologyAs(self):
        """Prompt user to save topology with a new filename, with overwrite confirmation and extension handling."""
        from PyQt5.QtWidgets import QApplication
        import threading
        debug_print("saveTopologyAs called")
        # Ensure this runs in the main thread
        if threading.current_thread() != threading.main_thread():
            error_print("saveTopologyAs must be called from the main thread!")
            return
        # Ensure main window is visible and active before showing dialog
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        QApplication.processEvents()  # Ensure window is updated
        # Show the save file dialog
        filename, selected_filter = QFileDialog.getSaveFileName(
            self.main_window, 
            "Save Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        debug_print(f"saveTopologyAs dialog result: filename={filename}, filter={selected_filter}")
        if not filename:
            self.main_window.status_manager.showCanvasStatus("Save cancelled", 2000)
            return
        # Ensure correct extension based on selected filter
        if selected_filter.startswith("NetFlux5G") and not filename.endswith(".nf5g"):
            filename += ".nf5g"
        elif selected_filter.startswith("JSON") and not filename.endswith(".json"):
            filename += ".json"
        # Confirm overwrite if file exists
        if os.path.exists(filename):
            reply = QMessageBox.question(
                self.main_window,
                "Overwrite File?",
                f"File '{filename}' already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                self.main_window.status_manager.showCanvasStatus("Save cancelled", 2000)
                return
        self.saveTopologyToFile(filename)
        self.main_window.status_manager.showCanvasStatus(f"Saved as {os.path.basename(filename)}", 2000)
            
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
            # Show progress dialog for complex topologies
            progress = QProgressDialog("Loading topology...", "Cancel", 0, 100, self.main_window)
            progress.setWindowTitle("Loading Topology")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            # Determine file type and load accordingly
            file_ext = os.path.splitext(filename)[1].lower()
            
            progress.setValue(10)
            QApplication.processEvents()
            
            if file_ext in ['.yaml', '.yml']:
                topology_data = self.loadYamlFile(filename)
            else:
                topology_data = self.loadJsonFile(filename)
            
            progress.setValue(20)
            QApplication.processEvents()
            
            # Validate file format
            if not self.validateTopologyFile(topology_data):
                raise ValueError("Invalid topology file format")
            
            # Clear current canvas
            if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
                self.main_window.canvas_view.scene.clear()
            
            progress.setValue(30)
            QApplication.processEvents()
            
            # Load metadata and canvas properties
            self.loadCanvasProperties(topology_data)
            
            progress.setValue(40)
            QApplication.processEvents()
            
            # Load nodes with enhanced configuration restoration
            nodes = topology_data.get('nodes', [])
            node_map = {}
            
            total_nodes = len(nodes)
            for i, node_data in enumerate(nodes):
                if progress.wasCanceled():
                    return
                    
                component = self.createComponentFromData(node_data)
                if component:
                    node_map[node_data['name']] = component
                
                # Update progress
                node_progress = 40 + int((i / max(total_nodes, 1)) * 40)
                progress.setValue(node_progress)
                QApplication.processEvents()
            
            progress.setValue(80)
            QApplication.processEvents()
            
            # Load links with enhanced properties
            links = topology_data.get('links', [])
            total_links = len(links)
            
            for i, link_data in enumerate(links):
                if progress.wasCanceled():
                    return
                    
                self.createLinkFromData(link_data, node_map)
                
                # Update progress
                if total_links > 0:
                    link_progress = 80 + int((i / total_links) * 15)
                    progress.setValue(link_progress)
                    QApplication.processEvents()
            
            progress.setValue(95)
            QApplication.processEvents()
            
            # Update canvas and finalize
            if hasattr(self.main_window, 'canvas_view'):
                self.main_window.canvas_view.scene.update()
                self.main_window.canvas_view.viewport().update()
            
            # Restore component counts if available
            self.restoreComponentCounts(topology_data)
            
            # Scan and initialize numbering based on loaded components
            from gui.components import NetworkComponent
            NetworkComponent.scanAndInitializeNumbering(self.main_window)
            
            progress.setValue(100)
            QApplication.processEvents()
            
            self.main_window.current_file = filename
            # Clear template flags when loading a regular file
            self.main_window.is_template_loaded = False
            if hasattr(self.main_window, 'template_name'):
                del self.main_window.template_name
            # Mark as saved since file was just loaded
            if hasattr(self.main_window, 'markAsSaved'):
                self.main_window.markAsSaved()
            else:
                # Fallback for older versions
                if hasattr(self.main_window, 'setWindowTitle'):
                    self.main_window.setWindowTitle(f"NetFlux5G Editor - {os.path.basename(filename)}")
            self.main_window.status_manager.showCanvasStatus(f"Topology loaded: {len(nodes)} components, {len(links)} links")
            debug_print(f"DEBUG: Topology loaded successfully from {filename}")
            
            progress.close()
            
            # Show success message
            QMessageBox.information(
                self.main_window,
                "Topology Loaded",
                f"Successfully loaded topology:\n\n"
                f"Components: {len(nodes)}\n"
                f"Links: {len(links)}\n"
                f"File: {os.path.basename(filename)}"
            )
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
                
            error_msg = f"Error loading topology: {str(e)}"
            self.main_window.status_manager.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()
            
            # Show error dialog
            QMessageBox.critical(
                self.main_window,
                "Error Loading Topology",
                f"Failed to load topology file:\n\n{error_msg}\n\nPlease check the file format and try again."
            )

    def loadJsonFile(self, filename):
        """Load JSON topology file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to read JSON file: {str(e)}")

    def loadYamlFile(self, filename):
        """Load YAML topology file and convert to standard format."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Convert YAML format to standard topology format if needed
            if self.isYamlTopologyFormat(yaml_data):
                return self.convertYamlToTopologyFormat(yaml_data)
            else:
                return yaml_data
                
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to read YAML file: {str(e)}")

    def isYamlTopologyFormat(self, yaml_data):
        """Check if YAML data is in topology format."""
        return isinstance(yaml_data, dict) and ('nodes' in yaml_data or 'components' in yaml_data)

    def convertYamlToTopologyFormat(self, yaml_data):
        """Convert YAML topology format to standard JSON format."""
        # Basic conversion - extend this based on your YAML topology format
        topology_data = {
            "version": "1.1",
            "type": "NetFlux5G_Topology",
            "metadata": {
                "converted_from": "YAML",
                "created_date": QDateTime.currentDateTime().toString(),
                "editor_version": "2.0"
            },
            "nodes": yaml_data.get('nodes', yaml_data.get('components', [])),
            "links": yaml_data.get('links', yaml_data.get('connections', [])),
            "canvas_properties": yaml_data.get('canvas_properties', {})
        }
        return topology_data

    def validateTopologyFile(self, topology_data):
        """Validate topology file format."""
        if not isinstance(topology_data, dict):
            error_print("ERROR: Topology data is not a dictionary")
            return False
            
        if 'nodes' not in topology_data and 'components' not in topology_data:
            error_print("ERROR: No 'nodes' or 'components' section found")
            return False
            
        # Check for required fields in nodes
        nodes = topology_data.get('nodes', topology_data.get('components', []))
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                error_print(f"ERROR: Node {i} is not a dictionary")
                return False
                
            required_fields = ['name', 'type']
            for field in required_fields:
                if field not in node:
                    warning_print(f"WARNING: Node {i} missing required field '{field}'")
        
        debug_print("DEBUG: Topology file validation passed")
        return True

    def loadCanvasProperties(self, topology_data):
        """Load and apply canvas properties."""
        try:
            canvas_props = topology_data.get('canvas_properties', {})
            
            # Restore zoom level
            if hasattr(self.main_window, 'canvas_view') and 'zoom_level' in canvas_props:
                zoom_level = canvas_props['zoom_level']
                if zoom_level != 1.0:
                    # Reset to 1.0 first, then apply the saved zoom
                    self.main_window.canvas_view.resetZoom()
                    scale_factor = zoom_level
                    self.main_window.canvas_view.scale(scale_factor, scale_factor)
                    self.main_window.canvas_view.zoom_level = zoom_level
                    debug_print(f"DEBUG: Restored zoom level to {zoom_level}")
            
            # Restore grid state
            if 'show_grid' in canvas_props:
                show_grid = canvas_props['show_grid']
                self.main_window.show_grid = show_grid
                if hasattr(self.main_window, 'canvas_view'):
                    self.main_window.canvas_view.setShowGrid(show_grid)
                if hasattr(self.main_window, 'actionShowGrid'):
                    self.main_window.actionShowGrid.setChecked(show_grid)
                debug_print(f"DEBUG: Restored grid state to {show_grid}")
                
        except Exception as e:
            warning_print(f"WARNING: Failed to load canvas properties: {e}")

    def restoreComponentCounts(self, topology_data):
        """Restore component counts to ensure proper numbering for new components."""
        try:
            metadata = topology_data.get('metadata', {})
            if 'component_counts' in metadata:
                # Update the component counts in NetworkComponent class
                from gui.components import NetworkComponent
                stored_counts = metadata['component_counts']
                
                for comp_type, count in stored_counts.items():
                    if comp_type in NetworkComponent.component_counts:
                        NetworkComponent.component_counts[comp_type] = max(
                            NetworkComponent.component_counts[comp_type], 
                            count
                        )
                
                debug_print(f"DEBUG: Restored component counts: {stored_counts}")
                
        except Exception as e:
            warning_print(f"WARNING: Failed to restore component counts: {e}")

    def createComponentFromData(self, node_data):
        """Create a component from saved node data with enhanced configuration restoration."""
        try:
            component_type = node_data.get('type')
            name = node_data.get('name')
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            properties = node_data.get('properties', {})
            
            # Validate component type
            if component_type not in self.main_window.component_icon_map:
                warning_print(f"WARNING: Unknown component type: {component_type}")
                return None
            
            icon_path = self.main_window.component_icon_map.get(component_type)
            if not icon_path or not os.path.exists(icon_path):
                warning_print(f"WARNING: Icon not found for {component_type} at {icon_path}")
                return None
            
            from gui.components import NetworkComponent
            component = NetworkComponent(component_type, icon_path, main_window=self.main_window)
            
            # Set position
            component.setPosition(x, y)
            
            # Restore name and properties
            component.display_name = name
            # Resolve relative config file paths before setting properties
            if component_type == 'VGcore':
                self.resolveConfigFilePaths(properties)
            component.setProperties(properties)
            
            # Add to scene
            self.main_window.canvas_view.scene.addItem(component)
            
            # Special handling for 5G Core components with imported configurations
            if component_type == 'VGcore':
                self.restore5GCoreConfigurations(component, properties)
            
            debug_print(f"DEBUG: Created component {name} of type {component_type} at ({x}, {y})")
            return component
            
        except Exception as e:
            error_print(f"ERROR: Failed to create component from data: {e}")
            traceback.print_exc()
            return None

    def resolveConfigFilePaths(self, properties):
        """Resolve relative config file paths to absolute paths based on project root."""
        try:
            # Get the project root directory (where main.py is located)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Component types that might have configurations
            component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
            
            for comp_type in component_types:
                config_key = f"{comp_type}_configs"
                if config_key in properties:
                    configs = properties[config_key]
                    if isinstance(configs, list):
                        for config in configs:
                            if 'config_file_path' in config:
                                file_path = config['config_file_path']
                                # If it's a relative path starting with ./
                                if file_path.startswith('./'):
                                    # Convert to absolute path relative to project root
                                    absolute_path = os.path.join(project_root, file_path[2:])
                                    config['config_file_path'] = absolute_path
                                    debug_print(f"DEBUG: Resolved config path: {file_path} -> {absolute_path}")
                                elif not os.path.isabs(file_path) and file_path:
                                    # Handle other relative paths
                                    absolute_path = os.path.join(project_root, file_path)
                                    config['config_file_path'] = absolute_path
                                    debug_print(f"DEBUG: Resolved relative config path: {file_path} -> {absolute_path}")
            
        except Exception as e:
            warning_print(f"WARNING: Failed to resolve config file paths: {e}")

    def restore5GCoreConfigurations(self, component, properties):
        """Restore 5G Core component configurations including imported YAML files."""
        try:
            # Component types that might have configurations
            component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
            
            for comp_type in component_types:
                config_key = f"{comp_type}_configs"
                if config_key in properties:
                    configs = properties[config_key]
                    if isinstance(configs, list):
                        for config in configs:
                            # If this configuration was imported from a YAML file
                            if config.get('imported', False) and config.get('config_content'):
                                debug_print(f"DEBUG: Restored imported {comp_type} configuration")
                                # The configuration is already stored in properties, 
                                # it will be available when the properties dialog is opened
                                
        except Exception as e:
            warning_print(f"WARNING: Failed to restore 5G Core configurations: {e}")

    def createLinkFromData(self, link_data, node_map):
        """Create a link from saved link data with enhanced properties."""
        try:
            source_name = link_data.get('source')
            dest_name = link_data.get('destination') or link_data.get('dest')  # Support both field names
            link_type = link_data.get('type', 'ethernet')
            properties = link_data.get('properties', {})
            
            source_component = node_map.get(source_name)
            dest_component = node_map.get(dest_name)
            
            if not source_component or not dest_component:
                warning_print(f"WARNING: Could not find components for link {source_name} -> {dest_name}")
                # Try to find components by alternative matching
                source_component = self.findComponentByAlternativeName(source_name, node_map)
                dest_component = self.findComponentByAlternativeName(dest_name, node_map)
                
                if not source_component or not dest_component:
                    warning_print(f"WARNING: Still could not find components for link, skipping")
                    return None
            
            from gui.links import NetworkLink
            link = NetworkLink(source_component, dest_component, main_window=self.main_window)
            link.link_type = link_type
            link.properties = properties
            
            # Set additional link properties if available
            if 'name' in link_data:
                link.name = link_data['name']
            
            self.main_window.canvas_view.scene.addItem(link)
            debug_print(f"DEBUG: Created link from {source_name} to {dest_name}")
            return link
            
        except Exception as e:
            error_print(f"ERROR: Failed to create link from data: {e}")
            traceback.print_exc()
            return None

    def findComponentByAlternativeName(self, name, node_map):
        """Try to find a component by alternative name matching."""
        # Try exact match first
        if name in node_map:
            return node_map[name]
        
        # Try case-insensitive match
        for node_name, component in node_map.items():
            if node_name.lower() == name.lower():
                return component
        
        # Try partial match
        for node_name, component in node_map.items():
            if name in node_name or node_name in name:
                return component
        
        return None

    def extractTopology(self):
        """Extract all nodes and links from the canvas with enhanced configuration preservation."""
        nodes = []
        links = []
        
        if not hasattr(self.main_window, 'canvas_view') or not hasattr(self.main_window.canvas_view, 'scene'):
            return nodes, links
        
        from gui.links import NetworkLink
        
        for item in self.main_window.canvas_view.scene.items():
            if hasattr(item, 'component_type'):  # NetworkComponent
                # Extract comprehensive node data
                node_data = {
                    'name': getattr(item, 'display_name', item.component_type),
                    'type': item.component_type,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'properties': item.getProperties() if hasattr(item, 'getProperties') else {},
                    'created_date': QDateTime.currentDateTime().toString(),
                    'component_id': id(item)  # Unique identifier
                }
                
                # Add additional metadata for special component types
                if item.component_type == 'VGcore':
                    # Ensure 5G Core configurations are properly preserved
                    self.ensure5GCoreConfigsInProperties(node_data)
                
                nodes.append(node_data)
                
            elif isinstance(item, NetworkLink):  # NetworkLink
                source_name = getattr(item.source_node, 'display_name', 
                                    getattr(item.source_node, 'component_type', 'Unknown'))
                dest_name = getattr(item.dest_node, 'display_name', 
                                  getattr(item.dest_node, 'component_type', 'Unknown'))
                
                link_data = {
                    'source': source_name,
                    'destination': dest_name,
                    'type': getattr(item, 'link_type', 'ethernet'),
                    'properties': getattr(item, 'properties', {}),
                    'name': getattr(item, 'name', f"link_{len(links)}"),
                    'created_date': QDateTime.currentDateTime().toString()
                }
                links.append(link_data)
        
        debug_print(f"DEBUG: Total extracted - {len(nodes)} nodes, {len(links)} links")
        return nodes, links

    def ensure5GCoreConfigsInProperties(self, node_data):
        """Ensure 5G Core component configurations are properly included in properties."""
        try:
            properties = node_data.get('properties', {})
            
            # Check if we have any 5G component configurations
            component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
            
            for comp_type in component_types:
                config_key = f"{comp_type}_configs"
                if config_key in properties:
                    configs = properties[config_key]
                    if isinstance(configs, list):
                        # Ensure all configuration data is properly serializable
                        for config in configs:
                            if 'config_content' in config and isinstance(config['config_content'], dict):
                                # YAML content is already in dict format, which is JSON serializable
                                pass
                            # Ensure all fields are present
                            if 'imported' not in config:
                                config['imported'] = False
                            if 'config_file_path' not in config:
                                config['config_file_path'] = ''
                                
        except Exception as e:
            warning_print(f"WARNING: Failed to ensure 5G Core configs in properties: {e}")

    def loadConfigurationFile(self, config_file_path):
        """Load a configuration file (YAML or JSON) and return its content."""
        try:
            if not os.path.exists(config_file_path):
                raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
            
            file_ext = os.path.splitext(config_file_path)[1].lower()
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                if file_ext in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif file_ext == '.json':
                    return json.load(f)
                else:
                    # Try to detect format by content
                    content = f.read()
                    f.seek(0)
                    
                    # Try YAML first
                    try:
                        return yaml.safe_load(f)
                    except yaml.YAMLError:
                        # Try JSON
                        f.seek(0)
                        try:
                            return json.load(f)
                        except json.JSONDecodeError:
                            raise ValueError("Unknown configuration file format")
                            
        except Exception as e:
            error_print(f"ERROR: Failed to load configuration file {config_file_path}: {e}")
            return None

    def importTopologyFromTemplate(self, template_name):
        """Import topology from a predefined template."""
        try:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "templates"
            )
            
            template_file = os.path.join(templates_dir, f"{template_name}.nf5g")
            
            if os.path.exists(template_file):
                self.loadTopologyFromFile(template_file)
                self.main_window.status_manager.showCanvasStatus(f"Template '{template_name}' loaded successfully")
                debug_print(f"DEBUG: Template {template_name} loaded from {template_file}")
            else:
                warning_print(f"WARNING: Template file not found: {template_file}")
                self.main_window.status_manager.showCanvasStatus(f"Template '{template_name}' not found")
                
        except Exception as e:
            error_print(f"ERROR: Failed to import template {template_name}: {e}")

    def exportTopologyAsTemplate(self, template_name):
        """Export current topology as a reusable template."""
        try:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "templates"
            )
            
            # Create templates directory if it doesn't exist
            os.makedirs(templates_dir, exist_ok=True)
            
            template_file = os.path.join(templates_dir, f"{template_name}.nf5g")
            self.saveTopologyToFile(template_file)
            
            self.main_window.status_manager.showCanvasStatus(f"Template '{template_name}' saved successfully")
            debug_print(f"DEBUG: Template {template_name} saved to {template_file}")
            
        except Exception as e:
            error_print(f"ERROR: Failed to export template {template_name}: {e}")

    def loadExampleTemplate(self, template_name):
        """Load a specific example template."""
        try:
            examples_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "examples"
            )
            
            template_files = {
                "basic_5g_topology": "basic_5g_topology.nf5g",
                "multi_ran_deployment": "multi_ran_deployment.nf5g",
                "sdn_topology": "sdn_topology.nf5g"
            }
            
            if template_name in template_files:
                template_file = os.path.join(examples_path, template_files[template_name])
                if os.path.exists(template_file):
                    self.loadTopologyFromFile(template_file)
                    # Mark as template - clear current_file to force Save As behavior
                    self.main_window.current_file = None
                    self.main_window.is_template_loaded = True
                    self.main_window.template_name = template_name
                    # Update window title to show template status
                    if hasattr(self.main_window, 'setWindowTitle'):
                        self.main_window.setWindowTitle(f"NetFlux5G Editor - Template: {template_name} (Unsaved)")
                    self.main_window.status_manager.showCanvasStatus(f"Loaded template: {template_name}")
                    debug_print(f"DEBUG: Template {template_name} loaded from {template_file}")
                    return True
                else:
                    warning_print(f"Template file not found: {template_file}")
                    self.main_window.status_manager.showCanvasStatus(f"Template file not found: {template_name}")
                    return False
            else:
                warning_print(f"Unknown template: {template_name}")
                self.main_window.status_manager.showCanvasStatus(f"Unknown template: {template_name}")
                return False
                
        except Exception as e:
            error_print(f"Failed to load template {template_name}: {e}")
            self.main_window.status_manager.showCanvasStatus(f"Failed to load template: {str(e)}")
            return False