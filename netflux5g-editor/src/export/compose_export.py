import os
import yaml
import shutil
import traceback
from PyQt5.QtWidgets import QFileDialog
from manager.debug_manager import debug_print, error_print, warning_print

class DockerComposeExporter:
    """Handler for exporting 5G Core components to Docker Compose configuration."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def export_to_docker_compose(self):
        """Export 5G Core components to docker-compose.yaml and configuration files."""
        # Ask user to select export directory
        export_dir = QFileDialog.getExistingDirectory(
            self.main_window, 
            "Select Export Directory for Docker Compose", 
            ""
        )
        if export_dir:
            self.export_docker_compose_files(export_dir)

    def export_docker_compose_files(self, export_dir):
        """Export docker-compose.yaml and configuration files for 5G Core components."""
        try:
            # Extract 5G Core components from the topology
            nodes, links = self.main_window.extractTopology()
            core5g_components = [n for n in nodes if n['type'] == 'VGcore']
            
            if not core5g_components:
                self.main_window.showCanvasStatus("No 5G Core components found to export!")
                return
            
            # Create config directory
            config_dir = os.path.join(export_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Generate docker-compose.yaml
            docker_compose_data = self.generate_docker_compose_config(core5g_components)
            
            # Write docker-compose.yaml
            compose_file = os.path.join(export_dir, "docker-compose.yaml")
            with open(compose_file, 'w') as f:
                yaml.dump(docker_compose_data, f, default_flow_style=False, sort_keys=False)
            
            # Generate configuration files for each component
            self.generate_configuration_files(core5g_components, config_dir)
            
            # Copy entrypoint.sh if it exists in the reference config
            self.copy_entrypoint_script(config_dir)
            
            self.main_window.showCanvasStatus(f"Docker Compose files exported to {export_dir}")
            debug_print(f"DEBUG: Docker Compose export completed to {export_dir}")
            
        except Exception as e:
            error_msg = f"Error exporting Docker Compose: {str(e)}"
            self.main_window.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def generate_docker_compose_config(self, core5g_components):
        """Generate docker-compose configuration based on 5G Core components."""
        services = {}
        
        # Group components by type and extract their configurations
        component_configs = self.extract_5g_component_configurations(core5g_components)
        
        # Define dependency chain for 5G Core components
        dependency_chain = {
            'NRF': [],
            'SCP': ['nrf'],
            'UDR': ['scp'],
            'UDM': ['scp'],
            'AUSF': ['scp'],
            'BSF': ['scp'],
            'NSSF': ['nrf', 'scp'],
            'AMF': ['scp'],
            'SMF': ['scp'],
            'PCF': ['scp'],
            'PCRF': [],
            'UPF': ['scp']
        }
        
        # Generate services for each component type
        for component_type, instances in component_configs.items():
            for instance in instances:
                service_name = instance['name'].lower().replace(' ', '_').replace('#', '')
                
                # Base service configuration
                service_config = {
                    'image': instance.get('image', 'adaptive/open5gs:1.0'),
                    'restart': 'on-failure',
                    'privileged': True,
                    'volumes': []
                }
                
                # Add component-specific configurations
                service_config.update(self.get_component_specific_config(component_type, instance))
                
                # Add dependencies
                dependencies = dependency_chain.get(component_type, [])
                if dependencies:
                    # Check if dependent services exist
                    existing_deps = []
                    for dep in dependencies:
                        if any(dep in svc_name for svc_name in services.keys()):
                            existing_deps.append(dep)
                    
                    if existing_deps:
                        if component_type in ['PCF', 'UDR']:
                            # Use condition for services that need database
                            service_config['depends_on'] = {
                                dep: {'condition': 'service_started'} for dep in existing_deps
                            }
                        else:
                            service_config['depends_on'] = existing_deps
                
                # Add volume bindings for configuration files
                config_file = f"{service_name}.yaml"
                service_config['volumes'].extend([
                    {
                        'type': 'bind',
                        'source': f'./config/{config_file}',
                        'target': f'/opt/open5gs/etc/open5gs/{component_type.lower()}.yaml'
                    },
                    {
                        'type': 'bind',
                        'source': './config/entrypoint.sh',
                        'target': '/opt/open5gs/etc/open5gs/entrypoint.sh'
                    }
                ])
                
                # Add any custom volume mappings from properties
                if 'volumes' in instance and instance['volumes']:
                    for volume in instance['volumes']:
                        service_config['volumes'].append(volume)
                
                services[service_name] = service_config
        
        return {'services': services}

    def get_component_specific_config(self, component_type, instance):
        """Get component-specific configuration."""
        config = {}
        
        if component_type == 'UPF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-upfd'],
                'cap_add': ['all'],
            })
            
        elif component_type == 'AMF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-amfd'],
                'cap_add': ['net_admin'],
            })
            
        elif component_type == 'SMF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-smfd'],
            })
            
        elif component_type == 'NRF':
            config.update({
                'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-nrfd',
            })
            
        elif component_type == 'SCP':
            config.update({
                'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-scpd',
            })
            
        elif component_type == 'AUSF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-ausfd'],
            })
            
        elif component_type == 'BSF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-bsfd'],
            })
            
        elif component_type == 'NSSF':
            config.update({
                'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-nssfd',
            })
            
        elif component_type == 'PCF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-pcfd'],
                'environment': {'DB_URI': 'mongodb://10.0.0.220/open5gs'}
            })
            
        elif component_type == 'PCRF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-pcrfd'],
                'environment': {'DB_URI': 'mongodb://10.0.0.220/open5gs'}
            })
            
        elif component_type == 'UDM':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-udmd'],
            })
            
        elif component_type == 'UDR':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-udrd'],
                'environment': {'DB_URI': 'mongodb://10.0.0.220/open5gs'}
            })
        
        return config

    def extract_5g_component_configurations(self, core5g_components):
        """Extract configurations from 5G Core components properties."""
        component_configs = {
            'UPF': [], 'AMF': [], 'SMF': [], 'NRF': [], 'SCP': [],
            'AUSF': [], 'BSF': [], 'NSSF': [], 'PCF': [], 'PCRF': [],
            'UDM': [], 'UDR': []
        }
        
        for component in core5g_components:
            props = component.get('properties', {})
            
            # Extract configurations for each component type
            for comp_type in component_configs.keys():
                configs = self.extract_component_type_configs(props, comp_type)
                component_configs[comp_type].extend(configs)
        
        return component_configs

    def extract_component_type_configs(self, properties, component_type):
        """Extract configurations for a specific component type from properties."""
        configs = []
        
        # Look for table data or stored configurations
        config_key = f"{component_type}_configs"
        if config_key in properties:
            stored_configs = properties[config_key]
            if isinstance(stored_configs, list):
                # Process each stored configuration
                for config in stored_configs:
                    # Ensure the config has all necessary fields
                    processed_config = {
                        'name': config.get('name', f"{component_type.lower()}1"),
                        'image': config.get('image', 'adaptive/open5gs:1.0'),
                        'config_file': config.get('config_file', f"{component_type.lower()}.yaml"),
                        'volumes': config.get('volumes', []),
                        'component_type': component_type,
                        'imported': config.get('imported', False),
                        'config_content': config.get('config_content', {}),
                        'config_file_path': config.get('config_file_path', ''),
                        'settings': config.get('settings', '')
                    }
                    configs.append(processed_config)
        
        # Fallback: create a default configuration if none exists but component is present
        if not configs:
            # Check if this component type is actually being used
            component_type_key = f"Component5G_Type"
            if component_type_key in properties and properties[component_type_key] == component_type:
                default_config = {
                    'name': f"{component_type.lower()}1",
                    'image': 'adaptive/open5gs:1.0',
                    'config_file': f"{component_type.lower()}.yaml",
                    'volumes': [],
                    'component_type': component_type,
                    'imported': False,
                    'config_content': {},
                    'config_file_path': '',
                    'settings': ''
                }
                configs.append(default_config)
        
        return configs

    def generate_configuration_files(self, core5g_components, config_dir):
        """Generate configuration files for each 5G Core component."""
        try:
            # Extract component configurations
            component_configs = self.extract_5g_component_configurations(core5g_components)
            
            # Base path for template configurations
            template_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "5g-configs")
            
            for component_type, instances in component_configs.items():
                for instance in instances:
                    service_name = instance['name'].lower().replace(' ', '_').replace('#', '')
                    config_filename = f"{service_name}.yaml"
                    config_file_path = os.path.join(config_dir, config_filename)
                    
                    # Check if this component has an imported configuration
                    if instance.get('imported', False) and instance.get('config_content'):
                        # Use the imported configuration
                        self.write_imported_config_file(config_file_path, instance, component_type)
                        debug_print(f"DEBUG: Used imported config for {service_name}")
                    elif instance.get('config_file_path') and os.path.exists(instance['config_file_path']):
                        # Copy from the imported file path
                        shutil.copy2(instance['config_file_path'], config_file_path)
                        self.customize_config_file(config_file_path, instance, component_type)
                        debug_print(f"DEBUG: Copied imported config from {instance['config_file_path']}")
                    else:
                        # Try to copy from template or create default config
                        template_file = os.path.join(template_config_path, f"{component_type.lower()}.yaml")
                        
                        if os.path.exists(template_file):
                            # Copy and modify template file
                            shutil.copy2(template_file, config_file_path)
                            self.customize_config_file(config_file_path, instance, component_type)
                            debug_print(f"DEBUG: Copied and customized config from template: {config_file_path}")
                        else:
                            # Create default configuration
                            self.create_default_config_file(config_file_path, instance, component_type)
                            debug_print(f"DEBUG: Created default config file: {config_file_path}")
            
        except Exception as e:
            error_print(f"ERROR: Failed to generate configuration files: {e}")
            traceback.print_exc()

    def write_imported_config_file(self, config_file_path, instance_config, component_type):
        """Write an imported configuration to a file with customizations."""
        try:
            # Get the imported configuration content
            config_data = instance_config.get('config_content', {})
            
            # Apply any additional customizations
            self.apply_instance_customizations(config_data, instance_config, component_type)
            
            # Write the configuration file
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                
            debug_print(f"DEBUG: Wrote imported configuration to {config_file_path}")
            
        except Exception as e:
            error_print(f"ERROR: Failed to write imported config file {config_file_path}: {e}")

    def apply_instance_customizations(self, config_data, instance_config, component_type):
        """Apply instance-specific customizations to imported configuration."""
        try:
            # Apply custom parameters from the settings field
            settings = instance_config.get('settings', '')
            if settings:
                # Parse settings (expecting key=value format, one per line)
                for line in settings.split('\n'):
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to apply to the main component section
                        main_section = component_type.lower()
                        if main_section in config_data and isinstance(config_data[main_section], dict):
                            # Try to convert value to appropriate type
                            if value.lower() in ['true', 'false']:
                                config_data[main_section][key] = value.lower() == 'true'
                            elif value.isdigit():
                                config_data[main_section][key] = int(value)
                            elif value.replace('.', '', 1).isdigit():
                                config_data[main_section][key] = float(value)
                            else:
                                config_data[main_section][key] = value
                                
            # Apply other instance-specific modifications based on component type
            if component_type == 'UPF':
                # Ensure unique identifiers for multiple UPF instances
                instance_name = instance_config.get('name', 'upf')
                if 'upf' in config_data and 'instance_id' not in config_data['upf']:
                    config_data['upf']['instance_id'] = instance_name
                    
            elif component_type == 'AMF':
                # Customize AMF instance identifiers
                instance_name = instance_config.get('name', 'amf')
                if 'amf' in config_data and 'amf_name' not in config_data['amf']:
                    config_data['amf']['amf_name'] = f"open5gs-{instance_name}"
            
            # Add any additional customizations based on component type and instance settings
            
        except Exception as e:
            error_print(f"ERROR: Failed to apply customizations to {component_type}: {e}")

    def customize_config_file(self, config_file_path, instance_config, component_type):
        """Customize a configuration file based on instance-specific settings."""
        try:
            # Load the existing configuration
            with open(config_file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Apply instance-specific customizations based on component type
            custom_params = instance_config.get('custom_parameters', {})
            
            if component_type == 'UPF':
                # Customize UPF-specific settings
                if 'upf' in config_data:
                    if 'session' in config_data['upf']:
                        # Apply custom session parameters
                        if 'subnet' in custom_params:
                            config_data['upf']['session'] = [{'subnet': custom_params['subnet']}]
                    
            elif component_type == 'AMF':
                # Customize AMF-specific settings
                if 'amf' in config_data:
                    if 'plmn_support' in config_data['amf'] and 'mcc' in custom_params:
                        for plmn in config_data['amf']['plmn_support']:
                            if 'plmn_id' in plmn:
                                plmn['plmn_id']['mcc'] = custom_params['mcc']
                                if 'mnc' in custom_params:
                                    plmn['plmn_id']['mnc'] = custom_params['mnc']
            
            # Apply any other custom parameters
            for key, value in custom_params.items():
                if key not in ['subnet', 'mcc', 'mnc']:  # Skip already processed params
                    # Try to apply to the component's main configuration section
                    main_section = component_type.lower()
                    if main_section in config_data and isinstance(config_data[main_section], dict):
                        config_data[main_section][key] = value
            
            # Write the modified configuration back
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
                
        except Exception as e:
            error_print(f"ERROR: Failed to customize config file {config_file_path}: {e}")

    def create_default_config_file(self, config_file_path, instance_config, component_type):
        """Create a default configuration file for a component type."""
        default_configs = {
            'UPF': {
                'logger': {'level': 'info'},
                'upf': {
                    'pfcp': [{'addr': '127.0.0.7'}],
                    'gtpu': [{'addr': '127.0.0.7'}],
                    'session': [{'subnet': '10.45.0.1/16'}, {'subnet': '2001:db8:cafe::1/48'}]
                }
            },
            'AMF': {
                'logger': {'level': 'info'},
                'amf': {
                    'sbi': [{'addr': '127.0.0.5', 'port': 7777}],
                    'ngap': [{'addr': '127.0.0.5'}],
                    'metrics': [{'addr': '127.0.0.5', 'port': 9090}],
                    'guami': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 'amf_id': {'region': 2, 'set': 1}}],
                    'tai': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 'tac': 1}],
                    'plmn_support': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 's_nssai': [{'sst': 1}]}],
                    'security': {'integrity_order': ['NIA2', 'NIA1', 'NIA0'], 'ciphering_order': ['NEA0', 'NEA1', 'NEA2']},
                    'network_name': {'full': 'Open5GS', 'short': 'Next'},
                    'amf_name': 'open5gs-amf0'
                }
            },
            'SMF': {
                'logger': {'level': 'info'},
                'smf': {
                    'sbi': [{'addr': '127.0.0.4', 'port': 7777}],
                    'pfcp': [{'addr': '127.0.0.4'}],
                    'gtpc': [{'addr': '127.0.0.4'}],
                    'gtpu': [{'addr': '127.0.0.4'}]
                }
            },
            'NRF': {
                'logger': {'level': 'info'},
                'nrf': {
                    'serving': [{'addr': '127.0.0.10', 'port': 7777}],
                    'sbi': [{'addr': '127.0.0.10', 'port': 7777}]
                }
            },
            'SCP': {
                'logger': {'level': 'info'},
                'scp': {
                    'sbi': [{'addr': '127.0.0.200', 'port': 7777}]
                }
            },
            'AUSF': {
                'logger': {'level': 'info'},
                'ausf': {
                    'sbi': [{'addr': '127.0.0.9', 'port': 7777}]
                }
            },
            'BSF': {
                'logger': {'level': 'info'},
                'bsf': {
                    'sbi': [{'addr': '127.0.0.15', 'port': 7777}]
                }
            },
            'NSSF': {
                'logger': {'level': 'info'},
                'nssf': {
                    'sbi': [{'addr': '127.0.0.14', 'port': 7777}],
                    'nsi': [{'addr': '127.0.0.14', 'port': 7777}]
                }
            },
            'PCF': {
                'logger': {'level': 'info'},
                'pcf': {
                    'sbi': [{'addr': '127.0.0.13', 'port': 7777}]
                }
            },
            'PCRF': {
                'logger': {'level': 'info'},
                'pcrf': {
                    'freeDiameter': '/opt/open5gs/etc/freeDiameter/pcrf.conf'
                }
            },
            'UDM': {
                'logger': {'level': 'info'},
                'udm': {
                    'sbi': [{'addr': '127.0.0.12', 'port': 7777}]
                }
            },
            'UDR': {
                'logger': {'level': 'info'},
                'udr': {
                    'sbi': [{'addr': '127.0.0.20', 'port': 7777}]
                }
            }
        }
        
        config_data = default_configs.get(component_type, {'logger': {'level': 'info'}})
        
        try:
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
        except Exception as e:
            error_print(f"ERROR: Failed to create default config file {config_file_path}: {e}")

    def copy_entrypoint_script(self, config_dir):
        """Copy the entrypoint.sh script to the config directory."""
        try:
            # Dynamically determine the path
            source_entrypoint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "5g-configs", "entrypoint.sh")
            dest_entrypoint = os.path.join(config_dir, "entrypoint.sh")
            
            if os.path.exists(source_entrypoint):
                shutil.copy2(source_entrypoint, dest_entrypoint)
                # Make sure it's executable
                os.chmod(dest_entrypoint, 0o755)
                debug_print(f"DEBUG: Copied entrypoint.sh to {dest_entrypoint}")
            else:
                # Create a basic entrypoint script
                self.create_default_entrypoint_script(dest_entrypoint)
                
        except Exception as e:
            error_print(f"ERROR: Failed to copy entrypoint script: {e}")

    def create_default_entrypoint_script(self, script_path):
        """Create a default entrypoint.sh script."""
        entrypoint_content = """#!/bin/bash

