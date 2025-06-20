# NetFlux5G

NetFlux5G is an interactive graphical application for designing, simulating, and exporting 5G, wireless, and container-based network topologies. It provides a drag-and-drop GUI for building complex networks, configuring properties, and exporting to Docker Compose or Mininet scripts for deployment and emulation.

![NetFlux5G Screenshot](https://raw.githubusercontent.com/adaptivenetworklab/Riset_23-24_SDN/main/docs/images/screenshot.png)

## Key Features

- **Visual Network Design:** Drag-and-drop interface for creating 5G network topologies
- **5G Core Components:** Open5GS-based 5G core network elements (AMF, UPF, SMF, etc.)
- **Radio Access Network:** gNB and UE components from UERANSIM
- **SDN Integration:** Support for SDN controllers and OpenFlow switches
- **Multi-Export:** Export to Docker Compose or Mininet scripts
- **End-to-End Testing:** Built-in tests for 5G network connectivity

---

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8+ 
- **Memory**: 4GB RAM minimum, 8GB+ recommended
- **Storage**: 10GB free space for Docker images

### Required Software

#### Core Dependencies (Required)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Install Python GUI dependencies
sudo apt-get install -y python3-tk python3-pyqt5
```

#### Docker & Docker Compose (Required for 5G Core)
```bash
# Install Docker
sudo apt-get install -y docker.io docker-compose

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### Network Simulation (Optional - for advanced features)
```bash
# Basic networking tools
sudo apt-get install -y wireless-tools rfkill iw

# For Mininet-WiFi and Containernet (use Docker method below)
# These require system-level installation and kernel modules
```

### Installation Methods

#### Method 1: Docker-based Installation (Recommended)
This method uses Docker containers for Mininet-WiFi and Containernet, avoiding complex system-level installations.

```bash
# 1. Clone the repository
git clone https://github.com/adaptivenetworklab/Riset_23-24_SDN.git
cd Riset_23-24_SDN

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Build the Mininet-WiFi Docker image
cd netflux5g-editor/src/automation/mininet
docker build -t mn-wifi:v1 .

# 4. Load kernel module for wireless simulation
sudo modprobe mac80211_hwsim radios=10

# 5. Allow X11 forwarding for GUI apps
xhost +local:root
```

#### Method 2: Native Installation (Advanced Users)
For users who want native Mininet-WiFi installation:

```bash
# Install system dependencies
sudo apt-get install -y mininet python3-mininet

# Install Mininet-WiFi from source
git clone https://github.com/intrig-unicamp/mininet-wifi.git
cd mininet-wifi
sudo util/install.sh -Wlnfv

# Install Containernet
git clone https://github.com/containernet/containernet.git
cd containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
```

---

## Quick Start

### 1. Launch the Application
```bash
cd netflux5g-editor/src
python3 main.py
```

You'll see a welcome screen with options to create a new topology, open an example, or load existing topology.

### 2. Creating a Basic 5G Network

1. **Create a New Topology**:
   - Click "New Topology" or use File → New
   - Start by dragging 5G core components (VGcore) from the left panel to the canvas

2. **Add Required Components**:
   - **5G Core**: Add VGcore components (AMF, UPF) - right-click to set properties
   - **Radio**: Add gNB and UE components
   - **Network**: Add switches and connect everything with the Link tool (L)

3. **Set Component Properties**:
   - Right-click on components to configure their properties
   - Configure matching MCC/MNC values across components
   - Set proper IP addresses and network configuration

4. **Test Your Design**:
   - Use the "Run End-to-End Test" option to validate your topology

### 3. Using Provided Examples

For quick testing, load one of our example topologies:

1. From the welcome screen, select "Open Example" or use File → Open Example
2. Choose "basic_5g_topology.nf5g" for a pre-configured 5G network
3. Click "Run End-to-End Test" to deploy and test the example topology

### 4. Export Your Design

#### Docker Compose Export
```bash
# In the application:
1. Design your 5G network
2. Select Export → Docker Compose (or press Ctrl+E)
3. Choose a destination directory

# Run the exported files:
cd <export_directory>
docker-compose up -d
```

#### Mininet Export
```bash
# In the application:
1. Design your network topology 
2. Select Export → Mininet (or press Ctrl+M)
3. Choose a destination file

# Run the exported Python script:
cd <export_directory>
sudo python3 exported_topology.py
```

When running Mininet scripts, use the CLI command `test5g` to run connectivity tests.

---

## Running Automated Tests

### GUI-based Testing
1. Create or load a topology
2. Select "Run" → "Run End-to-End Test" from the menu
3. View test results in the console output

### Command-line Testing
```bash
cd netflux5g-editor/src
python3 -m automation.test_runner --topology examples/basic_5g_topology.nf5g
```

### Example Network Testing
For the basic 5G topology example, the test will:
1. Start the 5G core components (AMF, UPF, etc.)
2. Verify gNB registration with the AMF
3. Test UE connection and registration
4. Verify PDU session establishment
5. Test data connectivity through the created tunnel

## Advanced Network Testing

### Emulating Network Conditions
Once your network is running, you can modify link conditions:

```bash
# In Mininet CLI (after running exported script)
# Add 100ms delay and 10% packet loss to UE-gNB link
tc qdisc add dev ue1-wlan0 root netem delay 100ms loss 10%

# Test impact on connectivity
ue1 ping -I uesimtun0 8.8.8.8
```

---

## Troubleshooting

### Missing Docker Compose
```bash
# Ubuntu 20.04+
sudo apt-get install docker-compose

# Or use Docker's compose plugin
sudo apt-get install docker-compose-plugin
```

### Missing Wireless Tools
```bash
sudo apt-get install wireless-tools wpasupplicant iw rfkill
```

### Kernel Module Issues
```bash
# Load wireless simulation module
sudo modprobe mac80211_hwsim radios=10

# Make it persistent
echo 'mac80211_hwsim' | sudo tee -a /etc/modules
```

### Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again

# Fix X11 permissions for GUI apps in containers
xhost +local:root
```

### Common Error Messages

| Error | Solution |
|-------|----------|
| "Connection refused" | Make sure Docker is running with `sudo systemctl start docker` |
| "Permission denied" | Run `sudo usermod -aG docker $USER` and restart session |
| "Failed to create container" | Check disk space with `df -h` and free up space if needed |
| "UE not connecting" | Verify matching MCC/MNC/TAC values in UE and AMF configurations |
| "AMF not starting" | Check Docker network exists with `docker network ls` |

---

## Project Structure

| Folder/File                | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `main.py`                  | Main application entry point (PyQt5 GUI)                                    |
| `automation/`              | Automation scripts and Docker environment for emulation                     |
| `export/`                  | Exporters for Docker Compose, Mininet, and 5G configs                       |
| `gui/`                     | GUI logic, widgets, and Qt Designer UI files                                |
| `manager/`                 | Application managers for window, file, tool, and component logic            |
| `prerequisites/`           | System checks for required dependencies                                     |
| `examples/`                | Ready-to-use example network topologies                                     |

---

## Frequently Asked Questions

### General Questions

**Q: Can I use this on Windows or macOS?**  
A: The application is primarily designed for Linux. While the GUI may work on other platforms, the emulation and container functionality require Linux.

**Q: How resource-intensive is running a full 5G network?**  
A: A basic setup requires about 4GB RAM and 2 CPU cores. Complex topologies with many UEs may need 8GB+ RAM.

### Technical Questions

**Q: How do I add custom Docker images for 5G components?**  
A: Edit the Component5G_Image property for VGcore components to use your custom images.

**Q: Can I connect to real hardware gNBs/UEs?**  
A: Not directly. This is an emulation environment for testing and development.

**Q: How do I customize the 5G configuration files?**  
A: Right-click on VGcore components, select "Edit Configuration" to modify YAML configs.

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see individual files for details.

---

## Acknowledgments

- [Open5GS](https://open5gs.org/) - 5G Core implementation
- [UERANSIM](https://github.com/aligungr/UERANSIM) - UE and RAN simulator
- [Mininet-WiFi](https://github.com/intrig-unicamp/mininet-wifi) - WiFi emulation
- [Containernet](https://github.com/containernet/containernet) - Container integration