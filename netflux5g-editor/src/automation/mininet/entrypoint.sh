#! /bin/bash -e

echo "Starting NetFlux5G Mininet-WiFi & Containernet Environment..."

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo "Running as root user"
        return 0
    else
        echo "Running as user: $(whoami)"
        return 1
    fi
}

# Function to start OVS safely
start_ovs() {
    echo "Starting Open vSwitch..."
    if check_root; then
        service openvswitch-switch start || echo "Warning: Could not start OVS service"
    else
        sudo service openvswitch-switch start || echo "Warning: Could not start OVS service"
    fi
}

# Function to load kernel modules
load_kernel_modules() {
    echo "Loading kernel modules..."
    if check_root; then
        modprobe mac80211_hwsim radios=10 2>/dev/null || echo "Warning: Could not load mac80211_hwsim module"
    else
        sudo modprobe mac80211_hwsim radios=10 2>/dev/null || echo "Warning: Could not load mac80211_hwsim module"
    fi
}

# Function to check Docker socket
check_docker_socket() {
    if [ ! -S /var/run/docker.sock ]; then
        echo 'Warning: Docker socket "/var/run/docker.sock" not found.'
        echo 'Containernet features may not work properly.'
        echo 'Make sure to mount the Docker socket: -v /var/run/docker.sock:/var/run/docker.sock'
        return 1
    else
        echo "Docker socket found - Containernet ready"
        return 0
    fi
}

# Function to check X11 display
check_x11() {
    if [ -z "$DISPLAY" ]; then
        echo 'Warning: DISPLAY environment variable not set.'
        echo 'GUI applications may not work.'
        echo 'Make sure to set DISPLAY and mount X11 socket.'
        return 1
    else
        echo "X11 display ready: $DISPLAY"
        return 0
    fi
}

# Main startup sequence
echo "Initializing container environment..."

# Start OVS
start_ovs

# Load kernel modules
load_kernel_modules

# Check Docker socket
check_docker_socket

# Check X11
check_x11

# Print environment info
echo ""
echo "Environment Information:"
echo "- Python version: $(python3 --version)"
echo "- Working directory: $(pwd)"
echo "- User: $(whoami)"
echo "- Available networks: $(ip link show | grep -E '^[0-9]+:' | cut -d: -f2 | tr -d ' ' | head -5 | tr '\n' ' ')"

# Check if Mininet is working
echo ""
echo "Testing Mininet installation..."
if mn --version >/dev/null 2>&1; then
    echo "✓ Mininet is working"
else
    echo "✗ Mininet test failed"
fi

# Check if Containernet is working
echo "Testing Containernet installation..."
if python3 -c "import containernet.cli" >/dev/null 2>&1; then
    echo "✓ Containernet is working"
else
    echo "✗ Containernet test failed"
fi

echo ""
echo "Welcome to NetFlux5G Mininet-WiFi & Containernet Environment!"
echo "Available commands:"
echo "  mn                 - Start Mininet"
echo "  mn --wifi          - Start Mininet-WiFi"
echo "  python3 topology.py - Run custom topology scripts"
echo ""

# Execute the command
if [[ $# -eq 0 ]]; then
    # No arguments, start interactive shell
    exec /bin/bash
else
    # Execute provided command
    exec "$@"
fi