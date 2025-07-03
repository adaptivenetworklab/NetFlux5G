#!/usr/bin/env python3
"""
Example topology showing how to use gNB containers with AP functionality in mininet-wifi

This example demonstrates:
1. How to deploy gNB containers that act as Access Points
2. Integration with OpenFlow controllers
3. UE connections to gNB Access Points
4. Network slicing and traffic management

Usage:
    python3 gnb_ap_topology_example.py
"""

import sys
import os
from mininet.net import Mininet
from mininet.link import TCLink, Link, Intf
from mininet.node import RemoteController, OVSKernelSwitch, Host, Node
from mininet.log import setLogLevel, info
from mn_wifi.net import Mininet_wifi
from mn_wifi.node import Station, OVSKernelAP
from mn_wifi.link import wmediumd, Intf
from mn_wifi.wmediumdConnector import interference
from containernet.cli import CLI
from containernet.node import DockerSta
from containernet.term import makeTerm as makeTerm2
from subprocess import call


def topology():
    """Create a topology with gNB containers acting as Access Points"""
    
    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd, wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')

    info('\n*** Adding controller\n')
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           port=6653)

    info('\n*** Add Core Network Components\n')
    # AMF (Access and Mobility Management Function)
    amf1 = net.addStation('amf1', 
                          network_mode="open5gs-ueransim_default", 
                          cap_add=["net_admin"],  
                          publish_all_ports=True,
                          dcmd="/bin/bash",
                          cls=DockerSta, 
                          dimage="adaptive/open5gs:1.0", 
                          position='400.0,300.0,0', 
                          range=116)

    # UPF (User Plane Function) 
    upf1 = net.addStation('upf1', 
                          cap_add=["net_admin"], 
                          network_mode="open5gs-ueransim_default", 
                          privileged=True, 
                          publish_all_ports=True,
                          dcmd="/bin/bash",
                          cls=DockerSta, 
                          dimage="adaptive/open5gs:1.0", 
                          position='600.0,300.0,0', 
                          range=116)

    info('\n*** Add gNB with AP functionality\n')
    # gNB1 with AP capability - acts as both 5G base station and WiFi AP
    gnb1_ap = net.addStation('gnb1', 
                             cap_add=["net_admin"], 
                             network_mode="open5gs-ueransim_default", 
                             privileged=True, 
                             publish_all_ports=True,
                             dcmd="/bin/bash",
                             cls=DockerSta, 
                             dimage="adaptive/ueransim:latest",  # Updated image with AP support
                             position='200.0,200.0,0', 
                             range=200, 
                             txpower=30,
                             environment={
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
                                 "AP_SSID": "5G-gNB1-Hotspot",
                                 "AP_CHANNEL": "6",
                                 "AP_MODE": "n",
                                 "AP_PASSWD": "5g_password",
                                 "AP_BRIDGE_NAME": "br-gnb1",
                                 "AP_FAILMODE": "standalone",
                                 "OPENFLOW_PROTOCOLS": "OpenFlow14",
                                 "OVS_CONTROLLER": "tcp:10.0.0.1:6653"
                             })

    # gNB2 with AP capability 
    gnb2_ap = net.addStation('gnb2', 
                             cap_add=["net_admin"], 
                             network_mode="open5gs-ueransim_default", 
                             privileged=True, 
                             publish_all_ports=True,
                             dcmd="/bin/bash",
                             cls=DockerSta, 
                             dimage="adaptive/ueransim:latest",
                             position='600.0,200.0,0', 
                             range=200, 
                             txpower=30,
                             environment={
                                 "AMF_IP": "10.0.0.3",
                                 "GNB_HOSTNAME": "mn.gnb2",
                                 "N2_IFACE": "gnb2-wlan0",
                                 "N3_IFACE": "gnb2-wlan0",
                                 "RADIO_IFACE": "gnb2-wlan0",
                                 "MCC": "999",
                                 "MNC": "70",
                                 "SST": "1",
                                 "SD": "0xffffff",
                                 "TAC": "2",
                                 # AP Configuration
                                 "AP_ENABLED": "true",
                                 "AP_SSID": "5G-gNB2-Hotspot",
                                 "AP_CHANNEL": "11",
                                 "AP_MODE": "n",
                                 "AP_PASSWD": "5g_password",
                                 "AP_BRIDGE_NAME": "br-gnb2",
                                 "AP_FAILMODE": "standalone",
                                 "OPENFLOW_PROTOCOLS": "OpenFlow14",
                                 "OVS_CONTROLLER": "tcp:10.0.0.1:6653"
                             })

    info('\n*** Add UE devices\n')
    # UE1 - will connect to gNB1's AP
    ue1 = net.addStation('ue1', 
                         devices=["/dev/net/tun"], 
                         cap_add=["net_admin"], 
                         range=150, 
                         txpower=15, 
                         network_mode="open5gs-ueransim_default",
                         dcmd="/bin/bash",
                         cls=DockerSta, 
                         dimage="adaptive/ueransim:latest", 
                         position='200.0,100.0,0',
                         environment={
                             "GNB_IP": "10.0.0.4",
                             "APN": "internet",
                             "MSISDN": '0000000001',
                             "MCC": "999",
                             "MNC": "70",
                             "SST": "1",
                             "SD": "0xffffff",
                             "TAC": "1",
                             "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                             "OP_TYPE": "OPC",
                             "OP": "E8ED289DEBA952E4283B54E88E6183CA"
                         })

    # UE2 - will connect to gNB2's AP  
    ue2 = net.addStation('ue2', 
                         devices=["/dev/net/tun"], 
                         cap_add=["net_admin"], 
                         range=150, 
                         txpower=15, 
                         network_mode="open5gs-ueransim_default",
                         dcmd="/bin/bash",
                         cls=DockerSta, 
                         dimage="adaptive/ueransim:latest", 
                         position='600.0,100.0,0',
                         environment={
                             "GNB_IP": "10.0.0.5",
                             "APN": "internet",
                             "MSISDN": '0000000002',
                             "MCC": "999",
                             "MNC": "70",
                             "SST": "1",
                             "SD": "0xffffff",
                             "TAC": "2",
                             "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                             "OP_TYPE": "OPC",
                             "OP": "E8ED289DEBA952E4283B54E88E6183CA"
                         })

    # Regular WiFi station for testing AP connectivity
    wifi_sta = net.addStation('wifi_sta', 
                              ip='192.168.1.100/24',
                              position='400.0,100.0,0',
                              range=100)

    info('\n*** Add traditional APs for comparison\n')
    # Traditional mininet-wifi AP
    ap1 = net.addAccessPoint('ap1', 
                             cls=OVSKernelAP, 
                             ssid='traditional-ap', 
                             failMode='standalone', 
                             datapath='user',
                             channel='1', 
                             mode='n', 
                             position='400.0,400.0,0', 
                             range=116, 
                             txpower=20, 
                             protocols="OpenFlow14")

    info('\n*** Add switches for core network\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, protocols="OpenFlow14")

    info("\n*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info('\n*** Configuring WiFi nodes\n')
    net.configureWifiNodes()

    info('\n*** Add links\n')
    # Core network links
    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s1, ap1)
    
    # Connect AMF and UPF to core network
    net.addLink(s2, amf1, cls=TCLink)
    net.addLink(s3, upf1, cls=TCLink)
    
    # Connect gNB APs to core network (they will also have wireless interfaces)
    net.addLink(s1, gnb1_ap, cls=TCLink)
    net.addLink(s2, gnb2_ap, cls=TCLink)

    # Note: UE connections to gNB APs will be wireless through the AP functionality

    net.plotGraph(max_x=800, max_y=600)

    info('\n*** Starting network\n')
    net.build()

    info('\n*** Starting controllers\n')
    c0.start()

    info('\n*** Starting switches and APs\n')
    net.get('ap1').start([c0])
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])

    info('\n*** Starting core network components\n')
    # Start AMF
    makeTerm2(amf1, cmd="open5gs-amfd 2>&1 | tee -a /logging/amf.log")
    
    # Start UPF
    makeTerm2(upf1, cmd="/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/upf1.log")

    CLI.do_sh(net, 'sleep 10')

    info('\n*** Starting gNB with AP functionality\n')
    # Start gNB1 with AP mode enabled
    makeTerm2(gnb1_ap, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb1_ap.log")
    
    # Start gNB2 with AP mode enabled  
    makeTerm2(gnb2_ap, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb2_ap.log")

    CLI.do_sh(net, 'sleep 15')

    info('\n*** Connecting devices to gNB APs\n')
    # Connect WiFi station to gNB1's AP
    wifi_sta.cmd('iw dev wifi_sta-wlan0 connect 5G-gNB1-Hotspot')
    
    # UE devices will connect both via 5G (UERANSIM) and WiFi (AP) interfaces
    makeTerm2(ue1, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue1.log")
    makeTerm2(ue2, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue2.log")

    CLI.do_sh(net, 'sleep 10')

    info('\n*** Network setup complete\n')
    info('*** gNB containers are now acting as both 5G base stations and WiFi Access Points\n')
    info('*** You can:\n')
    info('    - Connect to gNB1 AP: SSID="5G-gNB1-Hotspot", Password="5g_password"\n')
    info('    - Connect to gNB2 AP: SSID="5G-gNB2-Hotspot", Password="5g_password"\n')
    info('    - Use OpenFlow controller at tcp:127.0.0.1:6653\n')
    info('    - Monitor traffic and manage QoS through OVS bridges\n')
    info('    - Test handover between gNB APs\n')

    # Show some useful commands
    info('\n*** Useful commands to try:\n')
    info('wifi_sta ping 10.0.0.4  # Ping gNB1\n')
    info('wifi_sta ping 10.0.0.5  # Ping gNB2\n')
    info('ovs-vsctl show          # Show OVS configuration\n')
    info('hostapd_cli -i gnb1-wlan0 status  # Check AP status\n')

    info('\n*** Running CLI\n')
    CLI(net)

    info('\n*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
