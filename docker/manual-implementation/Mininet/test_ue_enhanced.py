#!/usr/bin/env python3

"""
Enhanced UE Test Script for NetFlux5G Editor
===========================================

This script tests the enhanced UE functionality including:
- Enhanced UE UI with tabbed interface (UE Config, Wireless, Network)
- Dynamic configuration through GUI
- Export to mininet-wifi with all enhanced parameters
- Docker environment variable passing
- Mininet-wifi station creation with wireless capabilities

Usage:
    python3 test_ue_enhanced.py

Requirements:
    - NetFlux5G editor with enhanced UE implementation
    - mininet-wifi environment
    - Docker with UERANSIM image
"""

import os
import sys
import subprocess
import tempfile
import time

# Add the NetFlux5G editor src directory to Python path
sys.path.insert(0, '/home/litfan/Code/NetFlux5G/netflux5g-editor/src')

from manager.configmap import ConfigurationMapper
from export.mininet_export import MininetExporter

def test_enhanced_ue_config_mapping():
    """Test the enhanced UE configuration mapping"""
    print("🔧 Testing Enhanced UE Configuration Mapping...")
    
    # Test configuration with enhanced UE properties
    test_properties = {
        # Basic UE Configuration
        'UE_GNBHostName': 'test.gnb',
        'UE_APN': 'test-internet',
        'UE_MSISDN': '0000000123',
        'UE_MCC': '001',
        'UE_MNC': '01',
        'UE_SST': '1',
        'UE_SD': '0x000001',
        'UE_KEY': 'TEST_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC',
        'UE_OPType': 'OP',
        'UE_OP': 'TEST_OP_E8ED289DEBA952E4283B54E88E6183CA',
        
        # Device Identifiers
        'UE_IMEI': '123456789012345',
        'UE_IMEISV': '1234567890123456',
        
        # Wireless Configuration
        'UE_Power': 25,
        'UE_Range': 150,
        'UE_AssociationMode': 'manual',
        'UE_Mobility': True,
        
        # Network Configuration
        'UE_GNB_IP': '192.168.1.100',
        'UE_TunnelInterface': 'uesimtun1',
        'UE_RadioInterface': 'wlan0',
        'UE_PDUSessions': 2,
        'UE_SessionType': 'IPv4v6'
    }
    
    config = ConfigurationMapper.map_ue_config(test_properties)
    
    # Verify all enhanced configurations are mapped correctly
    expected_mappings = {
        'gnb_hostname': 'test.gnb',
        'apn': 'test-internet',
        'msisdn': '0000000123',
        'mcc': '001',
        'mnc': '01',
        'sst': '1',
        'sd': '0x000001',
        'key': 'TEST_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC',
        'op_type': 'OP',
        'op': 'TEST_OP_E8ED289DEBA952E4283B54E88E6183CA',
        'imei': '123456789012345',
        'imeisv': '1234567890123456',
        'txpower': 25.0,
        'range': 150.0,
        'association': 'manual',
        'mobility': True,
        'gnb_ip': '192.168.1.100',
        'tunnel_iface': 'uesimtun1',
        'radio_iface': 'wlan0',
        'pdu_sessions': 2,
        'session_type': 'IPv4v6'
    }
    
    success = True
    for key, expected_value in expected_mappings.items():
        actual_value = config.get(key)
        if actual_value != expected_value:
            print(f"❌ Mapping error for {key}: expected {expected_value}, got {actual_value}")
            success = False
        else:
            print(f"✅ {key}: {actual_value}")
    
    if success:
        print("✅ Enhanced UE configuration mapping test PASSED")
    else:
        print("❌ Enhanced UE configuration mapping test FAILED")
    
    return success

