#!/usr/bin/env python3
"""
Test script for enhanced gNB with Access Point functionality
This demonstrates the new gNB AP features in mininet-wifi
"""

from mn_wifi.net import Mininet_wifi
from mn_wifi.node import OVSKernelAP
from containernet.node import DockerSta
from containernet.cli import CLI
from mininet.node import RemoteController
from mininet.log import setLogLevel, info

def test_gnb_ap_topology():
    """Test topology with gNB acting as Access Point"""
    
    net = Mininet_wifi(topo=None, build=False, ipBase='10.0.0.0/8')
    
    info('*** Adding controller\n')
    c0 = net.addController(name='c0', controller=RemoteController)
    
    info('*** Add enhanced gNB with AP functionality\n')
    gnb1 = net.addStation('gnb1',
                          cap_add=["net_admin"],
                          network_mode="open5gs-ueransim_default",
                          privileged=True,
                          publish_all_ports=True,
                          dcmd="/bin/bash",
                          cls=DockerSta,
                          dimage="adaptive/ueransim:latest",
                          volumes=["/sys:/sys", "/lib/modules:/lib/modules", "/sys/kernel/debug:/sys/kernel/debug"],
                          position='350.0,335.0,0',
                          range=300,
                          txpower=30,
                          environment={
                              # 5G Configuration
                              "AMF_IP": "10.0.0.3",
                              "GNB_HOSTNAME": "mn.gnb1",
                              "N2_IFACE": "gnb1-wlan0",
                              "N3_IFACE": "gnb1-wlan0", 
                              "RADIO_IFACE": "gnb1-wlan0",
                              "MCC": "999",
                              "MNC": "70",
                              "SST": "1",
                              "SD": "0xffffff",
                              "TAC": "1",
                              
                              # AP Configuration
                              "AP_ENABLED": "true",
                              "AP_SSID": "gNB-5G-Cell-1",
                              "AP_CHANNEL": "6",
                              "AP_MODE": "g",
                              "AP_PASSWD": "",  # Open network
                              "AP_BRIDGE_NAME": "br-gnb1",
                              "OVS_CONTROLLER": "tcp:127.0.0.1:6633",
                              "AP_FAILMODE": "standalone",
                              "OPENFLOW_PROTOCOLS": "OpenFlow14"
                          })
                          
    info('*** Adding UE nodes\n')
    ue1 = net.addStation('ue1',
                         devices=["/dev/net/tun"],
                         cap_add=["net_admin"],
                         range=150,
                         txpower=15,
                         network_mode="open5gs-ueransim_default",
                         dcmd="/bin/bash",
                         cls=DockerSta,
                         dimage="adaptive/ueransim:latest",
                         position='400.0,285.0,0',
                         environment={
                             "GNB_IP": "10.0.0.4",
                             "APN": "internet",
                             "MSISDN": "0000000001",
                             "MCC": "999",
                             "MNC": "70",
                             "SST": "1",
                             "SD": "0xffffff",
                             "TAC": "1",
                             "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                             "OP_TYPE": "OPC",
                             "OP": "E8ED289DEBA952E4283B54E88E6183CA"
                         })
    
    ue2 = net.addStation('ue2',
                         devices=["/dev/net/tun"],
                         cap_add=["net_admin"],
                         range=150,
                         txpower=15,
                         network_mode="open5gs-ueransim_default",
                         dcmd="/bin/bash",
                         cls=DockerSta,
                         dimage="adaptive/ueransim:latest",
                         position='300.0,385.0,0',
                         environment={
                             "GNB_IP": "10.0.0.4",
                             "APN": "internet",
                             "MSISDN": "0000000002",
                             "MCC": "999",
                             "MNC": "70",
                             "SST": "1",
                             "SD": "0xffffff",
                             "TAC": "1",
                             "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                             "OP_TYPE": "OPC",
                             "OP": "E8ED289DEBA952E4283B54E88E6183CA"
                         })
    
    info('\n*** Configuring WiFi nodes\n')
    net.configureWifiNodes()
    
    info('\n*** Starting network\n')
    net.build()
    
    info('\n*** Starting controllers\n')
    c0.start()
    
    info('\n*** Starting gNB with AP functionality\n')
    # The gNB container will automatically set up AP functionality
    # due to AP_ENABLED=true in environment variables
    
    info('\n*** Connecting UEs to gNB AP\n')
    # UEs should automatically connect to the gNB's AP
    # This simulates both 5G radio connection and WiFi association
    
    info('\n*** Network ready\n')
    info('The gNB is now acting as both:\n')
    info('1. A 5G base station (gNB)\n')
    info('2. A WiFi Access Point with SSID "gNB-5G-Cell-1"\n')
    info('3. An OpenFlow switch connected to controller\n')
    info('\nUse the CLI to interact with the network:\n')
    info('- gnb1 ovs-vsctl show  # Check OVS bridge\n')
    info('- gnb1 iw dev          # Check wireless interfaces\n')
    info('- ue1 iw dev ue1-wlan0 connect gNB-5G-Cell-1  # Connect UE to AP\n')
    
    CLI(net)
    
    info('\n*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    print("Enhanced gNB with Access Point functionality test")
    print("Make sure to run: sudo modprobe mac80211_hwsim radios=10")
    print("And have the enhanced UERANSIM Docker image built")
    test_gnb_ap_topology()
