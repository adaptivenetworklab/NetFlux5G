"""
Configuration mapping for different component types to Mininet parameters
"""

class ConfigurationMapper:
    """Maps UI component configurations to Mininet script parameters"""
    
    @staticmethod
    def map_host_config(properties):
        """Map host component properties to Mininet host parameters"""
        opts = []
        
        # IP Address
        ip_fields = ["STA_IPAddress", "Host_IPAddress", "UE_IPAddress"]
        for field in ip_fields:
            if properties.get(field):
                ip = properties[field].strip()
                if ip:
                    opts.append(f"ip='{ip}'")
                    break
        
        # Default Route
        route_fields = ["STA_DefaultRoute", "Host_DefaultRoute"]
        for field in route_fields:
            if properties.get(field):
                route = properties[field].strip()
                if route:
                    opts.append(f"defaultRoute='via {route}'")
                    break
        
        # CPU Configuration
        cpu_fields = ["STA_AmountCPU", "Host_AmountCPU"]
        for field in cpu_fields:
            if properties.get(field):
                cpu = properties[field].strip()
                if cpu:
                    try:
                        cpu_val = float(cpu)
                        opts.append(f"cpu={cpu_val}")
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_switch_config(properties):
        """Map switch/router properties to Mininet switch parameters"""
        opts = []
        
        # DPID
        dpid_fields = ["Switch_DPID", "Router_DPID", "AP_DPID"]
        for field in dpid_fields:
            if properties.get(field):
                dpid = properties[field].strip()
                if dpid:
                    opts.append(f"dpid='{dpid}'")
                    break
        
        return opts
    
    @staticmethod
    def map_ap_config(properties):
        """Map Access Point properties to Mininet AP parameters"""
        opts = []
        
        # SSID
        if properties.get("AP_SSID"):
            ssid = properties["AP_SSID"].strip()
            if ssid:
                opts.append(f"ssid='{ssid}'")
        
        # Channel
        if properties.get("AP_Channel"):
            channel = properties["AP_Channel"].strip()
            if channel:
                try:
                    ch_val = int(channel)
                    opts.append(f"channel={ch_val}")
                except ValueError:
                    pass
        
        # Mode
        if properties.get("AP_Mode"):
            mode = properties["AP_Mode"].strip()
            if mode:
                opts.append(f"mode='{mode}'")
        
        # Wireless protocol
        if properties.get("AP_WirelessProtocol"):
            protocol = properties["AP_WirelessProtocol"].strip()
            if protocol:
                opts.append(f"protocol='{protocol}'")
        
        return opts
    
    @staticmethod
    def map_controller_config(properties):
        """Map Controller properties to Mininet controller parameters"""
        opts = []
        
        # IP Address
        if properties.get("Controller_IPAddress"):
            ip = properties["Controller_IPAddress"].strip()
            if ip:
                opts.append(f"ip='{ip}'")
        
        # Port
        if properties.get("Controller_Port"):
            port = properties["Controller_Port"].strip()
            if port:
                try:
                    port_val = int(port)
                    opts.append(f"port={port_val}")
                except ValueError:
                    pass
        
        return opts
    
    @staticmethod
    def generate_post_config_commands(node_type, properties, var_name):
        """Generate post-configuration commands for a node"""
        commands = []
        
        # Start commands
        start_cmd_fields = ["STA_StartCommand", "Host_StartCommand", "GNB_StartCommand"]
        for field in start_cmd_fields:
            if properties.get(field):
                cmd = properties[field].strip()
                if cmd:
                    commands.append(f"    {var_name}.cmd('{cmd}')")
                    break
        
        # Stop commands (as comments for reference)
        stop_cmd_fields = ["STA_StopCommand", "Host_StopCommand", "GNB_StopCommand"]
        for field in stop_cmd_fields:
            if properties.get(field):
                cmd = properties[field].strip()
                if cmd:
                    commands.append(f"    # Stop command: {var_name}.cmd('{cmd}')")
                    break
        
        # Wireless authentication setup for STA
        if node_type == "STA":
            auth_type = properties.get("STA_AuthenticationType")
            if auth_type and auth_type != "none":
                commands.append(f"    # Wireless authentication setup for {var_name}")
                commands.append(f"    # Authentication type: {auth_type}")
                
                if properties.get("STA_Username"):
                    username = properties["STA_Username"]
                    commands.append(f"    # Username: {username}")
                
                if auth_type in ["WPA", "WPA2"]:
                    if properties.get("STA_Password"):
                        commands.append(f"    # WPA/WPA2 setup required")
        
        # Docker container setup
        if node_type == "DockerHost":
            if properties.get("DockerHost_ContainerImage"):
                image = properties["DockerHost_ContainerImage"]
                commands.append(f"    # Docker image: {image}")
            
            if properties.get("DockerHost_PortForward"):
                ports = properties["DockerHost_PortForward"]
                commands.append(f"    # Port forwarding: {ports}")
        
        return commands