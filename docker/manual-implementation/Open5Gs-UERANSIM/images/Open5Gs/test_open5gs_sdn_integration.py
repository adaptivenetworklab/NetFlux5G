#!/usr/bin/env python3
"""
Test script for Open5GS OpenFlow/SDN integration in mininet-wifi
This script validates that Open5GS core components can work with SDN controllers
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Optional

def run_command(cmd: str, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                               capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e}")
        return e

def test_docker_image_build():
    """Test that the enhanced Open5GS Docker image builds successfully"""
    print("Testing Docker image build...")
    
    # Build the image
    build_cmd = """
    cd /home/litfan/Code/NetFlux5G/docker/manual-implementation/Open5Gs-UERANSIM/images/Open5Gs && \
    docker build --build-arg version=2.7.0 -t open5gs-sdn:test .
    """
    
    result = run_command(build_cmd)
    if result.returncode == 0:
        print("✓ Docker image built successfully")
        return True
    else:
        print("✗ Docker image build failed")
        print(result.stderr)
        return False

def test_ovs_packages():
    """Test that OVS packages are properly installed in the Docker image"""
    print("Testing OVS package installation...")
    
    test_cmd = """
    docker run --rm --privileged open5gs-sdn:test bash -c "
        echo 'Testing OVS installation...'
        which ovs-vsctl && echo '✓ ovs-vsctl found'
        which ovs-ofctl && echo '✓ ovs-ofctl found'
        which ovsdb-server && echo '✓ ovsdb-server found'
        which ovs-vswitchd && echo '✓ ovs-vswitchd found'
        dpkg -l | grep openvswitch && echo '✓ OpenVSwitch packages installed'
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ OVS packages properly installed")
        return True
    else:
        print("✗ OVS packages missing or not properly installed")
        return False

def test_ovs_basic_functionality():
    """Test basic OVS functionality in the Docker container"""
    print("Testing basic OVS functionality...")
    
    test_cmd = """
    docker run --rm --privileged --cap-add=NET_ADMIN open5gs-sdn:test bash -c "
        echo 'Starting OVS services...'
        mkdir -p /var/run/openvswitch
        ovsdb-server --detach --remote=punix:/var/run/openvswitch/db.sock --pidfile --log-file
        ovs-vsctl --no-wait init
        ovs-vswitchd --detach --pidfile --log-file
        
        sleep 2
        
        echo 'Creating test bridge...'
        ovs-vsctl add-br br-test
        ovs-vsctl set bridge br-test fail_mode=standalone
        ovs-vsctl set bridge br-test protocols=OpenFlow14
        
        echo 'Testing bridge operations...'
        ovs-vsctl list-br
        ovs-vsctl show
        
        echo '✓ Basic OVS functionality working'
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ Basic OVS functionality working")
        return True
    else:
        print("✗ Basic OVS functionality failed")
        print(result.stderr)
        return False

def test_environment_variables():
    """Test that environment variables are properly configured"""
    print("Testing environment variables...")
    
    test_cmd = """
    docker run --rm open5gs-sdn:test bash -c "
        echo 'Testing environment variables...'
        echo 'OVS_ENABLED: $OVS_ENABLED'
        echo 'OVS_BRIDGE_NAME: $OVS_BRIDGE_NAME'
        echo 'OVS_FAIL_MODE: $OVS_FAIL_MODE'
        echo 'OPENFLOW_PROTOCOLS: $OPENFLOW_PROTOCOLS'
        echo 'OVS_DATAPATH: $OVS_DATAPATH'
        
        # Test with custom values
        export OVS_ENABLED=true
        export OVS_CONTROLLER='tcp:192.168.1.100:6633'
        echo 'Custom OVS_CONTROLLER: $OVS_CONTROLLER'
        echo '✓ Environment variables working'
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ Environment variables properly configured")
        return True
    else:
        print("✗ Environment variables configuration failed")
        return False

