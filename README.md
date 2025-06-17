# NetFlux5G

NetFlux5G is an interactive graphical application for designing, simulating, and exporting 5G, wireless, and container-based network topologies. It provides a drag-and-drop GUI for building complex networks, configuring properties, and exporting to Docker Compose or Mininet scripts for deployment and emulation.

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

### 1. Basic GUI Usage
```bash
cd netflux5g-editor/src
python3 main.py
```

### 2. Docker-only Testing (No Mininet required)
If you only have Docker installed, you can still test 5G Core functionality:

```bash
# Run the application
python3 main.py

# In the GUI:
# 1. Add 5G Core components (VGcore)
# 2. Add gNB and UE components
# 3. Use "Export to Docker Compose" 
# 4. The exported files can be run with docker-compose
```

### 3. Full End-to-End Testing
For complete testing with both 5G Core and network simulation:

```bash
# Ensure all prerequisites are installed
python3 -c "from prerequisites.checker import PrerequisitesChecker; print(PrerequisitesChecker.check_all_prerequisites())"

# Run the application and use "Run End-to-End Test"
python3 main.py
```

---

## Troubleshooting Prerequisites

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

---

## Folder Structure

| Folder/File                | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `main.py`                  | Main application entry point (PyQt5 GUI)                                    |
| `automation/`              | Automation scripts and Docker environment for emulation                     |
| `export/`                  | Exporters for Docker Compose, Mininet, and 5G configs                       |
| `gui/`                     | GUI logic, widgets, and Qt Designer UI files                                |
| `manager/`                 | Application managers for window, file, tool, and component logic            |
| `prerequisites/`           | System checks for required dependencies                                     |

---

## Usage Scenarios

### Scenario 1: 5G Network Design Only
- **Requirements**: Python, PyQt5
- **Use Case**: Design topologies, export configurations
- **Limitations**: No live simulation

### Scenario 2: Docker-based 5G Testing  
- **Requirements**: Python, PyQt5, Docker, Docker Compose
- **Use Case**: 5G Core simulation with Open5GS and UERANSIM
- **Limitations**: No advanced network simulation

### Scenario 3: Full Network Simulation
- **Requirements**: All prerequisites including Mininet-WiFi
- **Use Case**: Complete 5G network simulation with SDN control
- **Benefits**: Full feature set, advanced testing capabilities

---

## Getting Help

### Check Prerequisites
```bash
cd netflux5g-editor/src
python3 -c "
from prerequisites.checker import PrerequisitesChecker
all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
if not all_ok:
    instructions = PrerequisitesChecker.get_installation_instructions()
    for instruction in instructions:
        print(instruction)
"
```

### Common Issues
1. **"Docker not found"**: Install Docker and add user to docker group
2. **"Permission denied"**: Run `sudo usermod -aG docker $USER` and logout/login
3. **"Kernel module not found"**: Run `sudo modprobe mac80211_hwsim radios=10`
4. **"GUI not starting"**: Install `python3-pyqt5` and `python3-tk`

### Manual Implementation Examples
Check the `manual-implementation/` directory for working examples:
- `Open5Gs-UERANSIM/`: Docker-based 5G core setup
- `Mininet/`: Network simulation examples

---

## License

See individual files and dependencies for license details.