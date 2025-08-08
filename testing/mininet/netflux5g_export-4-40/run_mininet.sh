#!/bin/bash
echo "Starting Mininet topology..."
echo "Working directory: /home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export-4-40"
cd "/home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export-4-40"
sudo python3 "/home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export-4-40/netflux5g_topology.py"
echo "Mininet session ended. Press Enter to close..."
read
