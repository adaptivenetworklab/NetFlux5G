import os
import json
import yaml
import shutil
import traceback
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QDateTime
from manager.debug import debug_print, error_print, warning_print

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
            # Extract topology to analyze components
            nodes, links = self.main_window.extractTopology()
            
            # Find 5G Core components
            core5g_components = [n for n in nodes if n['type'] == 'VGcore']
            
            if not core5g_components:
                self.main_window.showCanvasStatus("No 5G Core components found to export!")
                return
            
            # Create config directory
            config_dir = os.path.join(export_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Extract component configurations from VGcore components
            component_configs = self.extract_5g_component_configurations(core5g_components)
            
            # Generate docker-compose.yaml based on ngc.yaml structure
            docker_compose_data = self.generate_docker_compose_config(component_configs)
            
            # Write docker-compose.yaml
            compose_file = os.path.join(export_dir, "docker-compose.yaml")
            with open(compose_file, 'w') as f:
                yaml.dump(docker_compose_data, f, default_flow_style=False, sort_keys=False)
            
            # Generate configuration files for each component
            self.generate_configuration_files(component_configs, config_dir)
            
            # Copy entrypoint.sh
            self.copy_entrypoint_script(config_dir)
            
            # Create MongoDB service if needed
            if self.requires_mongodb(component_configs):
                self.add_mongodb_service(docker_compose_data)
                # Write updated docker-compose.yaml with MongoDB
                with open(compose_file, 'w') as f:
                    yaml.dump(docker_compose_data, f, default_flow_style=False, sort_keys=False)
            
            self.main_window.showCanvasStatus(f"Docker Compose files exported to {export_dir}")
            debug_print(f"DEBUG: Docker Compose export completed to {export_dir}")
            
        except Exception as e:
            error_msg = f"Error exporting Docker Compose: {str(e)}"
            self.main_window.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

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
        
        # If no specific configurations found, create default set based on ngc.yaml
        if not any(component_configs.values()):
            component_configs = self.create_default_component_set()
            
        return component_configs

    def extract_component_type_configs(self, properties, component_type):
        """Extract configurations for a specific component type from properties."""
        configs = []
        
        # Look for table data or stored configurations
        config_key = f"{component_type}_configs"
        if config_key in properties:
            stored_configs = properties[config_key]
            if isinstance(stored_configs, list):
                for config in stored_configs:
                    configs.append(config)
        
        # Check if this component type is selected in the UI
        component_type_key = "Component5G_Type"
        if component_type_key in properties and properties[component_type_key] == component_type:
            default_config = {
                'name': f"{component_type.lower()}",
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

    def create_default_component_set(self):
        """Create a default set of 5G Core components based on ngc.yaml."""
        return {
            'NRF': [{'name': 'nrf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'nrf.yaml'}],
            'SCP': [{'name': 'scp', 'image': 'adaptive/open5gs:1.0', 'config_file': 'scp.yaml'}],
            'AMF': [{'name': 'amf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'amf.yaml'}],
            'SMF': [{'name': 'smf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'smf.yaml'}],
            'UPF': [{'name': 'upf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'upf.yaml'}],
            'AUSF': [{'name': 'ausf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'ausf.yaml'}],
            'BSF': [{'name': 'bsf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'bsf.yaml'}],
            'NSSF': [{'name': 'nssf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'nssf.yaml'}],
            'PCF': [{'name': 'pcf', 'image': 'adaptive/open5gs:1.0', 'config_file': 'pcf.yaml'}],
            'UDM': [{'name': 'udm', 'image': 'adaptive/open5gs:1.0', 'config_file': 'udm.yaml'}],
            'UDR': [{'name': 'udr', 'image': 'adaptive/open5gs:1.0', 'config_file': 'udr.yaml'}],
            'PCRF': [],  # Optional component
        }

    def generate_docker_compose_config(self, component_configs):
        """Generate docker-compose configuration based on ngc.yaml structure."""
        services = {}
        
        # Define dependency chain for 5G Core components (based on ngc.yaml)
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
                service_name = instance.get('name', f"{component_type.lower()}").lower().replace(' ', '_').replace('#', '')
                
                # Base service configuration
                service_config = {
                    'image': instance.get('image', 'adaptive/open5gs:1.0'),
                    'restart': 'on-failure',
                    'privileged': True,
                    'volumes': []
                }
                
                # Add component-specific configurations from ngc.yaml
                service_config.update(self.get_component_specific_config(component_type, instance, service_name))
                
                # Add dependencies
                dependencies = dependency_chain.get(component_type, [])
                if dependencies:
                    service_config['depends_on'] = dependencies
                
                # Add volume bindings for configuration files
                config_file = instance.get('config_file', f"{component_type.lower()}.yaml")
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
                custom_volumes = instance.get('volumes', [])
                if custom_volumes:
                    service_config['volumes'].extend(custom_volumes)
                
                services[service_name] = service_config
        
        return {'services': services}

    def get_component_specific_config(self, component_type, instance, service_name):
        """Get component-specific configuration based on ngc.yaml."""
        config = {}
        
        if component_type == 'UPF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-upfd'],
                'cap_add': ['net_admin'],
            })
            
        elif component_type == 'AMF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-amfd'],
                'cap_add': ['net_admin'],
            })
            
        elif component_type == 'SMF':
            config.update({
                'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-smfd',
                'cap_add': ['net_admin'],
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
                'environment': {'DB_URI': 'mongodb://mongo/open5gs'}
            })
            
        elif component_type == 'PCRF':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-pcrfd'],
                'environment': {'DB_URI': 'mongodb://mongo/open5gs'}
            })
            
        elif component_type == 'UDM':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-udmd'],
            })
            
        elif component_type == 'UDR':
            config.update({
                'command': ['/opt/open5gs/etc/open5gs/entrypoint.sh', 'open5gs-udrd'],
                'environment': {'DB_URI': 'mongodb://mongo/open5gs'}
            })
        
        return config

    def requires_mongodb(self, component_configs):
        """Check if any components require MongoDB."""
        mongodb_components = ['PCF', 'PCRF', 'UDR']
        return any(component_configs.get(comp, []) for comp in mongodb_components)

    def add_mongodb_service(self, docker_compose_data):
        """Add MongoDB service to docker-compose configuration."""
        mongodb_service = {
            'image': 'mongo:latest',
            'restart': 'unless-stopped',
            'environment': {
                'MONGO_INITDB_ROOT_USERNAME': 'root',
                'MONGO_INITDB_ROOT_PASSWORD': 'example',
                'MONGO_INITDB_DATABASE': 'open5gs'
            },
            'volumes': [
                'mongodb_data:/data/db'
            ],
            'ports': ['27017:27017']
        }
        
        docker_compose_data['services']['mongo'] = mongodb_service
        
        # Add volumes section
        if 'volumes' not in docker_compose_data:
            docker_compose_data['volumes'] = {}
        docker_compose_data['volumes']['mongodb_data'] = {}

    def generate_configuration_files(self, component_configs, config_dir):
        """Generate configuration files for each 5G Core component."""
        try:
            # Base path for template configurations
            template_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "5g-configs")
            
            for component_type, instances in component_configs.items():
                for instance in instances:
                    service_name = instance.get('name', f"{component_type.lower()}")
                    config_file = instance.get('config_file', f"{component_type.lower()}.yaml")
                    config_file_path = os.path.join(config_dir, config_file)
                    
                    # Check if imported configuration exists
                    if instance.get('imported', False) and instance.get('config_content'):
                        self.write_imported_config_file(config_file_path, instance, component_type)
                    else:
                        # Use template configuration
                        template_file = os.path.join(template_config_path, f"{component_type.lower()}.yaml")
                        if os.path.exists(template_file):
                            shutil.copy2(template_file, config_file_path)
                            debug_print(f"DEBUG: Copied template config {template_file} to {config_file_path}")
                            
                            # Apply any customizations
                            if instance.get('settings'):
                                self.customize_config_file(config_file_path, instance, component_type)
                        else:
                            # Create default configuration
                            self.create_default_config_file(config_file_path, instance, component_type)
                            debug_print(f"DEBUG: Created default config for {component_type} at {config_file_path}")
            
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
                        # Apply setting to config (simplified - could be more sophisticated)
                        if key and value:
                            self.apply_config_setting(config_data, key, value, component_type)
                                
            # Apply other instance-specific modifications based on component type
            instance_name = instance_config.get('name', component_type.lower())
            
            if component_type == 'UPF':
                # Ensure unique identifiers for multiple UPF instances
                if 'upf' in config_data:
                    if 'metrics' in config_data['upf']:
                        # Customize metrics port for multiple instances
                        config_data['upf']['metrics']['server'][0]['port'] = 9090 + hash(instance_name) % 100
                    
            elif component_type == 'AMF':
                # Customize AMF instance identifiers
                if 'amf' in config_data and 'amf_name' not in config_data['amf']:
                    config_data['amf']['amf_name'] = f"open5gs-{instance_name}"
            
        except Exception as e:
            error_print(f"ERROR: Failed to apply customizations to {component_type}: {e}")

    def apply_config_setting(self, config_data, key, value, component_type):
        """Apply a specific configuration setting to the config data."""
        try:
            # Convert value to appropriate type
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            
            # Apply setting based on key pattern
            component_section = component_type.lower()
            if component_section in config_data:
                # Simple dot notation support (e.g., "sbi.port=7777")
                if '.' in key:
                    parts = key.split('.')
                    current = config_data[component_section]
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    config_data[component_section][key] = value
                    
        except Exception as e:
            error_print(f"ERROR: Failed to apply config setting {key}={value}: {e}")

    def customize_config_file(self, config_file_path, instance_config, component_type):
        """Customize a configuration file based on instance-specific settings."""
        try:
            # Load the existing configuration
            with open(config_file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Apply instance-specific customizations
            self.apply_instance_customizations(config_data, instance_config, component_type)
            
            # Write the modified configuration back
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                
        except Exception as e:
            error_print(f"ERROR: Failed to customize config file {config_file_path}: {e}")

    def create_default_config_file(self, config_file_path, instance_config, component_type):
        """Create a default configuration file for a component type."""
        default_configs = {
            'UPF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/upf.log'}},
                'upf': {
                    'pfcp': {'server': [{'dev': 'eth0'}]},
                    'gtpu': {'server': [{'dev': 'eth0'}]},
                    'session': [
                        {'subnet': '10.100.0.0/16', 'gateway': '10.100.0.1', 'dnn': 'internet', 'dev': 'ogstun'},
                        {'subnet': '10.200.0.0/16', 'gateway': '10.200.0.1', 'dnn': 'internet2', 'dev': 'ogstun2'}
                    ],
                    'metrics': {'server': [{'dev': 'eth0', 'port': 9090}]}
                }
            },
            'AMF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/amf.log'}},
                'amf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}},
                    'ngap': {'server': [{'dev': 'eth0'}]},
                    'metrics': {'server': [{'dev': 'eth0', 'port': 9090}]},
                    'guami': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 'amf_id': {'region': 2, 'set': 1}}],
                    'tai': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 'tac': 1}],
                    'plmn_support': [{'plmn_id': {'mcc': '999', 'mnc': '70'}, 's_nssai': [{'sst': 1}]}],
                    'security': {'integrity_order': ['NIA2', 'NIA1', 'NIA0'], 'ciphering_order': ['NEA0', 'NEA1', 'NEA2']},
                    'network_name': {'full': 'Open5GS', 'short': 'Next'},
                    'amf_name': 'open5gs-amf0'
                }
            },
            'SMF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/smf.log'}},
                'smf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}},
                    'pfcp': {'server': [{'dev': 'eth0'}], 'client': {'upf': [{'address': 'upf', 'dnn': ['internet', 'internet2']}]}},
                    'gtpc': {'server': [{'dev': 'eth0'}]},
                    'gtpu': {'server': [{'dev': 'eth0'}]},
                    'metrics': {'server': [{'dev': 'eth0', 'port': 9090}]},
                    'session': [
                        {'subnet': '10.100.0.0/16', 'gateway': '10.100.0.1', 'dnn': 'internet'},
                        {'subnet': '10.200.0.0/16', 'gateway': '10.200.0.1', 'dnn': 'internet2'}
                    ],
                    'dns': ['1.1.1.1', '8.8.8.8'],
                    'mtu': 1400
                }
            },
            'NRF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/nrf.log'}},
                'nrf': {
                    'serving': [{'plmn_id': {'mcc': '999', 'mnc': '70'}}],
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}]}
                }
            },
            'SCP': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/scp.log'}},
                'scp': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'nrf': [{'uri': 'http://nrf:7777'}]}}
                }
            },
            'AUSF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/ausf.log'}},
                'ausf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}}
                }
            },
            'BSF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/bsf.log'}},
                'bsf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}}
                }
            },
            'NSSF': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/nssf.log'}},
                'nssf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}], 'nsi': [{'uri': 'http://nrf:7777', 's_nssai': {'sst': 1}}]}}
                }
            },
            'PCF': {
                'db_uri': 'mongodb://mongo/open5gs',
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/pcf.log'}},
                'pcf': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}},
                    'metrics': {'server': [{'dev': 'eth0', 'port': 9090}]}
                }
            },
            'UDM': {
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/udm.log'}},
                'udm': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}}
                }
            },
            'UDR': {
                'db_uri': 'mongodb://mongo/open5gs',
                'logger': {'file': {'path': '/opt/open5gs/var/log/open5gs/udr.log'}},
                'udr': {
                    'sbi': {'server': [{'dev': 'eth0', 'port': 7777}], 'client': {'scp': [{'uri': 'http://scp:7777'}]}}
                }
            }
        }
        
        config_data = default_configs.get(component_type, {'logger': {'file': {'path': f'/opt/open5gs/var/log/open5gs/{component_type.lower()}.log'}}})
        
        try:
            with open(config_file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            error_print(f"ERROR: Failed to create default config file {config_file_path}: {e}")

    def copy_entrypoint_script(self, config_dir):
        """Copy the entrypoint.sh script to the config directory."""
        try:
            # Try to find entrypoint.sh in the 5g-configs directory
            source_entrypoint = os.path.join(os.path.dirname(os.path.abspath(__file__)), "5g-configs", "entrypoint.sh")
            dest_entrypoint = os.path.join(config_dir, "entrypoint.sh")
            
            if os.path.exists(source_entrypoint):
                shutil.copy2(source_entrypoint, dest_entrypoint)
                # Make sure it's executable
                os.chmod(dest_entrypoint, 0o755)
                debug_print(f"DEBUG: Copied entrypoint.sh from {source_entrypoint} to {dest_entrypoint}")
            else:
                # Create a default entrypoint.sh script
                self.create_default_entrypoint_script(dest_entrypoint)
                
        except Exception as e:
            error_print(f"ERROR: Failed to copy entrypoint script: {e}")

    def create_default_entrypoint_script(self, script_path):
        """Create a default entrypoint.sh script based on the template."""
        entrypoint_content = '''#!/bin/bash

set -eo pipefail

# tun iface create
function tun_create {
    echo -e "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    if ! grep "ogstun" /proc/net/dev > /dev/null; then
        echo "Creating ogstun device"
        ip tuntap add name ogstun mode tun
    fi

    if ! grep "ogstun2" /proc/net/dev > /dev/null; then
        echo "Creating ogstun2 device"
        ip tuntap add name ogstun2 mode tun
    fi

    if ! grep "ogstun3" /proc/net/dev > /dev/null; then
        echo "Creating ogstun3 device"
        ip tuntap add name ogstun3 mode tun
    fi

    if ! grep "ogstun4" /proc/net/dev > /dev/null; then
        echo "Creating ogstun4 device"
        ip tuntap add name ogstun4 mode tun
    fi

    ip addr del 10.100.0.1/16 dev ogstun 2> /dev/null || true
    ip addr add 10.100.0.1/16 dev ogstun

    ip addr del 10.200.0.1/16 dev ogstun2 2> /dev/null || true
    ip addr add 10.200.0.1/16 dev ogstun2

    ip addr del 10.51.0.1/16 dev ogstun3 2> /dev/null || true
    ip addr add 10.51.0.1/16 dev ogstun3

    ip addr del 10.52.0.1/16 dev ogstun4 2> /dev/null || true
    ip addr add 10.52.0.1/16 dev ogstun4
    
    ip link set ogstun up
    ip link set ogstun2 up
    ip link set ogstun3 up
    ip link set ogstun4 up
    sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward";
    if [ "$ENABLE_NAT" = true ] ; then
      iptables -t nat -A POSTROUTING -s 10.100.0.0/16 ! -o ogstun -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.200.0.0/16 ! -o ogstun2 -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.51.0.0/16 ! -o ogstun3 -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.52.0.0/16 ! -o ogstun4 -j MASQUERADE
    fi
}
 
COMMAND=$1
if [[ "$COMMAND"  == *"open5gs-pgwd" ]] || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
tun_create
fi

# Temporary patch to solve the case of docker internal dns not resolving "not running" container names.
# Just wait 10 seconds to be "running" and resolvable
if [[ "$COMMAND"  == *"open5gs-pcrfd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-mmed" ]] \\
    || [[ "$COMMAND"  == *"open5gs-nrfd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-scpd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-pcfd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-hssd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-udrd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-sgwcd" ]] \\
    || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
sleep 10
fi

$@

exit 1
'''
        
        try:
            with open(script_path, 'w') as f:
                f.write(entrypoint_content)
            os.chmod(script_path, 0o755)
            debug_print(f"DEBUG: Created default entrypoint.sh at {script_path}")
        except Exception as e:
            error_print(f"ERROR: Failed to create default entrypoint script: {e}")