#!/bin/bash
# NetFlux5G Optimized High Load Traffic Generation Script
# Automated script to generate maximum traffic load across all 40 UE devices
# Optimized for the specific NetFlux5G topology configuration

echo "======================================================================"
echo "NetFlux5G Optimized High Load Traffic Generation Script"
echo "======================================================================"
echo "Starting high-load traffic generation for all 40 UE devices..."
echo "Timestamp: $(date)"

# Configuration
CAPTURE_DURATION=60      # Packet capture duration in seconds
IPERF_DURATION=45        # iPerf test duration in seconds
BANDWIDTH_LIMIT="500M"   # Bandwidth per stream (reduced to prevent overload)
PARALLEL_STREAMS=2       # Number of parallel streams per UE
RESULTS_DIR="/root/hasil_test"
LOG_DIR="/logging"

# Create directories if they don't exist
mkdir -p $RESULTS_DIR $LOG_DIR

# UE Configuration based on NetFlux5G topology
# Mapping UE names to their APN and expected gateway
declare -A UE_CONFIG
UE_CONFIG=(
    # UEs with internet APN -> 10.45.0.1
    ["UE__1"]="internet:10.45.0.1:5001"
    ["UE__2"]="internet:10.45.0.1:5001"
    ["UE__3"]="internet:10.45.0.1:5001"
    ["UE__4"]="internet:10.45.0.1:5001"
    ["UE__5"]="internet:10.45.0.1:5001"
    ["UE__31"]="internet:10.45.0.1:5001"
    ["UE__32"]="internet:10.45.0.1:5001"
    ["UE__33"]="internet:10.45.0.1:5001"
    ["UE__34"]="internet:10.45.0.1:5001"
    ["UE__35"]="internet:10.45.0.1:5001"
    
    # UEs with internet2 APN -> 10.46.0.1
    ["UE__6"]="internet2:10.46.0.1:5002"
    ["UE__7"]="internet2:10.46.0.1:5002"
    ["UE__8"]="internet2:10.46.0.1:5002"
    ["UE__9"]="internet2:10.46.0.1:5002"
    ["UE__10"]="internet2:10.46.0.1:5002"
    ["UE__26"]="internet2:10.46.0.1:5002"
    ["UE__27"]="internet2:10.46.0.1:5002"
    ["UE__28"]="internet2:10.46.0.1:5002"
    ["UE__29"]="internet2:10.46.0.1:5002"
    ["UE__30"]="internet2:10.46.0.1:5002"
    
    # UEs with web1 APN -> 10.47.0.1
    ["UE__11"]="web1:10.47.0.1:5003"
    ["UE__12"]="web1:10.47.0.1:5003"
    ["UE__13"]="web1:10.47.0.1:5003"
    ["UE__14"]="web1:10.47.0.1:5003"
    ["UE__15"]="web1:10.47.0.1:5003"
    ["UE__21"]="web1:10.47.0.1:5003"
    ["UE__22"]="web1:10.47.0.1:5003"
    ["UE__23"]="web1:10.47.0.1:5003"
    ["UE__24"]="web1:10.47.0.1:5003"
    ["UE__25"]="web1:10.47.0.1:5003"
    ["UE__36"]="web1:10.47.0.1:5003"
    ["UE__37"]="web1:10.47.0.1:5003"
    ["UE__38"]="web1:10.47.0.1:5003"
    ["UE__39"]="web1:10.47.0.1:5003"
    ["UE__40"]="web1:10.47.0.1:5003"
    
    # UEs with web2 APN -> 10.48.0.1
    ["UE__16"]="web2:10.48.0.1:5004"
    ["UE__17"]="web2:10.48.0.1:5004"
    ["UE__18"]="web2:10.48.0.1:5004"
    ["UE__19"]="web2:10.48.0.1:5004"
    ["UE__20"]="web2:10.48.0.1:5004"
)

# Function to get UE IP address
get_ue_ip() {
    local ue_name=$1
    docker exec mn.${ue_name} ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p' 2>/dev/null
}

# Function to check if UE is ready
check_ue_ready() {
    local ue_name=$1
    local max_retries=5
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if docker exec mn.${ue_name} ip addr show uesimtun0 >/dev/null 2>&1; then
            return 0
        fi
        retry=$((retry + 1))
        sleep 1
    done
    return 1
}

# Function to start packet capture
start_packet_capture() {
    local device=$1
    local interface=$2
    local output_file=$3
    
    echo "Starting packet capture on ${device} (${interface})"
    ${device} tshark -i ${interface} -w ${output_file} -F pcapng -a duration:${CAPTURE_DURATION} &
}

