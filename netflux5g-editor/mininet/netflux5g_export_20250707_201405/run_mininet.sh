#!/bin/bash
echo "Starting Mininet topology..."
echo "Working directory: /home/litfan/Code/NetFlux5G/netflux5g-editor/mininet/netflux5g_export_20250707_201405"
cd "/home/litfan/Code/NetFlux5G/netflux5g-editor/mininet/netflux5g_export_20250707_201405"
sudo python3 "/home/litfan/Code/NetFlux5G/netflux5g-editor/mininet/netflux5g_export_20250707_201405/netflux5g_topology.py"
echo "Mininet session ended. Press Enter to close..."
read
