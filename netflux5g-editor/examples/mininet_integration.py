"""
Mininet Integration Example
"""

# Mininet Integration Example
from mininet.net import Mininet
from mininet.node import OVSController
from mininet.link import TCLink

# Create mininet network
net = Mininet(controller=OVSController, link=TCLink)

# Add hosts
h1 = net.addHost('h1', ip='10.0.0.1/24')
h2 = net.addHost('h2', ip='10.0.0.2/24')

# Add switch
s1 = net.addSwitch('s1')

# Add links
net.addLink(h1, s1)
net.addLink(h2, s1)

# Start network
net.start()

# Now use traffic generator with this topology
# ... traffic generation code ...

# Stop network
net.stop()
