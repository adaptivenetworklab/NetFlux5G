# Integration Example: Enhanced gNB in NetFlux5G GUI

This example demonstrates how to use the enhanced gNB configuration through the NetFlux5G graphical interface.

## Step-by-Step Setup

### 1. Create a New Topology

1. Start NetFlux5G Editor
2. Create a new topology (File → New Topology)
3. Place network components on the canvas

### 2. Add Enhanced gNB Component

1. From the component panel, drag a **gNB** component onto the canvas
2. Double-click the gNB to open its properties dialog
3. Configure the following tabs:

#### 5G Configuration Tab
- **AMF Hostname**: `amf.core5g.local`
- **gNB Hostname**: `gnb.cell1.local`
- **TAC**: `100`
- **MCC**: `999`
- **MNC**: `70`
- **SST**: `1`
- **SD**: `0x123456`
- **TX Power**: `35` dBm
- **Range**: `500` meters

#### Access Point Tab
- ✅ **Enable Access Point Functionality**
- **SSID**: `5G-Network-Slice-1`
- **Channel**: `6`
- **Mode**: `ac`
- **Password**: `secure5g2025` (or leave empty for open)
- **Bridge Name**: `br-cell1`

#### OpenFlow/OVS Tab
- **Controller**: `tcp:192.168.1.100:6633`
- **Fail Mode**: `secure`
- **OpenFlow Protocols**: `OpenFlow14`
- **Datapath**: `kernel`

#### Network Interfaces Tab
- **N2 Interface**: `eth0`
- **N3 Interface**: `eth1`
- **Radio Interface**: `wlan0`

### 3. Add Additional Components

Add the following components and connect them:

1. **Controller** (for OpenFlow management)
   - IP: `192.168.1.100`
   - Port: `6633`

2. **UE Components** (User Equipment)
   - Connect to the gNB via links
   - Configure with matching MCC/MNC

3. **5G Core Components** (if needed)
   - AMF, SMF, UPF components
   - Configure appropriate hostnames

### 4. Export and Deploy

1. Click **File → Export to Mininet** to generate the Python script
2. The exported script will include:

```python
# Enhanced gNB with AP functionality
gnb1 = net.addStation('gnb1',
                      cap_add=["net_admin"],
                      privileged=True,
                      volumes=["/sys:/sys", "/lib/modules:/lib/modules", "/sys/kernel/debug:/sys/kernel/debug"],
                      dimage="adaptive/ueransim:latest",
                      range=500,
                      txpower=35,
                      position='350.0,335.0,0',
                      environment={
                          # 5G Configuration
                          "AMF_HOSTNAME": "amf.core5g.local",
                          "GNB_HOSTNAME": "gnb.cell1.local",
                          "N2_IFACE": "eth0",
                          "N3_IFACE": "eth1",
                          "RADIO_IFACE": "wlan0",
                          "MCC": "999",
                          "MNC": "70",
                          "SST": "1",
                          "SD": "0x123456",
                          "TAC": "100",
                          
                          # AP Configuration
                          "AP_ENABLED": "true",
                          "AP_SSID": "5G-Network-Slice-1",
                          "AP_CHANNEL": "6",
                          "AP_MODE": "ac",
                          "AP_PASSWD": "secure5g2025",
                          "AP_BRIDGE_NAME": "br-cell1",
                          "OVS_CONTROLLER": "tcp:192.168.1.100:6633",
                          "AP_FAILMODE": "secure",
                          "OPENFLOW_PROTOCOLS": "OpenFlow14"
                      })
```

### 5. Run the Network

1. Use **RunAll** button to deploy the complete topology
2. The system will:
   - Set up Docker containers
   - Configure wireless interfaces
   - Start the OpenFlow controller
   - Initialize the 5G core network
   - Enable AP functionality on gNBs

## Advanced Usage Scenarios

### Scenario 1: Multi-Cell Network with Different Slices

Create multiple gNBs with different network slice configurations:

1. **gNB1**: Emergency Services Slice
   - SSID: `Emergency-5G`
   - SST: `1` (eMBB)
   - Channel: `1`

2. **gNB2**: IoT Services Slice
   - SSID: `IoT-5G`
   - SST: `2` (mIoT)
   - Channel: `6`

3. **gNB3**: Industrial Automation Slice
   - SSID: `Industry-5G`
   - SST: `3` (URLLC)
   - Channel: `11`

### Scenario 2: SDN-Controlled Network

1. Add an **OpenFlow Controller** component
2. Configure all gNBs to connect to the same controller
3. Implement custom flow rules for:
   - Traffic steering between slices
   - Quality of Service enforcement
   - Load balancing across cells

### Scenario 3: Mobility Testing

1. Create overlapping coverage areas for multiple gNBs
2. Configure UEs to move between cells
3. Test handover procedures
4. Monitor performance metrics

## Verification Commands

After deployment, use these commands to verify the setup:

```bash
# Check gNB container status
docker ps | grep gnb

# Verify AP functionality
docker exec gnb1 pgrep -f hostapd
docker exec gnb1 iw dev

# Check OVS configuration
docker exec gnb1 ovs-vsctl show

# Test wireless connectivity
docker exec ue1 iw dev ue1-wlan0 scan | grep "5G-Network-Slice-1"

# Monitor OpenFlow flows
docker exec gnb1 ovs-ofctl dump-flows br-cell1
```

## Performance Monitoring

The enhanced gNB provides several monitoring capabilities:

1. **Radio Performance**: RSSI, throughput, connection quality
2. **Network Performance**: Latency, packet loss, jitter
3. **OpenFlow Metrics**: Flow statistics, controller connectivity
4. **5G Metrics**: Registration success rate, session establishment time

## Troubleshooting Tips

1. **AP Not Starting**: Ensure host has mac80211_hwsim loaded
2. **Controller Connection Failed**: Check network connectivity and firewall
3. **UE Registration Failed**: Verify 5G core components are running
4. **Poor Performance**: Check interference and channel allocation
5. **Bridge Issues**: Verify OVS is properly installed and configured

This comprehensive setup demonstrates the full capabilities of the enhanced gNB component in NetFlux5G, providing both 5G cellular functionality and WiFi access point capabilities with full SDN integration.
