#!/usr/bin/python
import sys
import os
from mininet.net import Mininet
from mininet.link import TCLink, Link
from mininet.node import RemoteController, OVSKernelSwitch
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
                       link=wmediumd,
                       wmediumd_mode=interference,
                       ipBase='10.0.0.0/8')
    
    # net2 = Containernet()

    info( '\n*** Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=RemoteController)

    info( '\n*** Add APs & Switches\n')
    ap1 = net.addAccessPoint('ap1', cls=OVSKernelAP, ssid='ap1-ssid', failMode='standalone', datapath='user', freq=5.0, band='5',
                             channel='36', mode='n', position='700.0,335.0,0', protocols="OpenFlow14")
    ap2 = net.addAccessPoint('ap2', cls=OVSKernelAP, ssid='ap2-ssid', failMode='standalone', datapath='user', freq=5.0, band='5',
                             channel='36', mode='n', position='350.0,335.0,0', protocols="OpenFlow14")
    ap3 = net.addAccessPoint('ap3', cls=OVSKernelAP, ssid='ap3-ssid', failMode='standalone', datapath='user', freq=5.0, band='5', range=80, txpower=4,
                             channel='36', mode='n', position='525.0,10.0,0', protocols="OpenFlow14")

    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch, protocols="OpenFlow14")
    s10 = net.addSwitch('s10', cls=OVSKernelSwitch, protocols="OpenFlow14")

    cwd = os.getcwd() # Current Working Directory

    info( '\n *** Add AMF\n')                             
    amf1 = net.addStation('amf1', network_mode="open5gs-ueransim_default", channel='36', mode='n', freq=5.0, band='5', cap_add=["net_admin"],
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/open5gs:1.0", position='520.0,10.0,0', range=0, 
                          volumes=[cwd + "/config/amf.yaml:/opt/open5gs/etc/open5gs/amf.yaml"])

    info( '\n *** Add gNB\n')
    gnb1 = net.addStation('gnb1', channel='36', mode='n', freq=5.0, band='5', cap_add=["net_admin"], network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='705.0,335.0,0', range=80, txpower=4,
                          environment={"AMF_IP": "10.0.0.1", "GNB_HOSTNAME": "mn.gnb1", "N2_IFACE":"gnb1-wlan0", "N3_IFACE":"gnb1-wlan0", "RADIO_IFACE":"gnb1-wlan0",
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1"})                               
    gnb2 = net.addStation('gnb2', channel='36', mode='n', freq=5.0, band='5', cap_add=["net_admin"], network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='345.0,335.0,0', range=80, txpower=4,
                          environment={"AMF_IP": "10.0.0.1", "GNB_HOSTNAME": "mn.gnb2", "N2_IFACE":"gnb2-wlan0", "N3_IFACE":"gnb2-wlan0", "RADIO_IFACE":"gnb2-wlan0",
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1"})                   

    info('\n*** Adding docker UE hosts\n')
    # Docker Host (UE) connected to ap1-ssid
    ue1 = net.addStation('ue1', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='700.0,163.0,0', range=71, 
                          environment={"GNB_IP": "10.0.0.2", "APN": "internet", "MSISDN": '0000000001',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1", 
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue2 = net.addStation('ue2', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='800.0,335.0,0', range=71,  
                          environment={"GNB_IP": "10.0.0.2", "APN": "internet", "MSISDN": '0000000002',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue3 = net.addStation('ue3', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='700.0,513.0,0', range=71, 
                          environment={"GNB_IP": "10.0.0.2", "APN": "internet2", "MSISDN": '0000000011',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    
    # Docker Host (UE) connected to ap2-ssid
    ue4 = net.addStation('ue4', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='390.0,496.0,0', range=71, 
                          environment={"GNB_IP": "10.0.0.3", "APN": "internet", "MSISDN": '0000000003',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue5 = net.addStation('ue5', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='201.0,323.0,0', range=71, 
                          environment={"GNB_IP": "10.0.0.3", "APN": "internet2", "MSISDN": '0000000012',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    ue6 = net.addStation('ue6', devices=["/dev/net/tun"], cap_add=["net_admin"], channel='36', mode='n', freq=5.0, band='5', network_mode="open5gs-ueransim_default",
                          dcmd="/bin/bash",cls=DockerSta, dimage="adaptive/ueransim:1.0", position='390.0,180.0,0', range=71, 
                          environment={"GNB_IP": "10.0.0.3", "APN": "internet2", "MSISDN": '0000000013',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"}) 

    info( '\n*** Connecting Docker nodes to APs\n')
    amf1.cmd('iw dev amf1-wlan0 connect ap3-ssid')
    gnb1.cmd('iw dev gnb1-wlan0 connect ap1-ssid')
    gnb2.cmd('iw dev gnb2-wlan0 connect ap2-ssid')
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
    net.addLink(s1, ap1, cls=TCLink)
    net.addLink(s2, ap1, cls=TCLink)
    net.addLink(s3, ap2, cls=TCLink)
    net.addLink(s4, ap2, cls=TCLink)
    net.addLink(s10, ap3, cls=TCLink)

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

    info( '\n *** Post configure Docker AMF connection to Core\n')
    makeTerm2(amf1, cmd="open5gs-amfd 2>&1 | tee -a /logging/amf.log")
    # amf1.cmd('open5gs-amfd | tee /logging/amf.log')

    info( '\n *** Capture all initialization flow and slice packet\n')
    Capture1 = cwd + "/capture-initialization-fixed.sh"
    CLI(net, script=Capture1)

    info( '\n *** pingall for testing and flow tables update\n')
    net.pingAll()

    info( '\n*** Post configure Docker gNB connection to AMF\n')
    makeTerm2(gnb1, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb1.log")
    makeTerm2(gnb2, cmd="/entrypoint.sh gnb 2>&1 | tee -a /logging/gnb2.log")
    # gnb1.cmd('/entrypoint.sh gnb 2>&1 | tee -a /gnb.log')
    # gnb2.cmd('/entrypoint.sh gnb 2>&1 | tee -a /gnb.log')

    info( '\n*** Post configure Docker UE nodes\n')
    makeTerm2(ue1, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue1.log")
    makeTerm2(ue2, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue2.log")
    makeTerm2(ue3, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue3.log")
    makeTerm2(ue4, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue4.log")
    makeTerm2(ue5, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue5.log")
    makeTerm2(ue6, cmd="/entrypoint.sh ue 2>&1 | tee -a /logging/ue6.log")
    # ue1.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')
    # ue2.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')
    # ue3.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')
    # ue4.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')
    # ue5.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')
    # ue6.cmd('/entrypoint.sh ue 2>&1 | tee -a /ue.log')

    CLI.do_sh(net, 'sleep 10')

    info( '\n *** Capture all packet sent through uesimtun0\n')
    Capture2 = cwd + "/capture-packet-fixed.sh"
    CLI(net, script=Capture2)

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)

