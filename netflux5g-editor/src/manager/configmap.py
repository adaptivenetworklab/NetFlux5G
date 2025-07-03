"""
Configuration mapping for different component types to Mininet parameters
Streamlined version focused on essential 5G core functionality
"""

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
                    except ValueError:
                        pass
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
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_gnb_config(properties):
        """Map gNB properties to configuration parameters"""
        config = {}
        
        # gNB specific configurations following fixed_topology-upf.py pattern
        config['amf_ip'] = properties.get('GNB_AMF_IP', '10.0.0.3')
        config['hostname'] = properties.get('GNB_Hostname', 'mn.gnb')
        config['mcc'] = properties.get('GNB_MCC', '999')
        config['mnc'] = properties.get('GNB_MNC', '70')
        config['sst'] = properties.get('GNB_SST', '1')
        config['sd'] = properties.get('GNB_SD', '0xffffff')
        config['tac'] = properties.get('GNB_TAC', '1')
        
        # Power configuration for radio propagation
        power_fields = ["GNB_Power", "GNB_TxPower", "lineEdit_power", "doubleSpinBox_power"]
        for field in power_fields:
            if properties.get(field):
                power = str(properties[field]).strip()
                if power:
                    try:
                        power_val = float(power)
                        if power_val > 0:
                            config['txpower'] = power_val
                    except ValueError:
                        pass
                    break
        
        # Range configuration (coverage area)
        range_fields = ["GNB_Range", "GNB_Coverage", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_int = int(range_val)
                        if range_int > 0:
                            config['range'] = range_int
                    except ValueError:
                        pass
                    break
        
        return config
    
    @staticmethod
    def map_ue_config(properties):
        """Map UE properties to configuration parameters"""
        config = {}
        # Use gNB hostname instead of IP
        gnb_hostname = properties.get('UE_GNB_HOSTNAME')
        if not gnb_hostname:
            # Try to find a gNB hostname in the topology if available (not possible here, so fallback)
            gnb_hostname = 'mn.gnb'
        config['gnb_hostname'] = gnb_hostname
        # Deprecated: config['gnb_ip'] = properties.get('UE_GNB_IP', '10.0.0.4')
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
        
        # Power configuration for radio propagation
        power_fields = ["UE_Power", "UE_TxPower", "lineEdit_power", "doubleSpinBox_power"]
        for field in power_fields:
            if properties.get(field):
                power = str(properties[field]).strip()
                if power:
                    try:
                        power_val = float(power)
                        if power_val > 0:
                            config['txpower'] = power_val
                    except ValueError:
                        pass
                    break
        
        # Range configuration (coverage area)
        range_fields = ["UE_Range", "UE_Coverage", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_int = int(range_val)
                        if range_int > 0:
                            config['range'] = range_int
                    except ValueError:
                        pass
                    break
        
        return config
    
    @staticmethod
    def get_5g_core_docker_options(component_type):
        """Get Docker-specific options for 5G components based on fixed_topology-upf.py"""
        base_options = {
            'cap_add': ["net_admin"],
            'network_mode': "open5gs-ueransim_default", 
            'publish_all_ports': True,
            'dcmd': "/bin/bash",
            'cls': "DockerSta",
            'range': 116
        }
        
        # Component-specific configurations
        component_configs = {
            'UPF': {
                'privileged': True,
                'dimage': 'adaptive/open5gs:1.0'
            },
            'AMF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'SMF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'NRF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'SCP': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'AUSF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'BSF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'NSSF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'PCF': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'UDM': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'UDR': {
                'dimage': 'adaptive/open5gs:1.0'
            },
            'GNB': {
                'dimage': 'gradiant/ueransim:3.2.6'
            },
            'UE': {
                'devices': ["/dev/net/tun"],
                'dimage': 'gradiant/ueransim:3.2.6'
            }
        }
        
        options = base_options.copy()
        if component_type in component_configs:
            options.update(component_configs[component_type])
            
        return options
    
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
        
        # Power configuration for radio propagation
        power_fields = ["AP_Power", "AP_TxPower", "lineEdit_power", "doubleSpinBox_power"]
        for field in power_fields:
            if properties.get(field):
                power = str(properties[field]).strip()
                if power:
                    try:
                        power_val = float(power)
                        if power_val > 0:
                            opts.append(f"txpower={power_val}")
                    except ValueError:
                        pass
                    break
        
        # Range configuration (coverage area)
        range_fields = ["AP_Range", "AP_Coverage", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_int = int(range_val)
                        if range_int > 0:
                            opts.append(f"range={range_int}")
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_controller_config(properties):
        """Map Controller properties to Mininet controller parameters"""
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
                if port:
                    try:
                        port_val = int(port)
                        if port_val != 6633:  # Only add if different from default
                            opts.append(f"port={port_val}")
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_sta_config(properties):
        """Map Station properties to Mininet station parameters"""
        opts = []
        
        # IP Address
        ip_fields = ["STA_IPAddress", "lineEdit_2"]
        for field in ip_fields:
            if properties.get(field):
                ip = properties[field].strip()
                if ip and ip != "10.0.0.1":
                    opts.append(f"ip='{ip}'")
                    break
        
        # Default Route
        route_fields = ["STA_DefaultRoute", "lineEdit_3"]
        for field in route_fields:
            if properties.get(field):
                route = properties[field].strip()
                if route:
                    opts.append(f"defaultRoute='via {route}'")
                    break
        
        # CPU Configuration
        cpu_fields = ["STA_AmountCPU", "doubleSpinBox"]
        for field in cpu_fields:
            if properties.get(field):
                cpu = str(properties[field]).strip()
                if cpu:
                    try:
                        cpu_val = float(cpu)
                        if cpu_val > 0 and cpu_val != 1.0:
                            opts.append(f"cpu={cpu_val}")
                    except ValueError:
                        pass
                    break
        
        # Memory Configuration
        memory_fields = ["STA_Memory", "spinBox"]
        for field in memory_fields:
            if properties.get(field):
                memory = str(properties[field]).strip()
                if memory:
                    try:
                        mem_val = int(memory)
                        if mem_val > 0:
                            opts.append(f"mem={mem_val}")
                    except ValueError:
                        pass
                    break
        
        # Power configuration for radio propagation
        power_fields = ["STA_Power", "STA_TxPower", "lineEdit_power", "doubleSpinBox_power"]
        for field in power_fields:
            if properties.get(field):
                power = str(properties[field]).strip()
                if power:
                    try:
                        power_val = float(power)
                        if power_val > 0:
                            opts.append(f"txpower={power_val}")
                    except ValueError:
                        pass
                    break
        
        # Range configuration (coverage area)
        range_fields = ["STA_Range", "STA_Coverage", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_int = int(range_val)
                        if range_int > 0:
                            opts.append(f"range={range_int}")
                    except ValueError:
                        pass
                    break
        
        return opts
    
    @staticmethod
    def get_component_config(node_type, properties):
        """Get the complete configuration for a component type"""
        config_map = {
            "Host": ConfigurationMapper.map_host_config,
            "STA": ConfigurationMapper.map_host_config,
            "UE": ConfigurationMapper.map_ue_config,
            "AP": ConfigurationMapper.map_ap_config,
            "Controller": ConfigurationMapper.map_controller_config,
            "GNB": ConfigurationMapper.map_gnb_config,
        }
        
        mapper = config_map.get(node_type, lambda p: [])
        return mapper(properties)