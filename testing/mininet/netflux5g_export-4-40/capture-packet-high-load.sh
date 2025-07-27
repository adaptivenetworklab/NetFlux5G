#!/bin/bash
# NetFlux5G High Load Traffic Generation Script
# Automated script to generate maximum traffic load across all 40 UE devices
# Compatible with the NetFlux5G topology

echo "Starting High Load Traffic Generation for NetFlux5G..."
echo "Targeting all 40 UE devices with maximum traffic load"

# Configuration
CAPTURE_DURATION=60  # Capture duration in seconds
IPERF_DURATION=45    # iPerf test duration in seconds
BANDWIDTH_LIMIT="1000M"  # Maximum bandwidth per UE
PARALLEL_STREAMS=4   # Number of parallel streams per UE
RESULTS_DIR="/root/hasil_test"
LOG_DIR="/logging"

# Create results directory if it doesn't exist
mkdir -p $RESULTS_DIR

# Function to get UE IP address
get_ue_ip() {
    local ue_name=$1
    docker exec mn.${ue_name} ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p'
}

# Function to get UPF IP address for specific interface
get_upf_ip() {
    local upf_name=$1
    local interface=$2
    docker exec mn.${upf_name} ip -f inet addr show ${interface} | sed -En -e 's/.*inet ([0-9.]+).*/\1/p'
}

echo "*** Starting packet capture on all UE devices ***"
# Start packet capture on all UE devices
for i in $(seq 1 40); do
    if [ $i -eq 1 ]; then
        ue_name="UE__1"
    else
        ue_name="UE__${i}"
    fi
    
    echo "Starting capture on ${ue_name}"
    ${ue_name} tshark -i uesimtun0 -w /captures/${ue_name}-packet -F pcapng -a duration:${CAPTURE_DURATION} &
done

# Start packet capture on UPF devices
echo "*** Starting packet capture on UPF devices ***"
upf1 tshark -i ogstun -i ogstun2 -w /captures/upf1-packet -F pcapng -a duration:${CAPTURE_DURATION} &
upf2 tshark -i ogstun -i ogstun2 -w /captures/upf2-packet -F pcapng -a duration:${CAPTURE_DURATION} &

# Wait for capture to start
sleep 5

echo "*** Starting iPerf servers on UPF devices ***"
# Start iPerf servers on UPF for different networks
# For internet APN (10.45.0.0/16)
upf1_ogstun_ip=$(get_upf_ip "upf1" "ogstun")
if [ ! -z "$upf1_ogstun_ip" ]; then
    echo "Starting iPerf server on UPF1 ogstun: $upf1_ogstun_ip"
    docker exec mn.upf1 iperf3 -s -B $upf1_ogstun_ip -p 5001 -f M &
fi

# For internet2 APN (10.46.0.0/16)
upf1_ogstun2_ip=$(get_upf_ip "upf1" "ogstun2")
if [ ! -z "$upf1_ogstun2_ip" ]; then
    echo "Starting iPerf server on UPF1 ogstun2: $upf1_ogstun2_ip"
    docker exec mn.upf1 iperf3 -s -B $upf1_ogstun2_ip -p 5002 -f M &
fi

# For web1 APN (10.47.0.0/16)
upf2_ogstun_ip=$(get_upf_ip "upf2" "ogstun")
if [ ! -z "$upf2_ogstun_ip" ]; then
    echo "Starting iPerf server on UPF2 ogstun: $upf2_ogstun_ip"
    docker exec mn.upf2 iperf3 -s -B $upf2_ogstun_ip -p 5003 -f M &
fi

# For web2 APN (10.48.0.0/16)
upf2_ogstun2_ip=$(get_upf_ip "upf2" "ogstun2")
if [ ! -z "$upf2_ogstun2_ip" ]; then
    echo "Starting iPerf server on UPF2 ogstun2: $upf2_ogstun2_ip"
    docker exec mn.upf2 iperf3 -s -B $upf2_ogstun2_ip -p 5004 -f M &
fi

# Wait for servers to start
sleep 3

