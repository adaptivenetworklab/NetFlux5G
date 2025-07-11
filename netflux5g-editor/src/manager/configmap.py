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
        """Map gNB properties to configuration parameters with enhanced UERANSIM Docker support"""
        config = {}
        
        # Enhanced 5G configuration using new field names matching UERANSIM Dockerfile
        config['amf_hostname'] = properties.get('GNB_AMFHostName', properties.get('5g_amf_hostname', 'amf'))
        config['amf_ip'] = properties.get('GNB_AMF_IP', properties.get('5g_amf_ip', ''))  # Explicit AMF IP for direct connection
        config['gnb_hostname'] = properties.get('GNB_GNBHostName', properties.get('5g_gnb_hostname', 'localhost'))
        config['mcc'] = properties.get('GNB_MCC', properties.get('5g_mcc', '999'))
        config['mnc'] = properties.get('GNB_MNC', properties.get('5g_mnc', '70'))
        config['sst'] = properties.get('GNB_SST', properties.get('5g_sst', '1'))
        config['sd'] = properties.get('GNB_SD', properties.get('5g_sd', '0xffffff'))
        config['tac'] = properties.get('GNB_TAC', properties.get('5g_tac', '1'))
        
        # Network interfaces configuration - must match Dockerfile environment variables
        config['n2_iface'] = properties.get('GNB_N2_Interface', properties.get('network_n2_iface', 'eth0'))
        config['n3_iface'] = properties.get('GNB_N3_Interface', properties.get('network_n3_iface', 'eth0'))
        config['radio_iface'] = properties.get('GNB_Radio_Interface', properties.get('network_radio_iface', 'eth0'))
        config['network_interface'] = properties.get('GNB_Network_Interface', properties.get('network_network_interface', 'eth0'))
        
        # UERANSIM component type
        config['ueransim_component'] = 'gnb'
        
        # Wireless configuration for mininet-wifi
        power_fields = ["GNB_Power", "wireless_txpower", "GNB_TxPower", "lineEdit_power", "doubleSpinBox_power"]
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
        range_fields = ["GNB_Range", "wireless_range", "GNB_Coverage", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_num = float(range_val)
                        if range_num > 0:
                            config['range'] = range_num
                    except ValueError:
                        pass
                    break
        
        # Set default values if not specified
        if 'txpower' not in config:
            config['txpower'] = 30  # Default gNB power
        if 'range' not in config:
            config['range'] = 300  # Default gNB range
        
        # OVS/OpenFlow configuration from GNB properties dialog
        ovs_config = {}
        
        # Check if OVS is enabled - look for various field names
        ovs_enabled_fields = ['GNB_OVS_Enabled', 'ovs_ovs_enabled', 'checkBox_ovs_enabled', 'ovs_enabled']
        ovs_enabled = False
        for field in ovs_enabled_fields:
            if properties.get(field):
                ovs_enabled = True
                break
        
        if ovs_enabled:
            ovs_config['OVS_ENABLED'] = 'true'
            
            # Bridge configuration
            ovs_config['OVS_BRIDGE_NAME'] = (
                properties.get('GNB_OVS_BridgeName') or 
                properties.get('ovs_ovs_bridge_name') or 
                properties.get('lineEdit_ovs_bridge_name') or
                'br-ueransim'
            )
            
            ovs_config['OVS_FAIL_MODE'] = (
                properties.get('GNB_OVS_FailMode') or 
                properties.get('ovs_ovs_fail_mode') or 
                properties.get('comboBox_ovs_fail_mode') or
                'standalone'
            )
            
            ovs_config['OPENFLOW_PROTOCOLS'] = (
                properties.get('GNB_OVS_Protocols') or 
                properties.get('ovs_openflow_protocols') or 
                properties.get('lineEdit_openflow_protocols') or
                'OpenFlow14'
            )
            
            ovs_config['OVS_DATAPATH'] = (
                properties.get('GNB_OVS_Datapath') or 
                properties.get('ovs_ovs_datapath') or 
                properties.get('comboBox_ovs_datapath') or
                'kernel'
            )
            
            # Auto setup configuration
            auto_setup_fields = ['GNB_OVS_AutoSetup', 'ovs_ovs_auto_setup', 'checkBox_ovs_auto_setup']
            ovs_auto_setup = False
            for field in auto_setup_fields:
                if properties.get(field):
                    ovs_auto_setup = True
                    break
            ovs_config['OVS_AUTO_SETUP'] = 'true' if ovs_auto_setup else 'false'
            
            # Controller configuration
            controller_fields = ['GNB_OVS_Controller', 'ovs_ovs_controller', 'lineEdit_ovs_controller']
            for field in controller_fields:
                controller = properties.get(field)
                if controller:
                    ovs_config['OVS_CONTROLLER'] = str(controller)
                    break
                    
            controller_ip_fields = ['GNB_OVS_ControllerIP', 'ovs_controller_ip', 'lineEdit_controller_ip']
            for field in controller_ip_fields:
                controller_ip = properties.get(field)
                if controller_ip:
                    ovs_config['CONTROLLER_IP'] = str(controller_ip)
                    break
                    
            controller_port_fields = ['GNB_OVS_ControllerPort', 'ovs_controller_port', 'spinBox_controller_port']
            for field in controller_port_fields:
                controller_port = properties.get(field)
                if controller_port:
                    ovs_config['CONTROLLER_PORT'] = str(controller_port)
                    break
            if 'CONTROLLER_PORT' not in ovs_config:
                ovs_config['CONTROLLER_PORT'] = '6633'
                
            # Bridge interfaces
            bridge_iface_fields = ['GNB_OVS_BridgeInterfaces', 'ovs_bridge_interfaces', 'lineEdit_bridge_interfaces']
            for field in bridge_iface_fields:
                bridge_ifaces = properties.get(field)
                if bridge_ifaces:
                    ovs_config['BRIDGE_INTERFACES'] = str(bridge_ifaces)
                    break
                
            # Bridge priority and STP
            priority_fields = ['GNB_Bridge_Priority', 'network_bridge_priority', 'spinBox_bridge_priority']
            for field in priority_fields:
                priority = properties.get(field)
                if priority:
                    ovs_config['BRIDGE_PRIORITY'] = str(priority)
                    break
            if 'BRIDGE_PRIORITY' not in ovs_config:
                ovs_config['BRIDGE_PRIORITY'] = '32768'
                
            # STP configuration
            stp_fields = ['GNB_STP_Enabled', 'network_stp_enabled', 'checkBox_stp_enabled']
            stp_enabled = False
            for field in stp_fields:
                if properties.get(field):
                    stp_enabled = True
                    break
            ovs_config['STP_ENABLED'] = 'true' if stp_enabled else 'false'
        else:
            ovs_config['OVS_ENABLED'] = 'false'
            
        config['ovs_config'] = ovs_config
        
        # AP configuration from GNB properties dialog
        ap_config = {}
        
        # Check if AP is enabled - look for various field names
        ap_enabled_fields = ['GNB_AP_Enabled', 'ap_ap_enabled', 'checkBox_ap_enabled', 'ap_enabled']
        ap_enabled = False
        for field in ap_enabled_fields:
            if properties.get(field):
                ap_enabled = True
                break
        
        if ap_enabled:
            ap_config['AP_ENABLED'] = 'true'
            
            # Basic AP configuration
            ap_config['AP_SSID'] = (
                properties.get('GNB_AP_SSID') or 
                properties.get('ap_ap_ssid') or 
                properties.get('lineEdit_ap_ssid') or
                'gnb-hotspot'
            )
            
            channel_fields = ['GNB_AP_Channel', 'ap_ap_channel', 'spinBox_ap_channel']
            for field in channel_fields:
                channel = properties.get(field)
                if channel:
                    ap_config['AP_CHANNEL'] = str(channel)
                    break
            if 'AP_CHANNEL' not in ap_config:
                ap_config['AP_CHANNEL'] = '6'
                
            ap_config['AP_MODE'] = (
                properties.get('GNB_AP_Mode') or 
                properties.get('ap_ap_mode') or 
                properties.get('comboBox_ap_mode') or
                'g'
            )
            
            # Password configuration
            passwd_fields = ['GNB_AP_Password', 'ap_ap_passwd', 'lineEdit_ap_password']
            for field in passwd_fields:
                passwd = properties.get(field)
                if passwd:
                    ap_config['AP_PASSWD'] = str(passwd)
                    break
            if 'AP_PASSWD' not in ap_config:
                ap_config['AP_PASSWD'] = ''
                
            # Bridge configuration
            ap_config['AP_BRIDGE_NAME'] = (
                properties.get('GNB_AP_BridgeName') or 
                properties.get('ap_ap_bridge_name') or 
                properties.get('lineEdit_ap_bridge_name') or
                'br-gnb'
            )
            
            # OpenFlow configuration for AP (shared with OVS configuration)
            if ovs_config.get('OVS_CONTROLLER'):
                ap_config['OVS_CONTROLLER'] = ovs_config['OVS_CONTROLLER']
            ap_config['AP_FAILMODE'] = ovs_config.get('OVS_FAIL_MODE', 'standalone')
            ap_config['OPENFLOW_PROTOCOLS'] = ovs_config.get('OPENFLOW_PROTOCOLS', 'OpenFlow14')
            
            # DHCP configuration (optional)
            dhcp_fields = ['GNB_AP_EnableDHCP', 'ap_enable_dhcp', 'checkBox_ap_dhcp']
            dhcp_enabled = False
            for field in dhcp_fields:
                if properties.get(field):
                    dhcp_enabled = True
                    break
            ap_config['ENABLE_DHCP'] = 'true' if dhcp_enabled else 'false'
        else:
            ap_config['AP_ENABLED'] = 'false'
            
        config['ap_config'] = ap_config
        
        return config
    
    @staticmethod
    def map_ue_config(properties):
        """Enhanced map UE properties to configuration parameters with UERANSIM Docker support"""
        config = {}
        
        # Core 5G/UE Configuration matching UERANSIM Dockerfile
        gnb_hostname = (properties.get('UE_GNBHostName') or 
                       properties.get('5g_gnb_hostname') or 
                       properties.get('network_gnb_hostname') or 
                       'localhost')
        config['gnb_hostname'] = gnb_hostname
        
        # Basic UE parameters - must match Dockerfile environment variables
        config['apn'] = properties.get('UE_APN', properties.get('5g_apn', 'internet'))
        config['msisdn'] = properties.get('UE_MSISDN', properties.get('5g_msisdn', '0000000001'))
        config['mcc'] = properties.get('UE_MCC', properties.get('5g_mcc', '999'))
        config['mnc'] = properties.get('UE_MNC', properties.get('5g_mnc', '70'))
        config['sst'] = properties.get('UE_SST', properties.get('5g_sst', '1'))
        config['sd'] = properties.get('UE_SD', properties.get('5g_sd', '0xffffff'))
        config['tac'] = properties.get('UE_TAC', properties.get('5g_tac', '1'))
        
        # Authentication parameters
        config['key'] = properties.get('UE_KEY', properties.get('5g_key', '465B5CE8B199B49FAA5F0A2EE238A6BC'))
        config['op_type'] = properties.get('UE_OPType', properties.get('5g_op_type', 'OPC'))
        config['op'] = properties.get('UE_OP', properties.get('5g_op', 'E8ED289DEBA952E4283B54E88E6183CA'))
        
        # Device identifiers
        config['imei'] = properties.get('UE_IMEI', properties.get('5g_imei', '356938035643803'))
        config['imeisv'] = properties.get('UE_IMEISV', properties.get('5g_imeisv', '4370816125816151'))
        
        # Network configuration
        gnb_ip = properties.get('UE_GNB_IP')
        if gnb_ip and gnb_ip.strip():
            config['gnb_ip'] = gnb_ip.strip()
        
        config['tunnel_iface'] = properties.get('UE_TunnelInterface', properties.get('network_tunnel_iface', 'uesimtun0'))
        config['radio_iface'] = properties.get('UE_RadioInterface', properties.get('network_radio_iface', 'eth0'))
        config['session_type'] = properties.get('UE_SessionType', properties.get('network_session_type', 'IPv4'))
        
        # PDU sessions
        pdu_sessions = properties.get('UE_PDUSessions', properties.get('network_pdu_sessions', 1))
        if pdu_sessions:
            try:
                config['pdu_sessions'] = int(pdu_sessions)
            except (ValueError, TypeError):
                config['pdu_sessions'] = 1
        else:
            config['pdu_sessions'] = 1
        
        # Mobility configuration
        config['mobility'] = properties.get('UE_Mobility', properties.get('network_mobility_enabled', False))
        
        # UERANSIM component type
        config['ueransim_component'] = 'ue'
        
        # Wireless configuration for mininet-wifi
        power_fields = ["UE_Power", "wireless_txpower", "UE_TxPower", "lineEdit_power", "doubleSpinBox_power"]
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
        range_fields = ["UE_Range", "wireless_range", "UE_Coverage", "UE_TxRange", "spinBox_range"]
        for field in range_fields:
            if properties.get(field):
                range_val = str(properties[field]).strip()
                if range_val:
                    try:
                        range_num = float(range_val)
                        if range_num > 0:
                            config['range'] = range_num
                    except ValueError:
                        pass
                    break
        
        # Set default values if not specified
        if 'txpower' not in config:
            config['txpower'] = 20  # Default UE power
        if 'range' not in config:
            config['range'] = 116  # Default UE range
        
        # Association and mobility
        config['association'] = properties.get('UE_AssociationMode', properties.get('wireless_association', 'auto'))
        
        # OVS configuration for UE (less common but possible)
        ovs_config = {}
        if properties.get('UE_OVS_Enabled') or properties.get('ovs_ovs_enabled'):
            ovs_config['OVS_ENABLED'] = 'true'
            ovs_config['OVS_BRIDGE_NAME'] = properties.get('UE_OVS_BridgeName', properties.get('ovs_ovs_bridge_name', 'br-ue'))
            ovs_config['OVS_FAIL_MODE'] = properties.get('UE_OVS_FailMode', properties.get('ovs_ovs_fail_mode', 'standalone'))
            ovs_config['OPENFLOW_PROTOCOLS'] = properties.get('UE_OVS_Protocols', properties.get('ovs_openflow_protocols', 'OpenFlow14'))
            ovs_config['OVS_DATAPATH'] = properties.get('UE_OVS_Datapath', properties.get('ovs_ovs_datapath', 'kernel'))
            ovs_config['UERANSIM_COMPONENT'] = 'ue'
        else:
            ovs_config['OVS_ENABLED'] = 'false'
        
        config['ovs_config'] = ovs_config
        
        return config
    
    @staticmethod
    def get_5g_core_docker_options(component_type):
        """Get Docker-specific options for 5G components based on fixed_topology-upf.py"""
        base_options = {
            'cap_add': ["net_admin"],
            'network_mode': "netflux5g", 
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
    def map_vgcore_config(properties):
        """Enhanced map VGCore properties to configuration parameters with Open5GS support"""
        config = {}
        
        # Docker configuration
        config['docker_enabled'] = properties.get('VGCore_DockerEnabled', 
                                                 properties.get('docker_docker_enabled', True))
        config['docker_image'] = properties.get('VGCore_DockerImage', 
                                               properties.get('docker_docker_image', 'adaptive/open5gs:1.0'))
        config['docker_network'] = properties.get('VGCore_DockerNetwork', 
                                                 properties.get('docker_docker_network', 'netflux5g'))
        config['database_uri'] = properties.get('VGCore_DatabaseURI', 
                                               properties.get('docker_database_uri', 'mongodb://mongo/open5gs'))
        
        # 5G Core network configuration
        config['network_interface'] = properties.get('VGCore_NetworkInterface', 
                                                    properties.get('5gcore_network_interface', 'eth0'))
        config['mcc'] = properties.get('VGCore_MCC', 
                                     properties.get('5gcore_mcc', '999'))
        config['mnc'] = properties.get('VGCore_MNC', 
                                     properties.get('5gcore_mnc', '70'))
        config['tac'] = properties.get('VGCore_TAC', 
                                     properties.get('5gcore_tac', '1'))
        config['sst'] = properties.get('VGCore_SST', 
                                     properties.get('5gcore_sst', '1'))
        config['sd'] = properties.get('VGCore_SD', 
                                    properties.get('5gcore_sd', '0xffffff'))
        config['enable_nat'] = properties.get('VGCore_EnableNAT', 
                                            properties.get('5gcore_enable_nat', True))
        
        # OVS/OpenFlow configuration
        config['ovs_enabled'] = properties.get('VGCore_OVSEnabled', 
                                              properties.get('ovs_ovs_enabled', False))
        config['ovs_controller'] = properties.get('VGCore_OVSController', 
                                                 properties.get('ovs_ovs_controller', ''))
        config['ovs_bridge_name'] = properties.get('VGCore_OVSBridgeName', 
                                                  properties.get('ovs_ovs_bridge_name', 'br-open5gs'))
        config['ovs_fail_mode'] = properties.get('VGCore_OVSFailMode', 
                                                properties.get('ovs_ovs_fail_mode', 'standalone'))
        config['openflow_protocols'] = properties.get('VGCore_OpenFlowProtocols', 
                                                     properties.get('ovs_openflow_protocols', 'OpenFlow14'))
        config['ovs_datapath'] = properties.get('VGCore_OVSDatapath', 
                                               properties.get('ovs_ovs_datapath', 'kernel'))
        config['controller_port'] = properties.get('VGCore_ControllerPort', 
                                                  properties.get('ovs_controller_port', '6633'))
        config['bridge_priority'] = properties.get('VGCore_BridgePriority', 
                                                  properties.get('ovs_bridge_priority', '32768'))
        config['stp_enabled'] = properties.get('VGCore_STPEnabled', 
                                              properties.get('ovs_stp_enabled', False))
        
        # Component configurations (from table data)
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        for comp_type in component_types:
            config_key = f"{comp_type.lower()}_configs"
            config[config_key] = properties.get(f"{comp_type}_configs", [])
        
        return config
    
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
            "VGcore": ConfigurationMapper.map_vgcore_config,
        }
        
        mapper = config_map.get(node_type, lambda p: [])
        return mapper(properties)