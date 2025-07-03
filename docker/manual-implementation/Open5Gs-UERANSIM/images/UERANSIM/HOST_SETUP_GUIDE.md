# Host Setup Guide for gNB Access Point Functionality

This guide explains how to properly set up your host system to enable gNB containers to function as wireless Access Points in mininet-wifi.

## Prerequisites

The gNB containers require specific host-level setup because:
1. Kernel modules cannot be loaded directly inside Docker containers
2. Wireless interface creation requires privileged access to host networking
3. OpenVSwitch needs access to host kernel features

## Host System Requirements

### 1. Install Required Packages on Host

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    wireless-tools \
    iw \
    hostapd \
    wpasupplicant \
    bridge-utils \
    openvswitch-switch \
    openvswitch-common

# Load mac80211_hwsim module with multiple radios
sudo modprobe mac80211_hwsim radios=10
```

### 2. Verify mac80211_hwsim Setup

```bash
# Check if module is loaded
lsmod | grep mac80211_hwsim

# Check available wireless interfaces
iw dev

# List PHY devices
ls /sys/kernel/debug/ieee80211/
```

Expected output should show multiple `phy#` devices and `wlan#` interfaces.

### 3. Enable X11 Forwarding (for GUI)

```bash
# Allow X11 connections from local root
xhost +local:root
```

## Running gNB Containers with AP Functionality

### Basic Container Run Command

```bash
docker run -it --rm \
    --privileged \
    --pid='host' \
    --net='host' \
    --cap-add=NET_ADMIN \
    --env DISPLAY=$DISPLAY \
    --env QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /sys/:/sys \
    -v /lib/modules:/lib/modules \
    -v /sys/kernel/debug:/sys/kernel/debug \
    -v /var/run/netns:/var/run/netns \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e AP_ENABLED=true \
    -e AP_SSID="gNB-5G-AP" \
    -e AP_CHANNEL=6 \
    -e AP_MODE=g \
    -e AP_BRIDGE_NAME="br-gnb" \
    -e OVS_CONTROLLER="tcp:127.0.0.1:6633" \
    -e AP_FAILMODE="standalone" \
    adaptive/ueransim:latest gnb
```

### Mininet-WiFi Integration Example

```bash
# Create and run a test network
docker run -it --rm \
    --privileged \
    --pid='host' \
    --net='host' \
    -v /sys/:/sys \
    -v /lib/modules:/lib/modules \
    -v /sys/kernel/debug:/sys/kernel/debug \
    -v /var/run/netns:/var/run/netns \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd):/workspace \
    -w /workspace \
    mn-wifi:v1 \
    python3 your_topology_script.py
```

## Environment Variables for AP Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AP_ENABLED` | `false` | Enable/disable AP functionality |
| `AP_SSID` | `gnb-hotspot` | Access Point SSID |
| `AP_CHANNEL` | `6` | Wireless channel (1-11 for 2.4GHz) |
| `AP_MODE` | `g` | Wireless mode (a/b/g/n/ac/ax) |
| `AP_PASSWD` | `""` | WiFi password (empty = open network) |
| `AP_BRIDGE_NAME` | `br-gnb` | OVS bridge name |
| `OVS_CONTROLLER` | `""` | OpenFlow controller (e.g., tcp:IP:PORT) |
| `AP_FAILMODE` | `standalone` | OVS fail mode (standalone/secure) |
| `OPENFLOW_PROTOCOLS` | `OpenFlow14` | OpenFlow protocols |

## Troubleshooting

### 1. No Wireless Interfaces Found

**Problem**: Container logs show "No wireless interface found"

**Solution**:
```bash
# Check host has mac80211_hwsim loaded
sudo modprobe mac80211_hwsim radios=10

# Verify interfaces exist
iw dev

# Restart container with proper mounts
```

### 2. Hostapd Driver Errors

**Problem**: `nl80211: Driver does not support authentication/association`

**Solution**:
- Ensure mac80211_hwsim is loaded on host
- Check that container has access to `/sys` and `/lib/modules`
- Verify wireless interface is properly created

### 3. OVS Connection Issues

**Problem**: Cannot connect to OpenFlow controller

**Solution**:
```bash
# Check OVS is running in container
ovs-vsctl show

# Verify controller is reachable
telnet CONTROLLER_IP CONTROLLER_PORT

# Check bridge configuration
ovs-vsctl list-br
```

### 4. Container Network Isolation

**Problem**: Container cannot access host network features

**Solution**:
- Use `--net='host'` or create proper bridge
- Ensure `--privileged` flag is set
- Mount `/var/run/netns:/var/run/netns`

## Mininet-WiFi Topology Example

```python
#!/usr/bin/env python3

from mn_wifi.net import Mininet_wifi
from mn_wifi.node import OVSKernelAP
from containernet.node import DockerSta
from containernet.cli import CLI

def topology():
    net = Mininet_wifi()
    
    # Add controller
    c0 = net.addController('c0')
    
    # Add gNB container as AP-capable station
    gnb1 = net.addStation('gnb1',
                          cls=DockerSta,
                          dimage="adaptive/ueransim:latest",
                          dcmd="gnb",
                          cap_add=["NET_ADMIN"],
                          privileged=True,
                          volumes=["/sys:/sys", "/lib/modules:/lib/modules"],
                          environment={
                              "AP_ENABLED": "true",
                              "AP_SSID": "gNB-Cell-1",
                              "AP_CHANNEL": "6",
                              "AP_MODE": "g",
                              "AP_BRIDGE_NAME": "br-gnb1",
                              "OVS_CONTROLLER": "tcp:127.0.0.1:6633"
                          },
                          position='100,100,0')
    
    # Add UE containers
    ue1 = net.addStation('ue1',
                         cls=DockerSta,
                         dimage="adaptive/ueransim:latest",
                         dcmd="ue",
                         environment={"GNB_IP": "10.0.0.1"},
                         position='50,100,0')
    
    # Configure and start network
    net.configureWifiNodes()
    net.build()
    c0.start()
    
    # Connect UE to gNB AP
    ue1.cmd('iw dev ue1-wlan0 connect gNB-Cell-1')
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    topology()
```

## Performance Optimization

### Host Kernel Module Parameters

```bash
# Load with more radios for larger topologies
sudo modprobe mac80211_hwsim radios=20

# Enable debugging if needed
echo 'module mac80211_hwsim +p' > /sys/kernel/debug/dynamic_debug/control
```

### Container Resource Limits

```bash
# Limit container resources if needed
docker run --memory=2g --cpus=2 ...
```

## Security Considerations

- Running containers with `--privileged` grants extensive access
- Mount only necessary host directories
- Use network namespaces to isolate container networking
- Consider using user namespaces for additional security

## References

- [Mininet-WiFi Documentation](https://github.com/intrig-unicamp/mininet-wifi)
- [Containernet Documentation](https://github.com/containernet/containernet)
- [mac80211_hwsim Documentation](https://wireless.wiki.kernel.org/en/users/drivers/mac80211_hwsim)
- [OpenVSwitch Documentation](https://docs.openvswitch.org/)
