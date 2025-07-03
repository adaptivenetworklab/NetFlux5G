# Docker Network Management in NetFlux5G

This document describes the Docker network management feature in NetFlux5G Editor.

## Overview

The Docker network management feature allows you to create and manage Docker networks for your network topologies. This is particularly useful when:

- Working with containerized 5G core components
- Integrating Docker containers with Mininet-WiFi topologies
- Maintaining network isolation between different topology experiments
- Enabling communication between containers and Mininet nodes

## Features

### 1. Automatic Network Naming
- Network names are automatically derived from your topology filename
- Naming format: `netflux5g_<filename>`
- Special characters are sanitized to comply with Docker naming requirements
- Examples:
  - `my_topology.json` → `netflux5g_my_topology`
  - `5G Network (v2.1).yaml` → `netflux5g_5G_Network__v2_1_`

### 2. Menu Actions
Two new menu actions are available in the main menu:

#### Create Docker Network
- **Menu**: Tools → Create Docker Network
- **Shortcut**: Ctrl+Shift+C
- **Function**: Creates a bridge Docker network for the current topology
- **Requirements**: File must be saved first

#### Delete Docker Network
- **Menu**: Tools → Delete Docker Network  
- **Shortcut**: Ctrl+Shift+X
- **Function**: Deletes the Docker network associated with the current topology
- **Safety**: Asks for confirmation before deletion

### 3. Integration with Automation
- The RunAll feature automatically checks for and creates Docker networks if needed
- Generated Mininet scripts include Docker network utility functions
- Network information is embedded in exported script headers

## Usage

### Basic Workflow

1. **Create/Open a Topology**
   ```
   File → New Topology
   or
   File → Open Topology
   ```

2. **Save the Topology**
   ```
   File → Save As → my_5g_network.json
   ```

3. **Create Docker Network**
   ```
   Tools → Create Docker Network
   or
   Ctrl+Shift+C
   ```

4. **Work with Your Topology**
   - Add 5G components (gNB, UE, Core5G)
   - Add Docker hosts
   - Configure component properties

5. **Export and Run**
   ```
   Tools → RunAll
   ```
   This will automatically use the created Docker network

6. **Cleanup (Optional)**
   ```
   Tools → Delete Docker Network
   or
   Ctrl+Shift+X
   ```

### Advanced Usage

#### Manual Docker Network Management
You can also manage Docker networks manually using command line:

```bash
# List NetFlux5G networks
docker network ls --filter name=netflux5g_

# Inspect a specific network
docker network inspect netflux5g_my_topology

# Connect a container to the network
docker network connect netflux5g_my_topology my_container

# Disconnect a container
docker network disconnect netflux5g_my_topology my_container
```

#### Integration in Custom Scripts
Generated Mininet scripts include utility functions:

```python
# Check if network exists
if check_docker_network():
    print("Network is available")

# Create network if needed
create_docker_network_if_needed()
```

## Network Configuration

### Default Settings
- **Driver**: Bridge
- **Attachable**: Yes (allows manual container attachment)
- **Scope**: Local
- **Internal**: No (allows external connectivity)

### Network Properties
- **Subnet**: Automatically assigned by Docker
- **Gateway**: Automatically assigned by Docker
- **IPv6**: Disabled by default
- **DNS**: Uses Docker's default DNS

## Error Handling

### Common Issues and Solutions

#### 1. File Not Saved
**Error**: "The current topology must be saved before creating a Docker network"
**Solution**: Save your topology file first using File → Save As

#### 2. Docker Not Available
**Error**: Network creation fails
**Solution**: 
- Ensure Docker is installed: `docker --version`
- Ensure Docker daemon is running: `sudo systemctl start docker`
- Check user permissions: `sudo usermod -aG docker $USER` (then logout/login)

#### 3. Network Already Exists
**Behavior**: The system will ask if you want to recreate the network
**Options**:
- Yes: Delete existing network and create new one
- No: Keep existing network

#### 4. Network In Use
**Error**: Cannot delete network (containers are connected)
**Solution**: Stop/disconnect containers first:
```bash
# List containers using the network
docker network inspect netflux5g_my_topology

# Stop containers
docker stop container_name

# Then try deletion again
```

## Best Practices

### 1. Consistent Naming
- Use descriptive filenames for your topologies
- Avoid special characters that complicate network names
- Consider using versioning: `topology_v1.json`, `topology_v2.json`

### 2. Network Lifecycle
- Create networks before running complex topologies
- Delete networks when done with experiments
- Use the automated RunAll/StopAll features for convenience

### 3. Resource Management
- Monitor Docker network usage: `docker network ls`
- Clean up unused networks periodically: `docker network prune`
- Be aware that multiple topologies can share the same network name if using the same filename

### 4. Development Workflow
```
1. Design topology in NetFlux5G
2. Save with descriptive name
3. Create Docker network
4. Test with RunAll
5. Iterate on design
6. Clean up when done
```

## Technical Details

### Network Creation Command
```bash
docker network create --driver bridge --attachable netflux5g_<topology_name>
```

### Network Deletion Command
```bash
docker network rm netflux5g_<topology_name>
```

### Network Inspection
```bash
docker network inspect netflux5g_<topology_name>
```

## Troubleshooting

### Debug Mode
Enable debug mode to see detailed network operations:
- Press Ctrl+Shift+D or use Tools → Toggle Debug Mode
- Check console output for network creation/deletion details

### Manual Verification
Verify network operations manually:
```bash
# Check if NetFlux5G networks exist
docker network ls | grep netflux5g

# Get detailed network information
docker network inspect netflux5g_my_topology

# Test network connectivity (from within containers)
ping <container_ip>
```

### Log Files
Check Docker daemon logs for detailed error information:
```bash
# On systemd systems
sudo journalctl -u docker

# Or check Docker logs
sudo docker logs <container_name>
```

## API Reference

### DockerNetworkManager Class

#### Methods
- `create_docker_network()`: Create network for current topology
- `delete_docker_network()`: Delete network for current topology
- `get_current_network_name()`: Get network name for current file
- `list_netflux_networks()`: List all NetFlux5G networks
- `get_network_info(network_name)`: Get detailed network information

#### Private Methods
- `_get_network_name_from_file()`: Extract sanitized network name
- `_network_exists(network_name)`: Check if network exists
- `_create_network(network_name)`: Create Docker network
- `_delete_network(network_name)`: Delete Docker network

## Future Enhancements

Planned improvements for Docker network management:

1. **Custom Network Configuration**
   - Subnet specification
   - Gateway configuration
   - DNS settings

2. **Network Templates**
   - Predefined network configurations
   - Import/export network settings

3. **Multi-Network Support**
   - Support for multiple networks per topology
   - Network segmentation for complex topologies

4. **Monitoring Integration**
   - Network traffic monitoring
   - Container connectivity status
   - Performance metrics

## Support

For issues with Docker network management:

1. Check this documentation
2. Enable debug mode for detailed logging
3. Verify Docker installation and permissions
4. Check the NetFlux5G GitHub repository for known issues
5. Create an issue with detailed error information and steps to reproduce
