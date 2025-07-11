#!/bin/bash

# OpenVSwitch and OpenFlow setup script for Open5GS containers
# Enhanced version for mininet-wifi integration

set -eo pipefail

echo "Starting OVS setup for Open5GS container..."

# Function to get compatible OpenFlow version for ovs-ofctl commands
function get_openflow_version {
    local bridge_name=${1:-"br-open5gs"}
    local protocols
    
    # Get the protocols configured on the bridge
    protocols=$(ovs-vsctl get bridge $bridge_name protocols 2>/dev/null | tr -d '[]"' | tr ',' ' ')
    
    # Try different OpenFlow versions in order of preference
    for proto in $protocols; do
        case $proto in
            "OpenFlow10")
                echo "OpenFlow10"
                return 0
                ;;
            "OpenFlow13")
                echo "OpenFlow13"  
                return 0
                ;;
            "OpenFlow14")
                echo "OpenFlow14"
                return 0
                ;;
        esac
    done
    
    # Default fallback
    echo "OpenFlow13"
}

# Function to check if OVS is enabled
function ovs_enabled {
    if [ "$OVS_ENABLED" = "true" ]; then
        return 0
    else
        return 1
    fi
}

# Function to add basic flows for connectivity when controller is not available
function setup_basic_flows {
    local bridge_name=$1
    
    echo "Setting up basic flows for bridge: $bridge_name"
    
    # Get OpenFlow version
    local of_version="OpenFlow13"
    local protocols=$(ovs-vsctl get bridge $bridge_name protocols 2>/dev/null | tr -d '[]"' | tr ',' ' ')
    
    for proto in $protocols; do
        case $proto in
            "OpenFlow10")
                of_version="OpenFlow10"
                break
                ;;
            "OpenFlow13")
                of_version="OpenFlow13"  
                break
                ;;
            "OpenFlow14")
                of_version="OpenFlow14"
                break
                ;;
        esac
    done
    
    echo "Using OpenFlow version: $of_version"
    
    # Clear existing flows
    ovs-ofctl -O $of_version del-flows $bridge_name
    
    # Add basic forwarding flows
    case $of_version in
        "OpenFlow10")
            # OpenFlow 1.0 basic forwarding
            ovs-ofctl add-flow $bridge_name "priority=100,actions=normal"
            ;;
        "OpenFlow13"|"OpenFlow14")
            # OpenFlow 1.3+ with table-based forwarding
            ovs-ofctl -O $of_version add-flow $bridge_name "table=0,priority=100,actions=normal"
            ;;
    esac
    
    echo "Basic flows added to bridge: $bridge_name"
}

# Function to setup OpenVSwitch bridge with mininet-wifi compatibility
function setup_ovs_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local fail_mode=${OVS_FAIL_MODE:-"standalone"}
    local protocols=${OPENFLOW_PROTOCOLS:-"OpenFlow10,OpenFlow13,OpenFlow14"}
    local datapath=${OVS_DATAPATH:-"kernel"}
    
    echo "Setting up OVS bridge: $bridge_name"
    
    # Start OVS services if not running
    if ! pgrep ovs-vswitchd > /dev/null; then
        echo "Starting OVS services..."
        
        # Create OVS database if it doesn't exist
        if [ ! -f /etc/openvswitch/conf.db ]; then
            echo "Creating OVS database..."
            ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema
        fi

        # Start OVS database server
        ovsdb-server --detach --remote=punix:/var/run/openvswitch/db.sock \
                     --remote=ptcp:6640 --pidfile --log-file \
                     --remote=db:Open_vSwitch,Open_vSwitch,manager_options
        
        # Initialize database
        ovs-vsctl --no-wait init
        
        # Start OVS switch daemon
        ovs-vswitchd --detach --pidfile --log-file
        
        # Wait for OVS to be ready
        sleep 3
        
        echo "OVS services started successfully"
    else
        echo "OVS services already running"
    fi
    
    # In mininet-wifi mode, don't create separate bridges
    # Let mininet-wifi manage the bridges and just configure flows
    if [ "$MININET_WIFI_MODE" = "true" ]; then
        echo "Mininet-wifi mode: skipping bridge creation, configuring for existing topology"
        
        # Find the bridge that this container's interface is connected to
        local container_bridge=""
        for iface in $(ip link show | grep -E '^[0-9]+:' | awk -F': ' '{print $2}' | grep '^eth'); do
            # Check if this interface is connected to an OVS bridge
            local connected_bridge=$(ovs-vsctl port-to-br $iface 2>/dev/null || echo "")
            if [ -n "$connected_bridge" ]; then
                container_bridge=$connected_bridge
                echo "Found container connected to bridge: $container_bridge via interface: $iface"
                break
            fi
        done
        
        if [ -n "$container_bridge" ]; then
            # Set controller on the existing bridge if specified
            if [ -n "$OVS_CONTROLLER" ]; then
                echo "Setting controller on existing bridge: $container_bridge"
                ovs-vsctl set-controller $container_bridge $OVS_CONTROLLER
                
                # Set fail mode
                ovs-vsctl set bridge $container_bridge fail_mode=$fail_mode
                
                # Test controller connectivity
                echo "Testing controller connectivity..."
                local controller_host=$(echo $OVS_CONTROLLER | sed 's/tcp://g' | cut -d':' -f1)
                local controller_port=$(echo $OVS_CONTROLLER | sed 's/tcp://g' | cut -d':' -f2)
                
                if timeout 5 nc -z $controller_host $controller_port 2>/dev/null; then
                    echo "Controller is reachable"
                else
                    echo "WARNING: Controller appears unreachable, continuing anyway..."
                    # Add basic flows for connectivity when controller is not available
                    setup_basic_flows $container_bridge
                fi
            else
                # Add basic flows for connectivity if no controller
                setup_basic_flows $container_bridge
            fi
            
        else
            echo "Container not connected to any OVS bridge - normal operation"
        fi
        
        return 0
    fi
    
    # Standard OVS bridge creation (when not in mininet-wifi mode)
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
        
        # Test controller connectivity
        echo "Testing controller connectivity..."
        local controller_host=$(echo $OVS_CONTROLLER | sed 's/tcp://g' | cut -d':' -f1)
        local controller_port=$(echo $OVS_CONTROLLER | sed 's/tcp://g' | cut -d':' -f2)
        
        if timeout 5 nc -z $controller_host $controller_port 2>/dev/null; then
            echo "Controller is reachable"
        else
            echo "WARNING: Controller appears unreachable, continuing anyway..."
        fi
    fi
    
    # Bring bridge up
    ip link set $bridge_name up
    
    echo "OVS bridge setup completed"
}

# Function to add interfaces to the bridge (only if not in mininet-wifi mode)
function add_interfaces_to_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local network_interface=${NETWORK_INTERFACE:-"eth0"}
    
    # Skip interface addition in mininet-wifi mode
    if [ "$MININET_WIFI_MODE" = "true" ]; then
        echo "Mininet-wifi mode: skipping interface addition"
        return 0
    fi
    
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

# Main execution
if ovs_enabled; then
    echo "OVS enabled for Open5GS container"
    setup_ovs_bridge
    add_interfaces_to_bridge
    
    echo "=== OVS Configuration Summary ==="
    echo "Mode: ${MININET_WIFI_MODE:-standard}"
    echo "Bridge: ${OVS_BRIDGE_NAME:-br-open5gs}"
    echo "Controller: ${OVS_CONTROLLER:-none}"
    echo "Fail mode: ${OVS_FAIL_MODE:-standalone}"
    echo "================================="
else
    echo "OVS not enabled for this container"
fi

echo "OVS setup completed"
