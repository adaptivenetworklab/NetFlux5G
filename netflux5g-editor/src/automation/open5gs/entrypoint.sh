#!/bin/bash

set -eo pipefail

# Import OVS setup functions
source /opt/open5gs/bin/ovs-setup.sh

# tun iface create
function tun_create {
    echo -e "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    if ! grep "ogstun" /proc/net/dev > /dev/null; then
        echo "Creating ogstun device"
        ip tuntap add name ogstun mode tun
    fi

    if ! grep "ogstun2" /proc/net/dev > /dev/null; then
        echo "Creating ogstun2 device"
        ip tuntap add name ogstun2 mode tun
    fi

    if ! grep "ogstun3" /proc/net/dev > /dev/null; then
        echo "Creating ogstun3 device"
        ip tuntap add name ogstun3 mode tun
    fi

    if ! grep "ogstun4" /proc/net/dev > /dev/null; then
        echo "Creating ogstun4 device"
        ip tuntap add name ogstun4 mode tun
    fi

    ip addr del 10.100.0.1/16 dev ogstun 2> /dev/null || true
    ip addr add 10.100.0.1/16 dev ogstun

    ip addr del 10.200.0.1/16 dev ogstun2 2> /dev/null || true
    ip addr add 10.200.0.1/16 dev ogstun2

    ip addr del 10.51.0.1/16 dev ogstun3 2> /dev/null || true
    ip addr add 10.51.0.1/16 dev ogstun3

    ip addr del 10.52.0.1/16 dev ogstun4 2> /dev/null || true
    ip addr add 10.52.0.1/16 dev ogstun4
    
    ip link set ogstun up
    ip link set ogstun2 up
    ip link set ogstun3 up
    ip link set ogstun4 up
    sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward";
    if [ "$ENABLE_NAT" = true ] ; then
      iptables -t nat -A POSTROUTING -s 10.100.0.0/16 ! -o ogstun -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.200.0.0/16 ! -o ogstun2 -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.51.0.0/16 ! -o ogstun3 -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.52.0.0/16 ! -o ogstun4 -j MASQUERADE
    fi
}
 
 COMMAND=$1

# Setup OpenFlow/OVS integration before starting the service
echo "Initializing Open5GS container with command: $COMMAND"

# Setup OVS if enabled (run in background)
if [ "$OVS_ENABLED" = "true" ]; then
    echo "Setting up OpenFlow/OVS integration..."
    
    # Enable mininet-wifi mode to prevent interface conflicts
    export MININET_WIFI_MODE=true
    export BRIDGE_INTERFACES=""
    
    /opt/open5gs/bin/ovs-setup.sh &
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

if [[ "$COMMAND"  == *"open5gs-pgwd" ]] || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
tun_create
fi

# Temporary patch to solve the case of docker internal dns not resolving "not running" container names.
# Just wait 10 seconds to be "running" and resolvable
if [[ "$COMMAND"  == *"open5gs-pcrfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-mmed" ]] \
    || [[ "$COMMAND"  == *"open5gs-nrfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-scpd" ]] \
    || [[ "$COMMAND"  == *"open5gs-pcfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-hssd" ]] \
    || [[ "$COMMAND"  == *"open5gs-udrd" ]] \
    || [[ "$COMMAND"  == *"open5gs-sgwcd" ]] \
    || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
sleep 10
fi

# Add debugging information for network setup
echo "=== Network Configuration ==="
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
    
    # Check for any OpenFlow version mismatches
    if ovs-vsctl list-br | grep -q "br-open5gs"; then
        echo "Bridge configuration:"
        ovs-vsctl list bridge br-open5gs | grep -E "(protocols|controller)"
        
        echo "Testing OpenFlow connectivity:"
        of_version="OpenFlow13"
        if ovs-ofctl -O $of_version show br-open5gs >/dev/null 2>&1; then
            echo "OpenFlow $of_version connectivity: OK"
        else
            echo "OpenFlow $of_version connectivity: FAILED"
            echo "Trying OpenFlow10..."
            if ovs-ofctl -O OpenFlow10 show br-open5gs >/dev/null 2>&1; then
                echo "OpenFlow10 connectivity: OK"
            else
                echo "OpenFlow10 connectivity: FAILED"
            fi
        fi
    fi
fi
echo "================================"

# Start the main Open5GS service
echo "Starting Open5GS service: $@"
exec "$@"
