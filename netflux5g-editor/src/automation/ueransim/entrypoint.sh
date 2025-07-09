#!/bin/bash

set -e

# Import OVS setup functions if available
if [ -f /usr/local/bin/ueransim-ovs-setup.sh ]; then
    source /usr/local/bin/ueransim-ovs-setup.sh
fi

# Global variables for process management
UERANSIM_PID=""
OVS_SETUP_PID=""
AP_SETUP_PID=""

_term() { 
    echo "Received SIGTERM, cleaning up..."
    
    case "$command" in
    ue) 
        echo "Cleaning up UE connections..."
        if [ -n "$UERANSIM_PID" ] && kill -0 "$UERANSIM_PID" 2>/dev/null; then
            kill -TERM "$UERANSIM_PID" 2>/dev/null || true
            wait "$UERANSIM_PID" 2>/dev/null || true
        fi
        
        # Clean up UE registrations using nr-cli
        for x in $(nr-cli -d 2>/dev/null || true); do 
            nr-cli $x --exec "deregister switch-off" 2>/dev/null || true
        done
        echo "UE cleanup completed"
        ;;
    gnb) 
        echo "Cleaning up gNB..."
        if [ -n "$UERANSIM_PID" ] && kill -0 "$UERANSIM_PID" 2>/dev/null; then
            kill -TERM "$UERANSIM_PID" 2>/dev/null || true
            wait "$UERANSIM_PID" 2>/dev/null || true
        fi
        
        # Clean up AP if running
        if [ "$AP_ENABLED" = "true" ]; then
            pkill -f hostapd 2>/dev/null || true
            echo "AP cleanup completed"
        fi
        ;;
    *) 
        echo "Cleaning up processes..."
        if [ -n "$UERANSIM_PID" ] && kill -0 "$UERANSIM_PID" 2>/dev/null; then
            kill -TERM "$UERANSIM_PID" 2>/dev/null || true
        fi
        ;;
    esac
    
    # Clean up OVS if enabled
    if [ "$OVS_ENABLED" = "true" ] && type cleanup_ovs > /dev/null 2>&1; then
        echo "Cleaning up OVS..."
        cleanup_ovs 2>/dev/null || true
    fi
    
    exit 0
}

if [ $# -lt 1 ]; then
    echo "Usage: $0 [gnb|ue] [additional_args...]"
    echo "  gnb - Start gNB (5G Base Station)"
    echo "  ue  - Start UE (User Equipment)"
    exit 1
fi

command=$1
trap _term SIGTERM SIGINT
shift

# Setup OpenFlow/OVS integration before starting the service
echo "=== Initializing UERANSIM container ==="
echo "Component: $command"
echo "OVS Enabled: ${OVS_ENABLED:-false}"
echo "AP Enabled: ${AP_ENABLED:-false}"
echo "==========================================="

# Set component type based on command
case "$command" in
    gnb)
        export UERANSIM_COMPONENT="gnb"
        ;;
    ue)
        export UERANSIM_COMPONENT="ue"
        ;;
    *)
        echo "Error: Unknown component '$command'"
        exit 1
        ;;
esac

# Function to wait for process setup
wait_for_setup() {
    local setup_pid=$1
    local setup_name=$2
    local max_wait=${3:-30}
    
    echo "Waiting for $setup_name to complete..."
    local wait_count=0
    
    while [ $wait_count -lt $max_wait ]; do
        if ! kill -0 $setup_pid 2>/dev/null; then
            echo "$setup_name setup completed"
            return 0
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    echo "WARNING: $setup_name setup taking longer than expected"
    return 1
}

# Setup OVS if enabled (run in background)
if [ "$OVS_ENABLED" = "true" ]; then
    echo "Setting up OpenFlow/OVS integration for UERANSIM $command..."
    /usr/local/bin/ueransim-ovs-setup.sh &
    OVS_SETUP_PID=$!
    wait_for_setup $OVS_SETUP_PID "OVS"
fi

case "$command" in

ue) 
    # Resolve GNB IP address
    if [ -z "$GNB_IP" ]; then
        if [ -n "$GNB_HOSTNAME" ]; then
            GNB_IP=$(host -4 "$GNB_HOSTNAME" 2>/dev/null | awk '/has.*address/{print $NF; exit}')
            if [ -z "$GNB_IP" ]; then
                echo "WARNING: Could not resolve $GNB_HOSTNAME, using localhost"
                GNB_IP="127.0.0.1"
            fi
        else
            GNB_IP="127.0.0.1"
        fi
    fi
    export GNB_IP
    
    echo "=== UERANSIM UE Configuration ==="
    echo "GNB Hostname: ${GNB_HOSTNAME:-localhost}"
    echo "GNB IP: $GNB_IP"
    echo "================================="
    
    # Generate UE configuration
    envsubst < /etc/ueransim/ue.yaml > ue.yaml
    
    # Debug network information
    echo "=== Network Configuration Debug ==="
    echo "Network interfaces:"
    ip link show | grep -E "^[0-9]+: |inet " || true
    echo ""
    echo "IP addresses:"
    ip addr show | grep -E "^[0-9]+: |inet " || true
    echo ""
    
    if [ "$OVS_ENABLED" = "true" ]; then
        echo "=== OVS Status Check ==="
        local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
        if command -v ovs-vsctl >/dev/null 2>&1; then
            echo "OVS bridges:"
            ovs-vsctl list-br 2>/dev/null || echo "No OVS bridges found"
            
            if ovs-vsctl br-exists "$bridge_name" 2>/dev/null; then
                echo "UE connected to OVS bridge: $bridge_name"
                ovs-vsctl list-ports "$bridge_name" 2>/dev/null || true
            fi
        else
            echo "OVS tools not available"
        fi
    fi
    echo "===================================="
    
    echo "Launching UE: nr-ue -c ue.yaml $@"
    nr-ue -c ue.yaml "$@" &
    UERANSIM_PID=$!
    wait "$UERANSIM_PID"
    ;;