# Configure TUN interfaces for UPF
configure_upf_tun() {
    ip tuntap add name ogstun mode tun
    ip addr add 10.45.0.1/16 dev ogstun
    ip addr add 2001:db8:cafe::1/48 dev ogstun
    ip link set ogstun up

    ip tuntap add name ogstun2 mode tun  
    ip addr add 10.46.0.1/16 dev ogstun2
    ip link set ogstun2 up
}

# Check if we need to configure TUN interfaces
if [[ "$1" == *"upf"* ]]; then
    configure_upf_tun
fi

# Temporary patch to solve the case of docker internal dns not resolving "not running" container names.
# Just wait 10 seconds to be "running" and resolvable
if [[ "$1"  == *"open5gs-pcrfd" ]] \\
    || [[ "$1"  == *"open5gs-mmed" ]] \\
    || [[ "$1"  == *"open5gs-nrfd" ]] \\
    || [[ "$1"  == *"open5gs-scpd" ]] \\
    || [[ "$1"  == *"open5gs-pcfd" ]] \\
    || [[ "$1"  == *"open5gs-hssd" ]] \\
    || [[ "$1"  == *"open5gs-udrd" ]] \\
    || [[ "$1"  == *"open5gs-sgwcd" ]] \\
    || [[ "$1"  == *"open5gs-upfd" ]]; then
sleep 10
fi

# Execute the main command
exec "$@"

exit 1
"""
        
        try:
            with open(script_path, 'w') as f:
                f.write(entrypoint_content)
            os.chmod(script_path, 0o755)
            debug_print(f"DEBUG: Created default entrypoint.sh at {script_path}")
        except Exception as e:
            error_print(f"ERROR: Failed to create default entrypoint script: {e}")