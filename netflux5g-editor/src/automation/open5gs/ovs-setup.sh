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

# Function to setup OpenVSwitch bridge with mininet-wifi compatibility
function setup_ovs_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    local fail_mode=${OVS_FAIL_MODE:-"standalone"}
    local protocols=${OPENFLOW_PROTOCOLS:-"OpenFlow10,OpenFlow13,OpenFlow14"}
    local datapath=${OVS_DATAPATH:-"kernel"}
    
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

    if ! ovs-vsctl br-exists $bridge_name; then
        echo "Setting bridge: $bridge_name"

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
        
        # Check if controller looks like a hostname/service name
        if [[ "$OVS_CONTROLLER" =~ ^[a-zA-Z] ]] && [[ ! "$OVS_CONTROLLER" =~ ^tcp: ]]; then
            echo "WARNING: Controller '$OVS_CONTROLLER' appears to be a hostname/service name."
            echo "For Docker environments, ensure the controller container is running and accessible."
            echo "Consider using 'tcp:controller-hostname:port' format for explicit TCP connections."
        fi
        
        # Test controller connectivity
        echo "Testing controller connectivity..."
        if timeout 5 nc -z $(echo $OVS_CONTROLLER | sed 's/tcp://g' | tr ':' ' ') 2>/dev/null; then
            echo "Controller is reachable"
        else
            echo "WARNING: Controller appears unreachable, continuing anyway..."
        fi
    fi   
    
    setup_basic_flows $bridge_name
    
    # Bring bridge up
    ip link set $bridge_name up
    
    echo "OVS bridge setup completed"
}

# Function to show OVS status
function show_ovs_status {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}
    
    echo "=== Open5GS OVS Status ==="
    echo "Bridges:"
    ovs-vsctl list-br
    
    if ovs-vsctl br-exists $bridge_name; then
        echo ""
        echo "Bridge $bridge_name details:"
        ovs-vsctl show
        
        echo ""
        echo "OpenFlow flows:"
        local of_version=$(get_openflow_version $bridge_name)
        echo "Using OpenFlow version: $of_version"
        ovs-ofctl -O $of_version dump-flows $bridge_name 2>/dev/null || {
            echo "Failed to dump flows with $of_version, trying fallback versions..."
            ovs-ofctl -O OpenFlow13 dump-flows $bridge_name 2>/dev/null || \
            ovs-ofctl -O OpenFlow10 dump-flows $bridge_name 2>/dev/null || \
            echo "Unable to dump flows - OpenFlow version mismatch"
        }
        
        echo ""
        echo "Controller connection:"
        ovs-vsctl get-controller $bridge_name || echo "No controller configured"
        
        echo ""
        echo "Bridge interfaces:"
        ovs-vsctl list-ports $bridge_name
    fi
    
    echo ""
    echo "Network interfaces:"
    ip link show | grep -E "^[0-9]+:" | awk '{print $2}' | tr -d ':'
    
    echo "=========================="
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

# Function to cleanup OVS on exit
function cleanup_ovs {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-open5gs"}

    echo "Cleaning up Open5GS OVS..."
    
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

# Main execution
function main {
    if ovs_enabled; then

        # Setup cleanup on exit
        # trap cleanup_ovs EXIT INT TERM

        echo "OVS is enabled, setting up OpenFlow integration for Open5GS..."
        
        # Setup OVS bridge
        setup_ovs_bridge
        
        # Show OVS status
        show_ovs_status
        
        echo "Open5GS OVS setup completed successfully"
        
    else
        echo "OVS is disabled, skipping OpenFlow setup"
    fi
}

# Execute main function
main

echo "Open5GS OVS setup script completed"
