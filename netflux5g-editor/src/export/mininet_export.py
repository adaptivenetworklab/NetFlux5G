"""
Enhanced Mininet-WiFi Export with Dynamic UI Configuration Support

This module generates working mininet-wifi scripts that dynamically use the properties
configured in the NetFlux5G UI. It supports:

- Standard mininet-wifi components (APs, STAs, Hosts)
- 5G components (gNBs, UEs with UERANSIM integration)
- Docker containers for 5G core functions
- Dynamic property mapping from UI to script parameters
- Proper mininet-wifi/containernet integration

The generated scripts follow mininet-wifi best practices and are compatible with
the mininet-wifi examples structure.
"""

import os
import re
import traceback
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QDateTime
from manager.configmap import ConfigurationMapper
from manager.debug import debug_print, error_print, warning_print

class MininetExporter:
    """Handler for exporting network topology to Mininet scripts with Level 2 features."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def export_to_mininet(self, skip_save_check=False):
        """Export the current topology to a Mininet script.
        
        This method first checks if there are unsaved changes or if the topology
        hasn't been saved to a file yet. If so, it prompts the user to save first
        to ensure proper Docker network naming and configuration consistency.
        
        Args:
            skip_save_check (bool): If True, skip the unsaved changes check.
                                   Useful for automated exports.
        """
        # Check for unsaved changes or unsaved file (unless skipped)
        if not skip_save_check and not self._check_save_status():
            return  # User cancelled or chose not to proceed
        
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window, 
            "Export to Mininet Script", 
            "", 
            "Python Files (*.py);;All Files (*)"
        )
        if filename:
            self.export_to_mininet_script(filename)

    def export_to_mininet_script(self, filename):
        """Export the current topology to a working Mininet-WiFi Python script."""
        nodes, links = self.main_window.extractTopology()
        
        if not nodes:
            self.main_window.showCanvasStatus("No components found to export!")
            return
        
        # Categorize nodes by type for proper script generation
        categorized_nodes = self.categorize_nodes(nodes)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, "w") as f:
                self.write_mininet_script(f, nodes, links, categorized_nodes)
            
            self.main_window.showCanvasStatus(f"Exported topology to {os.path.basename(filename)}")
            debug_print(f"DEBUG: Exported {len(nodes)} nodes and {len(links)} links to {filename}")
            
        except Exception as e:
            error_msg = f"Error exporting to Mininet: {str(e)}"
            self.main_window.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()

    def categorize_nodes(self, nodes):
        """Categorize nodes by type for proper script generation."""
        categorized = {
            'hosts': [n for n in nodes if n['type'] in ['Host']],
            'stas': [n for n in nodes if n['type'] == 'STA'],
            'ues': [n for n in nodes if n['type'] == 'UE'],
            'gnbs': [n for n in nodes if n['type'] == 'GNB'],
            'aps': [n for n in nodes if n['type'] == 'AP'],
            'switches': [n for n in nodes if n['type'] in ['Switch', 'Router']],
            'controllers': [n for n in nodes if n['type'] == 'Controller'],
            'docker_hosts': [n for n in nodes if n['type'] == 'DockerHost'],
            'core5g': [n for n in nodes if n['type'] == 'VGcore']
        }
        
        # Extract 5G core components from VGcore configurations
        categorized['core5g_components'] = self.extract_5g_components_by_type(categorized['core5g'])
        
        return categorized

    def write_mininet_script(self, f, nodes, links, categorized_nodes):
        """Write the complete Mininet-WiFi script following best practices."""
        # Write script header
        self.write_script_header(f)
        
        # Write imports based on components used
        self.write_imports(f, categorized_nodes)
        
        # Write utility functions
        self.write_utility_functions(f)
        
        # Write topology function
        self.write_topology_function(f, nodes, links, categorized_nodes)
        
        # Write main execution
        self.write_main_execution(f)

    def write_script_header(self, f):
        """Write the script header with metadata."""
        f.write('#!/usr/bin/env python\n\n')
        f.write('"""\n')
        f.write('NetFlux5G - Mininet-WiFi Topology\n')
        f.write('Generated by NetFlux5G Editor\n')
        f.write(f'Generated on: {QDateTime.currentDateTime().toString()}\n')
        
        # Add Docker network information
        network_name = "netflux5g"
        f.write(f'Docker Network: {network_name}\n')
        
        f.write('\n')
        f.write('This script creates a network topology using mininet-wifi\n')
        f.write('with dynamic configuration from the NetFlux5G UI.\n')
        f.write('\n')
        f.write('5G Configuration Files:\n')
        f.write('- Located in: ./5g-configs/ directory (relative to this script)\n')
        f.write('- Contains imported YAML configuration files for 5G core components\n')
        f.write('- Simplified naming scheme: {component_type}.yaml (e.g., upf.yaml, amf.yaml)\n')
        f.write('- Multiple instances: {component_type}_{index}.yaml (e.g., upf_2.yaml)\n')
        f.write('- Volume mounted as: /opt/open5gs/etc/open5gs/{component_type}.yaml inside containers\n')
        f.write('- Mount these configs into Docker containers as needed\n')
        f.write('\n')
        f.write('Network Mode Configuration:\n')
        f.write('- All Docker components (UEs, gNBs, 5G Core) use the universal netflux5g network\n')
        f.write('- Database, WebUI, Monitoring, and Controller services also use netflux5g network\n')
        f.write(f'- Current network mode: {network_name}\n')
        
        # Add Docker network usage note
        f.write('\n')
        f.write('Docker Network Usage:\n')
        f.write(f'- Network Name: {network_name}\n')
        f.write('- Type: Bridge network with attachable containers\n')
        f.write('- Create network: docker network create --driver bridge --attachable ' + network_name + '\n')
        f.write('- Delete network: docker network rm ' + network_name + '\n')
        
        f.write('"""\n\n')

    def write_imports(self, f, categorized_nodes):
        """Write necessary imports based on component types following fixed_topology-upf.py pattern."""
        f.write('import sys\n')
        f.write('import os\n')
        
        # Check if we need wireless functionality
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        # Check if we need containernet for Docker/5G components
        has_docker = (categorized_nodes['docker_hosts'] or categorized_nodes['ues'] or 
                     categorized_nodes['gnbs'] or categorized_nodes['core5g'])
        
        # Import standard Mininet components
        f.write('from mininet.net import Mininet\n')
        f.write('from mininet.link import TCLink, Link, Intf\n')
        f.write('from mininet.node import RemoteController, OVSKernelSwitch, Host, Node\n')
        f.write('from mininet.log import setLogLevel, info\n')
        
        if has_wireless:
            # Import mininet-wifi components
            f.write('from mn_wifi.node import Station, OVSKernelAP\n')
            f.write('from mn_wifi.link import wmediumd, Intf\n')
            f.write('from mn_wifi.wmediumdConnector import interference\n')
        
        if has_docker:
            # Import containernet components for Docker/5G support
            f.write('from containernet.net import Containernet\n')
            f.write('from containernet.cli import CLI\n')
            f.write('from containernet.node import DockerSta\n')
            f.write('from containernet.term import makeTerm as makeTerm2\n')
        else:
            f.write('from mininet.cli import CLI\n')
        
        f.write('from subprocess import call\n')
        f.write('\n\n')

    def write_utility_functions(self, f):
        """Write utility functions for the script."""
        f.write('def sanitize_name(name):\n')
        f.write('    """Convert display name to valid Python variable name."""\n')
        f.write('    import re\n')
        f.write('    # Remove special characters and spaces\n')
        f.write('    clean_name = re.sub(r\'[^a-zA-Z0-9_]\', \'_\', name)\n')
        f.write('    # Ensure it starts with a letter or underscore\n')
        f.write('    if clean_name and clean_name[0].isdigit():\n')
        f.write('        clean_name = \'_\' + clean_name\n')
        f.write('    return clean_name or \'node\'\n\n')
        
        f.write('def get_5g_config_path(component_type, index=1):\n')
        f.write('    """Get path to 5G configuration file for a component type."""\n')
        f.write('    script_dir = os.path.dirname(os.path.abspath(__file__))\n')
        f.write('    configs_dir = os.path.join(script_dir, "5g-configs")\n')
        f.write('    \n')
        f.write('    # Use simplified naming scheme (0-based internally, 1-based for user)\n')
        f.write('    comp_type = component_type.lower()\n')
        f.write('    \n')
        f.write('    # Convert 1-based user index to 0-based internal index\n')
        f.write('    internal_index = index - 1\n')
        f.write('    \n')
        f.write('    if internal_index == 0:\n')
        f.write('        # First instance uses simple name: upf.yaml\n')
        f.write('        config_file = f"{comp_type}.yaml"\n')
        f.write('    else:\n')
        f.write('        # Additional instances use numbered names: upf_2.yaml (user index)\n')
        f.write('        config_file = f"{comp_type}_{index}.yaml"\n')
        f.write('    \n')
        f.write('    config_path = os.path.join(configs_dir, config_file)\n')
        f.write('    \n')
        f.write('    # Check if file exists, return path regardless\n')
        f.write('    return config_path\n\n')
        
        f.write('def list_5g_configs():\n')
        f.write('    """List all available 5G configuration files."""\n')
        f.write('    script_dir = os.path.dirname(os.path.abspath(__file__))\n')
        f.write('    configs_dir = os.path.join(script_dir, "5g-configs")\n')
        f.write('    \n')
        f.write('    if os.path.exists(configs_dir):\n')
        f.write('        import glob\n')
        f.write('        configs = glob.glob(os.path.join(configs_dir, "*.yaml"))\n')
        f.write('        configs.extend(glob.glob(os.path.join(configs_dir, "*.yml")))\n')
        f.write('        return [os.path.basename(c) for c in configs]\n')
        f.write('    else:\n')
        f.write('        return []\n\n')
        
        f.write('def check_5g_configs():\n')
        f.write('    """Check if required 5G configuration files exist and warn about missing files."""\n')
        f.write('    script_dir = os.path.dirname(os.path.abspath(__file__))\n')
        f.write('    configs_dir = os.path.join(script_dir, "5g-configs")\n')
        f.write('    \n')
        f.write('    if not os.path.exists(configs_dir):\n')
        f.write('        print("WARNING: 5g-configs directory not found!")\n')
        f.write('        print("Run the NetFlux5G automation to copy configuration files.")\n')
        f.write('        return False\n')
        f.write('    \n')
        f.write('    configs = list_5g_configs()\n')
        f.write('    if configs:\n')
        f.write('        print(f"Found {len(configs)} 5G configuration files:")\n')
        f.write('        for config in configs:\n')
        f.write('            print(f"  - {config}")\n')
        f.write('        return True\n')
        f.write('    else:\n')
        f.write('        print("WARNING: No 5G configuration files found in 5g-configs directory!")\n')
        f.write('        print("Import configuration files in VGcore component properties first.")\n')
        f.write('        return False\n\n')
        
        # Add Docker network utility functions
        network_name = "netflux5g"
        f.write('def check_docker_network():\n')
        f.write('    """Check if the required Docker network exists."""\n')
        f.write('    import subprocess\n')
        f.write(f'    network_name = "{network_name}"\n')
        f.write('    try:\n')
        f.write('        result = subprocess.run(\n')
        f.write('            ["docker", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],\n')
        f.write('            capture_output=True, text=True, timeout=10\n')
        f.write('        )\n')
        f.write('        if result.returncode == 0:\n')
        f.write('            networks = result.stdout.strip().split(\'\\n\')\n')
        f.write('            return network_name in networks\n')
        f.write('        return False\n')
        f.write('    except Exception:\n')
        f.write('        return False\n\n')
        
        f.write('def create_docker_network_if_needed():\n')
        f.write('    """Create Docker network if it doesn\'t exist."""\n')
        f.write('    import subprocess\n')
        f.write(f'    network_name = "{network_name}"\n')
        f.write('    \n')
        f.write('    if check_docker_network():\n')
        f.write('        print(f"Docker network \'{network_name}\' already exists")\n')
        f.write('        return True\n')
        f.write('    \n')
        f.write('    print(f"Creating Docker network: {network_name}")\n')
        f.write('    try:\n')
        f.write('        result = subprocess.run(\n')
        f.write('            ["docker", "network", "create", "--driver", "bridge", "--attachable", network_name],\n')
        f.write('            capture_output=True, text=True, timeout=30\n')
        f.write('        )\n')
        f.write('        if result.returncode == 0:\n')
        f.write('            print(f"Successfully created Docker network: {network_name}")\n')
        f.write('            return True\n')
        f.write('        else:\n')
        f.write('            print(f"Failed to create Docker network: {result.stderr}")\n')
        f.write('            return False\n')
        f.write('    except Exception as e:\n')
        f.write('        print(f"Error creating Docker network: {e}")\n')
        f.write('        return False\n\n')

        f.write('def update_hosts(net):\n')
        f.write('    """\n')
        f.write('    Add all Mininet/Containernet nodes (hosts, Docker containers, stations)\n')
        f.write('    to each node\'s /etc/hosts file for name resolution.\n')
        f.write('    """\n')
        f.write('    # Gather all nodes that have a name, IP, and can run commands\n')
        f.write('    all_nodes = []\n')
        f.write('    for node in set(list(net.values()) + net.hosts + getattr(net, "stations", [])):\n')
        f.write('        if hasattr(node, "cmd") and hasattr(node, "name"):\n')
        f.write('            all_nodes.append(node)\n')
        f.write('\n')
        f.write('    # Build unique entries: "IP name"\n')
        f.write('    entries = []\n')
        f.write('    seen = set()\n')
        f.write('    for node in all_nodes:\n')
        f.write('        try:\n')
        f.write('            ip = node.IP() if callable(getattr(node, "IP", None)) else getattr(node, "ip", None)\n')
        f.write('            if ip and ip != "127.0.0.1":\n')
        f.write('                entry = f"{ip} {node.name}"\n')
        f.write('                if entry not in seen:\n')
        f.write('                    entries.append(entry)\n')
        f.write('                    seen.add(entry)\n')
        f.write('        except Exception:\n')
        f.write('            continue\n')
        f.write('\n')
        f.write('    # Update /etc/hosts for all nodes\n')
        f.write('    for node in all_nodes:\n')
        f.write('        try:\n')
        f.write('            node.cmd("sed -i \'/# NetFlux5G entries/,/# End NetFlux5G entries/d\' /etc/hosts")\n')
        f.write('            if entries:\n')
        f.write('                node.cmd("echo \'# NetFlux5G entries\' >> /etc/hosts")\n')
        f.write('                for entry in entries:\n')
        f.write('                    node.cmd(f"echo \'{entry}\' >> /etc/hosts")\n')
        f.write('                node.cmd("echo \'# End NetFlux5G entries\' >> /etc/hosts")\n')
        f.write('        except Exception:\n')
        f.write('            continue\n')
        f.write('\n')

        # Add working directory variable
        f.write(f'export_dir = os.path.dirname(os.path.abspath(__file__))  # Current Working Directory\n\n')

    def write_topology_function(self, f, nodes, links, categorized_nodes):
        """Write the main topology function following mininet-wifi patterns.
        
        Network Mode Behavior:
        - All Docker components (UEs, gNBs, 5G Core, services) use the universal "netflux5g" network
        - This ensures consistent networking across all NetFlux5G deployments
        - Network name: "netflux5g"
        """
        f.write('def topology(args):\n')
        f.write('    """Create network topology."""\n')
        
        # Add 5G config check at the beginning
        f.write('    \n')
        f.write('    # Check for 5G configuration files\n')
        f.write('    info("*** Checking 5G configuration files\\n")\n')
        f.write('    check_5g_configs()\n')
        f.write('    \n')
        
        # Use universal network name for all components
        network_name = "netflux5g"
        
        # Add Docker network setup
        f.write('    # Setup Docker network\n')
        f.write('    info("*** Setting up universal Docker network\\n")\n')
        f.write('    create_docker_network_if_needed()\n')
        f.write('    \n')
        
        # Store network name for use in component creation
        f.write(f'    # Universal network mode for all NetFlux5G components\n')
        f.write(f'    NETWORK_MODE = "{network_name}"\n')
        f.write(f'    info(f"*** Using universal Docker network: {{NETWORK_MODE}}\\n")\n')
        f.write('    \n')
        
        # Initialize network
        self.write_network_initialization(f, categorized_nodes)
        
        # Add controllers
        self.write_controllers(f, categorized_nodes)
        
        # Add network components
        f.write('    info("*** Creating nodes\\n")\n')
        self.write_access_points(f, categorized_nodes)
        self.write_stations(f, categorized_nodes)
        self.write_hosts(f, categorized_nodes)
        self.write_switches(f, categorized_nodes)
        self.write_5g_components(f, categorized_nodes)
        self.write_docker_hosts(f, categorized_nodes)
        
        # Add network configuration commands
        f.write('    info("*** Connecting Docker nodes to APs\\n")\n')
        f.write('    # Dynamic UE-to-gNB/AP connection based on canvas positioning and coverage\n')
        
        # Dynamic UE-to-gNB/AP assignment based on positioning and coverage
        self.write_dynamic_ue_connections(f, categorized_nodes)

        # Set propagation model if wireless components exist
        self.write_propagation_model(f, categorized_nodes)

        # Configure nodes
        f.write('    info("*** Configuring nodes\\n")\n')
        f.write('    net.configureWifiNodes()\n\n')
        
        # Create links
        f.write('    info("*** Creating links\\n")\n')
        self.write_links(f, links, categorized_nodes)
        
        # Add plot for wireless networks
        self.write_plot_graph(f, categorized_nodes)
        
        # Start network
        f.write('    info("*** Starting network\\n")\n')
        f.write('    net.build()\n')
        self.write_controller_startup(f, categorized_nodes)
        self.write_ap_startup(f, categorized_nodes)
        self.write_switch_startup(f, categorized_nodes)
                
        f.write(f'    update_hosts(net)\n\n')  # Update hostname dns after each link to ensure connectivity

        # Start 5G components
        self.write_5g_startup(f, categorized_nodes)
        
        # CLI and cleanup
        f.write('    info("*** Running CLI\\n")\n')
        f.write('    CLI(net)\n\n')
        f.write('    info("*** Stopping network\\n")\n')
        f.write('    net.stop()\n\n')

    def write_network_initialization(self, f, categorized_nodes):
        """Write network initialization code following fixed_topology-upf.py pattern."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        has_docker = (categorized_nodes['docker_hosts'] or categorized_nodes['ues'] or 
                     categorized_nodes['gnbs'] or categorized_nodes['core5g'])
        
        # Always use Containernet for 5G/wireless components like in the original
        if has_wireless or has_docker:
            f.write('    net = Containernet(topo=None,\n')
            f.write('                       build=False,\n')
            f.write('                       link=wmediumd, wmediumd_mode=interference,\n')
            f.write('                       ipBase=\'10.0.0.0/8\')\n')
        else:
            f.write('    net = Mininet(topo=None, build=False, ipBase=\'10.0.0.0/8\')\n')
        f.write('\n')

    def write_controllers(self, f, categorized_nodes):
        """Write controller creation code following fixed_topology-upf.py pattern."""
        f.write('    info("*** Adding controller\\n")\n')
        if categorized_nodes['controllers']:
            for controller in categorized_nodes['controllers']:
                props = controller.get('properties', {})
                ctrl_name = self.sanitize_variable_name(controller['name'])
                ctrl_ip = props.get('Controller_IPAddress', '127.0.0.1')
                ctrl_port = props.get('Controller_Port', 6633)
                
                f.write(f'    {ctrl_name} = net.addController(name=\'{ctrl_name}\',\n')
                f.write(f'                                   controller=RemoteController,\n')
                f.write(f'                                   ip=\'{ctrl_ip}\',\n')
                f.write(f'                                   port={ctrl_port})\n')
        else:
            # Add default controller like in the original
            f.write('    c0 = net.addController(name=\'c0\',\n')
            f.write('                           controller=RemoteController)\n')
        f.write('\n')

    def write_access_points(self, f, categorized_nodes):
        """Write Access Point creation code following fixed_topology-upf.py pattern."""
        if not categorized_nodes['aps']:
            return
            
        f.write('    info("*** Add APs & Switches\\n")\n')
        for ap in categorized_nodes['aps']:
            props = ap.get('properties', {})
            ap_name = self.sanitize_variable_name(ap['name'])
            
            # Extract properties from UI
            ssid = props.get('AP_SSID', props.get('lineEdit_5', f'{ap_name}-ssid'))
            channel = props.get('AP_Channel', props.get('spinBox_2', '36'))
            mode = props.get('AP_Mode', props.get('comboBox_2', 'a'))
            position = f"{ap.get('x', 0):.1f},{ap.get('y', 0):.1f},0"
            
            # Build AP parameters following the original pattern
            ap_params = [f"'{ap_name}'"]
            ap_params.append("cls=OVSKernelAP")
            ap_params.append(f"ssid='{ssid}'")
            ap_params.append("failMode='standalone'")
            ap_params.append("datapath='user'")
            ap_params.append(f"channel='{channel}'")
            ap_params.append(f"mode='{mode}'")
            ap_params.append(f"position='{position}'")
            
            # Add power configuration for radio propagation
            from manager.configmap import ConfigurationMapper
            ap_config_opts = ConfigurationMapper.map_ap_config(props)
            for opt in ap_config_opts:
                if 'txpower=' in opt or 'range=' in opt:
                    ap_params.append(opt)
            
            ap_params.append('protocols="OpenFlow13"')
            
            f.write(f'    {ap_name} = net.addAccessPoint({", ".join(ap_params)})\n')
        f.write('\n')

    def write_stations(self, f, categorized_nodes):
        """Write Station creation code with dynamic properties."""
        if not categorized_nodes['stas']:
            return
            
        for sta in categorized_nodes['stas']:
            props = sta.get('properties', {})
            sta_name = self.sanitize_variable_name(sta['name'])
            
            # Build station parameters using ConfigurationMapper
            sta_params = [f"'{sta_name}'"]
            
            # Add position
            position = f"{sta.get('x', 0):.1f},{sta.get('y', 0):.1f},0"
            sta_params.append(f"position='{position}'")
            
            # Add configuration options from ConfigurationMapper
            from manager.configmap import ConfigurationMapper
            sta_opts = ConfigurationMapper.map_sta_config(props)
            sta_params.extend(sta_opts)
            
            f.write(f'    {sta_name} = net.addStation({", ".join(sta_params)})\n')
        f.write('\n')

    def write_hosts(self, f, categorized_nodes):
        """Write Host creation code with dynamic properties."""
        if not categorized_nodes['hosts']:
            return
            
        for host in categorized_nodes['hosts']:
            props = host.get('properties', {})
            host_name = self.sanitize_variable_name(host['name'])
            
            # Build host parameters
            host_params = [f"'{host_name}'"]
            
            # Add IP if specified
            ip_addr = props.get('Host_IPAddress', props.get('lineEdit_2'))
            if ip_addr and str(ip_addr).strip() and str(ip_addr).strip() != "192.168.1.1":
                host_params.append(f"ip='{ip_addr}'")
            
            # Add MAC if specified
            mac_addr = props.get('Host_MACAddress', props.get('lineEdit'))
            if mac_addr and str(mac_addr).strip():
                host_params.append(f"mac='{mac_addr}'")
            
            # Add CPU if specified
            cpu = props.get('Host_AmountCPU', props.get('doubleSpinBox'))
            if cpu and float(cpu) != 1.0:
                host_params.append(f"cpu={cpu}")
            
            # Add memory if specified
            memory = props.get('Host_Memory', props.get('spinBox'))
            if memory and int(memory) > 0:
                host_params.append(f"mem={memory}")
            
            f.write(f'    {host_name} = net.addHost({", ".join(host_params)})\n')
        f.write('\n')

    def write_switches(self, f, categorized_nodes):
        """Write Switch creation code following fixed_topology-upf.py pattern."""
        if not categorized_nodes['switches']:
            return
            
        # Add switches to the same section as APs (continued from write_access_points)
        for i, switch in enumerate(categorized_nodes['switches'], 1):
            props = switch.get('properties', {})
            switch_name = self.sanitize_variable_name(switch['name'])
            
            # Build switch parameters following the original pattern
            switch_params = [f"'{switch_name}'"]
            switch_params.append("cls=OVSKernelSwitch")
            switch_params.append('protocols="OpenFlow13"')
            
            # Add DPID if specified
            dpid = props.get('Switch_DPID', props.get('Router_DPID', props.get('AP_DPID', props.get('lineEdit_4'))))
            if dpid and str(dpid).strip():
                switch_params.append(f"dpid='{dpid}'")
            
            f.write(f'    {switch_name} = net.addSwitch({", ".join(switch_params)})\n')
        f.write('\n')

    def write_docker_hosts(self, f, categorized_nodes):
        """Write Docker Host creation code with dynamic properties."""
        if not categorized_nodes['docker_hosts']:
            return
            
        for docker_host in categorized_nodes['docker_hosts']:
            props = docker_host.get('properties', {})
            host_name = self.sanitize_variable_name(docker_host['name'])
            
            # Build Docker host parameters
            host_params = [f"'{host_name}'"]
            host_params.append("cls=Docker")
            
            # Add Docker image if specified
            image = props.get('DockerHost_ContainerImage', props.get('lineEdit_10'))
            if image and str(image).strip():
                host_params.append(f"dimage='{image}'")
            
            # Add port forwarding if specified
            ports = props.get('DockerHost_PortForward', props.get('lineEdit_11'))
            if ports and str(ports).strip():
                host_params.append(f"ports='{ports}'")
            
            # Add volume mapping if specified
            volumes = props.get('DockerHost_VolumeMapping', props.get('lineEdit_12'))
            if volumes and str(volumes).strip():
                host_params.append(f"volumes='{volumes}'")
            
            # Add IP if specified
            ip_addr = props.get('DockerHost_IPAddress', props.get('lineEdit_2'))
            if ip_addr and str(ip_addr).strip() and str(ip_addr).strip() != "192.168.1.1":
                host_params.append(f"ip='{ip_addr}'")
            
            # Add MAC if specified
            mac_addr = props.get('DockerHost_MACAddress', props.get('lineEdit'))
            if mac_addr and str(mac_addr).strip():
                host_params.append(f"mac='{mac_addr}'")
            
            # Add CPU if specified
            cpu = props.get('DockerHost_AmountCPU', props.get('doubleSpinBox'))
            if cpu and float(cpu) != 1.0:
                host_params.append(f"cpu={cpu}")
            
            # Add memory if specified
            memory = props.get('DockerHost_Memory', props.get('spinBox'))
            if memory and int(memory) > 0:
                host_params.append(f"mem={memory}")
            
            f.write(f'    {host_name} = net.addHost({", ".join(host_params)})\n')
        f.write('\n')

    def write_5g_components(self, f, categorized_nodes):
        """Write 5G component creation code (gNBs and UEs) with enhanced OVS and AP functionality."""
        # Write 5G Core components first
        self.write_5g_core_components(f, categorized_nodes)
        
        # Write gNBs following the enhanced pattern with OVS and AP support
        if categorized_nodes['gnbs']:
            f.write('    info("*** Adding gNB with enhanced OVS/AP support\\n")\n')
            for i, gnb in enumerate(categorized_nodes['gnbs'], 1):
                props = gnb.get('properties', {})
                gnb_name = self.sanitize_variable_name(gnb['name'])
                
                # Build gNB parameters following the enhanced pattern
                gnb_params = [f"'{gnb_name}'"]
                
                # Essential Docker parameters for UERANSIM gNB
                gnb_params.append('cap_add=["net_admin"]')
                gnb_params.append('network_mode=NETWORK_MODE')
                gnb_params.append('publish_all_ports=True')
                gnb_params.append('privileged=True')  # Required for OVS and AP functionality
                gnb_params.append('dcmd="/bin/bash"')  # Use entrypoint command
                gnb_params.append("cls=DockerSta")
                gnb_params.append("dimage='adaptive/ueransim:latest'")
                
                # Add volumes for host hardware access and OVS functionality
                volumes = [
                    f'"/lib/modules:/lib/modules:ro"',
                    f'export_dir + "/log-{gnb_name}/:/logging/"'
                ]
                gnb_params.append(f'volumes=[{", ".join(volumes)}]')
                
                # Add position
                position = f"{gnb.get('x', 0):.1f},{gnb.get('y', 0):.1f},0"
                gnb_params.append(f"position='{position}'")
                
                # Get enhanced configuration from ConfigurationMapper
                from manager.configmap import ConfigurationMapper
                gnb_config = ConfigurationMapper.map_gnb_config(props)
                
                # Add txpower if specified (default 30)
                txpower = gnb_config.get('txpower', 30)
                gnb_params.append(f"txpower={txpower}")
                
                # Build comprehensive environment variables for UERANSIM gNB
                env_dict = {}
                
                # Core 5G configuration - matches UERANSIM Dockerfile
                env_dict["AMF_HOSTNAME"] = gnb_config.get('amf_hostname', 'amf')
                # Add AMF_IP for explicit IP connection (takes precedence over hostname if specified)
                if gnb_config.get('amf_ip'):
                    env_dict["AMF_IP"] = gnb_config.get('amf_ip')
                env_dict["GNB_HOSTNAME"] = gnb_config.get('gnb_hostname', f'localhost')
                env_dict["N2_IFACE"] = gnb_config.get('n2_iface', 'eth0')
                env_dict["N3_IFACE"] = gnb_config.get('n3_iface', 'eth0')
                env_dict["RADIO_IFACE"] = gnb_config.get('radio_iface', 'eth0')
                env_dict["NETWORK_INTERFACE"] = gnb_config.get('network_interface', 'eth0')
                env_dict["MCC"] = gnb_config.get('mcc', '999')
                env_dict["MNC"] = gnb_config.get('mnc', '70')
                env_dict["SST"] = gnb_config.get('sst', '1')
                env_dict["SD"] = gnb_config.get('sd', '0xffffff')
                env_dict["TAC"] = gnb_config.get('tac', '1')
                
                # UERANSIM component type
                env_dict["UERANSIM_COMPONENT"] = "gnb"
                
                # Add all OVS configuration if enabled
                ovs_config = gnb_config.get('ovs_config', {})
                if ovs_config.get('OVS_ENABLED') == 'true':
                    env_dict.update(ovs_config)
                else:
                    env_dict["OVS_ENABLED"] = "false"
                
                # Add all AP configuration if enabled
                ap_config = gnb_config.get('ap_config', {})
                if ap_config.get('AP_ENABLED') == 'true':
                    env_dict.update(ap_config)
                else:
                    env_dict["AP_ENABLED"] = "false"
                
                # Format environment
                env_str = str(env_dict).replace("'", '"')
                gnb_params.append(f"environment={env_str}")
                
                # Join parameters and replace network_mode placeholder with actual variable reference
                params_str = ", ".join(gnb_params)
                params_str = params_str.replace("'network_mode=NETWORK_MODE'", "network_mode=NETWORK_MODE")
                
                f.write(f'    {gnb_name} = net.addDocker({params_str})\n')
                
                # Create separate AP node if AP functionality is enabled
                if ap_config.get('AP_ENABLED') == 'true':
                    ap_name = f"ap{100 + i}"  # ap101, ap102, etc.
                    
                    # Extract AP parameters from configuration
                    ap_ssid = ap_config.get('AP_SSID', f'{gnb_config.get("gnb_hostname", f"gnb{i}")}-ssid')
                    ap_channel = ap_config.get('AP_CHANNEL', '36')
                    ap_mode = ap_config.get('AP_MODE', 'a')
                    ap_range = ap_config.get('AP_RANGE', 600.0)
                    ap_txpower = ap_config.get('AP_TXPOWER', 24.0)
                    
                    # Use OVS configuration for AP if OVS is enabled
                    if ovs_config.get('OVS_ENABLED') == 'true':
                        fail_mode = ovs_config.get('OVS_FAIL_MODE', 'secure')
                        datapath = ovs_config.get('OVS_DATAPATH', 'kernel')
                        protocols = ovs_config.get('OPENFLOW_PROTOCOLS', 'OpenFlow13')
                    else:
                        fail_mode = 'standalone'
                        datapath = 'user'
                        protocols = 'OpenFlow13'
                    
                    # Create AP with same position as gNB (slightly offset)
                    ap_position = f"{gnb.get('x', 0) - 2.3:.1f},{gnb.get('y', 0):.1f},0"
                    
                    f.write(f'    {ap_name} = net.addAccessPoint(\'{ap_name}\', cls=OVSKernelAP, ssid=\'{ap_ssid}\', failMode=\'{fail_mode}\', datapath=\'{datapath}\',\n')
                    f.write(f'                             channel=\'{ap_channel}\', mode=\'{ap_mode}\', position=\'{ap_position}\', range={ap_range}, txpower={ap_txpower}, protocols="{protocols}")\n')
                    f.write('\n')
                    
                    # Store AP information for later use in link creation
                    gnb['_generated_ap'] = {
                        'name': ap_name,
                        'ssid': ap_ssid
                    }

            f.write('\n')
        
        # Write UEs with enhanced UERANSIM configuration
        if categorized_nodes['ues']:
            f.write('    info("*** Adding enhanced UERANSIM UE hosts\\n")\n')
            for i, ue in enumerate(categorized_nodes['ues'], 1):
                props = ue.get('properties', {})
                ue_name = self.sanitize_variable_name(ue['name'])
                
                # Build UE parameters following the enhanced pattern
                ue_params = [f"'{ue_name}'"]
                
                # Essential Docker parameters for UERANSIM UE
                ue_params.append('devices=["/dev/net/tun"]')
                ue_params.append('cap_add=["net_admin"]')
                ue_params.append('network_mode=NETWORK_MODE')
                ue_params.append('dcmd="/bin/bash"')
                ue_params.append("cls=DockerSta")
                ue_params.append("dimage='adaptive/ueransim:latest'")

                # Add volumes for host hardware access and OVS functionality
                volumes = [
                    f'export_dir + "/log-{ue_name}/:/logging/"'
                ]
                ue_params.append(f'volumes=[{", ".join(volumes)}]')

                # Add enhanced power and range configuration from ConfigurationMapper
                from manager.configmap import ConfigurationMapper
                ue_config = ConfigurationMapper.map_ue_config(props)
                
                # Add range (default 116 if not specified)
                range_val = ue_config.get('range', 116)
                ue_params.append(f'range={range_val}')
                
                # Add txpower if specified
                if 'txpower' in ue_config:
                    ue_params.append(f"txpower={ue_config['txpower']}")
                
                # Add position
                position = f"{ue.get('x', 0):.1f},{ue.get('y', 0):.1f},0"
                ue_params.append(f"position='{position}'")
                
                # Enhanced UE environment variables with all new configuration options
                gnb_hostname = ue_config.get('gnb_hostname', 'localhost')
                
                # Build comprehensive environment dictionary matching UERANSIM Dockerfile
                env_dict = {
                    # Core 5G Configuration
                    "GNB_HOSTNAME": gnb_hostname,
                    "APN": ue_config.get('apn', 'internet'),
                    "MSISDN": ue_config.get('msisdn', f'000000000{i:01d}'),
                    "MCC": ue_config.get('mcc', '999'),
                    "MNC": ue_config.get('mnc', '70'),
                    "SST": ue_config.get('sst', '1'),
                    "SD": ue_config.get('sd', '0xffffff'),
                    "TAC": ue_config.get('tac', '1'),
                    
                    # Authentication Configuration
                    "KEY": ue_config.get('key', '465B5CE8B199B49FAA5F0A2EE238A6BC'),
                    "OP_TYPE": ue_config.get('op_type', 'OPC'),
                    "OP": ue_config.get('op', 'E8ED289DEBA952E4283B54E88E6183CA'),
                    
                    # Device Identifiers
                    "IMEI": ue_config.get('imei', '356938035643803'),
                    "IMEISV": ue_config.get('imeisv', '4370816125816151'),
                    
                    # Network Configuration
                    "TUNNEL_IFACE": ue_config.get('tunnel_iface', 'uesimtun0'),
                    "RADIO_IFACE": ue_config.get('radio_iface', 'eth0'),
                    "SESSION_TYPE": ue_config.get('session_type', 'IPv4'),
                    "PDU_SESSIONS": str(ue_config.get('pdu_sessions', 1)),
                    
                    # Mobility Configuration
                    "MOBILITY_ENABLED": 'true' if ue_config.get('mobility', False) else 'false',
                    
                    # UERANSIM component type
                    "UERANSIM_COMPONENT": "ue"
                }
                
                # Add gNB IP if specified
                if 'gnb_ip' in ue_config:
                    env_dict["GNB_IP"] = ue_config['gnb_ip']
                
                # Add OVS configuration if enabled for UE (less common but possible)
                if 'ovs_config' in ue_config:
                    ovs_config = ue_config['ovs_config']
                    if ovs_config.get('OVS_ENABLED') == 'true':
                        env_dict.update(ovs_config)
                        env_dict["OVS_BRIDGE_NAME"] = ovs_config.get('OVS_BRIDGE_NAME', 'br-ue')
                    else:
                        env_dict["OVS_ENABLED"] = "false"
                else:
                    env_dict["OVS_ENABLED"] = "false"
                
                # Format environment
                env_str = str(env_dict).replace("'", '"')
                ue_params.append(f"environment={env_str}")
                
                # Join parameters and replace network_mode placeholder with actual variable reference
                params_str = ", ".join(ue_params)
                params_str = params_str.replace("'network_mode=NETWORK_MODE'", "network_mode=NETWORK_MODE")
                
                f.write(f'    {ue_name} = net.addStation({params_str})\n')
            f.write('\n')
        
        if categorized_nodes['gnbs'] or categorized_nodes['ues'] or categorized_nodes['core5g']:
            f.write('\n')

    def write_5g_core_components(self, f, categorized_nodes):
        """
        Write 5G Core components with enhanced Open5GS integration and dynamic configuration.
        
        This function generates Docker-based 5G Core components that follow the latest Open5GS
        architecture and container configuration. Features include:
        
        - Dynamic Docker image configuration from UI
        - Environment variable injection for runtime configuration
        - Support for latest Open5GS component structure
        - OVS/OpenFlow integration for SDN functionality
        - Proper network interface binding
        - MongoDB database connectivity
        - Configuration file volume mounting
        - Component-specific startup commands
        
        The generated components are compatible with mininet-wifi and follow the
        patterns established in the latest Open5GS Docker implementations.
        """
        if not categorized_nodes['core5g']:
            return
            
        # Extract 5G core components from VGcore configurations
        core_components = self.extract_5g_components_by_type(categorized_nodes['core5g'])
        
        # Import configuration mapper for VGcore properties
        from manager.configmap import ConfigurationMapper
        
        # Get VGcore component configuration (if available)
        vgcore_config = {}
        if categorized_nodes['core5g']:
            vgcore_node = categorized_nodes['core5g'][0]  # Use first VGcore node
            vgcore_properties = vgcore_node.get('properties', {})
            vgcore_config = ConfigurationMapper.map_vgcore_config(vgcore_properties)
        
        # Debug: Print extracted VGcore configuration for troubleshooting
        if vgcore_config:
            debug_print("DEBUG: VGcore configuration extracted:")
            for key, value in vgcore_config.items():
                debug_print(f"  {key}: {value}")
        else:
            debug_print("DEBUG: No VGcore configuration found, using defaults")
        
        # Mapping of component types to their configurations based on latest Open5GS
        component_config = {
            'UPF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'upf.yaml',
                'startup_cmd': 'open5gs-upfd',
                'privileged': True,
                'requires_tun': False,
                'terminal_startup': True,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'ENABLE_NAT': 'true' if vgcore_config.get('enable_nat', True) else 'false',
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0'),
                    'OVS_ENABLED': 'true' if vgcore_config.get('ovs_enabled', False) else 'false',
                    'OVS_CONTROLLER': vgcore_config.get('ovs_controller', ''),
                    'OVS_BRIDGE_NAME': vgcore_config.get('ovs_bridge_name', 'br-open5gs'),
                    'OVS_FAIL_MODE': vgcore_config.get('ovs_fail_mode', 'standalone'),
                    'OPENFLOW_PROTOCOLS': vgcore_config.get('openflow_protocols', 'OpenFlow13'),
                    'OVS_DATAPATH': vgcore_config.get('ovs_datapath', 'kernel'),
                    'CONTROLLER_PORT': vgcore_config.get('controller_port', '6633'),
                    'BRIDGE_PRIORITY': vgcore_config.get('bridge_priority', '32768'),
                    'STP_ENABLED': 'true' if vgcore_config.get('stp_enabled', False) else 'false'
                }
            },
            'AMF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'amf.yaml',
                'startup_cmd': 'open5gs-amfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': True,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0'),
                    'MCC': vgcore_config.get('mcc', '999'),
                    'MNC': vgcore_config.get('mnc', '70'),
                    'TAC': vgcore_config.get('tac', '1'),
                    'SST': vgcore_config.get('sst', '1'),
                    'SD': vgcore_config.get('sd', '0xffffff'),
                    'OVS_ENABLED': 'true' if vgcore_config.get('ovs_enabled', False) else 'false',
                    'OVS_CONTROLLER': vgcore_config.get('ovs_controller', ''),
                    'OVS_BRIDGE_NAME': vgcore_config.get('ovs_bridge_name', 'br-open5gs'),
                    'OVS_FAIL_MODE': vgcore_config.get('ovs_fail_mode', 'standalone'),
                    'OPENFLOW_PROTOCOLS': vgcore_config.get('openflow_protocols', 'OpenFlow13'),
                    'OVS_DATAPATH': vgcore_config.get('ovs_datapath', 'kernel'),
                    'CONTROLLER_PORT': vgcore_config.get('controller_port', '6633'),
                    'BRIDGE_PRIORITY': vgcore_config.get('bridge_priority', '32768'),
                    'STP_ENABLED': 'true' if vgcore_config.get('stp_enabled', False) else 'false'
                }
            },
            'SMF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'smf.yaml',
                'startup_cmd': 'open5gs-smfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0'),
                    'OVS_ENABLED': 'true' if vgcore_config.get('ovs_enabled', False) else 'false',
                    'OVS_CONTROLLER': vgcore_config.get('ovs_controller', ''),
                    'OVS_BRIDGE_NAME': vgcore_config.get('ovs_bridge_name', 'br-open5gs'),
                    'OVS_FAIL_MODE': vgcore_config.get('ovs_fail_mode', 'standalone'),
                    'OPENFLOW_PROTOCOLS': vgcore_config.get('openflow_protocols', 'OpenFlow13'),
                    'OVS_DATAPATH': vgcore_config.get('ovs_datapath', 'kernel'),
                    'CONTROLLER_PORT': vgcore_config.get('controller_port', '6633'),
                    'BRIDGE_PRIORITY': vgcore_config.get('bridge_priority', '32768'),
                    'STP_ENABLED': 'true' if vgcore_config.get('stp_enabled', False) else 'false'
                }
            },
            'NRF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'nrf.yaml',
                'startup_cmd': 'open5gs-nrfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'SCP': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'scp.yaml',
                'startup_cmd': 'open5gs-scpd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'AUSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'ausf.yaml',
                'startup_cmd': 'open5gs-ausfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'BSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'bsf.yaml',
                'startup_cmd': 'open5gs-bsfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'NSSF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'nssf.yaml',
                'startup_cmd': 'open5gs-nssfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'PCF': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'pcf.yaml',
                'startup_cmd': 'open5gs-pcfd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'UDM': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'udm.yaml',
                'startup_cmd': 'open5gs-udmd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            },
            'UDR': {
                'image': vgcore_config.get('docker_image', 'adaptive/open5gs:latest'),
                'default_config': 'udr.yaml',
                'startup_cmd': 'open5gs-udrd',
                'privileged': False,
                'requires_tun': False,
                'terminal_startup': False,
                'env_vars': {
                    'DB_URI': vgcore_config.get('database_uri', 'mongodb://mongo/open5gs'),
                    'NETWORK_INTERFACE': vgcore_config.get('network_interface', 'eth0')
                }
            }
        }
        
        # Generate code for each 5G core component type
        for comp_type, components in core_components.items():
            if components:
                config = component_config.get(comp_type, component_config['AMF'])
                f.write(f'    info("*** Add {comp_type} ({len(components)} instances)\\n")\n')
                debug_print(f"DEBUG: Generating {comp_type} with {len(components)} components")
                
                for i, component in enumerate(components):  # Start from 0 to match copying logic
                    comp_name = self.sanitize_variable_name(component.get('name', f'{comp_type.lower()}{i+1}'))
                    debug_print(f"DEBUG: Processing {comp_type} index {i}: {comp_name}")

                    # Debug output for component processing
                    f.write(f'    info("    Creating {comp_type} instance {i+1}/{len(components)}: {comp_name}\\n")\n')
                    
                    # Build component parameter
                    comp_params = [f"'{comp_name}'"]
                    
                    # Add required Docker parameters
                    if config.get('requires_tun', False):
                        comp_params.append('devices=["/dev/net/tun"]')
                    comp_params.append('cap_add=["net_admin"]')
                    comp_params.append('network_mode=NETWORK_MODE')
                    
                    if config.get('privileged', False):
                        comp_params.append('privileged=True')
                    
                    comp_params.append('publish_all_ports=True')
                    comp_params.append('dcmd="/bin/bash"')
                    comp_params.append("cls=DockerSta")
                    comp_params.append(f"dimage='{config.get('image', 'adaptive/open5gs:latest')}'")
                    
                    # Add position
                    x_pos = component.get('x', 0)
                    y_pos = component.get('y', 0)
                    position = f"{x_pos:.1f},{y_pos:.1f},0"
                    comp_params.append(f"position='{position}'")
                    # comp_params.append("range=116")
                    
                    # Add volume mount for configuration using simplified naming
                    # Generate the config filename based on our simplified naming scheme
                    if i == 0:  # First instance gets simple name
                        config_filename = f'{comp_type.lower()}.yaml'
                    else:  # Additional instances get numbered
                        config_filename = f'{comp_type.lower()}_{i+1}.yaml'

                    debug_print(f"DEBUG: {comp_type} index {i} -> filename: {config_filename}")
                    # Debug output for config file mapping
                    f.write(f'    info("      Config file: {config_filename}\\n")\n')
                    
                    comp_params.append(f'volumes=[export_dir + "/5g-configs/{config_filename}:/opt/open5gs/etc/open5gs/{comp_type.lower()}.yaml", export_dir + "/log-{comp_name.lower()}/:/logging/"]')

                    # Add environment variables for configuration
                    if 'env_vars' in config and config['env_vars']:
                        env_list = []
                        for env_key, env_value in config['env_vars'].items():
                            env_list.append(f'"{env_key}={env_value}"')
                        if env_list:
                            comp_params.append(f'environment=[{", ".join(env_list)}]')
                    
                    # Join parameters and replace network_mode placeholder with actual variable reference
                    params_str = ", ".join(comp_params)
                    params_str = params_str.replace("'network_mode=NETWORK_MODE'", "network_mode=NETWORK_MODE")
                    
                    f.write(f'    {comp_name} = net.addDocker({params_str})\n')
        
        f.write('\n')

    def write_5g_startup(self, f, categorized_nodes):
        """Write 5G component startup commands with enhanced UERANSIM and OVS support."""
        if not (categorized_nodes['gnbs'] or categorized_nodes['ues'] or categorized_nodes['core5g']):
            return
            
        # Get core components for startup sequence
        core_components = categorized_nodes.get('core5g_components', {})
        
        # # Start APs
        # f.write('    info("*** Starting APs\\n")\n')
        # controller_name = 'c0'
        # if categorized_nodes['controllers']:
        #     controller_name = self.sanitize_variable_name(categorized_nodes['controllers'][0]['name'])
            
        # # Start traditional APs
        # for ap in categorized_nodes['aps']:
        #     ap_name = self.sanitize_variable_name(ap['name'])
        #     f.write(f'    net.get("{ap_name}").start([{controller_name}])\n')
            
        # # Start generated APs from gNBs
        # for gnb in categorized_nodes['gnbs']:
        #     if '_generated_ap' in gnb:
        #         ap_name = gnb['_generated_ap']['name']
        #         f.write(f'    net.get("{ap_name}").start([{controller_name}])\n')
            
        # # Start switches
        # for switch in categorized_nodes['switches']:
        #     switch_name = self.sanitize_variable_name(switch['name'])
        #     f.write(f'    net.get("{switch_name}").start([{controller_name}])\n')
        # f.write('\n')
        
        # Start 5G Core components in proper order with makeTerm2
        startup_order = ['NRF', 'SCP', 'AUSF', 'UDM', 'UDR', 'PCF', 'BSF', 'NSSF', 'SMF', 'AMF', 'UPF']

        # Start other core components (if configured)
        for comp_type in startup_order:
            if comp_type in core_components:
                f.write(f'    info("*** Starting {comp_type} components\\n")\n')
                for instance in core_components[comp_type]:
                    instance_name = self.sanitize_variable_name(instance.get('name', f'{comp_type.lower()}1'))
                    cmd = f'open5gs-{comp_type.lower()}d'
                    f.write(f'    {instance_name}.cmd("setsid nohup /opt/open5gs/etc/open5gs/entrypoint.sh {cmd} 2>&1 | tee -a /logging/{instance_name}.log  &")\n')
                f.write('\n')
        
        f.write('    CLI.do_sh(net, "sleep 10")\n\n')
        
        # Start gNBs with enhanced OVS and AP configuration
        if categorized_nodes['gnbs']:
            f.write('    info("*** Starting enhanced UERANSIM gNB with OVS/AP support\\n")\n')
            for gnb in categorized_nodes['gnbs']:
                gnb_name = self.sanitize_variable_name(gnb['name'])
                props = gnb.get('properties', {})
                
                # Check if OVS configuration is enabled
                ovs_enabled = (props.get('GNB_OVS_Enabled') or 
                              props.get('ovs_ovs_enabled', 'false') == 'true' or
                              props.get('ovs_ovs_enabled') is True)
                
                if ovs_enabled:
                    f.write(f'    info("*** Pre-configuring OVS for gNB {gnb_name}\\n")\n')
                    
                    # The OVS setup will be handled by the entrypoint.sh script
                    # based on environment variables we've already set
                    f.write(f'    # OVS_ENABLED environment variable will trigger setup in entrypoint\\n")\n')

                f.write(f'    {gnb_name}.cmd("setsid nohup /entrypoint.sh gnb 2>&1 | tee -a /logging/{gnb_name}.log &")\n')
            f.write('\n')
            f.write('    CLI.do_sh(net, "sleep 15")  # Allow time for gNB and OVS setup\n\n')
        
        # Start UEs with enhanced configuration
        if categorized_nodes['ues']:
            f.write('    info("*** Starting enhanced UERANSIM UE nodes\\n")\n')
            for ue in categorized_nodes['ues']:
                ue_name = self.sanitize_variable_name(ue['name'])
                props = ue.get('properties', {})
                
                # Check if OVS configuration is enabled for UE (uncommon but possible)
                ovs_enabled = (props.get('UE_OVS_Enabled') or 
                              props.get('ovs_ovs_enabled', 'false') == 'true' or
                              props.get('ovs_ovs_enabled') is True)
                
                if ovs_enabled:
                    f.write(f'    info("*** Pre-configuring OVS for UE {ue_name}\\n")\n')
                    f.write(f'    # OVS_ENABLED environment variable will trigger setup in entrypoint\\n')
                
                f.write(f'    {ue_name}.cmd("setsid nohup /entrypoint.sh ue 2>&1 | tee -a /logging/{ue_name}.log &")\n')
            f.write('\n')
            f.write('    CLI.do_sh(net, "sleep 20")  # Allow time for UE registration and OVS setup\n\n')
            
            # Add UE routing configuration
            f.write('    info("*** Route traffic on UE for End-to-End and End-to-Edge Connection\\n")\n')
            for i, ue in enumerate(categorized_nodes['ues'], 1):
                ue_name = self.sanitize_variable_name(ue['name'])
                props = ue.get('properties', {})
                apn = props.get('UE_APN', 'internet')
                
                # Route based on APN
                if apn == 'internet':
                    f.write(f'    {ue_name}.cmd("ip route add 10.100.0.0/16 dev uesimtun0")\n')
                elif apn == 'internet2':
                    f.write(f'    {ue_name}.cmd("ip route add 10.200.0.0/16 dev uesimtun0")\n')
                elif apn == 'web1':
                    f.write(f'    {ue_name}.cmd("ip route add 10.51.0.0/16 dev uesimtun0")\n')
                elif apn == 'web2':
                    f.write(f'    {ue_name}.cmd("ip route add 10.52.0.0/16 dev uesimtun0")\n')
                else:
                    f.write(f'    info("*** {ue_name} APN does not exist, please check your configuration\\n")\n')
            f.write('\n')
        
        # Add OVS status check if any gNB or UE has OVS enabled
        has_ovs = False
        for gnb in categorized_nodes.get('gnbs', []):
            props = gnb.get('properties', {})
            if (props.get('GNB_OVS_Enabled') or 
                props.get('ovs_ovs_enabled', 'false') == 'true' or
                props.get('ovs_ovs_enabled') is True):
                has_ovs = True
                break
        
        if not has_ovs:
            for ue in categorized_nodes.get('ues', []):
                props = ue.get('properties', {})
                if (props.get('UE_OVS_Enabled') or 
                    props.get('ovs_ovs_enabled', 'false') == 'true' or
                    props.get('ovs_ovs_enabled') is True):
                    has_ovs = True
                    break
        
        if has_ovs:
            f.write('    info("*** Checking OVS status for enhanced UERANSIM components\\n")\n')
            f.write('    CLI.do_sh(net, "sleep 5")  # Allow OVS setup to complete\\n")\n')
            for gnb in categorized_nodes.get('gnbs', []):
                props = gnb.get('properties', {})
                if (props.get('GNB_OVS_Enabled') or 
                    props.get('ovs_ovs_enabled', 'false') == 'true' or
                    props.get('ovs_ovs_enabled') is True):
                    gnb_name = self.sanitize_variable_name(gnb['name'])
                    f.write(f'    makeTerm2({gnb_name}, cmd="ovs-vsctl show || echo \\"OVS not ready for {gnb_name}\\"")\n')
            
            for ue in categorized_nodes.get('ues', []):
                props = ue.get('properties', {})
                if (props.get('UE_OVS_Enabled') or 
                    props.get('ovs_ovs_enabled', 'false') == 'true' or
                    props.get('ovs_ovs_enabled') is True):
                    ue_name = self.sanitize_variable_name(ue['name'])
                    f.write(f'    makeTerm2({ue_name}, cmd="ovs-vsctl show || echo \\"OVS not ready for {ue_name}\\"")\n')
            f.write('\n')

    def extract_5g_components_by_type(self, core5g_components):
        """Extract 5G components organized by type from VGcore configurations."""
        components_by_type = {
            'UPF': [], 'AMF': [], 'SMF': [], 'NRF': [], 'SCP': [],
            'AUSF': [], 'BSF': [], 'NSSF': [], 'PCF': [],
            'UDM': [], 'UDR': []
        }
        
        for vgcore in core5g_components:
            props = vgcore.get('properties', {})
            
            # Look for component configurations in properties
            for comp_type in components_by_type.keys():
                # Look for the new configs format first
                config_key = f"{comp_type}_configs"
                if config_key in props and props[config_key]:
                    config_data = props[config_key]
                    debug_print(f"DEBUG: Found {comp_type} configs: {len(config_data) if isinstance(config_data, list) else 'not a list'}")
                    if isinstance(config_data, list):
                        valid_count = 0
                        for row_idx, row_data in enumerate(config_data):
                            debug_print(f"DEBUG: {comp_type} row {row_idx}: {row_data}")
                            # Filter out empty or invalid rows
                            if (isinstance(row_data, dict) and 
                                row_data.get('name') and 
                                str(row_data.get('name')).strip()):
                                
                                # Extract configuration from new format
                                comp_name = row_data.get('name', f'{comp_type.lower()}{row_idx+1}')
                                config_file = row_data.get('config_filename', f'{comp_type.lower()}.yaml')
                                config_file_path = row_data.get('config_file_path', '')
                                
                                # Only include if we have actual configuration data
                                has_config = (
                                    (config_file_path and config_file_path.strip()) or 
                                    row_data.get('config_content') or
                                    row_data.get('imported', False)
                                )

                                debug_print(f"DEBUG: {comp_type} {comp_name} has_config: {has_config}")
                                if has_config:
                                    component_info = {
                                        'name': comp_name,
                                        'x': vgcore.get('x', 0),
                                        'y': vgcore.get('y', 0),
                                        'properties': props,
                                        'config_file': config_file,
                                        'config_file_path': config_file_path,
                                        'config_content': row_data.get('config_content', {}),
                                        'imported': row_data.get('imported', False),
                                        'component_type': comp_type,
                                        'row_data': row_data
                                    }
                                    components_by_type[comp_type].append(component_info)
                                    valid_count += 1
                                    debug_print(f"DEBUG: Added {comp_type} component {valid_count}: {comp_name}")
                        debug_print(f"DEBUG: {comp_type} final count: {len(components_by_type[comp_type])}")

                # Fallback to old table format for backward compatibility
                else:
                    table_key = f'Component5G_{comp_type}table'
                    if table_key in props and props[table_key]:
                        table_data = props[table_key]
                        if isinstance(table_data, list):
                            for row_idx, row_data in enumerate(table_data):
                                if isinstance(row_data, list) and len(row_data) >= 2:
                                    # Extract name and config file from old table format
                                    comp_name = row_data[0] if row_data[0] else f'{comp_type.lower()}{row_idx+1}'
                                    config_file = row_data[1] if len(row_data) > 1 and row_data[1] else f'{comp_type.lower()}.yaml'
                                    
                                    component_info = {
                                        'name': comp_name,
                                        'x': vgcore.get('x', 0),
                                        'y': vgcore.get('y', 0),
                                        'properties': props,
                                        'config_file': config_file,
                                        'config_file_path': '',  # Old format doesn't have file paths
                                        'config_content': {},
                                        'imported': False,
                                        'component_type': comp_type,
                                        'table_row': row_data  # Keep for backward compatibility
                                    }
                                    components_by_type[comp_type].append(component_info)
        
        # Store extracted components for use in startup
        return components_by_type

    def write_propagation_model(self, f, categorized_nodes):
        """Write propagation model configuration for wireless networks."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        if has_wireless:
            f.write('    info("*** Configuring propagation model\\n")\n')
            f.write('    net.setPropagationModel(model="logDistance", exp=3)\n\n')

    def write_links(self, f, links, categorized_nodes):
        """Write link creation code based on extracted links."""
        # First, write AP-gNB direct links
        self.write_ap_gnb_links(f, categorized_nodes)
        
        # Get gNB to AP mapping for link redirection
        gnb_to_ap = self.get_gnb_ap_mapping(categorized_nodes)
        
        if not links:
            return

        # Dynamically get AMF, UPF, SMF instance names from extracted 5G core components
        core5g_components = categorized_nodes.get('core5g_components', {})
        amf_names = [self.sanitize_variable_name(comp.get('name', f'amf{i+1}')) for i, comp in enumerate(core5g_components.get('AMF', []))]
        upf_names = [self.sanitize_variable_name(comp.get('name', f'upf{i+1}')) for i, comp in enumerate(core5g_components.get('UPF', []))]
        smf_names = [self.sanitize_variable_name(comp.get('name', f'smf{i+1}')) for i, comp in enumerate(core5g_components.get('SMF', []))]

        for link in links:
            source_name = self.sanitize_variable_name(link['source'])
            dest_name = self.sanitize_variable_name(link['destination'])

            # Replace VGcore connections with all core components dynamically
            # Use regex to match any VGcore pattern: VGcore, VGcore__1, VGCore__1, VGcore_1, VGCore_1, etc.
            vgcore_pattern = re.compile(r'^VGcore(?:__|_)?\d*$', re.IGNORECASE)
            source_is_vgcore = bool(vgcore_pattern.match(source_name))
            dest_is_vgcore = bool(vgcore_pattern.match(dest_name))

            # Track if we need to add extra links
            extra_links = []

            if source_is_vgcore or dest_is_vgcore:
                # Get all core component names for dynamic connections
                all_core_names = amf_names + upf_names + smf_names
                
                if source_is_vgcore:
                    orig_source = source_name
                    # Connect all core components to the destination
                    for i, core_name in enumerate(all_core_names):
                        if i == 0:
                            # Replace the first link with the first core component
                            source_name = core_name
                        else:
                            # Add additional links for other core components
                            extra_links.append((core_name, dest_name))
                
                if dest_is_vgcore:
                    orig_dest = dest_name
                    # Connect source to all core components
                    for i, core_name in enumerate(all_core_names):
                        if i == 0:
                            # Replace the first link with the first core component
                            dest_name = core_name
                        else:
                            # Add additional links for other core components
                            extra_links.append((source_name, core_name))
                
                # If no core components found, fallback to amf1
                if not all_core_names:
                    if source_is_vgcore:
                        source_name = "amf1"
                    if dest_is_vgcore:
                        dest_name = "amf1"

            # Redirect gNB connections to APs when AP functionality is enabled
            if source_name in gnb_to_ap:
                source_name = gnb_to_ap[source_name]
            if dest_name in gnb_to_ap:
                dest_name = gnb_to_ap[dest_name]

            # Also redirect any extra links
            for i, (extra_source, extra_dest) in enumerate(extra_links):
                if extra_source in gnb_to_ap:
                    extra_source = gnb_to_ap[extra_source]
                if extra_dest in gnb_to_ap:
                    extra_dest = gnb_to_ap[extra_dest]
                extra_links[i] = (extra_source, extra_dest)

            # Skip links if source or dest is Controller__{number}
            controller_pattern = re.compile(r'^Controller__\d+$')
            if controller_pattern.match(source_name) or controller_pattern.match(dest_name):
                continue

            # Check if we need to swap link order for Switch connected to 5G core components, GNBs, or APs
            switch_pattern = re.compile(r'^Switch__\d+$', re.IGNORECASE)
            gnb_pattern = re.compile(r'^GNB__\d+$', re.IGNORECASE)
            ap_pattern = re.compile(r'^ap\d+$', re.IGNORECASE)  # For generated APs like ap101, ap102
            core5g_components_names = set(amf_names + upf_names + smf_names)
            
            # Check if source is 5G core and dest is switch - if so, swap them
            if source_name in core5g_components_names and switch_pattern.match(dest_name):
                source_name, dest_name = dest_name, source_name
            # Check if source is GNB and dest is switch - if so, swap them
            elif gnb_pattern.match(source_name) and switch_pattern.match(dest_name):
                source_name, dest_name = dest_name, source_name
            # Check if source is AP and dest is switch - if so, swap them
            elif ap_pattern.match(source_name) and switch_pattern.match(dest_name):
                source_name, dest_name = dest_name, source_name
            # Check if source is switch and dest is 5G core, GNB, or AP - this is the desired order, no swap needed
            elif switch_pattern.match(source_name) and (dest_name in core5g_components_names or gnb_pattern.match(dest_name) or ap_pattern.match(dest_name)):
                pass  # Already in correct order (Switch, core_component/gnb/ap)

            # Build link parameters
            link_params = [source_name, dest_name]

            # Add link properties using configmap
            link_props = link.get('properties', {})
            if link_props:
                link_config_params = ConfigurationMapper.map_link_config(link_props)
                link_params.extend(link_config_params)

            # Change link if either end is a core component (was VGcore), GNB__{number}, or ap{number}
            gnb_pattern = re.compile(r'^GNB__\d+$', re.IGNORECASE)
            ap_pattern = re.compile(r'^ap\d+$', re.IGNORECASE)

            f.write(f'    net.addLink({", ".join(link_params)})\n')

            # Write extra links for upf and smf if needed
            for extra_source, extra_dest in extra_links:
                # Apply same switch swapping logic for extra links
                if extra_source in core5g_components_names and switch_pattern.match(extra_dest):
                    extra_source, extra_dest = extra_dest, extra_source
                elif gnb_pattern.match(extra_source) and switch_pattern.match(extra_dest):
                    extra_source, extra_dest = extra_dest, extra_source
                elif ap_pattern.match(extra_source) and switch_pattern.match(extra_dest):
                    extra_source, extra_dest = extra_dest, extra_source
                elif switch_pattern.match(extra_source) and (extra_dest in core5g_components_names or gnb_pattern.match(extra_dest) or ap_pattern.match(extra_dest)):
                    pass  # Already in correct order (Switch, core_component/gnb/ap)
                
                extra_params = [extra_source, extra_dest]
                # Use same link properties with configmap
                if link_props:
                    extra_config_params = ConfigurationMapper.map_link_config(link_props)
                    extra_params.extend(extra_config_params)

                # Write the extra link
                f.write(f'    net.addLink({", ".join(extra_params)})\n')
        
        f.write('\n')

    def write_plot_graph(self, f, categorized_nodes):
        """Write plot graph configuration for wireless networks."""
        has_wireless = (categorized_nodes['aps'] or categorized_nodes['stas'] or 
                       categorized_nodes['ues'] or categorized_nodes['gnbs'])
        
        if has_wireless:
            f.write('    if "-p" not in args:\n')
            f.write('        net.plotGraph(max_x=1000, max_y=1000)\n\n')

    def write_controller_startup(self, f, categorized_nodes):
        """Write controller startup code."""
        if categorized_nodes['controllers']:
            for controller in categorized_nodes['controllers']:
                ctrl_name = self.sanitize_variable_name(controller['name'])
                f.write(f'    {ctrl_name}.start()\n')
        else:
            f.write('    c0.start()\n')
        f.write('\n')

    def write_ap_startup(self, f, categorized_nodes):
        """Write Access Point startup code."""
        # Collect all APs (traditional + generated from gNBs)
        all_aps = []
        
        # Add traditional APs
        for ap in categorized_nodes['aps']:
            all_aps.append(self.sanitize_variable_name(ap['name']))
        
        # Add generated APs from gNBs
        for gnb in categorized_nodes['gnbs']:
            if '_generated_ap' in gnb:
                all_aps.append(gnb['_generated_ap']['name'])
        
        if not all_aps:
            return
            
        controller_name = 'c0'
        if categorized_nodes['controllers']:
            controller_name = self.sanitize_variable_name(categorized_nodes['controllers'][0]['name'])
            
        f.write('    info("*** Starting APs\\n")\n')
        for ap_name in all_aps:
            f.write(f'    net.get("{ap_name}").start([{controller_name}])\n')
        f.write('\n')

    def write_switch_startup(self, f, categorized_nodes):
        """Write switch startup code."""

        controller_name = 'c0'
        if categorized_nodes['controllers']:
            controller_name = self.sanitize_variable_name(categorized_nodes['controllers'][0]['name'])

        for switch in categorized_nodes['switches']:
            switch_name = self.sanitize_variable_name(switch['name'])
            f.write(f'    net.get("{switch_name}").start([{controller_name}])\n')
        f.write('\n')

    def write_main_execution(self, f):
        """Write the main execution block."""
        f.write('if __name__ == \'__main__\':\n')
        f.write('    setLogLevel(\'info\')\n')
        f.write('    topology(sys.argv)\n')

    def sanitize_variable_name(self, name):
        """Convert display name to valid Python variable name."""
        import re
        # Remove special characters and spaces
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
        # Ensure it starts with a letter or underscore
        if clean_name and clean_name[0].isdigit():
            clean_name = '_' + clean_name
        return clean_name or 'node'
    
    def _check_save_status(self):
        """Check if topology should be saved before export and prompt user if needed.
        
        Returns:
            bool: True if export should continue, False if user cancelled
        """
        debug_print("Checking save status before export...")
        
        # Check if there are unsaved changes or no file is saved
        has_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
        current_file = getattr(self.main_window, 'current_file', None)
        
        debug_print(f"Save status: has_unsaved={has_unsaved}, current_file={current_file}")
        
        # Get topology info for better messaging
        nodes, _ = self.main_window.extractTopology()
        has_components = len(nodes) > 0
        
        debug_print(f"Topology info: {len(nodes)} components found")
        
        if has_unsaved or not current_file:
            # Determine the message based on the situation
            if not current_file:
                title = "Unsaved Topology"
                if has_components:
                    message = (f"The topology has {len(nodes)} component(s) but has not been saved to a file yet.\n\n"
                              "It is recommended to save the topology first to ensure:\n"
                              "• Proper Docker network naming based on filename\n"
                              "• Configuration persistence\n"
                              "• Easier topology management\n\n"
                              "Do you want to save the topology first?")
                else:
                    message = ("The topology has not been saved to a file yet.\n\n"
                              "Although there are no components currently, saving the file first\n"
                              "will ensure proper Docker network naming for any components\n"
                              "you may add to the exported script.\n\n"
                              "Do you want to save the topology first?")
            else:
                title = "Unsaved Changes"
                message = ("The topology has unsaved changes.\n\n"
                          "It is recommended to save the changes first to ensure:\n"
                          "• Latest configuration is used in export\n"
                          "• Proper Docker network naming\n"
                          "• Configuration consistency\n\n"
                          "Do you want to save the changes first?")
            
            # Show dialog with options
            reply = QMessageBox.question(
                self.main_window,
                title,
                message,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes  # Default to Yes
            )
            
            if reply == QMessageBox.Yes:
                debug_print("User chose to save before export")
                # Try to save the file
                if hasattr(self.main_window, 'file_manager'):
                    # Store current state to check if save was successful
                    old_file = getattr(self.main_window, 'current_file', None)
                    old_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
                    
                    if not current_file:
                        # No file exists, use Save As
                        self.main_window.file_manager.saveTopologyAs()
                    else:
                        # File exists, just save
                        self.main_window.file_manager.saveTopology()
                    
                    # Check if save was successful by verifying file state changed
                    new_file = getattr(self.main_window, 'current_file', None)
                    new_unsaved = getattr(self.main_window, 'has_unsaved_changes', False)
                    
                    if not current_file and not new_file:
                        # Save As was cancelled (no file selected)
                        return False
                    elif current_file and new_unsaved == old_unsaved and old_unsaved:
                        # Save failed (unsaved state didn't change when it should have)
                        QMessageBox.warning(
                            self.main_window,
                            "Save Failed", 
                            "Failed to save the topology. Please try again."
                        )
                        return False
                        
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "Save Error", 
                        "Unable to save topology. File manager not available."
                    )
                    return False
                    
            elif reply == QMessageBox.Cancel:
                debug_print("User cancelled export")
                # User cancelled the operation
                return False
                
            # If reply == QMessageBox.No, continue with export anyway
            debug_print("User chose to continue export without saving")
        
        debug_print("Save status check passed, proceeding with export")
        return True

    def write_dynamic_ue_connections(self, f, categorized_nodes):
        """Dynamically assign UEs to APs (traditional or gNB-APs) based on canvas positioning and coverage areas."""
        import math
        
        def calculate_distance(ue, ap):
            """Calculate Euclidean distance between UE and AP positions."""
            ue_x, ue_y = ue.get('x', 0), ue.get('y', 0)
            ap_x, ap_y = ap.get('x', 0), ap.get('y', 0)
            return math.sqrt((ue_x - ap_x)**2 + (ue_y - ap_y)**2)
        
        def get_coverage_range(ap):
            """Get the coverage range of an AP from its properties."""
            props = ap.get('properties', {})
            
            # For gNBs, extract range from wireless configuration
            if ap.get('type') == 'GNB':
                range_fields = ['GNB_Range', 'wireless_range', 'range', 'lineEdit_6', 'spinBox_3']
                for field in range_fields:
                    range_val = props.get(field)
                    if range_val:
                        try:
                            return float(range_val)
                        except (ValueError, TypeError):
                            continue
                return 300  # Default gNB range
            
            # For APs, extract range from properties
            range_fields = ['AP_Range', 'range', 'lineEdit_6', 'spinBox_3']
            for field in range_fields:
                range_val = props.get(field)
                if range_val:
                    try:
                        return float(range_val)
                    except (ValueError, TypeError):
                        continue
            return 116  # Default AP range
        
        def is_gnb_ap_enabled(gnb):
            """Check if a gNB has AP functionality enabled."""
            props = gnb.get('properties', {})
            env = props.get('environment', {})
            
            # Check if it's a gNB first
            if gnb.get('type') != 'GNB':
                return False
            
            # Check if AP is enabled in environment (Docker containers)
            if isinstance(env, dict):
                ap_enabled = (env.get('AP_ENABLED') == 'true' or 
                            env.get('AP_ENABLED') == True)
                if ap_enabled:
                    return True
            
            # Check if AP is enabled directly in properties  
            if not ap_enabled:
                ap_enabled_fields = [
                    'GNB_APEnabled', 'AP_ENABLED', 'checkBox_ap_enable',
                    'checkBox', 'ap_enabled', 'enable_ap', 'apEnabled'
                ]
                for field in ap_enabled_fields:
                    if props.get(field):
                        ap_enabled = True
                        break
            
            # Check alternative property names
            if not ap_enabled:
                for key, value in props.items():
                    if 'ap' in key.lower() and 'enable' in key.lower():
                        ap_enabled = True
                        break
            
            debug_print(f"DEBUG: gNB {gnb.get('name', 'unknown')} AP enabled: {ap_enabled}")
            return ap_enabled
        
        def get_ap_ssid(ap):
            """Get the SSID/AP name that UEs should connect to."""
            props = ap.get('properties', {})
            
            # For gNB APs, check if we have a generated AP and use its SSID
            if ap.get('type') == 'GNB' and '_generated_ap' in ap:
                return ap['_generated_ap']['ssid']
            
            # For gNB APs without generated AP, extract SSID from AP configuration
            if ap.get('type') == 'GNB':
                env = props.get('environment', {})
                if isinstance(env, dict):
                    ap_ssid = env.get('AP_SSID')
                    if ap_ssid:
                        return ap_ssid
                
                # Check direct properties
                gnb_ap_ssid = (props.get('GNB_AP_SSID') or 
                              props.get('ap_ap_ssid') or 
                              props.get('lineEdit_ap_ssid'))
                if gnb_ap_ssid:
                    return gnb_ap_ssid
                
                # Default gNB AP SSID
                return 'gnb-hotspot'
            
            # For traditional APs
            ap_ssid = props.get('AP_SSID', props.get('lineEdit_5'))
            if ap_ssid:
                return ap_ssid
            
            # Default AP SSID format: ap-name + "-ssid"
            ap_name = self.sanitize_variable_name(ap.get('name', 'ap'))
            return f"{ap_name}-ssid"
        
        # Collect all access points (traditional APs + gNB-APs)
        access_points = []
        
        # Add traditional APs
        for ap in categorized_nodes.get('aps', []):
            access_points.append(ap)
        
        # Add gNBs that have AP functionality enabled
        for gnb in categorized_nodes.get('gnbs', []):
            if is_gnb_ap_enabled(gnb):
                access_points.append(gnb)
                debug_print(f"DEBUG: Added gNB {gnb.get('name')} as access point")
        
        if not access_points:
            f.write('    # No access points (traditional APs or gNB-APs) found\n')
            f.write('    # UEs will use 5G connectivity through gNBs only\n\n')
            return
        
        f.write('    # Dynamic UE assignment to access points (traditional APs and gNB-APs) based on distance and coverage\n')
        
        # Process each UE and find the best access point
        ue_assignments = {}
        
        for ue in categorized_nodes.get('ues', []):
            ue_name = self.sanitize_variable_name(ue['name'])
            best_ap = None
            best_distance = float('inf')
            
            f.write(f'    # Finding best access point for {ue_name} at position ({ue.get("x", 0):.1f}, {ue.get("y", 0):.1f})\n')
            
            # Check each access point
            for ap in access_points:
                distance = calculate_distance(ue, ap)
                coverage_range = get_coverage_range(ap)
                ap_name = ap.get('name', 'unknown')
                ap_type = ap.get('type', 'AP')
                
                f.write(f'    # {ap_name} ({ap_type}) at ({ap.get("x", 0):.1f}, {ap.get("y", 0):.1f}): distance={distance:.1f}m, range={coverage_range}m\n')
                
                # Check if UE is within coverage and find the closest one
                if distance <= coverage_range and distance < best_distance:
                    best_ap = ap
                    best_distance = distance
            
            if best_ap:
                ap_ssid = get_ap_ssid(best_ap)
                ue_assignments[ue_name] = {
                    'ssid': ap_ssid,
                    'ap_name': best_ap.get('name', 'unknown'),
                    'ap_type': best_ap.get('type', 'AP'),
                    'distance': best_distance
                }
                f.write(f'    # {ue_name} -> {best_ap.get("name")} (SSID: {ap_ssid}, distance: {best_distance:.1f}m)\n')
            else:
                # No AP in range, connect to the closest one anyway
                closest_ap = min(access_points, key=lambda ap: calculate_distance(ue, ap))
                ap_ssid = get_ap_ssid(closest_ap)
                closest_distance = calculate_distance(ue, closest_ap)
                ue_assignments[ue_name] = {
                    'ssid': ap_ssid,
                    'ap_name': closest_ap.get('name', 'unknown'),
                    'ap_type': closest_ap.get('type', 'AP'),
                    'distance': closest_distance
                }
                f.write(f'    # {ue_name} -> {closest_ap.get("name")} (SSID: {ap_ssid}, distance: {closest_distance:.1f}m) [OUT OF RANGE - connecting to closest]\n')
        
        f.write('\n')
        
        # Generate the connection commands
        for ue_name, assignment in ue_assignments.items():
            f.write(f'    {ue_name}.cmd("iw dev {ue_name}-wlan0 connect {assignment["ssid"]}")\n')
        
        f.write('\n')

    def write_ap_gnb_links(self, f, categorized_nodes):
        """Write direct links between APs and their corresponding gNBs."""
        gnbs_with_ap = []
        
        # Find gNBs that have AP functionality enabled
        for gnb in categorized_nodes['gnbs']:
            if '_generated_ap' in gnb:
                gnbs_with_ap.append(gnb)
        
        if gnbs_with_ap:
            f.write('    # Link APs to gNBs\n')
            for gnb in gnbs_with_ap:
                gnb_name = self.sanitize_variable_name(gnb['name'])
                ap_name = gnb['_generated_ap']['name']
                f.write(f'    net.addLink({ap_name}, {gnb_name})\n')
            f.write('    \n')
        
        return gnbs_with_ap

    def get_gnb_ap_mapping(self, categorized_nodes):
        """Get mapping of gNB names to their corresponding AP names."""
        gnb_to_ap = {}
        
        for gnb in categorized_nodes['gnbs']:
            if '_generated_ap' in gnb:
                gnb_name = self.sanitize_variable_name(gnb['name'])
                ap_name = gnb['_generated_ap']['name']
                gnb_to_ap[gnb_name] = ap_name
        
        return gnb_to_ap