echo "*** Starting high-load traffic generation ***"
# Generate high-load traffic from all UE devices
for i in $(seq 1 40); do
    if [ $i -eq 1 ]; then
        ue_name="UE__1"
    else
        ue_name="UE__${i}"
    fi
    
    echo "Generating traffic from ${ue_name}"
    
    # Get UE IP
    ue_ip=$(get_ue_ip "${ue_name}")
    if [ -z "$ue_ip" ]; then
        echo "Warning: Could not get IP for ${ue_name}"
        continue
    fi
    
    # Determine target server based on APN
    # You may need to adjust these IP addresses based on your actual network configuration
    case $i in
        # UEs with internet APN -> UPF1 ogstun (10.45.0.1)
        1|2|3|4|5|31|32|33|34|35)
            target_ip="10.45.0.1"
            target_port="5001"
            ;;
        # UEs with internet2 APN -> UPF1 ogstun2 (10.46.0.1)
        6|7|8|9|10|26|27|28|29|30)
            target_ip="10.46.0.1"
            target_port="5002"
            ;;
        # UEs with web1 APN -> UPF2 ogstun (10.47.0.1)
        11|12|13|14|15|21|22|23|24|25|36|37|38|39|40)
            target_ip="10.47.0.1"
            target_port="5003"
            ;;
        # UEs with web2 APN -> UPF2 ogstun2 (10.48.0.1)
        16|17|18|19|20)
            target_ip="10.48.0.1"
            target_port="5004"
            ;;
        *)
            target_ip="10.45.0.1"
            target_port="5001"
            ;;
    esac
    
    # Generate upstream traffic (multiple parallel streams for higher load)
    for stream in $(seq 1 $PARALLEL_STREAMS); do
        docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port -f M \
            -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -P 1 \
            2>&1 | tee ${LOG_DIR}/${ue_name}-up-stream${stream}.log &
    done
    
    # Generate downstream traffic (multiple parallel streams for higher load)
    for stream in $(seq 1 $PARALLEL_STREAMS); do
        docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port -f M \
            -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -P 1 -R \
            2>&1 | tee ${LOG_DIR}/${ue_name}-down-stream${stream}.log &
    done
    
    # Add UDP traffic for additional load
    docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port -f M \
        -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -u -P 2 \
        2>&1 | tee ${LOG_DIR}/${ue_name}-udp.log &
    
    # Small delay to prevent overwhelming the system
    sleep 0.1
done

echo "*** Generating additional synthetic traffic ***"
# Generate additional synthetic traffic patterns
for i in $(seq 1 40); do
    if [ $i -eq 1 ]; then
        ue_name="UE__1"
    else
        ue_name="UE__${i}"
    fi
    
    # HTTP-like traffic simulation
    docker exec mn.${ue_name} bash -c "
        while true; do
            curl -s http://httpbin.org/bytes/1000000 > /dev/null 2>&1 || true
            sleep 0.1
        done
    " &
    
    # Ping flood for additional packet generation
    docker exec mn.${ue_name} ping -i 0.01 -c 1000 8.8.8.8 > /dev/null 2>&1 &
done

echo "*** Traffic generation started for all UE devices ***"
echo "Waiting for traffic tests to complete..."

# Wait for iPerf tests to complete
sleep $(($IPERF_DURATION + 10))

echo "*** Stopping additional traffic generation ***"
# Kill background processes
pkill -f "curl.*httpbin"
pkill -f "ping.*8.8.8.8"

echo "*** Collecting results ***"
# Wait for packet capture to complete
sleep 10

# Copy packet captures and logs
echo "Copying packet captures..."
for i in $(seq 1 40); do
    if [ $i -eq 1 ]; then
        ue_name="UE__1"
    else
        ue_name="UE__${i}"
    fi
    
    # Copy packet captures
    docker cp mn.${ue_name}:/${ue_name}-packet $RESULTS_DIR/ 2>/dev/null || true
    
    # Copy logs
    docker cp mn.${ue_name}:/${ue_name}-init $RESULTS_DIR/ 2>/dev/null || true
done

# Copy UPF captures
docker cp mn.upf1:/upf1-packet $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.upf2:/upf2-packet $RESULTS_DIR/ 2>/dev/null || true

# Copy initialization logs
docker cp mn.amf1:/amf1-init $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.GNB__1:/GNB__1-init $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.GNB__2:/GNB__2-init $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.GNB__3:/GNB__3-init $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.GNB__4:/GNB__4-init $RESULTS_DIR/ 2>/dev/null || true

echo "*** Generating traffic summary report ***"
cat > $RESULTS_DIR/traffic_summary.txt << EOF
NetFlux5G High Load Traffic Generation Summary
==============================================
Generated: $(date)

Configuration:
- Total UE devices: 40
- Capture duration: ${CAPTURE_DURATION}s
- iPerf duration: ${IPERF_DURATION}s
- Bandwidth limit per UE: ${BANDWIDTH_LIMIT}
- Parallel streams per UE: ${PARALLEL_STREAMS}
- Total parallel streams: $((40 * PARALLEL_STREAMS * 2))

Traffic Distribution:
- UEs 1-5, 31-35: internet APN (10.45.0.1:5001)
- UEs 6-10, 26-30: internet2 APN (10.46.0.1:5002)
- UEs 11-15, 21-25, 36-40: web1 APN (10.47.0.1:5003)
- UEs 16-20: web2 APN (10.48.0.1:5004)

Additional Traffic:
- HTTP simulation on all UEs
- ICMP ping flood on all UEs
- UDP traffic on all UEs

Total estimated peak bandwidth: $((40 * PARALLEL_STREAMS * 2 * 1000))M bps
EOF

echo "*** Traffic generation completed ***"
echo "Results saved to: $RESULTS_DIR"
echo "Summary report: $RESULTS_DIR/traffic_summary.txt"
echo "Check individual UE logs in: $LOG_DIR"
