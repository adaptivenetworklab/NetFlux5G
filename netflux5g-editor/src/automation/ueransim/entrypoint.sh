#!/bin/bash

set -e

command=$1

# Import OVS setup functions if available
if [ -f /usr/local/bin/ueransim-ovs-setup.sh ]; then
    source /usr/local/bin/ueransim-ovs-setup.sh
fi

# Function to resolve hostname using interface-specific methods
resolve_hostname_via_interface() {
    local hostname=$1
    local interface=$2
    local resolved_ip=""
    
    if [ -n "$hostname" ] && [ -n "$interface" ]; then
        # Method 1: Try ping with interface binding
        resolved_ip=$(ping -I $interface -c 1 -W 1 $hostname 2>/dev/null | grep PING | awk '{print $3}' | tr -d '()' || echo "")
        
        # Method 2: Try interface-specific DNS if ping fails
        if [ -z "$resolved_ip" ] || [ "$resolved_ip" = "" ]; then
            # Try systemd-resolved interface-specific DNS
            local iface_dns=$(resolvectl status $interface 2>/dev/null | grep "DNS Servers:" | awk '{print $3}' | head -1)
            if [ -n "$iface_dns" ]; then
                echo "Using interface-specific DNS: $iface_dns"
                resolved_ip=$(nslookup $hostname $iface_dns 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1 || echo "")
            fi
        fi
        
        # Method 3: Try route-based resolution
        if [ -z "$resolved_ip" ] || [ "$resolved_ip" = "" ]; then
            # Check if there's a specific route for this interface
            local iface_network=$(ip route show dev $interface | grep -E '^[0-9]+\.' | head -1 | awk '{print $1}')
            if [ -n "$iface_network" ]; then
                echo "Checking route-based resolution for network: $iface_network"
                # Try to resolve within the interface's network context
                resolved_ip=$(ip netns exec $(ip netns identify $$) 2>/dev/null nslookup $hostname 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1 || echo "")
            fi
        fi
    fi
    
    echo "$resolved_ip"
}

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
}

