#!/bin/bash

# OpenVSwitch and OpenFlow setup script for UERANSIM containers
# This script configures OVS bridges and connects to SDN controllers
# for mininet-wifi DockerSta integration, similar to Open5GS implementation

set -eo pipefail

echo "Starting OVS setup for UERANSIM container..."

# Function to get compatible OpenFlow version for ovs-ofctl commands
function get_openflow_version {
    local bridge_name=${1:-"br-ueransim"}
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

# Function to setup OpenVSwitch bridge
function setup_ovs_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
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
        
    elif [ -n "$CONTROLLER_IP" ]; then
        local controller_port=${CONTROLLER_PORT:-"6633"}
        local controller_url="tcp:${CONTROLLER_IP}:${controller_port}"
        echo "Setting controller: $controller_url"
        ovs-vsctl set-controller $bridge_name $controller_url
        
        # Test controller connectivity
        echo "Testing controller connectivity..."
        if timeout 5 nc -z $CONTROLLER_IP $controller_port 2>/dev/null; then
            echo "Controller is reachable"
        else
            echo "WARNING: Controller appears unreachable, continuing anyway..."
        fi
    fi
    
    # Bring bridge up
    ip link set $bridge_name up
    
    echo "OVS bridge setup completed"
}

# Function to add interfaces to the bridge
function add_interfaces_to_bridge {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
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

# Function to setup UERANSIM-specific network configurations
function setup_ueransim_network_config {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
    local component_type=${UERANSIM_COMPONENT:-"unknown"}
    
    echo "Setting up UERANSIM-specific network configuration for: $component_type"
    
    case $component_type in
        "gnb")
            # gNB specific network setup
            echo "Configuring gNB networking..."
            
            # Configure wireless interface for AP functionality if enabled
            if [ "$AP_ENABLED" = "true" ]; then
                setup_wireless_ovs_integration
            fi
            ;;
        "ue")
            # UE specific network setup
            echo "Configuring UE networking..."
            
            # UE typically doesn't need special bridge configuration
            # but we can add specific configurations if needed
            ;;
        *)
            echo "Unknown UERANSIM component: $component_type"
            ;;
    esac
}

# Function to setup wireless OVS integration for AP functionality
function setup_wireless_ovs_integration {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
    
    echo "Setting up wireless OVS integration..."
    
    # Check if we have wireless interfaces available
    for iface in $(ls /sys/class/net/ 2>/dev/null | grep -E '^(wlan|hwsim)'); do
        if [ -d "/sys/class/net/$iface/wireless" ]; then
            echo "Found wireless interface: $iface"
            
            # Add wireless interface to bridge if not already added
            if ! ovs-vsctl list-ports $bridge_name | grep -q "^${iface}$"; then
                echo "Adding wireless interface $iface to bridge $bridge_name"
                ovs-vsctl add-port $bridge_name $iface
                
                # Set interface up
                ip link set $iface up
            fi
        fi
    done
    
    # If AP bridge name is different from OVS bridge, create connection
    if [ -n "$AP_BRIDGE_NAME" ] && [ "$AP_BRIDGE_NAME" != "$bridge_name" ]; then
        # Create patch ports to connect AP bridge to OVS bridge
        local patch_to_ap="patch-to-ap"
        local patch_to_ovs="patch-to-ovs"
        
        # Create patch ports if they don't exist
        if ! ovs-vsctl list-ports $bridge_name | grep -q "^${patch_to_ap}$"; then
            echo "Creating patch port from OVS bridge to AP bridge"
            ovs-vsctl add-port $bridge_name $patch_to_ap -- \
                      set interface $patch_to_ap type=patch options:peer=$patch_to_ovs
        fi
        
        if ! ovs-vsctl list-ports $AP_BRIDGE_NAME | grep -q "^${patch_to_ovs}$" 2>/dev/null; then
            # Create AP bridge if it doesn't exist
            if ! ovs-vsctl br-exists $AP_BRIDGE_NAME; then
                ovs-vsctl add-br $AP_BRIDGE_NAME
            fi
            
            echo "Creating patch port from AP bridge to OVS bridge"
            ovs-vsctl add-port $AP_BRIDGE_NAME $patch_to_ovs -- \
                      set interface $patch_to_ovs type=patch options:peer=$patch_to_ap
        fi
    fi
}