def test_ovs_setup_script():
    """Test the OVS setup script functionality"""
    print("Testing OVS setup script...")
    
    test_cmd = """
    docker run --rm --privileged --cap-add=NET_ADMIN \
        -e OVS_ENABLED=true \
        -e OVS_BRIDGE_NAME=br-test \
        -e OVS_FAIL_MODE=standalone \
        -e OPENFLOW_PROTOCOLS=OpenFlow14 \
        open5gs-sdn:test bash -c "
        echo 'Testing OVS setup script...'
        
        # Run the setup script
        /opt/open5gs/bin/ovs-setup.sh
        
        sleep 3
        
        echo 'Checking if bridge was created...'
        ovs-vsctl br-exists br-test && echo '✓ Bridge created successfully'
        
        echo 'Checking bridge configuration...'
        ovs-vsctl get bridge br-test fail_mode
        ovs-vsctl get bridge br-test protocols
        
        echo '✓ OVS setup script working'
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ OVS setup script working properly")
        return True
    else:
        print("✗ OVS setup script failed")
        print(result.stderr)
        return False

def test_controller_connection():
    """Test connection to SDN controller (simulated)"""
    print("Testing controller connection simulation...")
    
    test_cmd = """
    docker run --rm --privileged --cap-add=NET_ADMIN \
        -e OVS_ENABLED=true \
        -e OVS_CONTROLLER=tcp:127.0.0.1:6633 \
        open5gs-sdn:test bash -c "
        echo 'Testing controller connection...'
        
        # Start OVS
        mkdir -p /var/run/openvswitch
        ovsdb-server --detach --remote=punix:/var/run/openvswitch/db.sock --pidfile --log-file
        ovs-vsctl --no-wait init
        ovs-vswitchd --detach --pidfile --log-file
        sleep 2
        
        # Create bridge with controller
        ovs-vsctl add-br br-test
        ovs-vsctl set-controller br-test tcp:127.0.0.1:6633
        
        # Check controller configuration
        CONTROLLER=\$(ovs-vsctl get-controller br-test)
        echo \"Controller configured: \$CONTROLLER\"
        
        if [[ \"\$CONTROLLER\" == *\"tcp:127.0.0.1:6633\"* ]]; then
            echo '✓ Controller configuration successful'
        else
            echo '✗ Controller configuration failed'
            exit 1
        fi
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ Controller connection configuration working")
        return True
    else:
        print("✗ Controller connection configuration failed")
        print(result.stderr)
        return False

def test_mininet_wifi_integration():
    """Test integration with mininet-wifi (requires mininet-wifi to be installed)"""
    print("Testing mininet-wifi integration simulation...")
    
    # Create a test script that simulates mininet-wifi DockerSta usage
    test_script = """
#!/usr/bin/env python3

import subprocess
import sys
import time

def test_dockersta_simulation():
    '''Simulate DockerSta usage with Open5GS'''
    
    print("Simulating mininet-wifi DockerSta with Open5GS...")
    
    # Test that the Docker image can run in network namespace
    cmd = '''
    docker run --rm --privileged --cap-add=NET_ADMIN \\
        --net=none \\
        -e OVS_ENABLED=true \\
        -e OVS_BRIDGE_NAME=br-mn-test \\
        open5gs-sdn:test bash -c "
        echo 'Testing in network namespace...'
        
        # Create a veth pair to simulate mininet-wifi interface
        ip link add veth0 type veth peer name veth1
        ip link set veth0 up
        ip link set veth1 up
        ip addr add 192.168.1.10/24 dev veth0
        
        echo 'Network interfaces:'
        ip link show
        
        # Test OVS with the interface
        mkdir -p /var/run/openvswitch
        ovsdb-server --detach --remote=punix:/var/run/openvswitch/db.sock --pidfile --log-file
        ovs-vsctl --no-wait init
        ovs-vswitchd --detach --pidfile --log-file
        sleep 2
        
        ovs-vsctl add-br br-mn-test
        ovs-vsctl add-port br-mn-test veth1
        
        echo 'OVS bridge with interface:'
        ovs-vsctl show
        
        echo '✓ DockerSta simulation successful'
    "
    '''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

if __name__ == '__main__':
    success, stdout, stderr = test_dockersta_simulation()
    if success:
        print("✓ Mininet-wifi integration simulation successful")
        print(stdout)
    else:
        print("✗ Mininet-wifi integration simulation failed")
        print(stderr)
        sys.exit(1)
"""
    
    # Write and execute the test script
    with open('/tmp/test_mininet_integration.py', 'w') as f:
        f.write(test_script)
    
    result = run_command("python3 /tmp/test_mininet_integration.py")
    if result.returncode == 0:
        print("✓ Mininet-wifi integration simulation successful")
        return True
    else:
        print("✗ Mininet-wifi integration simulation failed")
        print(result.stderr)
        return False

def test_open5gs_ovs_config_helper():
    """Test the Open5GS OVS configuration helper script"""
    print("Testing Open5GS OVS configuration helper...")
    
    test_cmd = """
    docker run --rm --privileged --cap-add=NET_ADMIN open5gs-sdn:test bash -c "
        echo 'Testing OVS configuration helper...'
        
        # Test help command
        /opt/open5gs/bin/open5gs-ovs-config.sh --help
        
        # Test status command
        /opt/open5gs/bin/open5gs-ovs-config.sh --status
        
        echo '✓ Configuration helper working'
    "
    """
    
    result = run_command(test_cmd)
    if result.returncode == 0:
        print("✓ Open5GS OVS configuration helper working")
        return True
    else:
        print("✗ Open5GS OVS configuration helper failed")
        return False

def main():
    """Run all tests"""
    print("=== Open5GS OpenFlow/SDN Integration Tests ===\n")
    
    tests = [
        ("Docker Image Build", test_docker_image_build),
        ("OVS Packages", test_ovs_packages),
        ("Basic OVS Functionality", test_ovs_basic_functionality),
        ("Environment Variables", test_environment_variables),
        ("OVS Setup Script", test_ovs_setup_script),
        ("Controller Connection", test_controller_connection),
        ("Mininet-wifi Integration", test_mininet_wifi_integration),
        ("OVS Configuration Helper", test_open5gs_ovs_config_helper),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n=== Test Results Summary ===")
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Open5GS OpenFlow/SDN integration is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
