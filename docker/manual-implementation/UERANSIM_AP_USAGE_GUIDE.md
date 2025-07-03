# UERANSIM gNB as Access Point - Complete Implementation Guide

## 🎯 Overview

Your UERANSIM Docker image has been **fully enhanced** to enable gNB containers to act as mininet-wifi Access Points! The implementation includes all necessary packages, scripts, and configurations.

## ✅ What's Already Implemented

### 1. Enhanced Dockerfile
The Dockerfile includes all required packages:
- `hostapd` - Access Point daemon
- `wpasupplicant` - Wireless client support
- `openvswitch-switch` & `openvswitch-common` - OpenVSwitch support
- `bridge-utils` - Network bridge management
- Wireless tools (`iw`, `wireless-tools`, `ethtool`)
- Network utilities (`iproute2`, `net-tools`, etc.)

### 2. Environment Variables for AP Configuration
```bash
AP_ENABLED=true              # Enable AP functionality
AP_SSID=gnb-hotspot         # Access Point SSID
AP_CHANNEL=6                # Wireless channel
AP_MODE=g                   # Wireless mode (a/b/g/n/ac)
AP_PASSWD=""                # WiFi password (empty = open)
AP_BRIDGE_NAME=br-gnb       # OVS bridge name
OVS_CONTROLLER=""           # OpenFlow controller URL
AP_FAILMODE=standalone      # OVS failmode
OPENFLOW_PROTOCOLS=OpenFlow14  # OpenFlow version
```

### 3. Automated AP Setup Script
The `/usr/local/bin/ap-setup.sh` script handles:
- OVS bridge creation and configuration
- Wireless interface detection/creation
- Hostapd configuration generation
- OpenFlow controller integration
- Network bridge setup
- mininet-wifi compatibility

### 4. Enhanced Entrypoint
The `entrypoint.sh` manages both gNB and AP services simultaneously.

## 🚀 How to Use gNB Containers as Access Points

### Option 1: Replace Traditional APs in Your Topology

Instead of using:
```python
ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid', ...)
```

Use gNB containers with AP capability:
```python
gnb1_ap = net.addStation('gnb1', 
                         cap_add=["net_admin"], 
                         network_mode="open5gs-ueransim_default", 
                         privileged=True,
                         publish_all_ports=True, 
                         dcmd="/bin/bash",
                         cls=DockerSta, 
                         dimage="adaptive/ueransim:latest",  # Use enhanced image
                         position='705.0,335.0,0', 
                         range=300, 
                         txpower=30,
                         environment={
                             # gNB Configuration
                             "AMF_IP": "10.0.0.3", 
                             "GNB_HOSTNAME": "mn.gnb1", 
                             "N2_IFACE":"gnb1-wlan0", 
                             "N3_IFACE":"gnb1-wlan0", 
                             "RADIO_IFACE":"gnb1-wlan0",
                             "MCC": "999", "MNC": "70", "SST": "1", 
                             "SD": "0xffffff", "TAC": "1",
                             
                             # AP Configuration (equivalent to ap1-ssid)
                             "AP_ENABLED": "true",
                             "AP_SSID": "ap1-ssid",
                             "AP_CHANNEL": "36",
                             "AP_MODE": "a",
                             "AP_PASSWD": "",  # Open network
                             "AP_BRIDGE_NAME": "br-gnb1",
                             "OVS_CONTROLLER": "tcp:127.0.0.1:6653",
                             "AP_FAILMODE": "standalone",
                             "OPENFLOW_PROTOCOLS": "OpenFlow14"
                         })
```

### Option 2: Build the Enhanced Image

If you haven't built the enhanced image yet:

```bash
cd /home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/UERANSIM/
docker build -t adaptive/ueransim:latest .
```

### Option 3: Update Your Current Topology

I've created an updated version of your topology that replaces `ap1` and `ap2` with gNB containers:

**File**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Mininet/updated_topology_gnb_ap.py`

Key changes:
- `ap1` → `gnb1_ap` (gNB with AP functionality)
- `ap2` → `gnb2_ap` (gNB with AP functionality)  
- `ap3` → Kept as traditional AP for AMF connection
- UEs connect to gNB APs wirelessly
- Full OpenFlow/OVS support maintained

## 🔧 Configuration Options

### Basic AP Configuration
```bash
# Enable AP mode
AP_ENABLED=true
AP_SSID=my-5g-hotspot
AP_CHANNEL=6
AP_MODE=n
```

### Secured AP (WPA2)
```bash
AP_ENABLED=true
AP_SSID=secure-5g-network
AP_PASSWD=my_secure_password
AP_CHANNEL=11
```

### OpenFlow Integration
```bash
AP_ENABLED=true
AP_BRIDGE_NAME=br-gnb
OVS_CONTROLLER=tcp:192.168.1.100:6653
AP_FAILMODE=secure
OPENFLOW_PROTOCOLS=OpenFlow13,OpenFlow14
```

### Advanced Configuration
```bash
# Additional environment variables
AP_BRIDGE_IP=192.168.100.1/24    # Bridge IP address
AP_ENABLE_FORWARDING=true        # Enable IP forwarding
AP_ENABLE_QOS=true              # Enable QoS/traffic control
HOSTAPD_EXTRA_CONF="beacon_int=100\nmax_num_sta=50"  # Extra hostapd config
```

## 🌐 Network Topology Examples

### 1. Simple gNB-AP Deployment
```python
# Create gNB that acts as AP
gnb_ap = net.addStation('gnb1', 
                        cls=DockerSta,
                        dimage="adaptive/ueransim:latest",
                        environment={
                            "AP_ENABLED": "true",
                            "AP_SSID": "5G-Network",
                            "AP_CHANNEL": "6"
                        })

