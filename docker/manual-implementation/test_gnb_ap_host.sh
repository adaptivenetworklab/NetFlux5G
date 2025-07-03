#!/bin/bash

# Test script for gNB Access Point functionality
# This script sets up the host properly and tests the gNB container AP features

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
TEST_IMAGE="adaptive/ueransim:latest"
TEST_CONTAINER_NAME="gnb_ap_test"
TEST_NETWORK="test_5g_network"

# Function to check host prerequisites
check_host_prerequisites() {
    print_status "Checking host prerequisites..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        print_error "This script needs to be run with sudo privileges for host setup"
        print_status "Run: sudo $0"
        exit 1
    fi
    
    # Check if required packages are installed
    print_status "Checking required packages..."
    for pkg in iw hostapd bridge-utils openvswitch-switch; do
        if ! command -v $pkg >/dev/null 2>&1 && ! dpkg -l | grep -q $pkg; then
            print_warning "Package $pkg not found, installing..."
            apt-get update >/dev/null 2>&1
            apt-get install -y $pkg
        else
            print_success "Package $pkg is available"
        fi
    done
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is available"
}

# Function to setup mac80211_hwsim
setup_wireless_simulation() {
    print_status "Setting up wireless simulation environment..."
    
    # Remove existing mac80211_hwsim if loaded
    if lsmod | grep -q mac80211_hwsim; then
        print_status "Removing existing mac80211_hwsim module..."
        modprobe -r mac80211_hwsim 2>/dev/null || true
        sleep 2
    fi
    
    # Load mac80211_hwsim with multiple radios
    print_status "Loading mac80211_hwsim with 10 radios..."
    if modprobe mac80211_hwsim radios=10; then
        print_success "mac80211_hwsim loaded successfully"
        sleep 3
        
        # List available interfaces
        print_status "Available wireless interfaces:"
        iw dev | grep Interface | head -5
        
        # List PHY devices
        print_status "Available PHY devices:"
        ls /sys/kernel/debug/ieee80211/ 2>/dev/null | head -5 || print_warning "Cannot access /sys/kernel/debug - may need debugfs mounted"
        
    else
        print_error "Failed to load mac80211_hwsim module"
        exit 1
    fi
}

# Function to create test network
create_test_network() {
    print_status "Creating test Docker network..."
    
    # Remove existing network if exists
    docker network rm "$TEST_NETWORK" 2>/dev/null || true
    
    # Create new network
    if docker network create "$TEST_NETWORK" >/dev/null; then
        print_success "Test network '$TEST_NETWORK' created"
    else
        print_error "Failed to create test network"
        exit 1
    fi
}

# Function to test gNB container with AP functionality
test_gnb_ap_container() {
    print_status "Testing gNB container with AP functionality..."
    
    # Remove existing container if exists
    docker rm -f "$TEST_CONTAINER_NAME" 2>/dev/null || true
    
    # Run container with proper mounts and privileges
    print_status "Starting gNB container with AP enabled..."
    docker run -d --name "$TEST_CONTAINER_NAME" \
        --privileged \
        --pid='host' \
        --net='host' \
        --cap-add=NET_ADMIN \
        -v /sys/:/sys \
        -v /lib/modules:/lib/modules \
        -v /sys/kernel/debug:/sys/kernel/debug \
        -v /var/run/netns:/var/run/netns \
        -e AP_ENABLED=true \
        -e AP_SSID="Test-5G-AP" \
        -e AP_CHANNEL=6 \
        -e AP_MODE=g \
        -e AP_BRIDGE_NAME="br-test" \
        -e AP_FAILMODE="standalone" \
        -e OPENFLOW_PROTOCOLS="OpenFlow14" \
        "$TEST_IMAGE" gnb
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully"
    else
        print_error "Failed to start container"
        return 1
    fi
    
    # Wait for container to initialize
    print_status "Waiting for container initialization..."
    sleep 15
    
    # Check container logs
    print_status "Container logs:"
    docker logs "$TEST_CONTAINER_NAME" 2>&1 | tail -20
    
    # Check if container is still running
    if docker ps --filter "name=$TEST_CONTAINER_NAME" --filter "status=running" | grep -q "$TEST_CONTAINER_NAME"; then
        print_success "Container is running"
    else
        print_error "Container stopped unexpectedly"
        docker logs "$TEST_CONTAINER_NAME"
        return 1
    fi
}

