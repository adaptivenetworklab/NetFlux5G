#!/bin/bash

# OpenVSwitch and OpenFlow setup script for Open5GS containers
# This script configures OVS bridges and connects to SDN controllers
# for mininet-wifi DockerSta integration

set -eo pipefail

echo "Starting OVS setup for Open5GS container..."

# Function to check if OVS is enabled
function ovs_enabled {
    if [ "$OVS_ENABLED" = "true" ]; then
        return 0
    else
        return 1
    fi
}

# Function to setup OpenVSwitch bridge
function setup_ovs_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local fail_mode=${OVS_FAIL_MODE:-"standalone"}
    local protocols=${OPENFLOW_PROTOCOLS:-"OpenFlow14"}
    local datapath=${OVS_DATAPATH:-"kernel"}
    
    echo "Setting up OVS bridge: $bridge_name"
    
    # Start OVS services if not running
    if ! pgrep ovs-vswitchd > /dev/null; then
        echo "Starting OVS services..."
        ovsdb-server --detach --remote=punix:/var/run/openvswitch/db.sock \
                     --remote=ptcp:6640 --pidfile --log-file
        ovs-vsctl --no-wait init
        ovs-vswitchd --detach --pidfile --log-file
        
        # Wait for OVS to be ready
        sleep 2
    fi
    
    # Create bridge if it doesn't exist
    if ! ovs-vsctl br-exists $bridge_name; then
        echo "Creating OVS bridge: $bridge_name"
        ovs-vsctl add-br $bridge_name
        
        # Set bridge properties
        ovs-vsctl set bridge $bridge_name fail_mode=$fail_mode
        ovs-vsctl set bridge $bridge_name protocols=$protocols
        
        # Set datapath type if specified
        if [ "$datapath" != "kernel" ]; then
            ovs-vsctl set bridge $bridge_name datapath_type=$datapath
        fi
        
        echo "Bridge $bridge_name created successfully"
    else
        echo "Bridge $bridge_name already exists"
    fi
    
    # Add controller if specified
    if [ -n "$OVS_CONTROLLER" ]; then
        echo "Setting controller: $OVS_CONTROLLER"
        ovs-vsctl set-controller $bridge_name $OVS_CONTROLLER
    elif [ -n "$CONTROLLER_IP" ]; then
        local controller_port=${CONTROLLER_PORT:-"6633"}
        local controller_url="tcp:${CONTROLLER_IP}:${controller_port}"
        echo "Setting controller: $controller_url"
        ovs-vsctl set-controller $bridge_name $controller_url
    fi
    
    # Bring bridge up
    ip link set $bridge_name up
    
    echo "OVS bridge setup completed"
}

# Function to add interfaces to the bridge
function add_interfaces_to_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local network_interface=${NETWORK_INTERFACE:-"eth0"}
    
    # Add main network interface to bridge if specified
    if [ "$BRIDGE_INTERFACES" = "auto" ] || [ "$BRIDGE_INTERFACES" = "$network_interface" ]; then
        if ovs-vsctl list-ports $bridge_name | grep -q "^${network_interface}$"; then
            echo "Interface $network_interface already added to bridge"
        else
            echo "Adding interface $network_interface to bridge $bridge_name"
            
            # Save current IP configuration
            local ip_config=$(ip addr show $network_interface | grep -E "inet [0-9]" | head -1 | awk '{print $2}')
            local gateway=$(ip route show default | awk '/default/ { print $3 }' | head -1)
            
            # Add interface to bridge
            ovs-vsctl add-port $bridge_name $network_interface
            
            # Restore IP configuration to bridge
            if [ -n "$ip_config" ]; then
                ip addr flush dev $network_interface
                ip addr add $ip_config dev $bridge_name
                if [ -n "$gateway" ]; then
                    ip route add default via $gateway
                fi
            fi
            
            echo "Interface $network_interface added to bridge successfully"
        fi
    elif [ -n "$BRIDGE_INTERFACES" ]; then
        # Add specific interfaces if listed
        IFS=',' read -ra INTERFACES <<< "$BRIDGE_INTERFACES"
        for iface in "${INTERFACES[@]}"; do
            iface=$(echo $iface | xargs)  # trim whitespace
            if [ -n "$iface" ] && ip link show "$iface" > /dev/null 2>&1; then
                if ! ovs-vsctl list-ports $bridge_name | grep -q "^${iface}$"; then
                    echo "Adding interface $iface to bridge $bridge_name"
                    ovs-vsctl add-port $bridge_name $iface
                fi
            fi
        done
    fi
}