# UEs connect wirelessly
ue1.cmd('iw dev ue1-wlan0 connect 5G-Network')
```

### 2. Multi-AP Network Slicing
```python
# Slice 1: Emergency Services (High Priority)
gnb1_emergency = net.addStation('gnb1', 
                                environment={
                                    "AP_ENABLED": "true",
                                    "AP_SSID": "Emergency-5G",
                                    "AP_CHANNEL": "36",
                                    "SST": "1",  # eMBB slice
                                    "AP_ENABLE_QOS": "true"
                                })

# Slice 2: IoT Services (Low Latency)  
gnb2_iot = net.addStation('gnb2',
                          environment={
                              "AP_ENABLED": "true", 
                              "AP_SSID": "IoT-5G",
                              "AP_CHANNEL": "149",
                              "SST": "2",  # URLLC slice
                              "AP_MODE": "ac"
                          })
```

## 🔍 Verification Commands

### Check AP Status
```bash
# Inside gNB container
gnb1 ovs-vsctl show                    # Check OVS bridge
gnb1 hostapd_cli interface            # Check hostapd status
gnb1 iw dev                           # List wireless interfaces
gnb1 brctl show                       # Show bridges
```

### Check OpenFlow Controller Connection
```bash
gnb1 ovs-vsctl get-controller br-gnb  # Show controller
gnb1 ovs-ofctl dump-flows br-gnb      # Show flow table
```

### Monitor AP Activity
```bash
# Monitor hostapd logs
gnb1 tail -f /var/log/hostapd.log

# Monitor wireless activity
gnb1 iw dev wlan0 station dump
```

## 🚨 Troubleshooting

### 1. AP Not Starting
```bash
# Check if AP setup script ran
gnb1 cat /tmp/ap-setup.log

# Manually run AP setup
gnb1 /usr/local/bin/ap-setup.sh
```

### 2. No Wireless Interface
```bash
# Check for wireless interfaces
gnb1 ls /sys/class/net/*/wireless

# Load mac80211_hwsim module
gnb1 modprobe mac80211_hwsim
```

### 3. OVS Bridge Issues
```bash
# Restart OVS
gnb1 systemctl restart openvswitch-switch

# Recreate bridge
gnb1 ovs-vsctl del-br br-gnb
gnb1 ovs-vsctl add-br br-gnb
```

### 4. UEs Can't Connect
```bash
# Check AP is broadcasting
gnb1 iw dev wlan0 info

# Check SSID is visible
ue1 iw dev ue1-wlan0 scan | grep -A5 -B5 "SSID: ap1-ssid"

# Manual connection
ue1 iw dev ue1-wlan0 connect ap1-ssid
```

## 📋 Feature Comparison

| Feature | Traditional mininet-wifi AP | Enhanced gNB-AP |
|---------|----------------------------|-----------------|
| SSID Creation | ✅ | ✅ |
| OpenVSwitch | ✅ | ✅ |
| OpenFlow Protocol | ✅ | ✅ |
| Controller Connection | ✅ | ✅ |
| Wireless Standards | ✅ | ✅ |
| Security (WPA/WPA2) | ✅ | ✅ |
| QoS/Traffic Control | ✅ | ✅ |
| 5G gNB Functionality | ❌ | ✅ |
| Network Slicing | ❌ | ✅ |
| Container Deployment | ❌ | ✅ |

## 🎯 Benefits of gNB-AP Integration

1. **Unified 5G + WiFi**: Single container provides both 5G and WiFi connectivity
2. **Network Slicing**: Different SSIDs can represent different network slices  
3. **Resource Efficiency**: Fewer containers needed
4. **Realistic Deployment**: Mirrors real-world 5G base stations with WiFi capability
5. **Full SDN Support**: Complete OpenFlow and controller integration
6. **Container Scalability**: Easy to deploy and manage multiple gNB-APs

## 📚 Example Files

- **Enhanced Dockerfile**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/UERANSIM/Dockerfile`
- **AP Setup Script**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/UERANSIM/ap-setup.sh`
- **Updated Topology**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Mininet/updated_topology_gnb_ap.py`
- **Example Topology**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Mininet/gnb_ap_topology_example.py`
- **Documentation**: `/home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/UERANSIM/README_AP_FUNCTIONALITY.md`

Your UERANSIM Docker image is now fully equipped to act as mininet-wifi Access Points with complete OpenFlow, OVS, and SDN controller support! 🎉