# Function to start iPerf server
start_iperf_server() {
    local container=$1
    local bind_ip=$2
    local port=$3
    
    echo "Starting iPerf server on ${container} (${bind_ip}:${port})"
    docker exec mn.${container} iperf3 -s -B ${bind_ip} -p ${port} -f M -D &
}

# Function to generate traffic for a UE
generate_ue_traffic() {
    local ue_name=$1
    local config=$2
    
    # Parse configuration
    IFS=':' read -r apn target_ip target_port <<< "$config"
    
    # Check if UE is ready
    if ! check_ue_ready "$ue_name"; then
        echo "Warning: ${ue_name} is not ready, skipping..."
        return 1
    fi
    
    # Get UE IP
    local ue_ip=$(get_ue_ip "$ue_name")
    if [ -z "$ue_ip" ]; then
        echo "Warning: Could not get IP for ${ue_name}, skipping..."
        return 1
    fi
    
    echo "Generating traffic for ${ue_name} (${ue_ip}) -> ${target_ip}:${target_port} (${apn})"
    
    # TCP Upload streams
    for stream in $(seq 1 $PARALLEL_STREAMS); do
        docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port \
            -f M -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -P 1 -i 5 \
            --logfile ${LOG_DIR}/${ue_name}-up-tcp-${stream}.log &
        
        # Small delay to prevent port conflicts
        sleep 0.1
    done
    
    # TCP Download streams
    for stream in $(seq 1 $PARALLEL_STREAMS); do
        docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port \
            -f M -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -P 1 -R -i 5 \
            --logfile ${LOG_DIR}/${ue_name}-down-tcp-${stream}.log &
        
        # Small delay to prevent port conflicts
        sleep 0.1
    done
    
    # UDP streams for additional load
    docker exec mn.${ue_name} iperf3 -c $target_ip -B $ue_ip -p $target_port \
        -f M -b $BANDWIDTH_LIMIT -t $IPERF_DURATION -u -P 1 -i 5 \
        --logfile ${LOG_DIR}/${ue_name}-udp.log &
    
    # Additional background traffic
    docker exec mn.${ue_name} bash -c "
        # Continuous ping
        ping -i 0.1 -c 600 ${target_ip} > ${LOG_DIR}/${ue_name}-ping.log 2>&1 &
        
        # Simulated web traffic
        for i in {1..10}; do
            curl -s --max-time 5 http://httpbin.org/bytes/100000 > /dev/null 2>&1 &
            sleep 0.5
        done
    " &
}

echo "*** Phase 1: Starting packet capture ***"
# Start packet capture on all UE devices
for ue_name in "${!UE_CONFIG[@]}"; do
    start_packet_capture "$ue_name" "uesimtun0" "/captures/${ue_name}-packet" &
done

# Start packet capture on UPF devices
start_packet_capture "upf1" "ogstun" "/captures/upf1-ogstun-packet" &
start_packet_capture "upf1" "ogstun2" "/captures/upf1-ogstun2-packet" &
start_packet_capture "upf2" "ogstun" "/captures/upf2-ogstun-packet" &

echo "*** Phase 2: Starting iPerf servers ***"
# Start iPerf servers on different ports
start_iperf_server "upf1" "10.45.0.1" "5001"  # internet APN
start_iperf_server "upf1" "10.46.0.1" "5002"  # internet2 APN
start_iperf_server "upf2" "10.47.0.1" "5003"  # web1 APN  
start_iperf_server "upf2" "10.48.0.1" "5004"  # web2 APN

# Wait for servers to start
sleep 5

echo "*** Phase 3: Generating high-load traffic ***"
# Generate traffic for all UEs
total_ues=0
successful_ues=0

for ue_name in "${!UE_CONFIG[@]}"; do
    total_ues=$((total_ues + 1))
    config="${UE_CONFIG[$ue_name]}"
    
    if generate_ue_traffic "$ue_name" "$config"; then
        successful_ues=$((successful_ues + 1))
    fi
    
    # Small delay to prevent overwhelming the system
    sleep 0.2
done

echo "*** Traffic generation phase completed ***"
echo "Total UEs: $total_ues"
echo "Successful UEs: $successful_ues"
echo "Failed UEs: $((total_ues - successful_ues))"

# Calculate estimated peak bandwidth
total_tcp_streams=$((successful_ues * PARALLEL_STREAMS * 2))  # Up and down
total_udp_streams=$successful_ues
estimated_peak_mbps=$((total_tcp_streams * 500 + total_udp_streams * 500))  # 500M per stream