# Function to configure bridge properties
function configure_bridge_properties {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local priority=${BRIDGE_PRIORITY:-"32768"}
    local stp_enabled=${STP_ENABLED:-"false"}
    
    # Set bridge priority
    ovs-vsctl set bridge $bridge_name other-config:stp-priority=$priority
    
    # Enable/disable STP
    if [ "$stp_enabled" = "true" ]; then
        ovs-vsctl set bridge $bridge_name stp_enable=true
        echo "STP enabled on bridge $bridge_name"
    else
        ovs-vsctl set bridge $bridge_name stp_enable=false
    fi
}

# Function to show OVS status
function show_ovs_status {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    
    echo "=== OVS Status ==="
    echo "Bridges:"
    ovs-vsctl list-br
    
    if ovs-vsctl br-exists $bridge_name; then
        echo ""
        echo "Bridge $bridge_name details:"
        ovs-vsctl show
        
        echo ""
        echo "OpenFlow flows:"
        ovs-ofctl dump-flows $bridge_name
        
        echo ""
        echo "Controller connection:"
        ovs-vsctl get-controller $bridge_name || echo "No controller configured"
    fi
    echo "=================="
}

# Function to cleanup OVS on exit
function cleanup_ovs {
    echo "Cleaning up OVS..."
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    
    if ovs-vsctl br-exists $bridge_name; then
        # Remove controller
        ovs-vsctl del-controller $bridge_name 2>/dev/null || true
        
        # Delete bridge (this also removes all ports)
        ovs-vsctl del-br $bridge_name 2>/dev/null || true
        echo "Bridge $bridge_name removed"
    fi
    
    # Stop OVS services
    pkill ovs-vswitchd 2>/dev/null || true
    pkill ovsdb-server 2>/dev/null || true
}

# Function to wait for network interfaces
function wait_for_interfaces {
    local max_wait=30
    local wait_time=0
    local network_interface=${NETWORK_INTERFACE:-"eth0"}
    
    echo "Waiting for network interface $network_interface..."
    
    while [ $wait_time -lt $max_wait ]; do
        if ip link show $network_interface > /dev/null 2>&1; then
            echo "Network interface $network_interface is ready"
            return 0
        fi
        
        echo "Waiting for interface $network_interface... ($wait_time/$max_wait)"
        sleep 1
        wait_time=$((wait_time + 1))
    done
    
    echo "WARNING: Network interface $network_interface not found after $max_wait seconds"
    return 1
}

# Main execution
function main {
    if ovs_enabled; then
        echo "OVS is enabled, setting up OpenFlow integration..."
        
        # Wait for network interfaces to be available
        wait_for_interfaces
        
        # Setup OVS bridge
        setup_ovs_bridge
        
        # Configure bridge properties
        configure_bridge_properties
        
        # Add interfaces to bridge if auto setup is enabled
        if [ "$OVS_AUTO_SETUP" = "true" ]; then
            add_interfaces_to_bridge
        fi
        
        # Show OVS status
        show_ovs_status
        
        echo "OVS setup completed successfully"
        
        # Setup cleanup on exit
        trap cleanup_ovs EXIT INT TERM
        
    else
        echo "OVS is disabled, skipping OpenFlow setup"
    fi
}

# Execute main function
main

echo "OVS setup script completed"