if [ $# -lt 1 ]
then
        echo "Usage : $0 [gnb|ue]"
        exit
fi

trap _term SIGTERM
shift

# Setup OpenFlow/OVS integration before starting the service
echo "Initializing UERANSIM container with command: $command"

# Setup OVS if enabled (run in background)
if [ "$OVS_ENABLED" = "true" ]; then
    echo "Setting up OpenFlow/OVS integration for UERANSIM $command..."
    
    # Enable mininet-wifi mode to prevent interface conflicts
    export MININET_WIFI_MODE=true
    export BRIDGE_INTERFACES=""
    
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
else
    echo "OVS integration disabled (OVS_ENABLED not set to 'true')"
    echo "Proceeding with standard UERANSIM configuration..."
fi

case "$command" in

ue) 
    export UERANSIM_COMPONENT="ue"
    export GNB_HOSTNAME RADIO_IFACE GNB_IP
    echo "Get GNB"
    # Check if GNB_IP is already provided as environment variable
    if [ -n "$GNB_IP" ] && [ "$GNB_IP" != "" ]; then
        echo "Using pre-configured GNB_IP: $GNB_IP"
        echo "Skipping hostname resolution for GNB_HOSTNAME: $GNB_HOSTNAME"
    elif [ -n "$GNB_HOSTNAME" ]; then
        echo "Resolving GNB_HOSTNAME: $GNB_HOSTNAME"
        # Try interface-specific hostname resolution first
        if [ -n "$RADIO_IFACE" ]; then
            GNB_IP=$(resolve_hostname_via_interface "$GNB_HOSTNAME" "$RADIO_IFACE")
            export GNB_IP
        fi
        
        # Fallback to standard getent if interface-specific resolution fails
        if [ -z "$GNB_IP" ] || [ "$GNB_IP" = "" ]; then
            echo "Falling back to standard hostname resolution for GNB"
            GNB_IP=${GNB_IP:-"$(getent hosts $GNB_HOSTNAME | awk '{print $1; exit}')"}
            export GNB_IP
        fi
        
        # Additional fallback to nslookup if getent fails
        if [ -z "$GNB_IP" ] || [ "$GNB_IP" = "" ]; then
            GNB_IP=$(nslookup $GNB_HOSTNAME | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
            export GNB_IP
        fi
        
        # Final fallback to ping for local network resolution
        if [ -z "$GNB_IP" ] || [ "$GNB_IP" = "" ]; then
            GNB_IP=$(ping -I $RADIO_IFACE -c 1 -W 1 $GNB_HOSTNAME 2>/dev/null | grep PING | awk '{print $3}' | tr -d '()')
            export GNB_IP
        fi
        
        echo "Resolved GNB_HOSTNAME ($GNB_HOSTNAME) to GNB_IP: $GNB_IP"
    else
        echo "WARNING: Neither GNB_IP nor GNB_HOSTNAME is configured"
    fi
    export GNB_IP
    echo "GNB_HOSTNAME: $GNB_HOSTNAME"
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
    
    echo "Launching ue: nr-ue -c ue.yaml"
    nr-ue -c ue.yaml $@ &
    child=$!
    wait "$child"
    ;;
gnb)
    export UERANSIM_COMPONENT="gnb"
    export AMF_HOSTNAME N2_IFACE N3_IFACE RADIO_IFACE AMF_IP
    echo "Get N2"
    N2_BIND_IP=${N2_BIND_IP:-"$(ip addr show $N2_IFACE | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    echo "Get N3"
    N3_BIND_IP=${N3_BIND_IP:-"$(ip addr show $N3_IFACE | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    echo "Get Radio"
    RADIO_BIND_IP=${RADIO_BIND_IP:-"$(ip addr show $RADIO_IFACE | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    echo "Get AMF"
    # Check if AMF_IP is already provided as environment variable
    if [ -n "$AMF_IP" ] && [ "$AMF_IP" != "" ]; then
        echo "Using pre-configured AMF_IP: $AMF_IP"
        echo "Skipping hostname resolution for AMF_HOSTNAME: $AMF_HOSTNAME"
    elif [ -n "$AMF_HOSTNAME" ]; then
        echo "Resolving AMF_HOSTNAME: $AMF_HOSTNAME"
        # Try interface-specific hostname resolution first
        if [ -n "$RADIO_IFACE" ]; then
            AMF_IP=$(resolve_hostname_via_interface "$AMF_HOSTNAME" "$RADIO_IFACE")
            export AMF_IP
        fi
        
        # Fallback to standard getent if interface-specific resolution fails
        if [ -z "$AMF_IP" ] || [ "$AMF_IP" = "" ]; then
            echo "Falling back to standard hostname resolution for AMF"
            AMF_IP=${AMF_IP:-"$(getent hosts $AMF_HOSTNAME | awk '{print $1; exit}')"}
            export AMF_IP
        fi
        
        # Additional fallback to nslookup if getent fails
        if [ -z "$AMF_IP" ] || [ "$AMF_IP" = "" ]; then
            AMF_IP=$(nslookup $AMF_HOSTNAME | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
            export AMF_IP
        fi
        
        # Final fallback to ping for local network resolution
        if [ -z "$AMF_IP" ] || [ "$AMF_IP" = "" ]; then
            AMF_IP=$(ping -I $RADIO_IFACE -c 1 -W 1 $AMF_HOSTNAME 2>/dev/null | grep PING | awk '{print $3}' | tr -d '()')
            export AMF_IP
        fi
        
        echo "Resolved AMF_HOSTNAME ($AMF_HOSTNAME) to AMF_IP: $AMF_IP"
    else
        echo "WARNING: Neither AMF_IP nor AMF_HOSTNAME is configured"
    fi
    export N2_BIND_IP N3_BIND_IP RADIO_BIND_IP AMF_IP
    echo "N2_BIND_IP: $N2_BIND_IP"
    echo "N3_BIND_IP: $N3_BIND_IP"
    echo "RADIO_BIND_IP: $RADIO_BIND_IP"
    echo "AMF_HOSTNAME: $AMF_HOSTNAME"
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
        bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
        if ovs-vsctl br-exists $bridge_name 2>/dev/null; then
            echo "Bridge configuration:"
            ovs-vsctl list bridge $bridge_name | grep -E "(protocols|controller)" || true
            
            echo "Testing OpenFlow connectivity:"
            of_version="OpenFlow13"
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
    
    # Setup Access Point functionality if enabled
    if [ "$AP_ENABLED" = "true" ]; then
        echo "=== Access Point Setup ==="
        echo "AP_ENABLED is true, setting up access point functionality..."
        if [ -f /usr/local/bin/ap-setup.sh ]; then
            /usr/local/bin/ap-setup.sh &
            ap_setup_pid=$!
            echo "AP setup started with PID: $ap_setup_pid"
        else
            echo "WARNING: ap-setup.sh not found, AP functionality may not work"
        fi
    else
        echo "AP functionality disabled (AP_ENABLED=$AP_ENABLED)"
    fi
    
    # Start gNB normally
    nr-gnb -c gnb.yaml $@
    ;;
*) echo "unknown component $1 is not a component (gnb or ue). Running $@ as command"
   $@
   ;;
esac