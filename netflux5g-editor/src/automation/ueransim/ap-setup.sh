#!/bin/bash

# AP Setup Script for gNB container to act as Access Point
# This script enables the gNB container to create wireless access points like mininet-wifi APs

set -e

# Function to log messages
log() {
    echo "[AP-SETUP] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to setup OVS
setup_ovs() {
    log "Setting up Open vSwitch..."
    
    # Start OVS database
    if [ ! -f /etc/openvswitch/conf.db ]; then
        log "Creating OVS database..."
        ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema
    fi
    
    # Start OVS processes
    log "Starting OVS processes..."
    ovsdb-server --remote=punix:/var/run/openvswitch/db.sock \
                 --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
                 --pidfile --detach --log-file
    
    ovs-vswitchd --pidfile --detach --log-file
    
    # Wait for OVS to be ready
    sleep 2
    
    # Create bridge if it doesn't exist
    if ! ovs-vsctl br-exists "$AP_BRIDGE_NAME" 2>/dev/null; then
        log "Creating OVS bridge: $AP_BRIDGE_NAME"
        ovs-vsctl add-br "$AP_BRIDGE_NAME"
        
        # Set OpenFlow version
        if [ -n "$OPENFLOW_PROTOCOLS" ]; then
            log "Setting OpenFlow protocols: $OPENFLOW_PROTOCOLS"
            ovs-vsctl set bridge "$AP_BRIDGE_NAME" protocols="$OPENFLOW_PROTOCOLS"
        fi
        
        # Set fail mode
        log "Setting fail mode: $AP_FAILMODE"
        ovs-vsctl set-fail-mode "$AP_BRIDGE_NAME" "$AP_FAILMODE"
        
        # Add controller if specified
        if [ -n "$OVS_CONTROLLER" ]; then
            log "Adding controller: $OVS_CONTROLLER"
            ovs-vsctl set-controller "$AP_BRIDGE_NAME" "$OVS_CONTROLLER"
        fi
    fi
    
    # Bring bridge up
    ip link set dev "$AP_BRIDGE_NAME" up
}

# Function to create wireless interface
setup_wireless_interface() {
    log "Setting up wireless interface..."
    
    # Find available wireless interface (should be available from host's mac80211_hwsim)
    WLAN_IFACE=""
    for iface in $(ls /sys/class/net/ 2>/dev/null | grep -E '^(wlan|hwsim)'); do
        if [ -d "/sys/class/net/$iface/wireless" ]; then
            WLAN_IFACE="$iface"
            log "Found wireless interface: $WLAN_IFACE"
            break
        fi
    done
    
    # If no wireless interface found, check for host-mounted radios
    if [ -z "$WLAN_IFACE" ]; then
        log "No wireless interface found in container namespace."
        log "Checking for mac80211_hwsim virtual radios from host..."
        
        # Check if mac80211_hwsim is loaded on host (via /sys mount)
        if [ -d "/sys/kernel/debug/ieee80211" ] && ls /sys/kernel/debug/ieee80211/ 2>/dev/null | grep -q "phy"; then
            log "Host has mac80211_hwsim radios available"
            
            # List available PHY devices
            for phy in $(ls /sys/kernel/debug/ieee80211/ 2>/dev/null); do
                log "Available PHY device: $phy"
                
                # Try to create a new virtual interface using iw
                WLAN_IFACE="wlan-gnb-$(date +%s)"
                log "Attempting to create interface $WLAN_IFACE on $phy"
                
                if iw phy "$phy" interface add "$WLAN_IFACE" type managed 2>/dev/null; then
                    log "Successfully created virtual interface: $WLAN_IFACE"
                    break
                else
                    log "Failed to create interface on $phy, trying next..."
                    WLAN_IFACE=""
                fi
            done
        else
            log "No mac80211_hwsim radios found from host."
            log "Make sure to:"
            log "1. Load mac80211_hwsim on host: sudo modprobe mac80211_hwsim radios=10"
            log "2. Run container with: -v /sys:/sys -v /lib/modules:/lib/modules --privileged"
        fi
        
        # If we still can't create a wireless interface, create a bridge interface for basic testing
        if [ -z "$WLAN_IFACE" ]; then
            log "WARNING: No wireless capabilities available!"
            log "Creating bridge interface for basic connectivity testing..."
            WLAN_IFACE="wlan-bridge-$(date +%s)"
            ip link add name "$WLAN_IFACE" type bridge
            
            log "NOTE: This interface won't support real wireless features."
            log "For full wireless AP functionality, ensure mac80211_hwsim is loaded on host."
        fi
    fi
    
    if [ -z "$WLAN_IFACE" ] || [ ! -e "/sys/class/net/$WLAN_IFACE" ]; then
        log "ERROR: Could not find or create any interface"
        return 1
    fi
    
    log "Using interface: $WLAN_IFACE"
    
    # Bring interface up
    ip link set dev "$WLAN_IFACE" up
    
    # Add interface to OVS bridge
    if ! ovs-vsctl port-to-br "$WLAN_IFACE" 2>/dev/null; then
        log "Adding $WLAN_IFACE to bridge $AP_BRIDGE_NAME"
        ovs-vsctl add-port "$AP_BRIDGE_NAME" "$WLAN_IFACE"
    fi
    
    export WLAN_IFACE
}

# Function to create hostapd configuration
create_hostapd_config() {
    log "Creating hostapd configuration..."
    
    HOSTAPD_CONF="/tmp/hostapd_gnb.conf"
    
    # Determine the best driver to use
    HOSTAPD_DRIVER="nl80211"
    
    # Check if interface supports nl80211
    if [ -d "/sys/class/net/$WLAN_IFACE/wireless" ]; then
        log "Interface $WLAN_IFACE supports wireless - using nl80211 driver"
        HOSTAPD_DRIVER="nl80211"
    elif [ -d "/sys/class/net/$WLAN_IFACE/phy80211" ]; then
        log "Interface $WLAN_IFACE has phy80211 - using nl80211 driver"
        HOSTAPD_DRIVER="nl80211"
    else
        log "Interface $WLAN_IFACE doesn't support wireless - this may cause issues"
        log "Attempting to use nl80211 driver anyway"
        HOSTAPD_DRIVER="nl80211"
    fi
    
    cat > "$HOSTAPD_CONF" << EOF
# Hostapd configuration for gNB Access Point
interface=$WLAN_IFACE
driver=$HOSTAPD_DRIVER
ssid=$AP_SSID
hw_mode=$AP_MODE
channel=$AP_CHANNEL
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=0

# Enable logging for troubleshooting
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2

# Additional compatibility settings
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
EOF

    # Add WPA configuration if password is set
    if [ -n "$AP_PASSWD" ] && [ "$AP_PASSWD" != "" ]; then
        log "Adding WPA2 security to AP configuration"
        cat >> "$HOSTAPD_CONF" << EOF

# WPA2 Security
wpa=2
wpa_passphrase=$AP_PASSWD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
    fi
    
    # Add additional hostapd configurations if available
    if [ -n "$HOSTAPD_EXTRA_CONF" ]; then
        log "Adding extra hostapd configuration"
        echo "$HOSTAPD_EXTRA_CONF" >> "$HOSTAPD_CONF"
    fi
    
    export HOSTAPD_CONF
}

# Function to start hostapd
start_hostapd() {
    log "Starting hostapd..."
    
    # Kill any existing hostapd processes
    pkill -f hostapd || true
    sleep 1
    
    # Start hostapd in background
    hostapd -B "$HOSTAPD_CONF"
    
    # Wait a bit for hostapd to initialize
    sleep 3
    
    # Check if hostapd is running
    if pgrep -f hostapd > /dev/null; then
        log "Hostapd started successfully"
        return 0
    else
        log "ERROR: Failed to start hostapd"
        return 1
    fi
}

# Function to configure bridge networking
setup_bridge_networking() {
    log "Configuring bridge networking..."
    
    # Set bridge IP if specified
    if [ -n "$AP_BRIDGE_IP" ]; then
        log "Setting bridge IP: $AP_BRIDGE_IP"
        ip addr add "$AP_BRIDGE_IP" dev "$AP_BRIDGE_NAME" || true
    fi
    
    # Enable IP forwarding if required
    if [ "$AP_ENABLE_FORWARDING" = "true" ]; then
        log "Enabling IP forwarding"
        echo 1 > /proc/sys/net/ipv4/ip_forward
    fi
    
    # Setup DHCP if enabled
    if [ "$AP_ENABLE_DHCP" = "true" ] && [ -n "$AP_DHCP_RANGE" ]; then
        log "Starting DHCP server would go here (dnsmasq configuration)"
        # This would require dnsmasq to be installed and configured
        # Left as an exercise for more advanced setups
    fi
}

# Function to setup mininet-wifi compatibility
setup_mininet_compatibility() {
    log "Setting up mininet-wifi compatibility features..."
    
    # Create symbolic links for common mininet-wifi commands
    ln -sf /usr/bin/hostapd /usr/local/bin/hostapd_cli 2>/dev/null || true
    
    # Set up environment for OpenFlow controller communication
    if [ -n "$OVS_CONTROLLER" ]; then
        log "Configuring for OpenFlow controller: $OVS_CONTROLLER"
        # Additional controller-specific setup can go here
    fi
    
    # Setup traffic control (tc) if needed for QoS
    if [ "$AP_ENABLE_QOS" = "true" ]; then
        log "Setting up QoS (traffic control)"
        # TC setup would go here
    fi
}

# Main function
main() {
    if [ "$AP_ENABLED" = "true" ]; then
        log "=== Starting AP Setup for gNB container ==="
        log "AP SSID: $AP_SSID"
        log "AP Channel: $AP_CHANNEL"
        log "AP Mode: $AP_MODE"
        log "Bridge Name: $AP_BRIDGE_NAME"
        log "Fail Mode: $AP_FAILMODE"
        log "OpenFlow Protocols: $OPENFLOW_PROTOCOLS"
        
        # Setup components
        setup_ovs
        setup_wireless_interface
        create_hostapd_config
        setup_mininet_compatibility
        
        # Start AP services
        if start_hostapd; then
            setup_bridge_networking
            log "=== AP Setup completed successfully ==="
            log "Access Point '$AP_SSID' is now running on interface $WLAN_IFACE"
            log "OVS Bridge '$AP_BRIDGE_NAME' is configured and ready"
        else
            log "=== AP Setup failed ==="
            exit 1
        fi
    else
        log "AP functionality is disabled (AP_ENABLED=false)"
    fi
}

# Execute main function
main "$@"