# Function to configure bridge properties
function configure_bridge_properties {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
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
    
    # Set additional UERANSIM-specific bridge options
    ovs-vsctl set bridge $bridge_name other-config:hwaddr=$(ip link show eth0 | awk '/ether/ {print $2}')
}

# Function to show OVS status
function show_ovs_status {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
    
    echo "=== UERANSIM OVS Status ==="
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

# Function to setup OpenFlow flows for UERANSIM
function setup_openflow_flows {
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
    local component_type=${UERANSIM_COMPONENT:-"unknown"}
    
    if ! ovs-vsctl br-exists $bridge_name; then
        echo "Bridge $bridge_name does not exist, skipping flow setup"
        return 1
    fi
    
    echo "Setting up OpenFlow flows for UERANSIM $component_type..."
    
    local of_version=$(get_openflow_version $bridge_name)
    
    # Basic flows for normal operation
    case $component_type in
        "gnb")
            # Allow ARP traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,arp,actions=normal" 2>/dev/null || true
            
            # Allow ICMP traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,icmp,actions=normal" 2>/dev/null || true
            
            # Allow N2 interface traffic (AMF communication)
            if [ -n "$AMF_IP" ]; then
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_dst=$AMF_IP,actions=normal" 2>/dev/null || true
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_src=$AMF_IP,actions=normal" 2>/dev/null || true
            fi
            
            # Default flow for other traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=0,actions=normal" 2>/dev/null || true
            ;;
        "ue")
            # Allow ARP traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,arp,actions=normal" 2>/dev/null || true
            
            # Allow ICMP traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,icmp,actions=normal" 2>/dev/null || true
            
            # Allow gNB communication
            if [ -n "$GNB_IP" ]; then
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_dst=$GNB_IP,actions=normal" 2>/dev/null || true
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_src=$GNB_IP,actions=normal" 2>/dev/null || true
            fi
            
            # Default flow for other traffic
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=0,actions=normal" 2>/dev/null || true
            ;;
    esac
    
    echo "OpenFlow flows configured for $component_type"
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
    echo "Cleaning up UERANSIM OVS..."
    local bridge_name=${OVS_BRIDGE_NAME:-"br-ueransim"}
    
    if ovs-vsctl br-exists $bridge_name; then
        # Remove controller
        ovs-vsctl del-controller $bridge_name 2>/dev/null || true
        
        # Delete bridge (this also removes all ports)
        ovs-vsctl del-br $bridge_name 2>/dev/null || true
        echo "Bridge $bridge_name removed"
    fi
    
    # Clean up AP bridge if it's separate
    if [ -n "$AP_BRIDGE_NAME" ] && [ "$AP_BRIDGE_NAME" != "$bridge_name" ]; then
        if ovs-vsctl br-exists $AP_BRIDGE_NAME; then
            ovs-vsctl del-br $AP_BRIDGE_NAME 2>/dev/null || true
            echo "AP bridge $AP_BRIDGE_NAME removed"
        fi
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
        echo "OVS is enabled, setting up OpenFlow integration for UERANSIM..."
        
        # Wait for network interfaces to be available
        wait_for_interfaces
        
        # Setup OVS bridge
        setup_ovs_bridge
        
        # Configure bridge properties
        configure_bridge_properties
        
        # Setup UERANSIM-specific network configuration
        setup_ueransim_network_config
        
        # Add interfaces to bridge if auto setup is enabled
        if [ "$OVS_AUTO_SETUP" = "true" ]; then
            add_interfaces_to_bridge
        fi
        
        # Setup basic OpenFlow flows
        # setup_openflow_flows
        
        # Show OVS status
        show_ovs_status
        
        echo "UERANSIM OVS setup completed successfully"
        
        # Setup cleanup on exit
        # trap cleanup_ovs EXIT INT TERM
        
    else
        echo "OVS is disabled, skipping OpenFlow setup"
    fi
}

# Execute main function
main

echo "UERANSIM OVS setup script completed"