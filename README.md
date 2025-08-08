# NetFlux5G

NetFlux5G is an interactive graphical application for designing, simulating, and exporting 5G, wireless, and container-based network topologies. It provides a drag-and-drop GUI for building complex networks, configuring properties, and exporting Mininet scripts for deployment and emulation.

---

## Folder Structure

### Root Directory
- **install.sh**  
  Installation script that sets up Python venv, installs dependencies, Mininet-WiFi, Containernet, and Docker.
- **docker/**  
  Docker environment for containerized deployment.
  - **Dockerfile**: Container build instructions for Mininet-WiFi/Containernet environment.
  - **containernet-install.sh**: Containernet installation script for container.
  - **entrypoint.sh**: Container startup script.
  - **manual-implementation/**: Manual implementation examples and configurations.

### NetFlux5G Editor (`netflux5g-editor/src/`)
- **main.py**  
  Main entry point for the NetFlux5G application (PyQt5 GUI).

- **automation/**  
  Automated deployment and emulation management.
  - **automation_runner.py**: Core automation handler for running Mininet scripts and managing deployments.
  - **monitoring/**: Network monitoring and telemetry tools.
  - **onos-controller/**: ONOS SDN controller integration and configurations.
  - **open5gs/**: Open5GS 5G core network automation and configs.
  - **ryu-controller/**: Ryu SDN controller integration and applications.
  - **srs-lte/**: SRS LTE stack automation and configurations.
  - **srs-nr/**: SRS 5G NR stack automation and configurations.
  - **ueransim/**: UERANSIM 5G UE and gNB simulator automation.
  - **webshark/**: Wireshark web interface integration for packet analysis.

- **examples/**  
  Sample topology files demonstrating NetFlux5G capabilities.
  - **basic_5g_topology.nf5g**: Simple 5G network topology example.
  - **multi_ran_deployment.nf5g**: Multi-RAN deployment scenario.
  - **sdn_topology.nf5g**: SDN-enabled network topology example.

- **export/**  
  Topology export functionality for various target platforms.
  - **mininet_export.py**: Core exporter for generating Mininet Python scripts from topologies.
  - **5g-configs/**: Templates and generated configuration files for 5G components.
  - **mininet/**: Generated Mininet deployment files and working directories.

- **gui/**  
  PyQt5-based graphical user interface components.
  - **window.py**: Main application window and layout management.
  - **canvas.py**: Interactive canvas for topology design and component placement.
  - **component_panel.py**: Component palette and properties panel.
  - **components.py**: Network component definitions and rendering logic.
  - **links.py**: Network link management and visualization.
  - **toolbar.py**: Application toolbar and action handlers.
  - **status.py**: Status bar and application state display.
  - **welcome.py**: Welcome screen and project selection interface.
  - **ui/**: Qt Designer `.ui` files for dialogs and windows.
  - **widgets/**: Custom PyQt5 widgets and specialized dialogs.
  - **Icon/**: Application icons and component graphics.

- **manager/**  
  Application logic and state management modules.
  - **automation.py**: Automation workflow coordination and task scheduling.
  - **canvas.py**: Canvas state management and interaction handling.
  - **component_operations.py**: Component creation, modification, and deletion operations.
  - **controller.py**: SDN controller integration and management.
  - **database.py**: Topology data persistence and project file management.
  - **deployment_monitor.py**: Real-time monitoring of deployed network emulations.
  - **docker_network.py**: Docker network management for containerized deployments.
  - **file.py**: File I/O operations for saving/loading topologies and configurations.
  - **keyboard.py**: Keyboard shortcut handling and hotkey management.
  - **monitoring.py**: Network performance monitoring and metrics collection.
  - **packet_analyzer.py**: Packet capture and analysis integration.
  - **tool.py**: Tool selection and mode management for the GUI.

- **prerequisites/**  
  System dependency checking and validation.
  - **checker.py**: Validates required system dependencies before deployment.

- **utils/**  
  Utility functions and helper modules.
  - **configmap.py**: Configuration file parsing and template management.
  - **debug.py**: Centralized debug logging and error reporting system.
  - **docker_utils.py**: Docker container management and helper functions.
  - **power_range_calculator.py**: RF power and coverage calculations for wireless components.
  - **template_updater.py**: Dynamic template updating for configuration files.

---

# How to Run the Application

### Options to Run NetFlux5G

1. Native Installation
2. Docker

## 1. Native Installation to Run NetFlux5G


### Prerequisites

- **Python 3.11+** recommended
- **Ubuntu 20.04+** (Ubuntu 24.04+ requires venv for installing requirements)
- **Docker** (for Mininet/Containernet emulation)

### Installation

This will install the latest compatible version of:
- Mininet-WiFi
- Containernet
- PyQt5 and dependencies (in a Python venv)
- Docker Engine

Clone the repository:
```sh
git clone -b netflux5g https://github.com/adaptivenetworklab/Riset_23-24_SDN.git NetFlux5G
```

Run the installation script (this will set up a Python venv and install all requirements inside it):
```sh
cd NetFlux5G
chmod +x ./install.sh
sudo ./install.sh
```

### Running the GUI

Activate the Python venv:
```sh
cd NetFlux5G
source venv/bin/activate
```

From the `netflux5g-editor/src/` directory, launch the application:
```sh
cd netflux5g-editor/src/
python3 main.py
```

> **Note:** All Python dependencies are installed in the `venv` created by the install script. Always activate the venv before running the application.


### Exporting and Emulation

- **Export to Mininet:**  
  Use the export option for Mininet scripts.
- **Automated Deployment:**  
  The app can create a working directory and launch Mininet/Containernet environments using the scripts in `automation/mininet/`.

## 2. Docker to Run NetFlux5G

See [`docker/README.md`](docker/README.md) for detailed instructions on building and running the Netflux 5G Docker environment.

---

## Folder Details

| Folder/File                | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `install.sh`               | Installation script for venv, dependencies, Mininet-WiFi, Containernet, and Docker |
| `docker/`                  | Docker environment and containerized deployment scripts                     |
| `main.py`                  | Main application entry point (PyQt5 GUI)                                   |
| `automation/`              | Automated deployment, monitoring, and 5G/SDN component integration         |
| `examples/`                | Sample topology files (.nf5g) demonstrating various network scenarios      |
| `export/`                  | Topology exporters for Mininet scripts and 5G configuration generation     |
| `gui/`                     | PyQt5 GUI components, widgets, canvas, and user interface elements         |
| `manager/`                 | Application logic managers for state, components, deployment, and monitoring |
| `prerequisites/`           | System dependency validation and requirement checking                       |
| `utils/`                   | Utility functions for debugging, Docker, configuration, and calculations    |

---


## Notes

- For Mininet/Containernet emulation, ensure you have Docker and the required kernel modules loaded (see the Mininet README).
- All GUI dialogs and windows are defined in the `gui/ui/` folder as `.ui` files and loaded dynamically.
- The application supports drag-and-drop topology design, property dialogs for each component, and export to multiple formats.
- The install script will automatically create a Python virtual environment (`venv`) in the project root if it does not exist, and install all Python dependencies there.
- Always activate the venv before running the GUI or any Python scripts.

---

## Credit

Thanks to Mr. Ramonfontes & Contributors of Mininet-Wifi and Continernet. This project won't go smoothly without a top notch open source Wifi SDN Emulator and the comprehensive detail of documentations.

Checkout the source Repo :

- Mininet-WiFi : [`Mininet-Wifi`](https://github.com/intrig-unicamp/mininet-wifi)

- Containernet : [`Containernet`](https://github.com/containernet/containernet)

- Containernet Fork : [`Containernet w/ Mininet-WiFi Support`](https://github.com/ramonfontes/containernet)

## License

See individual files and dependencies for license details.
