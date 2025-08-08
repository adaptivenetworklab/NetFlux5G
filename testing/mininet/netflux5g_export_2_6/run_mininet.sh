#!/bin/bash
echo "Starting Mininet topology..."
echo "Working directory: /home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export_2_6"
cd "/home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export_2_6"
sudo python3 "/home/litfan/TA/NetFlux5G/testing/mininet/netflux5g_export_2_6/netflux5g_topology.py"
echo "Mininet session ended. Press Enter to close..."
read
