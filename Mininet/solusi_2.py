#!/usr/bin/python
"""
This is the most simple example to showcase Containernet.
"""
from containernet.net import Containernet
from containernet.node import DockerSta
from containernet.cli import CLI
from containernet.term import makeTerm
from mininet.log import info, setLogLevel


def topology():
    net = Containernet()

    info('*** Adding docker containers\n')
    sta1 = net.addStation('UE1', mac='00:02:00:00:00:01', network_mode="open5gs-ueransim_default",
                          dcmd="/entrypoint.sh && ue -n 1",cls=DockerSta, dimage="openverso/ueransim:3.2.6", cpu_shares=20,
                          environment={"GNB_HOSTNAME": "mn.proxy1", "APN": "internet", "MSISDN": '0000000001',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})
    sta2 = net.addStation('UE2', mac='00:02:00:00:00:02', network_mode="open5gs-ueransim_default",
                          dcmd="/entrypoint.sh && ue -n 1",cls=DockerSta, dimage="openverso/ueransim:3.2.6", cpu_shares=20,
                          environment={"GNB_HOSTNAME": "mn.proxy1", "APN": "internet", "MSISDN": '0000000001',
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1",
                                        "KEY": "465B5CE8B199B49FAA5F0A2EE238A6BC", "OP_TYPE": "OPC", "OP": "E8ED289DEBA952E4283B54E88E6183CA"})                          
    ap1 = net.addAccessPoint('ap1')
    proxy1 = net.addDocker('gNB', mac='00:02:00:00:00:03', network_mode="open5gs-ueransim_default",
                          dcmd="gnb",cls=DockerSta, dimage="openverso/ueransim:3.2.6", cpu_shares=20,
                          environment={"AMF_HOSTNAME": "open5gs-ueransim-amf-1", "GNB_HOSTNAME": "mn.proxy1",
                                        "MCC": "999", "MNC": "70", "SST": "1", "SD": "0xffffff", "TAC": "1"})
    c0 = net.addController('c0')

    info('*** Configuring WiFi nodes\n')
    net.configureWifiNodes()

    info('*** Starting network\n')
    net.start()

    #makeTerm(sta1, cmd="bash -c 'apt-get update && apt-get install iw wireless-tools ethtool iproute2 net-tools -y;'")
    #makeTerm(sta2, cmd="bash -c 'apt-get update && apt-get install iw wireless-tools ethtool iproute2 net-tools -y;'")

    #sta1.cmd('iw dev sta1-wlan0 connect new-ssid')
    #sta2.cmd('iw dev sta2-wlan0 connect new-ssid')

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()

