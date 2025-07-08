# UERANSIM with OpenVSwitch and OpenFlow Support

This UERANSIM Docker implementation provides comprehensive OpenVSwitch (OVS) and OpenFlow support for integration with SDN controllers and mininet-wifi environments, similar to the Open5GS implementation.

## Features

### OpenFlow/SDN Integration
- **OpenFlow Support**: Full OpenFlow 1.0, 1.3, and 1.4 support
- **SDN Controller Integration**: Connect to external SDN controllers (OpenDaylight, ONOS, Floodlight, etc.)
- **Dynamic Flow Management**: Automatic flow setup for 5G traffic patterns
- **Bridge Management**: Automatic OVS bridge creation and configuration

### Enhanced Networking
- **Multiple Interface Support**: Support for N2, N3, and Radio interfaces
- **Wireless AP Integration**: Enhanced AP functionality with OVS integration
- **Bridge Connectivity**: Patch ports for connecting multiple bridges
- **Traffic Control**: QoS and traffic shaping capabilities

### Container Orchestration
- **Supervisor Support**: Multi-process management for OVS, UERANSIM, and AP services
- **Health Monitoring**: Service restart and monitoring capabilities
- **Graceful Shutdown**: Proper cleanup of OVS resources on container stop
- **mininet-wifi Compatibility**: Behaves like standard mininet-wifi Access Points
- **Network Slicing**: Support for different network slices through AP configuration
- **QoS Management**: Traffic control and quality of service features

### Supported Access Point Features
- **SSID Configuration**: Customizable network name
- **Security Options**: Open, WPA2, WPA3 support  
- **Channel Selection**: Configurable wireless channels
- **Bridge Networking**: OVS bridge integration
- **Hostapd Integration**: Industry-standard AP daemon
- **Controller Integration**: OpenFlow controller connectivity

## Installation and Build

### Prerequisites
```bash
# Required packages on host system
sudo apt-get update
sudo apt-get install -y \
    wireless-tools \
    hostapd \
    openvswitch-switch
```

### Building the Enhanced Image
```bash
# Navigate to the UERANSIM directory
cd /path/to/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/UERANSIM/

# Build the enhanced UERANSIM image
docker build -t adaptive/ueransim:latest .
```

## Environment Variables

### Core gNB Configuration
- `AMF_IP`: AMF IP address
- `GNB_HOSTNAME`: gNB hostname 
- `N2_IFACE`: N2 interface name
- `N3_IFACE`: N3 interface name
- `RADIO_IFACE`: Radio interface name
- `MCC`, `MNC`, `SST`, `SD`, `TAC`: 5G network parameters

### Access Point Configuration
- `AP_ENABLED`: Enable/disable AP functionality (true/false)
- `AP_SSID`: WiFi network name (default: "gnb-hotspot")
- `AP_CHANNEL`: WiFi channel (1-13, default: 6)
- `AP_MODE`: WiFi mode (g, n, ac, ax, default: g)
- `AP_PASSWD`: WiFi password (empty for open network)
- `AP_BRIDGE_NAME`: OVS bridge name (default: "br-gnb")
- `AP_FAILMODE`: OVS fail mode (standalone/secure, default: standalone)
- `OPENFLOW_PROTOCOLS`: OpenFlow versions (default: OpenFlow14)
- `OVS_CONTROLLER`: Controller address (e.g., "tcp:192.168.1.1:6653")

### Optional Configuration
- `AP_BRIDGE_IP`: Bridge IP address
- `AP_ENABLE_FORWARDING`: Enable IP forwarding (true/false)
- `AP_ENABLE_QOS`: Enable QoS features (true/false)
- `HOSTAPD_EXTRA_CONF`: Additional hostapd configuration

## Usage Examples

### Basic gNB with AP Functionality

```python
# In mininet-wifi topology
gnb1 = net.addStation('gnb1', 
                      cls=DockerSta, 
                      dimage="adaptive/ueransim:latest",
                      environment={
                          "AMF_IP": "10.0.0.3",
                          "AP_ENABLED": "true",
                          "AP_SSID": "5G-Hotspot",
                          "AP_CHANNEL": "6",
                          "AP_PASSWD": "secure123"
                      })
```

### Advanced Configuration with OpenFlow Controller

```python
gnb_ap = net.addStation('gnb_ap', 
                        cls=DockerSta, 
                        dimage="adaptive/ueransim:latest",
                        environment={
                            # 5G Configuration
                            "AMF_IP": "10.0.0.3",
                            "GNB_HOSTNAME": "mn.gnb1",
                            "MCC": "999",
                            "MNC": "70",
                            "TAC": "1",
                            
                            # AP Configuration  
                            "AP_ENABLED": "true",
                            "AP_SSID": "Enterprise-5G",
                            "AP_CHANNEL": "11",
                            "AP_MODE": "n",
                            "AP_PASSWD": "enterprise_pwd",
                            "AP_BRIDGE_NAME": "br-enterprise",
                            "AP_FAILMODE": "secure",
                            "OPENFLOW_PROTOCOLS": "OpenFlow14",
                            "OVS_CONTROLLER": "tcp:192.168.1.100:6653"
                        })
```

### Network Slicing Example