def test_enhanced_ue_export():
    """Test UE export with enhanced configuration"""
    print("\n📤 Testing Enhanced UE Export...")
    
    # Create a test topology with enhanced UE
    test_topology = {
        'nodes': [
            {
                'id': 'ue1',
                'name': 'UE-Enhanced',
                'type': 'UE',
                'x': 100,
                'y': 200,
                'properties': {
                    # Enhanced UE properties
                    'UE_GNBHostName': 'enhanced.gnb',
                    'UE_APN': 'enhanced-internet',
                    'UE_MSISDN': '1234567890',
                    'UE_MCC': '999',
                    'UE_MNC': '99',
                    'UE_SST': '2',
                    'UE_SD': '0x123456',
                    'UE_KEY': 'ENHANCED_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC',
                    'UE_OPType': 'OPC',
                    'UE_OP': 'ENHANCED_OP_E8ED289DEBA952E4283B54E88E6183CA',
                    'UE_IMEI': '987654321098765',
                    'UE_IMEISV': '9876543210987654',
                    'UE_Power': 30,
                    'UE_Range': 200,
                    'UE_AssociationMode': 'auto',
                    'UE_Mobility': False,
                    'UE_GNB_IP': '10.0.0.10',
                    'UE_TunnelInterface': 'uesimtun2',
                    'UE_RadioInterface': 'eth1',
                    'UE_PDUSessions': 3,
                    'UE_SessionType': 'IPv4'
                }
            }
        ],
        'edges': []
    }
    
    # Export to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_path = temp_file.name
        
        try:
            exporter = MininetExporter(test_topology)
            exporter.export_topology(temp_path, skip_save_check=True)
            
            # Read and verify the exported content
            with open(temp_path, 'r') as f:
                exported_content = f.read()
            
            # Verify enhanced UE configuration is present
            required_patterns = [
                'UE_Enhanced = net.addStation(',
                '"GNB_HOSTNAME": "enhanced.gnb"',
                '"APN": "enhanced-internet"',
                '"MSISDN": "1234567890"',
                '"MCC": "999"',
                '"MNC": "99"',
                '"SST": "2"',
                '"SD": "0x123456"',
                '"KEY": "ENHANCED_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC"',
                '"OP_TYPE": "OPC"',
                '"OP": "ENHANCED_OP_E8ED289DEBA952E4283B54E88E6183CA"',
                '"IMEI": "987654321098765"',
                '"IMEISV": "9876543210987654"',
                '"GNB_IP": "10.0.0.10"',
                '"TUNNEL_IFACE": "uesimtun2"',
                '"RADIO_IFACE": "eth1"',
                '"SESSION_TYPE": "IPv4"',
                '"PDU_SESSIONS": "3"',
                '"MOBILITY_ENABLED": "false"',
                'range=200',
                'txpower=30',
                'cls=DockerSta',
                'dimage=\'gradiant/ueransim:3.2.6\'',
                'position=\'100.0,200.0,0\''
            ]
            
            success = True
            for pattern in required_patterns:
                if pattern not in exported_content:
                    print(f"❌ Missing pattern in export: {pattern}")
                    success = False
                else:
                    print(f"✅ Found: {pattern}")
            
            if success:
                print("✅ Enhanced UE export test PASSED")
                print(f"📄 Export saved to: {temp_path}")
            else:
                print("❌ Enhanced UE export test FAILED")
                print(f"📄 Export content saved to: {temp_path}")
                
        except Exception as e:
            print(f"❌ Enhanced UE export test FAILED with error: {e}")
            success = False
        
    return success

def test_ue_docker_environment():
    """Test UE Docker environment variable generation"""
    print("\n🐳 Testing UE Docker Environment Variables...")
    
    test_properties = {
        'UE_GNBHostName': 'docker.gnb',
        'UE_APN': 'docker-internet',
        'UE_MSISDN': '5555555555',
        'UE_KEY': 'DOCKER_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC',
        'UE_IMEI': '111222333444555',
        'UE_TunnelInterface': 'dockertun0',
        'UE_PDUSessions': 2,
        'UE_Mobility': True
    }
    
    config = ConfigurationMapper.map_ue_config(test_properties)
    
    # Simulate the environment dict creation from export
    env_dict = {
        "GNB_HOSTNAME": config.get('gnb_hostname', 'mn.gnb'),
        "APN": config.get('apn', 'internet'),
        "MSISDN": config.get('msisdn', '0000000001'),
        "KEY": config.get('key', '465B5CE8B199B49FAA5F0A2EE238A6BC'),
        "IMEI": config.get('imei', '356938035643803'),
        "TUNNEL_IFACE": config.get('tunnel_iface', 'uesimtun0'),
        "PDU_SESSIONS": str(config.get('pdu_sessions', 1)),
        "MOBILITY_ENABLED": 'true' if config.get('mobility', False) else 'false'
    }
    
    expected_env = {
        "GNB_HOSTNAME": "docker.gnb",
        "APN": "docker-internet", 
        "MSISDN": "5555555555",
        "KEY": "DOCKER_KEY_465B5CE8B199B49FAA5F0A2EE238A6BC",
        "IMEI": "111222333444555",
        "TUNNEL_IFACE": "dockertun0",
        "PDU_SESSIONS": "2",
        "MOBILITY_ENABLED": "true"
    }
    
    success = True
    for key, expected_value in expected_env.items():
        actual_value = env_dict.get(key)
        if actual_value != expected_value:
            print(f"❌ Environment variable error for {key}: expected {expected_value}, got {actual_value}")
            success = False
        else:
            print(f"✅ {key}: {actual_value}")
    
    if success:
        print("✅ UE Docker environment test PASSED")
    else:
        print("❌ UE Docker environment test FAILED")
        
    return success

