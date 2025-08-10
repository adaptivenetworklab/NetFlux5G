"""
Configuration mapping for different component types to Mininet parameters
Enhanced version with power-based range calculation following Mininet-WiFi methodology
"""

from utils.power_range_calculator import PowerRangeCalculator
from utils.debug import debug_print, error_print, warning_print

class ConfigurationMapper:
    """Maps UI component configurations to Mininet script parameters"""
    
    @staticmethod
    def map_host_config(properties):
        """Map host component properties to Mininet host parameters"""
        opts = []
        
        # IP Address - standardized field mapping
        ip_fields = ["Host_IPAddress", "STA_IPAddress", "UE_IPAddress"]
        for field in ip_fields:
            if properties.get(field):
                ip = properties[field].strip()
                if ip and ip != "10.0.0.1": 
                    opts.append(f"ip='{ip}'")
                    break
        
        # Default Route - standardized field mapping
        route_fields = ["Host_DefaultRoute", "STA_DefaultRoute"]
        for field in route_fields:
            if properties.get(field):
                route = properties[field].strip()
                if route:
                    opts.append(f"defaultRoute='via {route}'")
                    break
        
        # CPU Configuration - standardized field mapping
        cpu_fields = ["Host_AmountCPU", "STA_AmountCPU"]
        for field in cpu_fields:
            if properties.get(field):
                cpu = str(properties[field]).strip()
                if cpu:
                    try:
                        cpu_val = float(cpu)
                        if cpu_val > 0 and cpu_val != 1.0:  # Only add if different from default
                            opts.append(f"cpu={cpu_val}")
                    except (ValueError, TypeError):
                        pass
                    break
        
        # Memory Configuration - standardized field mapping
        memory_fields = ["Host_Memory", "STA_Memory"]
        for field in memory_fields:
            if properties.get(field):
                memory = str(properties[field]).strip()
                if memory:
                    try:
                        mem_val = int(memory)
                        if mem_val > 0:
                            opts.append(f"mem={mem_val}")
                    except (ValueError, TypeError):
                        pass
                    break
        
        return opts
    
    @staticmethod
    def map_gnb_config(properties):
        """Map gNB properties to configuration parameters with enhanced UERANSIM Docker support"""
        config = {}
        
        # Enhanced 5G configuration using standardized field names
        config['amf_hostname'] = properties.get('GNB_AMFHostName', 'amf')
        config['amf_ip'] = properties.get('GNB_AMF_IP', '')
        config['gnb_hostname'] = properties.get('GNB_GNBHostName', 'gnb')
        config['mcc'] = properties.get('GNB_MCC', '999')
        config['mnc'] = properties.get('GNB_MNC', '70')
        config['sst'] = properties.get('GNB_SST', '1')
        config['sd'] = properties.get('GNB_SD', '0xffffff')
        config['tac'] = properties.get('GNB_TAC', '1')
        
        # Network interfaces configuration
        config['n2_iface'] = properties.get('GNB_N2_Interface', 'eth0')
        config['n3_iface'] = properties.get('GNB_N3_Interface', 'eth0')
        config['radio_iface'] = properties.get('GNB_Radio_Interface', 'eth0')
        
        # UERANSIM component type
        config['ueransim_component'] = 'gnb'
        
        # Wireless configuration for mininet-wifi - use power-based approach
        power_val = properties.get('GNB_Power')
        if power_val:
            try:
                power_val = float(power_val)
                if power_val > 0:
                    config['txpower'] = power_val
                    debug_print(f"DEBUG: gNB configured with txpower={power_val}dBm")
            except (ValueError, TypeError):
                pass
        
        # Set default power if not specified
        if 'txpower' not in config:
            config['txpower'] = PowerRangeCalculator._get_default_power("GNB")
            debug_print(f"DEBUG: gNB using default txpower={config['txpower']}dBm")
        
        # Remove explicit range configuration - let mininet-wifi calculate from power
        # This ensures consistency with mininet-wifi's propagation models
        
        # OVS/OpenFlow configuration
        ovs_config = {
            'OVS_ENABLED': 'true' if properties.get('GNB_OVS_Enabled') else 'false',
            'OVS_BRIDGE_NAME': properties.get('GNB_OVS_BridgeName', 'br-gnb'),
            'OVS_FAIL_MODE': properties.get('GNB_OVS_FailMode', 'secure'),
            'OPENFLOW_PROTOCOLS': properties.get('GNB_OVS_Protocols', 'OpenFlow14'),
            'OVS_DATAPATH': properties.get('GNB_OVS_Datapath', 'kernel'),
            'BRIDGE_PRIORITY': str(properties.get('GNB_Bridge_Priority', '32768')),
            'STP_ENABLED': 'true' if properties.get('GNB_STP_Enabled') else 'false'
        }
        
        if properties.get('GNB_OVS_Controller'):
            ovs_config['OVS_CONTROLLER'] = properties['GNB_OVS_Controller']
            
        config['ovs_config'] = ovs_config
        
        # AP configuration - use power-based approach
        ap_power = properties.get('GNB_Power', config.get('txpower', 20))
        ap_config = {
            'AP_ENABLED': 'true' if properties.get('GNB_AP_Enabled') else 'false',
            'AP_SSID': properties.get('GNB_AP_SSID', 'gnb-hotspot'),
            'AP_CHANNEL': str(properties.get('GNB_AP_Channel', '6')),
            'AP_MODE': properties.get('GNB_AP_Mode', 'g'),
            'AP_PASSWD': properties.get('GNB_AP_Password', ''),
            'AP_FAILMODE': ovs_config.get('OVS_FAIL_MODE', 'secure'),
            'OPENFLOW_PROTOCOLS': ovs_config.get('OPENFLOW_PROTOCOLS', 'OpenFlow14'),
            'AP_TXPOWER': str(ap_power)
        }
        
        # Remove explicit range - let mininet-wifi calculate from power
        debug_print(f"DEBUG: gNB AP configured with txpower={ap_power}dBm")
        
        if ovs_config.get('OVS_CONTROLLER'):
            ap_config['OVS_CONTROLLER'] = ovs_config['OVS_CONTROLLER']
            
        config['ap_config'] = ap_config
        
        return config
    
    @staticmethod
    def map_ue_config(properties):
        """Enhanced map UE properties to configuration parameters with UERANSIM Docker support"""
        config = {}
        
        # Core 5G/UE Configuration
        config['gnb_hostname'] = properties.get('UE_GNBHostName', 'gnb')
        config['apn'] = properties.get('UE_APN', 'internet')
        config['msisdn'] = properties.get('UE_MSISDN', '0000000001')
        config['mcc'] = properties.get('UE_MCC', '999')
        config['mnc'] = properties.get('UE_MNC', '70')
        config['sst'] = properties.get('UE_SST', '1')
        config['sd'] = properties.get('UE_SD', '0xffffff')
        
        # Authentication parameters
        config['key'] = properties.get('UE_KEY', '465B5CE8B199B49FAA5F0A2EE238A6BC')
        config['op_type'] = properties.get('UE_OPType', 'OPC')
        config['op'] = properties.get('UE_OP', 'E8ED289DEBA952E4283B54E88E6183CA')
        
        # Device identifiers
        config['imei'] = properties.get('UE_IMEI', '356938035643803')
        config['imeisv'] = properties.get('UE_IMEISV', '4370816125816151')
        
        # Network configuration
        gnb_ip = properties.get('UE_GNB_IP')
        if gnb_ip and gnb_ip.strip():
            config['gnb_ip'] = gnb_ip.strip()
        
        config['tunnel_iface'] = properties.get('UE_TunnelInterface', 'uesimtun0')
        config['radio_iface'] = properties.get('UE_RadioInterface', 'eth0')
        config['session_type'] = properties.get('UE_SessionType', 'IPv4')
        
        # PDU sessions
        pdu_sessions = properties.get('UE_PDUSessions', 1)
        if pdu_sessions:
            try:
                config['pdu_sessions'] = int(pdu_sessions)
            except (ValueError, TypeError):
                config['pdu_sessions'] = 1
        else:
            config['pdu_sessions'] = 1
        
        # UERANSIM component type
        config['ueransim_component'] = 'ue'
        
        # Wireless configuration for mininet-wifi - use power-based approach
        power_val = properties.get('UE_Power')
        if power_val:
            try:
                power_val = float(power_val)
                if power_val > 0:
                    config['txpower'] = power_val
                    debug_print(f"DEBUG: UE configured with txpower={power_val}dBm")
            except (ValueError, TypeError):
                pass
        
        # Set default power if not specified
        if 'txpower' not in config:
            config['txpower'] = PowerRangeCalculator._get_default_power("UE")
            debug_print(f"DEBUG: UE using default txpower={config['txpower']}dBm")
        
        # Remove explicit range configuration - let mininet-wifi calculate from power
        # This ensures consistency with mininet-wifi's propagation models
        
        # Association mode
        config['association'] = properties.get('UE_AssociationMode', 'auto')
        
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
                'dimage': 'adaptive/open5gs:latest'
            },
            'AMF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'SMF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'NRF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'SCP': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'AUSF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'BSF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'NSSF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'PCF': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'UDM': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'UDR': {
                'dimage': 'adaptive/open5gs:latest'
            },
            'GNB': {
                'dimage': 'adaptive/ueransim:latest'
            },
            'UE': {
                'devices': ["/dev/net/tun"],
                'dimage': 'adaptive/ueransim:latest'
            }
        }
        
        options = base_options.copy()
        if component_type in component_configs:
            options.update(component_configs[component_type])
            
        return options
    
    @staticmethod
    def map_ap_config(properties):
        """Map Access Point properties to Mininet AP parameters with power-based range calculation"""
        opts = []
        
        # SSID - standardized field mapping
        ssid = properties.get('AP_SSID', '')
        if ssid and ssid.strip() and ssid != "my-ssid":
            opts.append(f"ssid='{ssid.strip()}'")
        
        # Channel - standardized field mapping
        channel = properties.get('AP_Channel')
        if channel:
            try:
                ch_val = int(channel)
                if ch_val > 0 and ch_val != 1:  # Only add if different from default
                    opts.append(f"channel={ch_val}")
            except (ValueError, TypeError):
                pass
        
        # Mode - standardized field mapping
        mode = properties.get('AP_Mode', '')
        if mode and mode.strip() and mode != "g":
            opts.append(f"mode='{mode.strip()}'")
        
        # Power configuration for radio propagation - PRIMARY parameter
        power = properties.get('AP_Power')
        if power:
            try:
                power_val = float(power)
                if power_val > 0:
                    opts.append(f"txpower={power_val}")
                    # Note: Range will be calculated automatically by mininet-wifi based on txpower
                    # This ensures consistency with mininet-wifi's behavior
                    debug_print(f"DEBUG: AP configured with txpower={power_val}dBm")
            except (ValueError, TypeError):
                pass
        else:
            # Use default power if not specified
            default_power = PowerRangeCalculator._get_default_power("AP")
            opts.append(f"txpower={default_power}")
            debug_print(f"DEBUG: AP using default txpower={default_power}dBm")
        
        # Remove explicit range configuration to let mininet-wifi calculate it from power
        # This ensures the GUI visualization matches the actual mininet-wifi behavior
        
        return opts
    
    @staticmethod
    def map_controller_config(properties):
        """Map Controller properties to Mininet controller parameters"""
        opts = []
        
        # IP Address - standardized field mapping
        ip = properties.get('Controller_IPAddress', '')
        if ip and ip.strip() and ip != "127.0.0.1":
            opts.append(f"ip='{ip.strip()}'")
        
        # Port - standardized field mapping
        port = properties.get('Controller_Port')
        if port:
            try:
                port_val = int(port)
                if port_val > 0 and port_val != 6633:  # Only add if different from default
                    opts.append(f"port={port_val}")
            except (ValueError, TypeError):
                pass
        
        # Controller Type - standardized field mapping
        controller_type = properties.get('Controller_Type', 'OVS Controller')
        if controller_type == 'Remote Controller':
            opts.append("controller_class='RemoteController'")
        else:  # Default to OVS Controller
            opts.append("controller_class='OVSController'")
        
        return opts
    
    @staticmethod
    def map_sta_config(properties):
        """Map Station properties to Mininet station parameters"""
        opts = []
        
        # IP Address - standardized field mapping
        ip = properties.get('STA_IPAddress', '')
        if ip and ip.strip() and ip != "10.0.0.1":
            opts.append(f"ip='{ip.strip()}'")
        
        # Default Route - standardized field mapping
        route = properties.get('STA_DefaultRoute', '')
        if route and route.strip():
            opts.append(f"defaultRoute='via {route.strip()}'")
        
        # CPU Configuration - standardized field mapping
        cpu = properties.get('STA_AmountCPU')
        if cpu:
            try:
                cpu_val = float(cpu)
                if cpu_val > 0 and cpu_val != 1.0:
                    opts.append(f"cpu={cpu_val}")
            except (ValueError, TypeError):
                pass
        
        # Memory Configuration - standardized field mapping
        memory = properties.get('STA_Memory')
        if memory:
            try:
                mem_val = int(memory)
                if mem_val > 0:
                    opts.append(f"mem={mem_val}")
            except (ValueError, TypeError):
                pass
        
        # Power configuration for radio propagation - PRIMARY parameter
        power = properties.get('STA_Power')
        if power:
            try:
                power_val = float(power)
                if power_val > 0:
                    opts.append(f"txpower={power_val}")
                    debug_print(f"DEBUG: STA configured with txpower={power_val}dBm")
            except (ValueError, TypeError):
                pass
        else:
            # Use default power if not specified
            default_power = PowerRangeCalculator._get_default_power("STA")
            opts.append(f"txpower={default_power}")
            debug_print(f"DEBUG: STA using default txpower={default_power}dBm")
        
        # Remove explicit range configuration to let mininet-wifi calculate it from power
        # This ensures consistency with mininet-wifi's propagation models
        
        return opts
    
    @staticmethod
    def map_vgcore_config(properties):
        """Enhanced map VGCore properties to configuration parameters with Open5GS support"""
        config = {}
        
        # Docker configuration - standardized field mapping
        config['docker_enabled'] = properties.get('VGCore_DockerEnabled', True)
        config['docker_image'] = properties.get('VGCore_DockerImage', 'adaptive/open5gs:latest')
        config['docker_network'] = properties.get('VGCore_DockerNetwork', 'netflux5g')
        config['database_uri'] = properties.get('VGCore_DatabaseURI', 'mongodb://netflux5g-mongodb/open5gs')
        
        # 5G Core network configuration - standardized field mapping
        config['network_interface'] = properties.get('VGCore_NetworkInterface', 'eth0')
        config['mcc'] = properties.get('VGCore_MCC', '999')
        config['mnc'] = properties.get('VGCore_MNC', '70')
        config['tac'] = properties.get('VGCore_TAC', '1')
        config['sst'] = properties.get('VGCore_SST', '1')
        config['sd'] = properties.get('VGCore_SD', '0xffffff')
        config['enable_nat'] = properties.get('VGCore_EnableNAT', True)
        
        # OVS/OpenFlow configuration - standardized field mapping
        config['ovs_enabled'] = properties.get('VGCore_OVSEnabled', False)
        config['ovs_controller'] = properties.get('VGCore_OVSController', '')
        config['ovs_bridge_name'] = properties.get('VGCore_OVSBridgeName', 'br-open5gs')
        config['ovs_fail_mode'] = properties.get('VGCore_OVSFailMode', 'standalone')
        config['openflow_protocols'] = properties.get('VGCore_OpenFlowProtocols', 'OpenFlow14')
        config['ovs_datapath'] = properties.get('VGCore_OVSDatapath', 'kernel')
        config['controller_port'] = properties.get('VGCore_ControllerPort', '6633')
        config['bridge_priority'] = properties.get('VGCore_BridgePriority', '32768')
        config['stp_enabled'] = properties.get('VGCore_STPEnabled', False)
        
        # Component configurations (from table data)
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'UDM', 'UDR']
        for comp_type in component_types:
            config_key = f"{comp_type}_configs"
            if config_key in properties:
                config[f"{comp_type.lower()}_configs"] = properties[config_key]
        
        return config
    
    @staticmethod
    def map_link_config(properties):
        """Map link properties to Mininet link parameters with validation"""
        params = []
        
        # Bandwidth configuration
        bandwidth = properties.get('bandwidth', '')
        if bandwidth and str(bandwidth).strip() and str(bandwidth).strip() != '0':
            try:
                bw_value = int(bandwidth)
                if bw_value > 0:
                    params.append(f"bw={bw_value}")
            except (ValueError, TypeError):
                pass
        
        # Delay configuration
        delay = properties.get('delay', '')
        if delay and str(delay).strip():
            # Ensure delay has proper format (e.g., "10ms", "1s")
            delay_str = str(delay).strip()
            if delay_str and not delay_str.endswith(('ms', 's', 'us')):
                delay_str += 'ms'  # Default to milliseconds
            params.append(f"delay='{delay_str}'")
        
        # Loss configuration
        loss = properties.get('loss', '')
        if loss and str(loss).strip() and str(loss).strip() not in ['0', '0.0']:
            try:
                loss_value = float(loss)
                if loss_value > 0:
                    params.append(f"loss={loss_value}")
            except (ValueError, TypeError):
                pass
        
        return params
    
    @staticmethod
    def get_link_ip_config(properties):
        """Get IP configuration for link endpoints"""
        ip_config = {}
        
        if properties.get('enable_ip', False):
            source_ip = properties.get('source_ip', '').strip()
            dest_ip = properties.get('dest_ip', '').strip()
            
            if source_ip:
                ip_config['source_ip'] = source_ip
            if dest_ip:
                ip_config['dest_ip'] = dest_ip
        
        return ip_config
    
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