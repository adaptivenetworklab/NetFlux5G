# NetFlux5G

NetFlux5G is an interactive graphical application for designing, simulating, and exporting 5G, wireless, and container-based network topologies. It provides a drag-and-drop GUI for building complex networks, configuring properties, and exporting to Docker Compose or Mininet scripts for deployment and emulation.

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
    - **compose_export.py**  
      Exports topologies to Docker Compose YAML.
    - **mininet_export.py**  
      Exports topologies to Mininet scripts.
    - **5g-configs/**  
      Templates and generated configs for 5G components.
    - **started/**  
      Stores generated deployment files and working directories.
    - **templates/**  
      Template files for export formats.
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

## How to Run the Application

### Prerequisites

- **Python 3.11+** recommended
- **Linux** (for full Mininet/Containernet support)
- **Docker** (for Mininet/Containernet emulation)
- **PyQt5** and **PyYAML** Python packages

Install Python dependencies:
```sh
pip install -r requirements.txt
```

### Running the GUI

From the `netflux5g-editor/src/` directory, launch the application:
```sh
python3 main.py
```

### Exporting and Emulation

- **Export to Docker Compose:**  
  Use the File menu or toolbar to export your topology to a Docker Compose YAML file.
- **Export to Mininet:**  
  Use the export option for Mininet scripts.
- **Automated Deployment:**  
  The app can create a working directory and launch Mininet/Containernet environments using the scripts in `automation/mininet/`.

#### Running Mininet/Containernet in Docker

See [`automation/mininet/README.md`](automation/mininet/README.md) for detailed instructions on building and running the Mininet-WiFi Docker environment.

---

## Folder Details

| Folder/File                | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| `main.py`                  | Main application entry point (PyQt5 GUI)                                    |
| `automation/`              | Automation scripts and Docker environment for emulation                     |
| `export/`                  | Exporters for Docker Compose, Mininet, and 5G configs                       |
| `gui/`                     | GUI logic, widgets, and Qt Designer UI files                                |
| `manager/`                 | Application managers for window, file, tool, and component logic            |
| `prerequisites/`           | System checks for required dependencies                                     |

---

## Notes

- For Mininet/Containernet emulation, ensure you have Docker and the required kernel modules loaded (see the Mininet README).
- All GUI dialogs and windows are defined in the `gui/ui/` folder as `.ui` files and loaded dynamically.
- The application supports drag-and-drop topology design, property dialogs for each component, and export to multiple formats.

---

## License

See individual files and dependencies for license details.