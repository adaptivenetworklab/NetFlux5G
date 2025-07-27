#!/bin/bash
# NetFlux5G Maximum Load Traffic Generator
# This script generates the highest possible traffic load for testing
# 
# Network Configuration (based on UPF YAML configs and actual topology routing):
# UPF1 (upf.yaml):
#   - 10.100.0.0/16 (gateway: 10.100.0.1) - internet APN  - ogstun  - UE 1-5, 31-35
#   - 10.200.0.0/16 (gateway: 10.200.0.1) - internet2 APN - ogstun2 - UE 6-10, 26-30
# UPF2 (upf_2.yaml):
#   - 10.51.0.0/16  (gateway: 10.51.0.1)  - web1 APN     - ogstun3 - UE 11-15, 21-25, 36-40
#   - 10.52.0.0/16  (gateway: 10.52.0.1)  - web2 APN     - ogstun4 - UE 16-20

echo "===================================================="
echo "NetFlux5G Maximum Load Traffic Generator"
echo "===================================================="
echo "Starting maximum load traffic generation..."

# Configuration for maximum load
MAX_BANDWIDTH="2000M"    # Maximum bandwidth per stream
MAX_STREAMS=3            # Maximum parallel streams per UE
TEST_DURATION=60         # Test duration in seconds

# Start iPerf servers with higher capacity on correct gateway IPs
echo "Starting high-capacity iPerf servers..."
docker exec mn.upf1 iperf3 -s -B 10.100.0.1 -p 5001 -f M &  # internet APN
docker exec mn.upf1 iperf3 -s -B 10.200.0.1 -p 5002 -f M &  # internet2 APN  
docker exec mn.upf2 iperf3 -s -B 10.51.0.1 -p 5003 -f M &   # web1 APN
docker exec mn.upf2 iperf3 -s -B 10.52.0.1 -p 5004 -f M &   # web2 APN

sleep 3

# Generate maximum load traffic
echo "Generating MAXIMUM LOAD traffic on all UEs..."
for i in $(seq 1 40); do
    ue="UE__${i}"
    
    # Get UE IP
    ue_ip=$(docker exec mn.${ue} ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p' 2>/dev/null)
    
    if [ -n "$ue_ip" ]; then
        # Select target based on actual UE APN configuration from topology
        case $i in
            1|2|3)
                target="10.100.0.1"  # UPF1 internet APN gateway
                port="5001"
                ;;
            4|5|6)
                target="10.200.0.1"  # UPF1 internet2 APN gateway
                port="5002"
                ;;
            *)
                target="10.100.0.1"  # Default fallback
                port="5001"
                ;;
        esac
        
        # Generate multiple high-bandwidth streams
        for stream in $(seq 1 $MAX_STREAMS); do
            # TCP upload
            docker exec mn.${ue} iperf3 -c $target -B $ue_ip -p $port -f M -b $MAX_BANDWIDTH -t $TEST_DURATION -P 2 &
            
            # TCP download
            docker exec mn.${ue} iperf3 -c $target -B $ue_ip -p $port -f M -b $MAX_BANDWIDTH -t $TEST_DURATION -P 2 -R &
            
            # UDP flood
            docker exec mn.${ue} iperf3 -c $target -B $ue_ip -p $port -f M -b $MAX_BANDWIDTH -t $TEST_DURATION -u -P 2 &
        done
        
        # Additional background load
        docker exec mn.${ue} bash -c "
            # Continuous ping flood
            ping -f $target &
            
            # HTTP requests
            for j in {1..50}; do
                curl -s --max-time 2 http://httpbin.org/bytes/1000000 > /dev/null 2>&1 &
            done
        " &
        
        echo "Started maximum load for ${ue} -> ${target}:${port}"
    fi
    
    # Small delay to prevent system overload
    sleep 0.05
done

echo "All traffic generation started!"
echo "Traffic distribution (based on actual topology routing):"
echo "  - Internet APN  (10.100.0.1:5001): UE 1-5, 31-35 (10 UEs)"
echo "  - Internet2 APN (10.200.0.1:5002): UE 6-10, 26-30 (10 UEs)"
echo "  - Web1 APN     (10.51.0.1:5003):  UE 11-15, 21-25, 36-40 (15 UEs)"
echo "  - Web2 APN     (10.52.0.1:5004):  UE 16-20 (5 UEs)"
echo "Estimated total bandwidth: $((40 * MAX_STREAMS * 2 * 2000))M bps"
echo "Test duration: ${TEST_DURATION}s"

# Wait for tests to complete
sleep $((TEST_DURATION + 10))

# Clean up background processes
echo "Stopping background processes..."
pkill -f "ping -f" 2>/dev/null || true
pkill -f "curl.*httpbin" 2>/dev/null || true

# Wait for capture to complete
sleep 10

echo "Traffic generation completed!"
echo "Results will be available in /captures/ directory"
