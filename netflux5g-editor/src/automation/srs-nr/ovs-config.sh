#!/bin/bash

# UERANSIM Component OVS Configuration Helper
# This script helps configure OpenFlow settings for specific UERANSIM components

set -eo pipefail

COMPONENT_TYPE=""
CONTROLLER_IP=""
CONTROLLER_PORT="6633"
BRIDGE_NAME=""

# Function to show usage
function show_usage {
    cat << EOF
Usage: $0 [OPTIONS]

Configure OpenFlow/OVS for UERANSIM components in mininet-wifi

OPTIONS:
    -c, --component     UERANSIM component type (gnb, ue)
    --controller-ip     SDN Controller IP address
    --controller-port   SDN Controller port (default: 6633)
    --bridge-name       OVS bridge name (default: br-<component>)
    --protocols         OpenFlow protocols (default: OpenFlow14)
    --fail-mode         Bridge fail mode (default: standalone)
    --enable            Enable OVS for this component
    --disable           Disable OVS for this component
    --status            Show OVS status
    -h, --help          Show this help message

EXAMPLES:
    # Enable OVS for gNB with controller
    $0 --component gnb --controller-ip 192.168.1.100 --enable
    
    # Configure UE with custom bridge
    $0 --component ue --controller-ip 10.0.0.1 --bridge-name br-ue-data --enable
    
    # Show current OVS status
    $0 --status
    
    # Disable OVS for gNB
    $0 --component gnb --disable

EOF
}

# Function to configure component-specific OVS settings
function configure_component_ovs {
    local component=$1
    local action=$2
    
    # Set component-specific defaults
    case $component in
        "gnb")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-gnb"}
            export UERANSIM_COMPONENT="gnb"
            ;;
        "ue")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-ue"}
            export UERANSIM_COMPONENT="ue"
            ;;
        *)
            BRIDGE_NAME=${BRIDGE_NAME:-"br-${component}"}
            export UERANSIM_COMPONENT="$component"
            ;;
    esac
    
    if [ "$action" = "enable" ]; then
        echo "Enabling OVS for UERANSIM component: $component"
        export OVS_ENABLED=true
        export OVS_BRIDGE_NAME=$BRIDGE_NAME
        
        # For mininet-wifi integration, disable automatic interface bridging
        export MININET_WIFI_MODE=true
        export BRIDGE_INTERFACES=""
        
        if [ -n "$CONTROLLER_IP" ]; then
            export OVS_CONTROLLER="tcp:${CONTROLLER_IP}:${CONTROLLER_PORT}"
            echo "Controller configured: $OVS_CONTROLLER"
        fi
        
        # Run OVS setup
        /usr/local/bin/ueransim-ovs-setup.sh
        
    elif [ "$action" = "disable" ]; then
        echo "Disabling OVS for UERANSIM component: $component"
        export OVS_ENABLED=false
        
        # Remove bridge if it exists
        if ovs-vsctl br-exists $BRIDGE_NAME 2>/dev/null; then
            ovs-vsctl del-br $BRIDGE_NAME
            echo "Removed bridge: $BRIDGE_NAME"
        fi
        
        # Remove AP bridge if it exists and is separate
        if [ "$component" = "gnb" ] && [ "$AP_ENABLED" = "true" ]; then
            local ap_bridge=${AP_BRIDGE_NAME:-"br-gnb-ap"}
            if [ "$ap_bridge" != "$BRIDGE_NAME" ] && ovs-vsctl br-exists $ap_bridge 2>/dev/null; then
                ovs-vsctl del-br $ap_bridge
                echo "Removed AP bridge: $ap_bridge"
            fi
        fi
    fi
}

# Function to show OVS status for UERANSIM
function show_ovs_status {
    echo "=== UERANSIM OVS Status ==="
    
    if pgrep ovs-vswitchd > /dev/null; then
        echo "OVS Status: Running"
        echo ""
        echo "Bridges:"
        ovs-vsctl list-br 2>/dev/null || echo "No bridges found"
        
        echo ""
        echo "Bridge details:"
        for bridge in $(ovs-vsctl list-br 2>/dev/null); do
            echo "Bridge: $bridge"
            echo "  Controller: $(ovs-vsctl get-controller $bridge 2>/dev/null || echo 'None')"
            echo "  Fail mode: $(ovs-vsctl get bridge $bridge fail_mode 2>/dev/null || echo 'Unknown')"
            echo "  Protocols: $(ovs-vsctl get bridge $bridge protocols 2>/dev/null || echo 'Unknown')"
            echo "  Ports: $(ovs-vsctl list-ports $bridge 2>/dev/null | tr '\n' ' ')"
            echo ""
        done
        
        echo "OpenFlow flows:"
        for bridge in $(ovs-vsctl list-br 2>/dev/null); do
            echo "Bridge $bridge flows:"
            # Try different OpenFlow versions
            ovs-ofctl -O OpenFlow14 dump-flows $bridge 2>/dev/null || \
            ovs-ofctl -O OpenFlow13 dump-flows $bridge 2>/dev/null || \
            ovs-ofctl -O OpenFlow10 dump-flows $bridge 2>/dev/null || \
            echo "  No flows or version mismatch"
            echo ""
        done
        
    else
        echo "OVS Status: Not running"
    fi
    
    echo "UERANSIM environment variables:"
    env | grep -E "(UERANSIM|N2_|N3_|RADIO_|GNB_|UE_|AMF_|AP_|OVS_)" | sort
    
    echo ""
    echo "Network interfaces:"
    ip link show | grep -E "^[0-9]+:" | awk '{print $2}' | tr -d ':'
    
    echo ""
    echo "Wireless interfaces:"
    for iface in $(ls /sys/class/net/ 2>/dev/null); do
        if [ -d "/sys/class/net/$iface/wireless" ]; then
            echo "  $iface (wireless)"
        fi
    done
    
    echo "=============================="
}