gnb)
    # Setup Access Point functionality if enabled
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Setting up Access Point functionality for gNB..."
        /usr/local/bin/ap-setup.sh &
        AP_SETUP_PID=$!
        wait_for_setup $AP_SETUP_PID "AP" 10
    fi
    
    # Get network interface information for gNB
    N2_BIND_IP=${N2_BIND_IP:-"$(ip addr show "${N2_IFACE:-eth0}" 2>/dev/null | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}' | head -1 | cut -c 6-)"}
    N3_BIND_IP=${N3_BIND_IP:-"$(ip addr show "${N3_IFACE:-eth0}" 2>/dev/null | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}' | head -1 | cut -c 6-)"}
    RADIO_BIND_IP=${RADIO_BIND_IP:-"$(ip addr show "${RADIO_IFACE:-eth0}" 2>/dev/null | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}' | head -1 | cut -c 6-)"}
    
    # Resolve AMF IP
    if [ -z "$AMF_IP" ]; then
        if [ -n "$AMF_HOSTNAME" ]; then
            AMF_IP=$(host -4 "$AMF_HOSTNAME" 2>/dev/null | awk '/has.*address/{print $NF; exit}')
            if [ -z "$AMF_IP" ]; then
                echo "WARNING: Could not resolve $AMF_HOSTNAME, using default"
                AMF_IP="10.0.0.5"
            fi
        else
            AMF_IP="10.0.0.5"
        fi
    fi
    
    export N2_BIND_IP N3_BIND_IP RADIO_BIND_IP AMF_IP
    
    echo "=== UERANSIM gNB Configuration ==="
    echo "AMF Hostname: ${AMF_HOSTNAME:-amf}"
    echo "AMF IP: $AMF_IP"
    echo "N2 Interface: ${N2_IFACE:-eth0} (IP: $N2_BIND_IP)"
    echo "N3 Interface: ${N3_IFACE:-eth0} (IP: $N3_BIND_IP)"
    echo "Radio Interface: ${RADIO_IFACE:-eth0} (IP: $RADIO_BIND_IP)"
    echo "================================="
    
    # Generate gNB configuration
    envsubst < /etc/ueransim/gnb.yaml > gnb.yaml
    
    # Debug network information
    echo "=== Network Configuration Debug ==="
    echo "Network interfaces:"
    ip link show | grep -E "^[0-9]+: |inet " || true
    echo ""
    echo "IP addresses:"
    ip addr show | grep -E "^[0-9]+: |inet " || true
    echo ""
    echo "Routing table:"
    ip route show | head -10 || true
    echo ""

    if [ "$OVS_ENABLED" = "true" ]; then
        echo "=== OVS Status Check ==="
        local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
        if command -v ovs-vsctl >/dev/null 2>&1; then
            echo "OVS bridges:"
            ovs-vsctl list-br 2>/dev/null || echo "No OVS bridges found"
            
            if ovs-vsctl br-exists "$bridge_name" 2>/dev/null; then
                echo "Bridge $bridge_name configuration:"
                ovs-vsctl list bridge "$bridge_name" | grep -E "(protocols|controller|fail_mode)" || true
                
                # Test OpenFlow connectivity
                echo "Testing OpenFlow connectivity:"
                local of_version="OpenFlow13"
                if timeout 5 ovs-ofctl -O "$of_version" show "$bridge_name" >/dev/null 2>&1; then
                    echo "OpenFlow $of_version connectivity: OK"
                else
                    echo "OpenFlow $of_version connectivity: FAILED"
                    echo "Trying OpenFlow10..."
                    if timeout 5 ovs-ofctl -O OpenFlow10 show "$bridge_name" >/dev/null 2>&1; then
                        echo "OpenFlow10 connectivity: OK"
                    else
                        echo "OpenFlow10 connectivity: FAILED"
                    fi
                fi
            fi
        else
            echo "OVS tools not available"
        fi
    fi
    echo "===================================="
    
    # Start gNB with appropriate process management
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Starting gNB in background mode (AP enabled)"
        nr-gnb -c gnb.yaml "$@" &
        UERANSIM_PID=$!
        
        # Monitor both gNB and AP services
        while true; do
            # Check if gNB is still running
            if ! kill -0 $UERANSIM_PID 2>/dev/null; then
                echo "gNB process has stopped, restarting..."
                nr-gnb -c gnb.yaml "$@" &
                UERANSIM_PID=$!
            fi
            
            # Check if hostapd is still running (if AP enabled)
            if [ "$AP_ENABLED" = "true" ] && ! pgrep -f hostapd > /dev/null 2>&1; then
                echo "Hostapd process has stopped, attempting restart..."
                /usr/local/bin/ap-setup.sh &
            fi
            
            sleep 10
        done
    else
        # Normal gNB operation without AP
        echo "Starting gNB: nr-gnb -c gnb.yaml $@"
        nr-gnb -c gnb.yaml "$@" &
        UERANSIM_PID=$!
        wait "$UERANSIM_PID"
    fi
    ;;

*) 
    echo "ERROR: Unknown component '$command'. Supported: gnb, ue"
    echo "Running command directly: $command $@"
    exec "$command" "$@"
    ;;

esac
