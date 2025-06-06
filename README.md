# NetFlux5G

NetFlux5G is a PyQt5-based GUI application for designing, deploying, and testing 5G network topologies using Mininet-WiFi and Dockerized 5G core/RAN components.

---

## Features

- **Visual Topology Editor:** Drag-and-drop interface for building 5G/SDN topologies.
- **Mininet-WiFi Integration:** Export and run topologies as Mininet scripts.
- **Docker Compose Integration:** Deploy 5G core and RAN components using Docker Compose.
- **Automation:** One-click deployment and teardown of your entire network.

---

## Project Structure

- `netflux5g-editor/` — Main GUI application (PyQt5)
- `mininet-scenarios/` — Example and exported Mininet topology scripts
- `docker/` — Docker images, compose files, and entrypoints
- `docs/` — Additional documentation and tutorials
- `install.sh` — Automated installation script for dependencies
- `requirements.txt` — Python dependencies

---

## Quick Start

### 1. Install System Dependencies

```sh
sudo apt-get update
sudo apt-get install -y python3-pip git libxcb-xinerama0
   ```

## 2. Running

Navigate to the `netflux5g-editor/src` folder and start the application:

```bash
python3 main.py
```

The application will launch a window when a display server is available. In a headless environment it will run using the offscreen plugin.