# Function to test OpenFlow connectivity
function test_openflow_connectivity {
    local component=${1:-"unknown"}
    local bridge_name=${BRIDGE_NAME:-"br-${component}"}
    
    if ! ovs-vsctl br-exists $bridge_name 2>/dev/null; then
        echo "Bridge $bridge_name does not exist"
        return 1
    fi
    
    echo "Testing OpenFlow connectivity for $component..."
    
    local controller=$(ovs-vsctl get-controller $bridge_name 2>/dev/null)
    if [ -n "$controller" ] && [ "$controller" != "[]" ]; then
        echo "Controller configured: $controller"
        
        # Extract IP and port from controller string
        local controller_clean=$(echo $controller | sed 's/tcp://g' | tr -d '"[]')
        local controller_ip=$(echo $controller_clean | cut -d: -f1)
        local controller_port=$(echo $controller_clean | cut -d: -f2)
        
        if timeout 5 nc -z $controller_ip $controller_port 2>/dev/null; then
            echo "✓ Controller is reachable"
        else
            echo "✗ Controller is unreachable"
        fi
        
        # Test OpenFlow versions
        for version in OpenFlow14 OpenFlow13 OpenFlow10; do
            if ovs-ofctl -O $version show $bridge_name >/dev/null 2>&1; then
                echo "✓ $version is working"
            else
                echo "✗ $version failed"
            fi
        done
    else
        echo "No controller configured"
    fi
}

# Function to setup default flows for UERANSIM components
function setup_default_flows {
    local component=$1
    local bridge_name=${BRIDGE_NAME:-"br-${component}"}
    
    if ! ovs-vsctl br-exists $bridge_name 2>/dev/null; then
        echo "Bridge $bridge_name does not exist"
        return 1
    fi
    
    echo "Setting up default flows for UERANSIM $component..."
    
    # Determine OpenFlow version
    local of_version="OpenFlow13"
    if ovs-ofctl -O OpenFlow14 show $bridge_name >/dev/null 2>&1; then
        of_version="OpenFlow14"
    elif ovs-ofctl -O OpenFlow10 show $bridge_name >/dev/null 2>&1; then
        of_version="OpenFlow10"
    fi
    
    echo "Using OpenFlow version: $of_version"
    
    # Clear existing flows
    ovs-ofctl -O $of_version del-flows $bridge_name
    
    # Add default flows based on component type
    case $component in
        "gnb")
            # High priority flows for 5G control plane
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,arp,actions=normal"
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,icmp,actions=normal"
            
            # N2 interface (AMF) traffic
            if [ -n "$AMF_IP" ]; then
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_dst=$AMF_IP,actions=normal"
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_src=$AMF_IP,actions=normal"
            fi
            
            # SCTP traffic for 5G signaling
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1500,ip,nw_proto=132,actions=normal"
            
            # Default flow
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=0,actions=normal"
            ;;
        "ue")
            # UE specific flows
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,arp,actions=normal"
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=1000,icmp,actions=normal"
            
            # gNB communication
            if [ -n "$GNB_IP" ]; then
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_dst=$GNB_IP,actions=normal"
                ovs-ofctl -O $of_version add-flow $bridge_name "priority=2000,ip,nw_src=$GNB_IP,actions=normal"
            fi
            
            # Default flow
            ovs-ofctl -O $of_version add-flow $bridge_name "priority=0,actions=normal"
            ;;
    esac
    
    echo "Default flows configured for $component"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--component)
            COMPONENT_TYPE="$2"
            shift 2
            ;;
        --controller-ip)
            CONTROLLER_IP="$2"
            shift 2
            ;;
        --controller-port)
            CONTROLLER_PORT="$2"
            shift 2
            ;;
        --bridge-name)
            BRIDGE_NAME="$2"
            shift 2
            ;;
        --protocols)
            export OPENFLOW_PROTOCOLS="$2"
            shift 2
            ;;
        --fail-mode)
            export OVS_FAIL_MODE="$2"
            shift 2
            ;;
        --enable)
            ACTION="enable"
            shift
            ;;
        --disable)
            ACTION="disable"
            shift
            ;;
        --status)
            show_ovs_status
            exit 0
            ;;
        --test)
            test_openflow_connectivity "$COMPONENT_TYPE"
            exit 0
            ;;
        --setup-flows)
            setup_default_flows "$COMPONENT_TYPE"
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
if [ -n "$COMPONENT_TYPE" ] && [ -n "$ACTION" ]; then
    configure_component_ovs "$COMPONENT_TYPE" "$ACTION"
elif [ -z "$COMPONENT_TYPE" ] && [ -z "$ACTION" ]; then
    show_ovs_status
else
    echo "Error: Component type and action must be specified together"
    show_usage
    exit 1
fi

echo "UERANSIM OVS configuration completed"