#!/usr/bin/python
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
# from mn_wifi.cli import CLI
from containernet.cli import CLI
# from containernet.net import Containernet
from containernet.node import DockerSta
from containernet.term import makeTerm as makeTerm2
from subprocess import call


def topology(args):
    
    net = Mininet_wifi(topo=None,
                       build=False,
                       link=wmediumd, wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')
    
    # net2 = Containernet()

    info( '\n*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                                  ip='127.0.0.1',
                                  port=6653)

    info( '\n*** Add APs & Switches\n')
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid', failMode='standalone', datapath='user',
                             channel='36', mode='a', position='700.0,335.0,0', range=116, txpower=20, protocols="OpenFlow13")
    ap2 = net.addAccessPoint('ap2', cls=OVSKernelAP, ssid='ap2-ssid', failMode='standalone', datapath='user',
                             channel='36', mode='a', position='350.0,335.0,0', range=116, txpower=20, protocols="OpenFlow13")
    ap3 = net.addAccessPoint('ap3', cls=OVSKernelAP, ssid='ap3-ssid', failMode='standalone', datapath='user',
                             channel='36', mode='a', position='525.0,10.0,0', range=116, txpower=20, protocols="OpenFlow13")

    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch, protocols="OpenFlow13")
    s10 = net.addSwitch('s10', cls=OVSKernelSwitch, protocols="OpenFlow13")

    cwd = os.getcwd() # Current Working Directory

    info( '\n *** Add UPF\n')
    upf1 = net.addStation('upf1', cap_add=["net_admin"], network_mode="open5gs-ueransim_default", privileged=True, publish_all_ports=True,
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/open5gs:latest", position='695.0,335.0,0', range=116)
                        #   volumes=[cwd + "/config/upf1.yaml:/opt/open5gs/etc/open5gs/upf.yaml"])
    upf2 = net.addStation('upf2', cap_add=["net_admin"], network_mode="open5gs-ueransim_default", privileged=True, publish_all_ports=True,
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/open5gs:latest", position='355.0,335.0,0', range=116)
                        #   volumes=[cwd + "/config/upf2.yaml:/opt/open5gs/etc/open5gs/upf.yaml"])

    info( '\n *** Add AMF\n')
    amf1 = net.addStation('amf1', network_mode="open5gs-ueransim_default", cap_add=["net_admin"],  publish_all_ports=True,
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/open5gs:latest", position='520.0,10.0,0', range=116)
                        #   volumes=[cwd + "/config/amf.yaml:/opt/open5gs/etc/open5gs/amf.yaml"])

    info( '\n *** Add gNB\n')
    gnb1 = net.addStation('gnb1', cap_add=["net_admin"], network_mode="open5gs-ueransim_default", publish_all_ports=True, 
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='705.0,335.0,0', range=300, txpower=30,
                          environment={"AMF_IP": "10.0.0.3", "GNB_HOSTNAME": "mn.gnb1", "N2_IFACE":"gnb1-wlan0", "N3_IFACE":"gnb1-wlan0", "RADIO_IFACE":"gnb1-wlan0",
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1"})                               
    gnb2 = net.addStation('gnb2', cap_add=["net_admin"], network_mode="open5gs-ueransim_default", publish_all_ports=True,
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='345.0,335.0,0', range=300, txpower=30,
                          environment={"AMF_IP": "10.0.0.3", "GNB_HOSTNAME": "mn.gnb2", "N2_IFACE":"gnb2-wlan0", "N3_IFACE":"gnb2-wlan0", "RADIO_IFACE":"gnb2-wlan0",
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1"})                   

    info('\n*** Adding docker UE hosts\n')
    # Docker Host (UE) connected to ap1-ssid
    ue1 = net.addStation('ue1', devices=["/dev/net/tun"], cap_add=["net_admin"], range=150, txpower=15, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='700.0,163.0,0', 
                          environment={"GNB_IP": "10.0.0.4", "APN": "internet", "MSISDN": '0000000001',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1", 
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue2 = net.addStation('ue2', devices=["/dev/net/tun"], cap_add=["net_admin"], range=150, txpower=15, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='815.0,335.0,0', 
                          environment={"GNB_IP": "10.0.0.4", "APN": "internet", "MSISDN": '0000000002',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue3 = net.addStation('ue3', devices=["/dev/net/tun"], cap_add=["net_admin"], range=150, txpower=15, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='700.0,513.0,0', 
                          environment={"GNB_IP": "10.0.0.4", "APN": "internet2", "MSISDN": '0000000011',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    
    # Docker Host (UE) connected to ap2-ssid - different power levels
    ue4 = net.addStation('ue4', devices=["/dev/net/tun"], cap_add=["net_admin"], range=100, txpower=10, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='390.0,496.0,0', 
                          environment={"GNB_IP": "10.0.0.5", "APN": "internet", "MSISDN": '0000000003',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue5 = net.addStation('ue5', devices=["/dev/net/tun"], cap_add=["net_admin"], range=100, txpower=10, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='195.0,323.0,0', 
                          environment={"GNB_IP": "10.0.0.5", "APN": "internet2", "MSISDN": '0000000012',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue6 = net.addStation('ue6', devices=["/dev/net/tun"], cap_add=["net_admin"], range=100, txpower=10, network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:latest", position='390.0,180.0,0', 
                          environment={"GNB_IP": "10.0.0.5", "APN": "internet2", "MSISDN": '0000000013',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    
    

    info( '\n*** Connecting Docker nodes to APs\n')
    # amf1.cmd('iw dev amf1-wlan0 connect ap3-ssid')
    # upf1.cmd('iw dev upf1-wlan0 connect ap1-ssid')
    # upf2.cmd('iw dev upf1-wlan0 connect ap2-ssid')
    # gnb1.cmd('iw dev gnb1-wlan0 connect ap1-ssid')
    # gnb2.cmd('iw dev gnb2-wlan0 connect ap2-ssid')
    ue1.cmd('iw dev ue1-wlan0 connect ap1-ssid')
    ue2.cmd('iw dev ue2-wlan0 connect ap1-ssid')
    ue3.cmd('iw dev ue3-wlan0 connect ap1-ssid')
    ue4.cmd('iw dev ue4-wlan0 connect ap2-ssid')
    ue5.cmd('iw dev ue5-wlan0 connect ap2-ssid')
    ue6.cmd('iw dev ue6-wlan0 connect ap2-ssid')

    info("\n*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3)

    info('\n*** Configuring WiFi nodes\n')
    net.configureWifiNodes()

    info( '\n*** Add links\n')
    net.addLink(s10, s8)
    net.addLink(s10, s9)
    net.addLink(s10, s6)
    net.addLink(s8, s5)
    net.addLink(s9, s7)
    net.addLink(s7, s4)
    net.addLink(s5, s1)
    net.addLink(s6, s2)
    net.addLink(s6, s3)
    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s4)
    net.addLink(s5, s2)
    net.addLink(s7, s3)
    net.addLink(s1, ap1)
    net.addLink(s4, ap2)
    net.addLink(s10, ap3)
    net.addLink(ap3, amf1, cls=TCLink)
    net.addLink(ap1, gnb1, cls=TCLink)
    net.addLink(ap1, upf1, cls=TCLink)
    net.addLink(ap2, gnb2, cls=TCLink)
    net.addLink(ap2, upf2, cls=TCLink)
    # net.addLink(s10, amf1, cls=TCLink)
    net.addLink(s2, upf1, cls=TCLink)
    net.addLink(s3, upf2, cls=TCLink)

    net.plotGraph(max_x=1000, max_y=1000)

    info('\n*** Starting network\n')
    net.build()

    info( '\n*** Starting controllers\n')
    c0.start()

    info( '\n*** Starting APs\n')
    net.get('ap1').start([c0])
    net.get('ap2').start([c0])
    net.get('ap3').start([c0])
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])
    net.get('s6').start([c0])
    net.get('s7').start([c0])
    net.get('s8').start([c0])
    net.get('s9').start([c0])
    net.get('s10').start([c0])

    info( '\n *** Capture all initialization flow and slice packet\n')
    Capture1 = cwd + "/capture-initialization-fixed.sh"
    CLI(net, script=Capture1)

    CLI.do_sh(net, 'sleep 20')

    info( '\n *** pingall for testing and flow tables update\n')
    net.pingAll()

    CLI.do_sh(net, 'sleep 10')

    info( '\n *** Post configure Docker UPF connection to Core\n')
    makeTerm2(upf1, cmd="/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/upf1.log")
    makeTerm2(upf2, cmd="/entrypoint.sh open5gs-upfd 2>&1 | tee -a /logging/upf2.log")
    # amf1.cmd('open5gs-amfd | tee /logging/amf.log')

    info( '\n *** Post configure Docker AMF connection to Core\n')
    makeTerm2(amf1, cmd="open5gs-amfd 2>&1 | tee -a /logging/amf.log")
    # amf1.cmd('open5gs-amfd | tee /logging/amf.log')
    
    CLI.do_sh(net, 'sleep 10')

    info( '\n*** Post configure Docker gNB connection to AMF\n')
    makeTerm2(gnb1, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb1.log")
    makeTerm2(gnb2, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb2.log")
    # gnb1.cmd('/entrypoint.sh gnb 2>&1 | tee -a /gnb.log')
    # gnb2.cmd('/entrypoint.sh gnb 2>&1 | tee -a /gnb.log')

    CLI.do_sh(net, 'sleep 10')

    info( '\n*** Post configure Docker UE nodes\n')
    makeTerm2(ue1, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue1.log")
    makeTerm2(ue2, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue2.log")
    makeTerm2(ue3, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue3.log")
    makeTerm2(ue4, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue4.log")
    makeTerm2(ue5, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue5.log")
    makeTerm2(ue6, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue6.log")

    CLI.do_sh(net, 'sleep 20')

    info( '\n ***Route traffic on UE for End-to-End and End-to-Edge Connection\n')
    ue1.cmd('ip route add 10.45.0.0/16 dev uesimtun0')
    ue2.cmd('ip route add 10.45.0.0/16 dev uesimtun0')
    ue3.cmd('ip route add 10.46.0.0/16 dev uesimtun0')
    ue4.cmd('ip route add 10.45.0.0/16 dev uesimtun0')
    ue5.cmd('ip route add 10.46.0.0/16 dev uesimtun0')
    ue6.cmd('ip route add 10.46.0.0/16 dev uesimtun0')

    # info( '\n *** Capture all packet sent through uesimtun0\n')
    # Capture2 = cwd + "/capture-packet-fixed.sh"
    # CLI(net, script=Capture2)

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)