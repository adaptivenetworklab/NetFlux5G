#!/bin/bash

# AP Setup Script for gNB container to act as Access Point
# This script enables the gNB container to create wireless access points like mininet-wifi APs

set -e

# Function to log messages
log() {
    echo "[AP-SETUP] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to cleanup on exit
cleanup() {
    log "Cleaning up AP setup..."
    pkill -f hostapd 2>/dev/null || true
    pkill -f dnsmasq 2>/dev/null || true
    # Remove interfaces that were created
    if [ -n "$VIRTUAL_WLAN_IFACE" ] && ip link show "$VIRTUAL_WLAN_IFACE" >/dev/null 2>&1; then
        ip link delete "$VIRTUAL_WLAN_IFACE" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Check if AP functionality is enabled
if [ "$AP_ENABLED" != "true" ]; then
    log "AP functionality is disabled (AP_ENABLED != true)"
    exit 0
fi

# Set default values
AP_SSID=${AP_SSID:-"gnb-hotspot"}
AP_CHANNEL=${AP_CHANNEL:-"6"}
AP_MODE=${AP_MODE:-"g"}
AP_PASSWD=${AP_PASSWD:-""}
AP_BRIDGE_NAME=${AP_BRIDGE_NAME:-"br-gnb"}
AP_FAILMODE=${AP_FAILMODE:-"standalone"}
OPENFLOW_PROTOCOLS=${OPENFLOW_PROTOCOLS:-"OpenFlow14"}

log "Starting AP setup with configuration:"
log "  SSID: $AP_SSID"
log "  Channel: $AP_CHANNEL"
log "  Mode: $AP_MODE"
log "  Bridge: $AP_BRIDGE_NAME"
log "  Password: ${AP_PASSWD:+[SET]}${AP_PASSWD:-[NONE]}"

# Function to setup OVS bridge for AP
setup_ovs() {
    log "Setting up Open vSwitch for AP functionality..."
    
    # Use the main UERANSIM OVS setup if available and enabled
    if [ "$OVS_ENABLED" = "true" ] && [ -f /usr/local/bin/ueransim-ovs-setup.sh ]; then
        log "Integrating with main UERANSIM OVS setup..."
        
        # Set AP-specific bridge name if not set
        if [ -z "$OVS_BRIDGE_NAME" ]; then
            export OVS_BRIDGE_NAME="$AP_BRIDGE_NAME"
        fi
        
        # Let the main OVS setup handle the bridge creation
        source /usr/local/bin/ueransim-ovs-setup.sh
        
        # Setup OVS bridge using the main script functions
        if type setup_ovs_bridge >/dev/null 2>&1; then
            setup_ovs_bridge
        fi
        
        # Check if the bridge exists
        if ovs-vsctl br-exists "$AP_BRIDGE_NAME" 2>/dev/null; then
            log "AP bridge $AP_BRIDGE_NAME is ready via main OVS setup"
            return 0
        elif ovs-vsctl br-exists "$OVS_BRIDGE_NAME" 2>/dev/null; then
            log "Using main OVS bridge $OVS_BRIDGE_NAME for AP functionality"
            AP_BRIDGE_NAME="$OVS_BRIDGE_NAME"
            return 0
        fi
    fi
    
    # Fallback to standalone OVS setup for AP
    log "Setting up standalone OVS for AP..."
    
    # Check if OVS is available
    if ! command -v ovs-vsctl >/dev/null 2>&1; then
        log "ERROR: OVS tools not available, cannot setup AP bridge"
        return 1
    fi
    
    # Start OVS services if not running
    if ! pgrep -f ovs-vswitchd >/dev/null 2>&1; then
        log "Starting OVS services..."
        
        # Create OVS database if it doesn't exist
        if [ ! -f /etc/openvswitch/conf.db ]; then
            log "Creating OVS database..."
            ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema
        fi
        
        # Start OVS processes
        ovsdb-server --remote=punix:/var/run/openvswitch/db.sock \
                     --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
                     --pidfile --detach --log-file
        
        ovs-vswitchd --pidfile --detach --log-file
        
        # Wait for OVS to be ready
        sleep 3
        
        # Initialize database
        ovs-vsctl --no-wait init
    fi
    
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
    else
        log "Bridge $AP_BRIDGE_NAME already exists"
    fi
    
    # Bring bridge up
    ip link set dev "$AP_BRIDGE_NAME" up
    
    # Assign IP to bridge if not already assigned
    if ! ip addr show "$AP_BRIDGE_NAME" | grep -q "inet "; then
        log "Assigning IP address to bridge $AP_BRIDGE_NAME"
        ip addr add 192.168.4.1/24 dev "$AP_BRIDGE_NAME"
    fi
    
    log "OVS bridge setup completed"
}

# Function to create wireless interface
setup_wireless_interface() {
    log "Setting up wireless interface..."
    
    # Check for existing wireless interfaces
    WLAN_IFACE=""
    for iface in $(ls /sys/class/net/ 2>/dev/null | grep -E '^(wlan|hwsim)'); do
        if [ -d "/sys/class/net/$iface/wireless" ]; then
            WLAN_IFACE="$iface"
            log "Found wireless interface: $WLAN_IFACE"
            break
        fi
    done
    
    # If no wireless interface found, try to create one from available hardware
    if [ -z "$WLAN_IFACE" ]; then
        log "No wireless interface found, attempting to create virtual interface..."
        
        # Check for available physical wireless devices
        if [ -d "/sys/class/ieee80211" ]; then
            for phy in $(ls /sys/class/ieee80211/ 2>/dev/null); do
                log "Found wireless PHY: $phy"
                
                # Create virtual interface
                VIRTUAL_WLAN_IFACE="ap-$phy"
                if iw phy "$phy" interface add "$VIRTUAL_WLAN_IFACE" type __ap 2>/dev/null; then
                    WLAN_IFACE="$VIRTUAL_WLAN_IFACE"
                    log "Created virtual AP interface: $WLAN_IFACE"
                    break
                else
                    log "Failed to create virtual interface on $phy"
                fi
            done
        fi
    fi
    
    # If still no interface, check if we're in a container and create simulation interface
    if [ -z "$WLAN_IFACE" ]; then
        log "No wireless hardware found, creating simulation interface..."
        
        # Create a bridge interface for simulation
        if ! ip link show "${AP_BRIDGE_NAME}-wlan0" >/dev/null 2>&1; then
            ip link add "${AP_BRIDGE_NAME}-wlan0" type dummy
            ip link set "${AP_BRIDGE_NAME}-wlan0" up
            WLAN_IFACE="${AP_BRIDGE_NAME}-wlan0"
            log "Created simulation interface: $WLAN_IFACE"
        else
            WLAN_IFACE="${AP_BRIDGE_NAME}-wlan0"
            log "Using existing simulation interface: $WLAN_IFACE"
        fi
    fi
    
    if [ -z "$WLAN_IFACE" ]; then
        log "ERROR: Could not create or find wireless interface"
        return 1
    fi
    
    # Configure the wireless interface
    log "Configuring wireless interface: $WLAN_IFACE"
    
    # Bring interface up
    ip link set "$WLAN_IFACE" up
    
    # Add to bridge if OVS is enabled
    if [ "$OVS_ENABLED" = "true" ] && ovs-vsctl br-exists "$AP_BRIDGE_NAME" 2>/dev/null; then
        if ! ovs-vsctl list-ports "$AP_BRIDGE_NAME" | grep -q "^$WLAN_IFACE$"; then
            log "Adding wireless interface to OVS bridge"
            ovs-vsctl add-port "$AP_BRIDGE_NAME" "$WLAN_IFACE"
        fi
    fi
    
    export WLAN_IFACE
    log "Wireless interface setup completed: $WLAN_IFACE"
}
# Function to create hostapd configuration  
create_hostapd_config() {
    log "Creating hostapd configuration..."
    
    if [ -z "$WLAN_IFACE" ]; then
        log "ERROR: No wireless interface available for hostapd"
        return 1
    fi
    
    HOSTAPD_CONF="/tmp/hostapd_gnb.conf"
    
    # Determine the best driver to use
    HOSTAPD_DRIVER="nl80211"
    
    # Check if interface supports wireless features
    if [ -d "/sys/class/net/$WLAN_IFACE/wireless" ]; then
        log "Interface $WLAN_IFACE supports wireless - using nl80211 driver"
        HOSTAPD_DRIVER="nl80211"
    else
        log "Interface $WLAN_IFACE - attempting nl80211 driver"
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
    else
        log "No password set - creating open AP"
        echo "wpa=0" >> "$HOSTAPD_CONF"
    fi
    
    log "Hostapd configuration created at $HOSTAPD_CONF"
    export HOSTAPD_CONF
}

# Function to start hostapd
start_hostapd() {
    log "Starting hostapd AP service..."
    
    if [ -z "$HOSTAPD_CONF" ] || [ ! -f "$HOSTAPD_CONF" ]; then
        log "ERROR: Hostapd configuration not found"
        return 1
    fi
    
    # Kill any existing hostapd processes
    pkill -f hostapd 2>/dev/null || true
    sleep 1
    
    # Create runtime directory
    mkdir -p /var/run/hostapd
    
    # Start hostapd
    log "Launching hostapd with config: $HOSTAPD_CONF"
    hostapd -dd "$HOSTAPD_CONF" &
    HOSTAPD_PID=$!
    
    # Wait a moment and check if hostapd started successfully
    sleep 3
    
    if kill -0 "$HOSTAPD_PID" 2>/dev/null; then
        log "Hostapd started successfully (PID: $HOSTAPD_PID)"
        echo "$HOSTAPD_PID" > /var/run/hostapd.pid
        
        # Show AP status
        log "AP Status:"
        log "  SSID: $AP_SSID"
        log "  Interface: $WLAN_IFACE"
        log "  Channel: $AP_CHANNEL"
        log "  Mode: $AP_MODE"
        log "  Security: ${AP_PASSWD:+WPA2}${AP_PASSWD:-Open}"
        
        return 0
    else
        log "ERROR: Hostapd failed to start"
        log "Check the hostapd configuration and interface status"
        return 1
    fi
}

# Function to setup DHCP for AP clients (optional)
setup_dhcp() {
    if [ "$ENABLE_DHCP" = "true" ]; then
        log "Setting up DHCP server for AP clients..."
        
        # Create dnsmasq configuration
        DNSMASQ_CONF="/tmp/dnsmasq_gnb.conf"
        cat > "$DNSMASQ_CONF" << EOF
interface=$AP_BRIDGE_NAME
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,12h
dhcp-option=3,192.168.4.1
dhcp-option=6,8.8.8.8,8.8.4.4
domain=gnb.local
EOF
        
        # Start dnsmasq
        dnsmasq -C "$DNSMASQ_CONF" --log-facility=/var/log/dnsmasq.log
        log "DHCP server started"
    fi
}

# Main AP setup logic
main() {
    log "=== gNB Access Point Setup ==="
    
    # Step 1: Setup OVS bridge
    if ! setup_ovs; then
        log "ERROR: Failed to setup OVS bridge"
        exit 1
    fi
    
    # Step 2: Setup wireless interface
    if ! setup_wireless_interface; then
        log "ERROR: Failed to setup wireless interface"
        exit 1
    fi
    
    # Step 3: Create hostapd configuration
    if ! create_hostapd_config; then
        log "ERROR: Failed to create hostapd configuration"
        exit 1
    fi
    
    # Step 4: Start hostapd
    if ! start_hostapd; then
        log "ERROR: Failed to start hostapd"
        exit 1
    fi
    
    # Step 5: Setup DHCP (optional)
    setup_dhcp
    
    log "=== AP Setup Complete ==="
    log "gNB Access Point is now running!"
    
    # Keep the script running to monitor the AP
    while true; do
        sleep 30
        
        # Check if hostapd is still running
        if [ -f /var/run/hostapd.pid ]; then
            HOSTAPD_PID=$(cat /var/run/hostapd.pid)
            if ! kill -0 "$HOSTAPD_PID" 2>/dev/null; then
                log "WARNING: Hostapd process died, attempting restart..."
                start_hostapd
            fi
        fi
    done
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi

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
