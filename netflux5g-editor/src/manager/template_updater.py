"""
Template Configuration Updater for NetFlux5G Editor

This module automatically updates template files (.nf5g) to ensure config_file_path
and config_path values are correctly set for the current installation directory.
This ensures templates work correctly regardless of where the application is installed.
"""

import os
import json
import glob
from manager.debug import debug_print, error_print, warning_print

class TemplateUpdater:
    """Updates template files to use correct config paths for the current installation."""
    
    def __init__(self, main_window=None):
        self.main_window = main_window
        # Get the base directory of the NetFlux5G installation
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_base_path = os.path.join(self.base_dir, "export", "5g-configs")
        
    def update_all_templates(self):
        """Update all template files in the examples directory."""
        try:
            examples_dir = os.path.join(self.base_dir, "examples")
            
            if not os.path.exists(examples_dir):
                warning_print(f"Examples directory not found: {examples_dir}")
                return False
            
            # Find all .nf5g files in the examples directory
            template_files = glob.glob(os.path.join(examples_dir, "*.nf5g"))
            
            if not template_files:
                warning_print("No template files found in examples directory")
                return False
            
            updated_count = 0
            for template_file in template_files:
                if self.update_template_file(template_file):
                    updated_count += 1
                    
            debug_print(f"Updated {updated_count} template files with correct config paths")
            return True
            
        except Exception as e:
            error_print(f"Error updating templates: {e}")
            return False
    
    def update_template_file(self, template_file):
        """Update a single template file with correct config paths."""
        try:
            debug_print(f"Updating template: {os.path.basename(template_file)}")
            
            # Read the template file
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Track if any changes were made
            changes_made = False
            
            # Update nodes with VGcore (5G core) components
            if 'nodes' in template_data:
                for node in template_data['nodes']:
                    if node.get('type') == 'VGcore':
                        if self.update_node_config_paths(node):
                            changes_made = True
            
            # Save the file if changes were made
            if changes_made:
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
                debug_print(f"Successfully updated {os.path.basename(template_file)}")
                return True
            else:
                debug_print(f"No changes needed for {os.path.basename(template_file)}")
                return False
                
        except Exception as e:
            error_print(f"Error updating template file {template_file}: {e}")
            return False
    
    def update_node_config_paths(self, node):
        """Update config paths for a single node."""
        changes_made = False
        
        try:
            properties = node.get('properties', {})
            
            # Update main config_file_path and config_path
            if 'config_file_path' in properties:
                old_path = properties['config_file_path']
                if old_path:  # Only update if there's a value
                    filename = os.path.basename(old_path)
                    new_path = os.path.join(self.config_base_path, filename)
                    if old_path != new_path:
                        properties['config_file_path'] = new_path
                        changes_made = True
                        debug_print(f"Updated config_file_path: {filename}")
            
            if 'config_path' in properties:
                old_path = properties['config_path']
                if old_path:  # Only update if there's a value
                    filename = os.path.basename(old_path)
                    new_path = os.path.join(self.config_base_path, filename)
                    if old_path != new_path:
                        properties['config_path'] = new_path
                        changes_made = True
                        debug_print(f"Updated config_path: {filename}")
            
            # Update nested 5G core configurations for each component type
            config_types = ['UPF_configs', 'AMF_configs', 'SMF_configs', 'NRF_configs', 
                           'SCP_configs', 'AUSF_configs', 'BSF_configs', 'NSSF_configs', 
                           'PCF_configs', 'UDM_configs', 'UDR_configs', 'WEBUI_configs']
            
            for config_type in config_types:
                if config_type in properties and isinstance(properties[config_type], list):
                    for core_config in properties[config_type]:
                        if self.update_core_config_paths(core_config):
                            changes_made = True
            
            # Also update legacy core_configs if present
            if 'core_configs' in properties:
                if isinstance(properties['core_configs'], list):
                    for core_config in properties['core_configs']:
                        if self.update_core_config_paths(core_config):
                            changes_made = True
            
            return changes_made
            
        except Exception as e:
            error_print(f"Error updating node config paths: {e}")
            return False
    
    def update_core_config_paths(self, core_config):
        """Update config paths in core configuration objects."""
        changes_made = False
        
        try:
            # Update config_file_path in core config
            if 'config_file_path' in core_config:
                old_path = core_config['config_file_path']
                if old_path:  # Only update if there's a value
                    filename = os.path.basename(old_path)
                    new_path = os.path.join(self.config_base_path, filename)
                    if old_path != new_path:
                        core_config['config_file_path'] = new_path
                        changes_made = True
                        debug_print(f"Updated core config_file_path: {filename}")
            
            # Update config_path in core config
            if 'config_path' in core_config:
                old_path = core_config['config_path']
                if old_path:  # Only update if there's a value
                    filename = os.path.basename(old_path)
                    new_path = os.path.join(self.config_base_path, filename)
                    if old_path != new_path:
                        core_config['config_path'] = new_path
                        changes_made = True
                        debug_print(f"Updated core config_path: {filename}")
            
            return changes_made
            
        except Exception as e:
            error_print(f"Error updating core config paths: {e}")
            return False
    
    def get_config_base_path(self):
        """Get the base configuration path for the current installation."""
        return self.config_base_path
    
    def validate_config_directory(self):
        """Validate that the config directory exists and contains expected files."""
        try:
            if not os.path.exists(self.config_base_path):
                warning_print(f"Config directory does not exist: {self.config_base_path}")
                return False
            
            # Check for some expected config files
            expected_files = ['amf.yaml', 'smf.yaml', 'upf.yaml', 'nrf.yaml']
            found_files = []
            
            for expected_file in expected_files:
                config_file = os.path.join(self.config_base_path, expected_file)
                if os.path.exists(config_file):
                    found_files.append(expected_file)
            
            if found_files:
                debug_print(f"Found {len(found_files)} config files in {self.config_base_path}")
                return True
            else:
                warning_print(f"No expected config files found in {self.config_base_path}")
                return False
                
        except Exception as e:
            error_print(f"Error validating config directory: {e}")
            return False
    
    def get_status_report(self):
        """Get a status report of the template updater."""
        try:
            examples_dir = os.path.join(self.base_dir, "examples")
            template_files = glob.glob(os.path.join(examples_dir, "*.nf5g"))
            
            report = {
                'base_dir': self.base_dir,
                'config_base_path': self.config_base_path,
                'examples_dir': examples_dir,
                'template_count': len(template_files),
                'template_files': [os.path.basename(f) for f in template_files],
                'config_dir_exists': os.path.exists(self.config_base_path),
                'examples_dir_exists': os.path.exists(examples_dir)
            }
            
            return report
            
        except Exception as e:
            error_print(f"Error generating status report: {e}")
            return None
