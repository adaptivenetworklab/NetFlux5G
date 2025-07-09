#!/bin/bash

set -e

# Import OVS setup functions if available
if [ -f /usr/local/bin/ueransim-ovs-setup.sh ]; then
    source /usr/local/bin/ueransim-ovs-setup.sh
fi

_term() { 
    case "$command" in
    ue) 
        echo "Deleting ue: nr-ue -c ue.yaml"
        for x in $(./usr/local/bin/nr-cli -d); do 
            ./usr/local/bin/nr-cli $x --exec "deregister switch-off"
        done
        echo "UEs switched off"
        sleep 5
        ;;
    *) 
        echo "It isn't necessary to perform any cleanup"
        ;;
    esac
    
    # Clean up OVS if enabled
    if [ "$OVS_ENABLED" = "true" ] && type cleanup_ovs > /dev/null 2>&1; then
        cleanup_ovs
    fi
}

if [ $# -lt 1 ]
then
        echo "Usage : $0 [gnb|ue]"
        exit
fi

command=$1
trap _term SIGTERM
shift

# Setup OpenFlow/OVS integration before starting the service
echo "Initializing UERANSIM container with command: $command"

# Set component type based on command
case "$command" in
    gnb)
        export UERANSIM_COMPONENT="gnb"
        ;;
    ue)
        export UERANSIM_COMPONENT="ue"
        ;;
esac

# Setup OVS if enabled (run in background)
if [ "$OVS_ENABLED" = "true" ]; then
    echo "Setting up OpenFlow/OVS integration for UERANSIM $command..."
    /usr/local/bin/ueransim-ovs-setup.sh &
    OVS_SETUP_PID=$!
    
    # Wait for OVS setup to complete or timeout
    echo "Waiting for OVS setup to complete..."
    wait_count=0
    max_wait=30
    
    while [ $wait_count -lt $max_wait ]; do
        if ! kill -0 $OVS_SETUP_PID 2>/dev/null; then
            echo "OVS setup completed"
            break
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    if [ $wait_count -eq $max_wait ]; then
        echo "WARNING: OVS setup taking longer than expected"
    fi
fi

case "$command" in

ue) 
    GNB_IP=${GNB_IP:-"$(host -4 $GNB_HOSTNAME |awk '/has.*address/{print $NF; exit}')"}
    export GNB_IP
    echo "GNB_IP: $GNB_IP"
    envsubst < /etc/ueransim/ue.yaml > ue.yaml
    
    # Add debugging information for UE network setup
    echo "=== UERANSIM UE Network Configuration ==="
    echo "Network interfaces:"
    ip link show
    echo ""
    echo "IP addresses:"
    ip addr show
    echo ""
    
    if [ "$OVS_ENABLED" = "true" ]; then
        echo "=== OVS Status Check ==="
        echo "OVS bridges:"
        ovs-vsctl list-br 2>/dev/null || echo "OVS not ready yet"
        
        local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
        if ovs-vsctl br-exists $bridge_name 2>/dev/null; then
            echo "UE connected to OVS bridge: $bridge_name"
        fi
    fi
    echo "=============================================="
    
    echo "Launching ue: nr-ue -c ue.yaml"
    nr-ue -c ue.yaml $@ &
    child=$!
    wait "$child"
    ;;
gnb)
    # Setup Access Point functionality if enabled
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Setting up Access Point functionality for gNB..."
        /usr/local/bin/ap-setup.sh
        if [ $? -ne 0 ]; then
            echo "WARNING: AP setup failed, continuing with gNB startup"
        fi
    fi
    
    N2_BIND_IP=${N2_BIND_IP:-"$(ip addr show ${N2_IFACE}  | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    N3_BIND_IP=${N3_BIND_IP:-"$(ip addr show ${N3_IFACE} | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    RADIO_BIND_IP=${RADIO_BIND_IP:-"$(ip addr show ${RADIO_IFACE} | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    AMF_IP=${AMF_IP:-"$(host -4 $AMF_HOSTNAME |awk '/has.*address/{print $NF; exit}')"}
    export N2_BIND_IP N3_BIND_IP RADIO_BIND_IP AMF_IP
    echo "N2_BIND_IP: $N2_BIND_IP"
    echo "N3_BIND_IP: $N3_BIND_IP"
    echo "RADIO_BIND_IP: $RADIO_BIND_IP"
    echo "AMF_IP: $AMF_IP"
    envsubst < /etc/ueransim/gnb.yaml > gnb.yaml
    echo "Launching gnb: nr-gnb -c gnb.yaml"
    
    # Add debugging information for network setup
    echo "=== UERANSIM gNB Network Configuration ==="
    echo "Network interfaces:"
    ip link show
    echo ""
    echo "IP addresses:"
    ip addr show
    echo ""
    echo "Routing table:"
    ip route show
    echo ""

    if [ "$OVS_ENABLED" = "true" ]; then
        echo "=== OVS Status Check ==="
        echo "OVS bridges:"
        ovs-vsctl list-br 2>/dev/null || echo "OVS not ready yet"
        
        # Check for OpenFlow connectivity
        local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
        if ovs-vsctl br-exists $bridge_name 2>/dev/null; then
            echo "Bridge configuration:"
            ovs-vsctl list bridge $bridge_name | grep -E "(protocols|controller)" || true
            
            echo "Testing OpenFlow connectivity:"
            local of_version="OpenFlow13"
            if ovs-ofctl -O $of_version show $bridge_name >/dev/null 2>&1; then
                echo "OpenFlow $of_version connectivity: OK"
            else
                echo "OpenFlow $of_version connectivity: FAILED"
                echo "Trying OpenFlow10..."
                if ovs-ofctl -O OpenFlow10 show $bridge_name >/dev/null 2>&1; then
                    echo "OpenFlow10 connectivity: OK"
                else
                    echo "OpenFlow10 connectivity: FAILED"
                fi
            fi
        fi
    fi
    echo "=============================================="
    
    # Start gNB in background if AP is enabled to allow both services
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Starting gNB in background mode (AP enabled)"
        nr-gnb -c gnb.yaml $@ &
        GNB_PID=$!
        
        # Keep container running and monitor both services
        while true; do
            sleep 10
            
            # Check if gNB is still running
            if ! kill -0 $GNB_PID 2>/dev/null; then
                echo "gNB process has stopped, restarting..."
                nr-gnb -c gnb.yaml $@ &
                GNB_PID=$!
            fi
            
            # Check if hostapd is still running (if AP enabled)
            if ! pgrep -f hostapd > /dev/null; then
                echo "Hostapd process has stopped, attempting restart..."
                /usr/local/bin/ap-setup.sh
            fi
        done
    else
        # Normal gNB operation without AP
        nr-gnb -c gnb.yaml $@
    fi
    ;;
*) echo "unknown component $1 is not a component (gnb or ue). Running $@ as command"
   $@
   ;;
esac