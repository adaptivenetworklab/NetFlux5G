"""
Configuration mapping for different component types to Mininet parameters
"""
from manager.debug import debug_print, error_print, warning_print

class ConfigurationMapper:
    """Maps UI component configurations to Mininet script parameters"""
    
    @staticmethod
    def map_host_config(properties):
        """Map host component properties to Mininet host parameters"""
        opts = []
        
        # IP Address
        ip_fields = ["STA_IPAddress", "Host_IPAddress", "UE_IPAddress", "lineEdit_2", "lineEdit"]
        for field in ip_fields:
            if properties.get(field):
                ip = properties[field].strip()
                if ip and ip != "192.168.1.1":  # Skip default values
                    opts.append(f"ip='{ip}'")
                    break
        
        # Default Route
        route_fields = ["STA_DefaultRoute", "Host_DefaultRoute", "lineEdit_3"]
        for field in route_fields:
            if properties.get(field):
                route = properties[field].strip()
                if route:
                    opts.append(f"defaultRoute='via {route}'")
                    break
        
        # CPU Configuration
        cpu_fields = ["STA_AmountCPU", "Host_AmountCPU", "doubleSpinBox"]
        for field in cpu_fields:
            if properties.get(field):
                cpu = str(properties[field]).strip()
                if cpu:
                    try:
                        cpu_val = float(cpu)
                        if cpu_val != 1.0:  # Only add if different from default
                            opts.append(f"cpu={cpu_val}")
                    except (ValueError, TypeError):
                        warning_print(f"Invalid CPU value: {cpu}")
                    break
        
        # Memory Configuration
        memory_fields = ["Host_Memory", "STA_Memory", "spinBox"]
        for field in memory_fields:
            if properties.get(field):
                memory = str(properties[field]).strip()
                if memory:
                    try:
                        mem_val = int(memory)
                        if mem_val > 0:
                            opts.append(f"mem={mem_val}")
                    except (ValueError, TypeError):
                        warning_print(f"Invalid memory value: {memory}")
                    break
        
        return opts
    
    @staticmethod
    def map_gnb_config(properties):
        """Map gNB properties to configuration parameters"""
        config = {}
        
        # gNB specific configurations
        config['amf_ip'] = properties.get('GNB_AMF_IP', '10.0.0.3')
        config['hostname'] = properties.get('GNB_Hostname', 'mn.gnb')
        config['mcc'] = properties.get('GNB_MCC', '999')
        config['mnc'] = properties.get('GNB_MNC', '70')
        config['sst'] = properties.get('GNB_SST', '1')
        config['sd'] = properties.get('GNB_SD', '0xffffff')
        config['tac'] = properties.get('GNB_TAC', '1')
        config['frequency'] = properties.get('GNB_Frequency', '3500')
        config['band'] = properties.get('GNB_Band', 'n78')
        
        return config
    
    @staticmethod
    def map_ue_config(properties):
        """Map UE properties to configuration parameters"""
        config = {}
        
        # UE specific configurations
        config['gnb_ip'] = properties.get('UE_GNB_IP', '10.0.0.4')
        config['apn'] = properties.get('UE_APN', 'internet')
        config['msisdn'] = properties.get('UE_MSISDN', '0000000001')
        config['mcc'] = properties.get('UE_MCC', '999')
        config['mnc'] = properties.get('UE_MNC', '70')
        config['sst'] = properties.get('UE_SST', '1')
        config['sd'] = properties.get('UE_SD', '0xffffff')
        config['tac'] = properties.get('UE_TAC', '1')
        config['key'] = properties.get('UE_Key', '465B5CE8B199B49FAA5F0A2EE238A6BC')
        config['op_type'] = properties.get('UE_OP_Type', 'OPC')
        config['op'] = properties.get('UE_OP', 'E8ED289DEBA952E4283B54E88E6183CA')
        
        return config
    
    @staticmethod
    def map_5g_core_config(properties):
        """Map 5G Core component properties to configuration parameters"""
        config = {}
        
        # 5G Core specific configurations
        config['component_type'] = properties.get('Component5G_Type', 'AMF')
        config['network_mode'] = properties.get('Component5G_NetworkMode', 'open5gs-ueransim_default')
        config['image'] = properties.get('Component5G_Image', 'adaptive/open5gs:1.0')
        config['config_file'] = properties.get('Component5G_ConfigFile', 'default.yaml')
        
        return config
    
    @staticmethod
    def map_ap_config(properties):
        """Map Access Point properties to Mininet AP parameters"""
        opts = []
        
        # SSID
        ssid_fields = ["AP_SSID", "lineEdit_5"]
        for field in ssid_fields:
            if properties.get(field):
                ssid = properties[field].strip()
                if ssid and ssid != "my-ssid":
                    opts.append(f"ssid='{ssid}'")
                    break
        
        # Channel
        channel_fields = ["AP_Channel", "spinBox_2"]
        for field in channel_fields:
            if properties.get(field):
                channel = str(properties[field]).strip()
                if channel:
                    try:
                        ch_val = int(channel)
                        if ch_val != 1:  # Only add if different from default
                            opts.append(f"channel={ch_val}")
                    except ValueError:
                        pass
                    break
        
        # Mode
        mode_fields = ["AP_Mode", "comboBox_2"]
        for field in mode_fields:
            if properties.get(field):
                mode = properties[field].strip()
                if mode and mode != "g":
                    opts.append(f"mode='{mode}'")
                    break
        
        # Wireless protocol
        protocol_fields = ["AP_WirelessProtocol", "comboBox_3"]
        for field in protocol_fields:
            if properties.get(field):
                protocol = properties[field].strip()
                if protocol:
                    opts.append(f"protocol='{protocol}'")
                    break
        
        # Range/Position
        range_fields = ["AP_Range", "spinBox_3"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        r_val = int(range_val)
                        if r_val != 30:  # Only add if different from default
                            opts.append(f"range={r_val}")
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_switch_config(properties):
        """Map switch/router properties to Mininet switch parameters"""
        opts = []
        
        # DPID
        dpid_fields = ["Switch_DPID", "Router_DPID", "AP_DPID", "lineEdit_4"]
        for field in dpid_fields:
            if properties.get(field):
                dpid = properties[field].strip()
                if dpid:
                    opts.append(f"dpid='{dpid}'")
                    break
        
        # Protocol
        protocol_fields = ["Switch_Protocol", "comboBox"]
        for field in protocol_fields:
            if properties.get(field):
                protocol = properties[field].strip()
                if protocol and protocol != "OpenFlow":
                    opts.append(f"protocols='{protocol}'")
                    break
        
        return opts
    
    @staticmethod
    def map_controller_config(properties):
        """Map Controller properties to Mininet controller parameters."""
        opts = []
        
        # IP Address
        ip_fields = ["Controller_IPAddress", "lineEdit_6"]
        for field in ip_fields:
            if properties.get(field):
                ip = properties[field].strip()
                if ip and ip != "127.0.0.1":
                    opts.append(f"ip='{ip}'")
                    break
        
        # Port
        port_fields = ["Controller_Port", "spinBox_4"]
        for field in port_fields:
            if properties.get(field):
                port = str(properties[field]).strip()
                if port and port != "6633":
                    opts.append(f"port={port}")
                    break
        
        # Controller type
        type_fields = ["Controller_Type", "comboBox_4"]
        for field in type_fields:
            if properties.get(field):
                ctrl_type = properties[field].strip()
                if ctrl_type and ctrl_type != "RemoteController":
                    opts.append(f"controller={ctrl_type}")
                    break
        
        return opts
    
    @staticmethod
    def map_docker_config(properties):
        """Map Docker Host properties to container parameters."""
        opts = []
        
        # Container Image
        image_fields = ["DockerHost_ContainerImage", "DockerHost_Image"]
        for field in image_fields:
            if properties.get(field):
                image = properties[field].strip()
                if image:
                    opts.append(f"dimage='{image}'")
                    break
        
        # Container Command
        cmd_fields = ["DockerHost_Command", "DockerHost_Cmd"]
        for field in cmd_fields:
            if properties.get(field):
                cmd = properties[field].strip()
                if cmd:
                    opts.append(f"dcmd='{cmd}'")
                    break
        
        return opts

    @staticmethod
    def get_component_config(component_type, properties):
        """Get configuration for any component type."""
        if component_type in ['Host', 'STA']:
            return ConfigurationMapper.map_host_config(properties)
        elif component_type == 'GNB':
            return ConfigurationMapper.map_gnb_config(properties)
        elif component_type == 'UE':
            return ConfigurationMapper.map_ue_config(properties)
        elif component_type == 'VGcore':
            return ConfigurationMapper.map_5g_core_config(properties)
        elif component_type == 'AP':
            return ConfigurationMapper.map_ap_config(properties)
        elif component_type in ['Switch', 'Router']:
            return ConfigurationMapper.map_switch_config(properties)
        elif component_type == 'Controller':
            return ConfigurationMapper.map_controller_config(properties)
        elif component_type == 'DockerHost':
            return ConfigurationMapper.map_docker_config(properties)
        else:
            return []