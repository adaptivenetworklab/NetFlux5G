# NetFlux5G

NetFlux5G is an interactive graphical application for designing, simulating, and exporting 5G, wireless, and container-based network topologies. It provides a drag-and-drop GUI for building complex networks, configuring properties, and exporting Mininet scripts for deployment and emulation.

---

## Folder Structure

- **netflux5g-editor/src/**
  - **main.py**  
    Main entry point for the NetFlux5G application (PyQt5 GUI).
  - **automation/**
    - **automation_runner.py**  
      Handles automated deployment and working directory management for exports.
    - **mininet/**  
      Docker environment and scripts for Mininet-WiFi and Containernet.
      - **Dockerfile**: Docker build instructions for Mininet-WiFi/Containernet.
      - **install.sh**: Installs Mininet-WiFi and dependencies inside the container.
      - **README.md**: Usage and troubleshooting for the Mininet Docker environment.
  - **export/**
    - **mininet_export.py**  
      Exports topologies to Mininet scripts.
    - **5g-configs/**  
      Templates and generated configs for 5G components.
    - **mininet/**  
      Stores generated deployment files and working directories.
  - **gui/**
    - **canvas.py**  
      Canvas widget for drawing and interacting with network topologies.
    - **components.py, links.py, toolbar.py**  
      GUI logic for components, links, and toolbar actions.
    - **ui/**  
      Qt Designer `.ui` files for all dialogs and windows (e.g., Main_Window.ui, Host_properties.ui).
    - **widgets/**  
      Custom PyQt5 widgets and dialogs.
    - **Icon/**  
      Application and component icons.
  - **manager/**
    - **window.py, status.py, component_panel.py, file.py, tool.py, canvas.py, automation.py, keyboard.py, debug.py**  
      Managers for window handling, status bar, component panel, file operations, tools, canvas logic, automation, keyboard shortcuts, and debugging.
  - **prerequisites/**
    - **checker.py**  
      Checks for required system dependencies before running exports or emulations.

---

# How to Run the Application

### Options to Run NetFlux5G

1. Native Installation
2. Docker

## 1. Native Installation to Run NetFlux5G

### Prerequisites

- **Python 3.11+** recommended
- **Ubuntu 20.04+** (Ubuntu 24.04 require venv for installing the requirement)
- **Docker** (for Mininet/Containernet emulation)
- **PyQt5** and **PyYAML** Python packages

### Run the Installation Script

This will Install the latest compatible version of :
- Mininet-WiFi
- Containernet
- PyQT
- Docker Engine 

```sh
git clone -b netflux5g https://github.com/adaptivenetworklab/Riset_23-24_SDN.git NetFlux5G
```

```sh
cd NetFlux5G
chmod +x ./install.sh
sudo ./install.sh
```
### Build Open5Gs & UERANSIM Custom Image

This image will provide a number of networking tools and additional support of OpenVSwitch & OpenFlow

```sh
cd netflux5g-editor/src/automation/open5gs/
docker build -t adaptive/open5gs:latest .
cd ../ueransim
docker build -t adaptive/ueransim:latest .
cd ../../../..
```

### Running the GUI

From the `netflux5g-editor/src/` directory, launch the application:
```sh
python3 main.py
```

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
| `main.py`                  | Main application entry point (PyQt5 GUI)                                    |
| `automation/`              | Automation scripts and Docker environment for emulation                     |
| `export/`                  | Exporters for Docker Mininet, and 5G configs                       |
| `gui/`                     | GUI logic, widgets, and Qt Designer UI files                                |
| `manager/`                 | Application managers for window, file, tool, and component logic            |
| `prerequisites/`           | System checks for required dependencies                                     |

---

## Notes

- For Mininet/Containernet emulation, ensure you have Docker and the required kernel modules loaded (see the Mininet README).
- All GUI dialogs and windows are defined in the `gui/ui/` folder as `.ui` files and loaded dynamically.
- The application supports drag-and-drop topology design, property dialogs for each component, and export to multiple formats.

---

## Credit

Thanks to Mr. Ramonfontes & Contributors of Mininet-Wifi and Continernet. This project won't go smoothly without a top notch open source Wifi SDN Emulator and the comprehensive detail of documentations.

Checkout the source Repo :

- Mininet-WiFi : [`Mininet-Wifi`](https://github.com/intrig-unicamp/mininet-wifi)

- Containernet : [`Containernet`](https://github.com/containernet/containernet)

- Containernet Fork : [`Containernet w/ Mininet-WiFi Support`](https://github.com/ramonfontes/containernet)

## License

See individual files and dependencies for license details.
