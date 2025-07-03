#!/usr/bin/env python

import sys
from mininet.node import OVSKernelSwitch,  Host
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi

def topology(args):
    "Create a network."
    net = Mininet_wifi()

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:02', ip='10.0.0.2/24', position='10,55,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:03', ip='10.0.0.3/24', position='120,55,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:04', ip='10.0.0.4/24', position='200,55,0')
    '''sta4 = net.addStation('sta4', mac='00:00:00:00:00:05', ip='10.0.0.5/24', position='280,120,0')'''

    info("*** adding access point and switch\n")
    ap1 = net.addAccessPoint('ap1', ssid='new-ssid1', mode='g', channel='1',
                             position='120,55,0')
    ap2 = net.addAccessPoint('ap2', ssid='new-ssid2', mode='g', channel='1',
                            position='200,55,0')
    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, position='120,55,0')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch, position='200,55,0')

    c1 = net.addController('c1')


    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring nodes\n")
    net.configureNodes()

    info("*** Associating and Creating links\n")
    net.addLink(ap1, ap2)

    if '-p' not in args:
        net.plotGraph(max_x=350, max_y=350)


    net.startMobility(time=0, mob_rep=5, reverse=False)

    p1, p2, p3= {}, {}, {}
    if '-c' not in args:
        p1 = {'position': '40.0,55.0,0.0'}
        p2 = {'position': '290.0,55.0,0.0'}
        p3 = {'position': '290.0,55.0,0.0'}
        


    net.mobility(sta1, 'start', time=5, position='10,30,0')
    net.mobility(sta1, 'stop', time=10, position='10,40,0')

    '''net.mobility(sta2, 'start', time=15, **p1)
    net.mobility(sta3, 'start', time=15, **p1)
    net.mobility(sta2, 'stop', time=30, **p2)
    net.mobility(sta3, 'stop', time=30, **p3)'''

    '''net.mobility(sta1, 'start', time=25, **p1)
    net.mobility(sta1, 'stop', time=30, **p2)
    net.mobility(sta2, 'start', time=25, **p1)
    net.mobility(sta2, 'stop', time=30, **p2)
    net.mobility(sta3, 'start', time=25, **p1)
    net.mobility(sta3, 'stop', time=30, **p2)

    net.mobility(sta1, 'start', time=35, **p1)
    net.mobility(sta1, 'stop', time=40, **p2)
    net.mobility(sta2, 'start', time=35, **p1)
    net.mobility(sta2, 'stop', time=40, **p2)
    net.mobility(sta3, 'start', time=35, **p1)
    net.mobility(sta3, 'stop', time=40, **p2)
    net.mobility(sta4, 'start', time=35, **p1)
    net.mobility(sta4, 'stop', time=40, **p2)'''


    net.stopMobility(time=100)

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
