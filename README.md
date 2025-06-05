# NetFlux5G Editor

This repository contains a PyQt5-based GUI application for building and deploying 5G network topologies.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. If running in a headless environment (e.g. server without a display) the application will automatically fall back to the `offscreen` Qt platform plugin. Ensure the `libxcb-xinerama0` package is installed on Ubuntu:
   ```bash
   sudo apt-get update && sudo apt-get install -y libxcb-xinerama0
   ```

## Running

Navigate to the `netflux5g-editor/src` folder and start the application:

```bash
python3 main.py
```

The application will launch a window when a display server is available. In a headless environment it will run using the offscreen plugin.