echo "*** Traffic Statistics ***"
echo "Total TCP streams: $total_tcp_streams"
echo "Total UDP streams: $total_udp_streams"
echo "Estimated peak bandwidth: ${estimated_peak_mbps}M bps"

echo "*** Waiting for traffic tests to complete ***"
# Wait for iPerf tests to complete
sleep $(($IPERF_DURATION + 15))

echo "*** Phase 4: Collecting results ***"
# Kill any remaining background processes
pkill -f "curl.*httpbin" 2>/dev/null || true
pkill -f "ping.*10\." 2>/dev/null || true

# Wait for packet capture to complete
sleep 15

echo "*** Phase 5: Copying results ***"
# Copy packet captures and logs
for ue_name in "${!UE_CONFIG[@]}"; do
    echo "Copying results for ${ue_name}..."
    
    # Copy packet captures
    docker cp mn.${ue_name}:/captures/${ue_name}-packet $RESULTS_DIR/ 2>/dev/null || true
    
    # Copy initialization logs
    docker cp mn.${ue_name}:/${ue_name}-init $RESULTS_DIR/ 2>/dev/null || true
done

# Copy UPF captures
docker cp mn.upf1:/captures/upf1-ogstun-packet $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.upf1:/captures/upf1-ogstun2-packet $RESULTS_DIR/ 2>/dev/null || true
docker cp mn.upf2:/captures/upf2-ogstun-packet $RESULTS_DIR/ 2>/dev/null || true

# Copy core network logs
docker cp mn.amf1:/amf1-init $RESULTS_DIR/ 2>/dev/null || true
for gnb in GNB__1 GNB__2 GNB__3 GNB__4; do
    docker cp mn.${gnb}:/${gnb}-init $RESULTS_DIR/ 2>/dev/null || true
done

echo "*** Phase 6: Generating comprehensive report ***"
cat > $RESULTS_DIR/netflux5g_traffic_report.txt << EOF
====================================================================
NetFlux5G High Load Traffic Generation Report
====================================================================
Generated: $(date)
Script: capture-packet-high-load.sh

CONFIGURATION
=============
Total UE devices: 40
Successful UEs: $successful_ues
Failed UEs: $((total_ues - successful_ues))
Capture duration: ${CAPTURE_DURATION}s
iPerf duration: ${IPERF_DURATION}s
Bandwidth limit per stream: ${BANDWIDTH_LIMIT}
Parallel streams per UE: ${PARALLEL_STREAMS}
Total TCP streams: $total_tcp_streams
Total UDP streams: $total_udp_streams
Estimated peak bandwidth: ${estimated_peak_mbps}M bps

TRAFFIC DISTRIBUTION
===================
Internet APN (10.45.0.1:5001): UE__1-5, UE__31-35 (10 UEs)
Internet2 APN (10.46.0.1:5002): UE__6-10, UE__26-30 (10 UEs)
Web1 APN (10.47.0.1:5003): UE__11-15, UE__21-25, UE__36-40 (15 UEs)
Web2 APN (10.48.0.1:5004): UE__16-20 (5 UEs)

TRAFFIC TYPES
=============
- TCP Upload streams: $((successful_ues * PARALLEL_STREAMS))
- TCP Download streams: $((successful_ues * PARALLEL_STREAMS))
- UDP streams: $successful_ues
- Continuous ping: $successful_ues
- Simulated web traffic: $successful_ues

RESULTS LOCATION
===============
Results directory: $RESULTS_DIR
Logs directory: $LOG_DIR
Individual UE logs: ${LOG_DIR}/UE__*-*.log
Packet captures: ${RESULTS_DIR}/*-packet

NETWORK TOPOLOGY
===============
UPF1 (upf1): Handles internet and internet2 APNs
UPF2 (upf2): Handles web1 and web2 APNs
gNBs: GNB__1, GNB__2, GNB__3, GNB__4
Total network elements: 40 UEs + 2 UPFs + 4 gNBs + Core network

PERFORMANCE METRICS
==================
Peak theoretical throughput: ${estimated_peak_mbps}M bps
Peak packet rate: ~$(($successful_ues * 2000)) pps
Test duration: ${IPERF_DURATION}s
Data captured: ${CAPTURE_DURATION}s

====================================================================
EOF

echo "*** Traffic generation completed successfully ***"
echo "======================================================================"
echo "Summary:"
echo "  - Total UEs tested: $successful_ues/$total_ues"
echo "  - Peak bandwidth: ${estimated_peak_mbps}M bps"
echo "  - Results saved to: $RESULTS_DIR"
echo "  - Detailed report: $RESULTS_DIR/netflux5g_traffic_report.txt"
echo "  - Individual logs: $LOG_DIR"
echo "======================================================================"
