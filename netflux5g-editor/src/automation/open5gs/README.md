# Open5gs Container Image

This repository provides a container image to deploy [Open5gs](https://open5gs.org/) services as a containers.

[Open5gs](https://open5gs.org/) is an open source project of 5GC and EPC (Release-16).

This project can be used to configure your own NR/LTE network. If gNB/eNB and USIM are available, you can build a private network using Open5GS.

Open5GS implemented 5GC and EPC using C-language. And WebUI is provided for testing purposes and is implemented in Node.JS and React.

## Usage

The idea is to deploy a container image for each of the core network services (i.e. hss, sgwc, amf, etc.). The image default CMD launches `/bin/bash`, so the recommendation is to change the command to `open5gs-hssd`, `open5gs-sgwcd`, `open5gs-amfd` or the corresponding daemon for the service you want to deploy. 

The daemons take their configuration from the `/opt/open5gs/etc/open5gs/` and the `/opt/open5gs/etc/freeDiameter` image folders.
The folders include minimal working configurations for all the services.
The original open5gs configuration files are also provided at `/opt/open5gs/etc/orig`, with comments on available parameters.

Data plane service upf needs `/dev/ogstun` tun device access. You can create the tun interface in your host and mount it in the container or you can run upf container in privileged mode.

Some services must have access to a mongodb. You can modify the container environment variable `DB_URI=mongodb://mongo/open5gs` to configure access to mongodb.

# Open5GS SDN/OpenFlow Integration

This enhanced Open5GS Docker image provides full SDN (Software-Defined Networking) and OpenFlow support for integration with mininet-wifi DockerSta nodes and SDN controllers.

## Features

- **OpenVSwitch Integration**: Full OVS support with bridge management
- **OpenFlow Protocol Support**: OpenFlow 1.0, 1.3, and 1.4 protocols
- **SDN Controller Integration**: Connect to external SDN controllers
- **Mininet-wifi Compatibility**: Works seamlessly with DockerSta nodes
- **Dynamic Configuration**: Runtime configuration via environment variables
- **Multi-component Support**: Individual configuration for each Open5GS component

## Quick Start

### 1. Build the Enhanced Image

```bash
cd /home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/Open5Gs
docker build --build-arg version=2.7.0 -t open5gs-sdn:latest .
```

### 2. Basic Usage with SDN Controller

```bash
# Run AMF with OpenFlow integration
docker run -d --name amf --privileged --cap-add=NET_ADMIN \
    -e OVS_ENABLED=true \
    -e OVS_CONTROLLER=tcp:192.168.1.100:6633 \
    -e OVS_BRIDGE_NAME=br-amf \
    open5gs-sdn:latest open5gs-amfd
```

### 3. Mininet-wifi Integration

```python
# Example mininet-wifi script with Open5GS DockerSta
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import DockerSta
from mn_wifi.cli import CLI

net = Mininet_wifi()

# Create Open5GS AMF as DockerSta
amf = net.addDockerSta(
    'amf',
    dimage='open5gs-sdn:latest',
    dcmd='open5gs-amfd',
    environment={
        'OVS_ENABLED': 'true',
        'OVS_CONTROLLER': 'tcp:192.168.1.100:6633',
        'OVS_BRIDGE_NAME': 'br-amf'
    }
)

net.build()
net.start()
CLI(net)
```

## Configuration Options

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OVS_ENABLED` | Enable/disable OVS integration | `false` | `true` |
| `OVS_CONTROLLER` | SDN controller URL | `""` | `tcp:192.168.1.100:6633` |
| `OVS_BRIDGE_NAME` | OVS bridge name | `br-open5gs` | `br-amf` |
| `OVS_FAIL_MODE` | Bridge fail mode | `standalone` | `secure` |
| `OPENFLOW_PROTOCOLS` | OpenFlow protocols | `OpenFlow14` | `OpenFlow13` |
| `OVS_DATAPATH` | OVS datapath type | `kernel` | `user` |
| `CONTROLLER_IP` | Controller IP (alternative) | `""` | `192.168.1.100` |
| `CONTROLLER_PORT` | Controller port | `6633` | `6653` |
| `BRIDGE_INTERFACES` | Interfaces to add to bridge | `""` | `eth0,eth1` |
| `OVS_AUTO_SETUP` | Auto-setup bridge | `true` | `false` |
| `NETWORK_INTERFACE` | Primary network interface | `eth0` | `wlan0` |
| `BRIDGE_PRIORITY` | Bridge STP priority | `32768` | `4096` |
| `STP_ENABLED` | Enable Spanning Tree Protocol | `false` | `true` |

### Component-Specific Configuration

Each Open5GS component can have its own bridge and controller:

```bash
# AMF with dedicated bridge
docker run -d --name amf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_BRIDGE_NAME=br-amf \
    -e OVS_CONTROLLER=tcp:controller:6633 \
    open5gs-sdn:latest open5gs-amfd

# UPF with different controller
docker run -d --name upf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_BRIDGE_NAME=br-upf \
    -e OVS_CONTROLLER=tcp:upf-controller:6634 \
    open5gs-sdn:latest open5gs-upfd
```

## Advanced Usage

### 1. Using the Configuration Helper

The image includes a helper script for component-specific configuration:

```bash
# Enable OVS for AMF
docker exec amf /opt/open5gs/bin/open5gs-ovs-config.sh \
    --component amf --controller-ip 192.168.1.100 --enable

# Show OVS status
docker exec amf /opt/open5gs/bin/open5gs-ovs-config.sh --status

# Disable OVS for component
docker exec amf /opt/open5gs/bin/open5gs-ovs-config.sh \
    --component amf --disable
```

### 2. Custom OpenFlow Rules

You can add custom OpenFlow rules after the container starts:

```bash
# Add flow rule to forward traffic
docker exec amf ovs-ofctl add-flow br-amf \
    "in_port=1,actions=output:2"

# Add VLAN tagging rule
docker exec amf ovs-ofctl add-flow br-amf \
    "in_port=1,actions=mod_vlan_vid:100,output:2"
```

### 3. Multi-Controller Setup

For complex deployments with multiple controllers:

```bash
# AMF with primary controller
docker run -d --name amf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_CONTROLLER=tcp:primary-controller:6633 \
    open5gs-sdn:latest open5gs-amfd

# Add secondary controller
docker exec amf ovs-vsctl set-controller br-amf \
    tcp:primary-controller:6633 tcp:backup-controller:6633
```

## Integration with NetFlux5G GUI

The NetFlux5G GUI automatically generates the correct environment variables for SDN integration. When you enable OpenFlow in the GUI:

1. **Core Component Properties**: Configure SDN settings in the component properties dialog
2. **Export to Mininet-wifi**: The export will include all SDN configuration
3. **Docker Environment**: Environment variables are automatically set

Example exported mininet-wifi code:
```python
amf = net.addDockerSta(
    'amf',
    dimage='open5gs-sdn:latest',
    dcmd='open5gs-amfd',
    environment={
        'OVS_ENABLED': 'true',
        'OVS_CONTROLLER': 'tcp:192.168.1.100:6633',
        'OVS_BRIDGE_NAME': 'br-amf',
        'OVS_FAIL_MODE': 'standalone',
        'OPENFLOW_PROTOCOLS': 'OpenFlow14'
    }
)
```

## Troubleshooting

### 1. OVS Not Starting

```bash
# Check OVS services
docker exec container_name ps aux | grep ovs

# Check OVS logs
docker exec container_name cat /var/log/openvswitch/ovs-vswitchd.log

# Restart OVS manually
docker exec container_name /opt/open5gs/bin/ovs-setup.sh
```

### 2. Controller Connection Issues

```bash
# Check controller configuration
docker exec container_name ovs-vsctl get-controller br-bridge-name

# Test controller connectivity
docker exec container_name nc -zv controller_ip controller_port

# Check OpenFlow connection
docker exec container_name ovs-ofctl show br-bridge-name
```

### 3. Bridge Configuration Problems

```bash
# List all bridges
docker exec container_name ovs-vsctl list-br

# Show bridge details
docker exec container_name ovs-vsctl show

# Check bridge ports
docker exec container_name ovs-vsctl list-ports br-bridge-name
```

### 4. Network Interface Issues

```bash
# Check network interfaces
docker exec container_name ip link show

# Check bridge interface status
docker exec container_name ip addr show br-bridge-name

# Verify routing
docker exec container_name ip route show
```

## Testing

Run the comprehensive test suite to validate SDN functionality:

```bash
python3 /home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/Open5Gs/test_open5gs_sdn_integration.py
```

## Examples

### 1. Complete 5G Core with SDN

```bash
# MongoDB
docker run -d --name mongo mongo:4.4

# AMF with SDN
docker run -d --name amf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_CONTROLLER=tcp:192.168.1.100:6633 \
    -e OVS_BRIDGE_NAME=br-amf \
    open5gs-sdn:latest open5gs-amfd

# SMF with SDN
docker run -d --name smf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_CONTROLLER=tcp:192.168.1.100:6633 \
    -e OVS_BRIDGE_NAME=br-smf \
    open5gs-sdn:latest open5gs-smfd

# UPF with dedicated data plane controller
docker run -d --name upf --privileged \
    -e OVS_ENABLED=true \
    -e OVS_CONTROLLER=tcp:192.168.1.101:6633 \
    -e OVS_BRIDGE_NAME=br-upf \
    open5gs-sdn:latest open5gs-upfd
```

### 2. Mininet-wifi with Multiple Controllers

```python
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import DockerSta, RemoteController

net = Mininet_wifi()

# Add SDN controllers
c1 = net.addController('c1', controller=RemoteController, 
                       ip='192.168.1.100', port=6633)
c2 = net.addController('c2', controller=RemoteController, 
                       ip='192.168.1.101', port=6633)

# Add Open5GS components with SDN
amf = net.addDockerSta('amf', 
                       dimage='open5gs-sdn:latest',
                       dcmd='open5gs-amfd',
                       environment={
                           'OVS_ENABLED': 'true',
                           'OVS_CONTROLLER': 'tcp:192.168.1.100:6633'
                       })

upf = net.addDockerSta('upf',
                       dimage='open5gs-sdn:latest', 
                       dcmd='open5gs-upfd',
                       environment={
                           'OVS_ENABLED': 'true',
                           'OVS_CONTROLLER': 'tcp:192.168.1.101:6633'
                       })

net.build()
net.start()
```

## Performance Considerations

1. **Datapath Selection**: Use `kernel` datapath for better performance in production
2. **Flow Table Size**: Monitor flow table usage for high-traffic scenarios
3. **Controller Latency**: Place controllers close to Open5GS components
4. **Bridge Configuration**: Use appropriate fail modes based on reliability requirements

## Security

1. **Controller Authentication**: Use TLS for controller connections in production
2. **Flow Rules**: Implement proper access control in OpenFlow rules
3. **Network Isolation**: Use separate bridges for different traffic types
4. **Container Security**: Run with minimal required privileges

## Support

For issues and questions:
- Check the troubleshooting section above
- Run the test suite for diagnostics
- Review container logs for detailed error information
- Consult OpenVSwitch and Open5GS documentation for advanced configuration


