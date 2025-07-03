# Enhanced gNB Configuration Guide

## Overview

The enhanced gNB component in NetFlux5G now supports full Access Point functionality, enabling it to act as both a 5G base station and a WiFi Access Point in mininet-wifi environments. This integration provides comprehensive network slicing and SDN capabilities.

## Configuration Tabs

### 1. 5G Configuration
Configure the core 5G parameters for the gNB:

- **AMF Hostname**: The hostname/IP of the Access and Mobility Function (default: `amf`)
- **gNB Hostname**: The hostname for this gNB instance (default: `mn.gnb`)
- **TAC**: Tracking Area Code for the 5G cell (default: `1`)
- **MCC**: Mobile Country Code (default: `999`)
- **MNC**: Mobile Network Code (default: `70`)
- **SST**: Slice/Service Type (default: `1`)
- **SD**: Slice Differentiator (default: `0xffffff`)
- **TX Power**: Transmission power in dBm (range: 1-50, default: 30)
- **Range**: Coverage range in meters (range: 50-1000, default: 300)

### 2. Access Point Configuration
Enable and configure the WiFi AP functionality:

- **Enable Access Point Functionality**: Check to enable AP mode
- **SSID**: WiFi network name (default: `gnb-hotspot`)
- **Channel**: WiFi channel 1-11 (default: 6)
- **Mode**: WiFi mode (g/a/n/ac, default: g)
- **Password**: WiFi password (leave empty for open network)
- **Bridge Name**: OVS bridge name (default: `br-gnb`)

### 3. OpenFlow/OVS Configuration
Configure the OpenFlow switch behavior:

- **Controller**: OpenFlow controller address (e.g., `tcp:127.0.0.1:6633`)
- **Fail Mode**: Behavior when controller disconnects (`standalone` or `secure`)
- **OpenFlow Protocols**: OpenFlow version (`OpenFlow14`, `OpenFlow13`, `OpenFlow10`)
- **Datapath**: OVS datapath type (`kernel` or `user`)

### 4. Network Interfaces
Configure the network interfaces used by the gNB:

- **N2 Interface**: Interface for control plane communication (default: `eth0`)
- **N3 Interface**: Interface for user plane communication (default: `eth0`)
- **Radio Interface**: Interface for radio communication (default: `eth0`)

## Environment Variables

When the enhanced gNB is deployed, the following environment variables are automatically configured:

### 5G Core Variables
```bash
AMF_IP=10.0.0.3
GNB_HOSTNAME=mn.gnb
N2_IFACE=gnb1-wlan0
N3_IFACE=gnb1-wlan0
RADIO_IFACE=gnb1-wlan0
MCC=999
MNC=70
SST=1
SD=0xffffff
TAC=1
```

### Access Point Variables
```bash
AP_ENABLED=true
AP_SSID=gnb-hotspot
AP_CHANNEL=6
AP_MODE=g
AP_PASSWD=
AP_BRIDGE_NAME=br-gnb
OVS_CONTROLLER=tcp:127.0.0.1:6633
AP_FAILMODE=standalone
OPENFLOW_PROTOCOLS=OpenFlow14
```

## Docker Container Configuration

The enhanced gNB uses the `adaptive/ueransim:latest` Docker image with the following capabilities:

```python
gnb1 = net.addStation('gnb1',
                      cap_add=["net_admin"],
                      privileged=True,
                      volumes=["/sys:/sys", "/lib/modules:/lib/modules", "/sys/kernel/debug:/sys/kernel/debug"],
                      dimage="adaptive/ueransim:latest",
                      environment={
                          # 5G and AP configuration variables
                      })
```

## Host Requirements

For full AP functionality, ensure the host system has:

1. **mac80211_hwsim module loaded**:
   ```bash
   sudo modprobe mac80211_hwsim radios=10
   ```

2. **Required packages installed**:
   ```bash
   sudo apt-get install wireless-tools iw hostapd openvswitch-switch
   ```

3. **Proper Docker run configuration** (for manual testing):
   ```bash
   docker run --privileged --pid='host' --net='host' \
     -v /sys:/sys -v /lib/modules:/lib/modules \
     -v /sys/kernel/debug:/sys/kernel/debug \
     -e AP_ENABLED=true -e AP_SSID="Test-gNB" \
     adaptive/ueransim:latest gnb
   ```

## Usage Examples

### Example 1: Basic gNB with AP
Configure a gNB that acts as both 5G base station and WiFi AP:
- Enable AP functionality
- Set SSID to "5G-Cell-1"
- Use channel 6
- Open network (no password)

### Example 2: SDN-Controlled gNB
Configure a gNB with OpenFlow controller integration:
- Enable AP functionality
- Set controller to "tcp:192.168.1.100:6633"
- Use OpenFlow 1.4
- Fail mode: secure

### Example 3: Multi-Cell Network
Deploy multiple gNBs with different configurations:
- gNB1: Channel 1, SSID "Cell-North"
- gNB2: Channel 6, SSID "Cell-South"  
- gNB3: Channel 11, SSID "Cell-Central"

## Integration with UEs

UEs can connect to the enhanced gNB in two ways:

1. **5G Radio Connection**: Through the 5G control/user plane interfaces
2. **WiFi Association**: By connecting to the gNB's WiFi AP

This dual connectivity enables advanced scenarios like:
- Network slicing with different access methods
- Load balancing between 5G and WiFi
- Handover testing between different access technologies

## Troubleshooting

### Common Issues

1. **AP not starting**: Check if mac80211_hwsim is loaded on host
2. **OVS bridge errors**: Verify OpenVSwitch is installed and running
3. **Container permissions**: Ensure privileged mode and proper volume mounts
4. **Controller connection**: Check network connectivity to OpenFlow controller

### Debug Commands

```bash
# Check AP status
gnb1 pgrep -f hostapd

# Check OVS configuration
gnb1 ovs-vsctl show

# Check wireless interfaces
gnb1 iw dev

# Check 5G configuration
gnb1 cat /tmp/gnb.yaml

# Check environment variables
gnb1 env | grep -E "(AP_|GNB_|MCC|MNC)"
```

## Advanced Features

The enhanced gNB supports additional advanced features:

- **QoS Configuration**: Traffic control and prioritization
- **Network Slicing**: Multiple virtual networks over single infrastructure
- **SDN Integration**: Full OpenFlow switch capabilities
- **Mobility Management**: Handover support between cells
- **Security**: WPA2/WPA3 encryption options
- **Monitoring**: RSSI reporting and performance metrics

For more detailed configuration options, see the [HOST_SETUP_GUIDE.md](HOST_SETUP_GUIDE.md) and [README_AP_FUNCTIONALITY.md](README_AP_FUNCTIONALITY.md).