# Function to test AP functionality
test_ap_functionality() {
    print_status "Testing Access Point functionality..."
    
    # Test if OVS bridge was created
    print_status "Checking OVS bridge..."
    if docker exec "$TEST_CONTAINER_NAME" ovs-vsctl br-exists br-test 2>/dev/null; then
        print_success "OVS bridge 'br-test' exists"
        
        # Show bridge details
        print_status "Bridge details:"
        docker exec "$TEST_CONTAINER_NAME" ovs-vsctl show
    else
        print_warning "OVS bridge not found or accessible"
    fi
    
    # Test if hostapd is running
    print_status "Checking hostapd process..."
    if docker exec "$TEST_CONTAINER_NAME" pgrep -f hostapd >/dev/null; then
        print_success "Hostapd is running"
        
        # Show hostapd configuration
        print_status "Hostapd configuration:"
        docker exec "$TEST_CONTAINER_NAME" cat /tmp/hostapd_gnb.conf 2>/dev/null || print_warning "Cannot read hostapd config"
    else
        print_warning "Hostapd process not found"
    fi
    
    # Test wireless interface
    print_status "Checking wireless interfaces in container..."
    docker exec "$TEST_CONTAINER_NAME" ip link show | grep -E "(wlan|hwsim)" || print_warning "No wireless interfaces found"
    
    # Check if AP is broadcasting
    print_status "Scanning for test AP..."
    if iw dev | head -1 | cut -d' ' -f2 | xargs -I {} iw dev {} scan 2>/dev/null | grep -q "Test-5G-AP"; then
        print_success "AP 'Test-5G-AP' is broadcasting!"
    else
        print_warning "AP not detected in scan (may take time to appear)"
    fi
}

# Function to cleanup test environment
cleanup_test_environment() {
    print_status "Cleaning up test environment..."
    
    # Stop and remove container
    docker rm -f "$TEST_CONTAINER_NAME" 2>/dev/null || true
    
    # Remove test network
    docker network rm "$TEST_NETWORK" 2>/dev/null || true
    
    # Optional: Remove mac80211_hwsim (comment out to keep for other tests)
    # modprobe -r mac80211_hwsim 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Function to display test results
display_test_results() {
    print_status "=== TEST RESULTS SUMMARY ==="
    
    if docker ps --filter "name=$TEST_CONTAINER_NAME" --filter "status=running" | grep -q "$TEST_CONTAINER_NAME"; then
        print_success "✓ Container is running"
    else
        print_error "✗ Container failed to run"
    fi
    
    if docker exec "$TEST_CONTAINER_NAME" ovs-vsctl br-exists br-test 2>/dev/null; then
        print_success "✓ OVS bridge created"
    else
        print_error "✗ OVS bridge not found"
    fi
    
    if docker exec "$TEST_CONTAINER_NAME" pgrep -f hostapd >/dev/null 2>&1; then
        print_success "✓ Hostapd is running"
    else
        print_error "✗ Hostapd not running"
    fi
    
    print_status "=== END RESULTS ==="
}

# Main execution
main() {
    print_status "=== gNB Access Point Functionality Test ==="
    print_status "This script will test the gNB container AP capabilities"
    
    # Trap for cleanup on exit
    trap cleanup_test_environment EXIT
    
    # Run tests
    check_host_prerequisites
    setup_wireless_simulation
    create_test_network
    test_gnb_ap_container
    test_ap_functionality
    display_test_results
    
    print_status "Test completed. Container '$TEST_CONTAINER_NAME' is still running for inspection."
    print_status "To cleanup manually: docker rm -f $TEST_CONTAINER_NAME"
    print_status "To view logs: docker logs $TEST_CONTAINER_NAME"
    print_status "To enter container: docker exec -it $TEST_CONTAINER_NAME bash"
    
    # Remove trap so cleanup doesn't run automatically
    trap - EXIT
}

# Run main function
main "$@"
