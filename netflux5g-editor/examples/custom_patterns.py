"""
Custom Patterns Example
"""

# Custom Traffic Patterns
from utils.traffic_utils import TrafficPatterns

# Generate 5G eMBB traffic
source = {"name": "ue1", "type": "UE", "properties": {"ip": "172.16.0.100"}}
dest = {"name": "core1", "type": "VGcore", "properties": {"ip": "172.16.0.10"}}

embb_patterns = TrafficPatterns.generate_5g_embb_traffic(source, dest, 300)
urllc_patterns = TrafficPatterns.generate_5g_urllc_traffic(source, dest, 300)
mmtc_patterns = TrafficPatterns.generate_5g_mmtc_traffic(source, dest, 300)
