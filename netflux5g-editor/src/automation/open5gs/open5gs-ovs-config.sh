#!/bin/bash

# Open5GS Component OVS Configuration Helper
# This script helps configure OpenFlow settings for specific Open5GS components

set -eo pipefail

COMPONENT_TYPE=""
CONTROLLER_IP=""
CONTROLLER_PORT="6633"
BRIDGE_NAME=""

# Function to show usage
function show_usage {
    cat << EOF
Usage: $0 [OPTIONS]

Configure OpenFlow/OVS for Open5GS components in mininet-wifi

OPTIONS:
    -c, --component     Open5GS component type (amf, smf, upf, nrf, etc.)
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
    # Enable OVS for AMF with controller
    $0 --component amf --controller-ip 192.168.1.100 --enable
    
    # Configure UPF with custom bridge
    $0 --component upf --controller-ip 10.0.0.1 --bridge-name br-upf-data --enable
    
    # Show current OVS status
    $0 --status
    
    # Disable OVS for SMF
    $0 --component smf --disable

EOF
}

# Function to configure component-specific OVS settings
function configure_component_ovs {
    local component=$1
    local action=$2
    
    # Set component-specific defaults
    case $component in
        "amf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-amf"}
            ;;
        "smf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-smf"}
            ;;
        "upf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-upf"}
            ;;
        "nrf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-nrf"}
            ;;
        "udm")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-udm"}
            ;;
        "udr")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-udr"}
            ;;
        "pcf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-pcf"}
            ;;
        "ausf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-ausf"}
            ;;
        "nssf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-nssf"}
            ;;
        "bsf")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-bsf"}
            ;;
        "scp")
            BRIDGE_NAME=${BRIDGE_NAME:-"br-scp"}
            ;;
        *)
            BRIDGE_NAME=${BRIDGE_NAME:-"br-${component}"}
            ;;
    esac
    
    if [ "$action" = "enable" ]; then
        echo "Enabling OVS for component: $component"
        export OVS_ENABLED=true
        export OVS_BRIDGE_NAME=$BRIDGE_NAME
        
        if [ -n "$CONTROLLER_IP" ]; then
            export OVS_CONTROLLER="tcp:${CONTROLLER_IP}:${CONTROLLER_PORT}"
            echo "Controller configured: $OVS_CONTROLLER"
        fi
        
        # Run OVS setup
        /opt/open5gs/bin/ovs-setup.sh
        
    elif [ "$action" = "disable" ]; then
        echo "Disabling OVS for component: $component"
        export OVS_ENABLED=false
        
        # Remove bridge if it exists
        if ovs-vsctl br-exists $BRIDGE_NAME 2>/dev/null; then
            ovs-vsctl del-br $BRIDGE_NAME
            echo "Removed bridge: $BRIDGE_NAME"
        fi
    fi
}

# Function to show OVS status
function show_ovs_status {
    echo "=== Open5GS OVS Status ==="
    
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
            ovs-ofctl dump-flows $bridge 2>/dev/null || echo "  No flows"
            echo ""
        done
        
    else
        echo "OVS Status: Not running"
    fi
    
    echo "Network interfaces:"
    ip link show | grep -E "^[0-9]+:" | awk '{print $2}' | tr -d ':'
    
    echo "=========================="
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

echo "OVS configuration completed"