```python
# Slice 1: Enterprise users
gnb_enterprise = net.addStation('gnb_enterprise',
                                cls=DockerSta,
                                dimage="adaptive/ueransim:latest",
                                environment={
                                    "AP_ENABLED": "true",
                                    "AP_SSID": "Enterprise-Slice",
                                    "AP_CHANNEL": "6",
                                    "SST": "1",
                                    "SD": "0x000001"
                                })

# Slice 2: IoT devices  
gnb_iot = net.addStation('gnb_iot',
                         cls=DockerSta,
                         dimage="adaptive/ueransim:latest",
                         environment={
                             "AP_ENABLED": "true", 
                             "AP_SSID": "IoT-Slice",
                             "AP_CHANNEL": "11",
                             "SST": "2",
                             "SD": "0x000002"
                         })
```

## Running the Container

### Standalone Mode
```bash
docker run -it --privileged --cap-add=NET_ADMIN \
    -e AP_ENABLED=true \
    -e AP_SSID="Test-5G-AP" \
    -e AP_CHANNEL=6 \
    -e AP_PASSWD="testpass" \
    adaptive/ueransim:latest gnb
```

### In mininet-wifi
```bash
# Start the example topology
python3 gnb_ap_topology_example.py
```

## Monitoring and Management

### Check AP Status
```bash
# Inside container
hostapd_cli -i wlan0 status

# Check OVS configuration
ovs-vsctl show

# Monitor connected clients
hostapd_cli -i wlan0 list_sta
```

### OpenFlow Flow Management
```bash
# View flows on gNB bridge
ovs-ofctl dump-flows br-gnb

# Add custom flow
ovs-ofctl add-flow br-gnb "priority=100,in_port=1,actions=output:2"
```

### Network Debugging
```bash
# Check wireless interface
iw dev wlan0 info

# Monitor traffic
tcpdump -i br-gnb

# Check bridge connectivity
ping -I br-gnb 192.168.1.1
```

## Integration with SDN Controllers

### OpenDaylight Integration
```python
environment={
    "OVS_CONTROLLER": "tcp:192.168.1.100:6633",
    "OPENFLOW_PROTOCOLS": "OpenFlow13",
    "AP_FAILMODE": "secure"
}
```

### ONOS Integration  
```python
environment={
    "OVS_CONTROLLER": "tcp:192.168.1.100:6653",
    "OPENFLOW_PROTOCOLS": "OpenFlow14"
}
```

### Custom Controller
```python
environment={
    "OVS_CONTROLLER": "tcp:controller.example.com:6653"
}
```

## Troubleshooting

### Common Issues

#### AP Not Starting
```bash
# Check hostapd logs
docker logs <container_id>

# Verify wireless interface
docker exec <container_id> iw list

# Check OVS status
docker exec <container_id> ovs-vsctl show
```

#### No Client Connectivity
```bash
# Verify bridge configuration
docker exec <container_id> ip link show br-gnb

# Check hostapd status
docker exec <container_id> hostapd_cli status

# Verify routing
docker exec <container_id> ip route show
```

#### OpenFlow Controller Issues
```bash
# Check controller connection
docker exec <container_id> ovs-vsctl get-controller br-gnb

# Test connectivity
docker exec <container_id> telnet <controller_ip> 6653

# Check OVS logs
docker exec <container_id> tail -f /var/log/openvswitch/ovs-vswitchd.log
```

### Debugging Commands
```bash
# Enable debug logging
docker run -e HOSTAPD_EXTRA_CONF="logger_syslog=0\nlogger_stdout=2" ...

# Monitor wireless activity
docker exec <container_id> iw event

# Check bridge MAC table
docker exec <container_id> ovs-appctl fdb/show br-gnb
```

## Performance Optimization

### Resource Allocation
```bash
# Allocate more CPU/memory
docker run --cpus="2" --memory="2g" ...
```

### Network Performance
```python
# QoS configuration
environment={
    "AP_ENABLE_QOS": "true",
    "HOSTAPD_EXTRA_CONF": "wmm_enabled=1\nap_max_inactivity=300"
}
```

## Security Considerations

### WPA3 Security
```python
environment={
    "AP_MODE": "ax",
    "AP_PASSWD": "secure_password",
    "HOSTAPD_EXTRA_CONF": "wpa=3\nwpa_key_mgmt=SAE"
}
```

### Enterprise Security
```python
environment={
    "HOSTAPD_EXTRA_CONF": "ieee8021x=1\nauth_server_addr=192.168.1.10\nauth_server_port=1812\nauth_server_shared_secret=secret"
}
```

## Limitations

1. **Hardware Dependencies**: Some wireless features require specific hardware
2. **Kernel Modules**: mac80211_hwsim may not be available in all environments  
3. **Privileged Mode**: Requires privileged container mode for full functionality
4. **Network Namespace**: May have limitations in certain network configurations

## Contributing

To extend this functionality:

1. **Modify ap-setup.sh**: Add new AP features
2. **Update Dockerfile**: Install additional packages
3. **Extend entrypoint.sh**: Add new startup logic
4. **Test thoroughly**: Ensure compatibility with existing features

## License

This enhanced UERANSIM image maintains the same license as the original UERANSIM project.