def test_mininet_wifi_integration():
    """Test mininet-wifi integration parameters"""
    print("\n📡 Testing Mininet-WiFi Integration...")
    
    # Test various wireless configurations
    test_configs = [
        {
            'name': 'High Power UE',
            'properties': {'UE_Power': 50, 'UE_Range': 500, 'UE_AssociationMode': 'manual'},
            'expected': {'txpower': 50.0, 'range': 500.0, 'association': 'manual'}
        },
        {
            'name': 'Low Power UE', 
            'properties': {'UE_Power': 10, 'UE_Range': 50, 'UE_Mobility': True},
            'expected': {'txpower': 10.0, 'range': 50.0, 'mobility': True}
        },
        {
            'name': 'Default UE',
            'properties': {},
            'expected': {'association': 'auto', 'mobility': False}
        }
    ]
    
    success = True
    for test_config in test_configs:
        print(f"\n  Testing {test_config['name']}...")
        config = ConfigurationMapper.map_ue_config(test_config['properties'])
        
        for key, expected_value in test_config['expected'].items():
            actual_value = config.get(key)
            if actual_value != expected_value:
                print(f"    ❌ {key}: expected {expected_value}, got {actual_value}")
                success = False
            else:
                print(f"    ✅ {key}: {actual_value}")
    
    if success:
        print("✅ Mininet-WiFi integration test PASSED")
    else:
        print("❌ Mininet-WiFi integration test FAILED")
        
    return success

def print_test_summary(results):
    """Print a summary of all test results"""
    print("\n" + "="*60)
    print("🧪 ENHANCED UE TEST SUMMARY")
    print("="*60)
    
    test_names = [
        "Enhanced UE Configuration Mapping",
        "Enhanced UE Export", 
        "UE Docker Environment Variables",
        "Mininet-WiFi Integration"
    ]
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")
    
    print("-" * 60)
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Enhanced UE functionality is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the enhanced UE implementation.")
        return False

def main():
    """Run all enhanced UE tests"""
    print("🚀 Starting Enhanced UE Test Suite")
    print("="*60)
    
    # Run all tests
    results = [
        test_enhanced_ue_config_mapping(),
        test_enhanced_ue_export(),
        test_ue_docker_environment(),
        test_mininet_wifi_integration()
    ]
    
    # Print summary
    overall_success = print_test_summary(results)
    
    if overall_success:
        print("\n📋 Next Steps:")
        print("1. Test the enhanced UE UI in the NetFlux5G Editor")
        print("2. Create a topology with enhanced UEs")
        print("3. Export and run in mininet-wifi environment")
        print("4. Verify UE connectivity and 5G functionality")
        print("\n📚 Enhanced UE Features Available:")
        print("- Tabbed UI (UE Config, Wireless, Network)")
        print("- Comprehensive 5G/authentication parameters")
        print("- Wireless power/range/association controls")
        print("- Network interface and PDU session configuration")
        print("- Full Docker environment variable support")
        print("- Mininet-WiFi station integration")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check that enhanced UE UI file exists")
        print("2. Verify configmap.py has enhanced UE mapping")
        print("3. Ensure mininet_export.py includes UE enhancements")
        print("4. Test with simple UE configuration first")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
