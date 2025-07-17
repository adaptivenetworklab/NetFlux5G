"""
Basic Usage Example
"""

# Basic Traffic Generation Usage
from manager.traffic_generator import TrafficGeneratorManager
from utils.advanced_traffic_generator import AdvancedTrafficGenerator

# Initialize the traffic generator
main_window = None  # Your main window instance
traffic_manager = TrafficGeneratorManager(main_window)

# Generate traffic for 5 minutes
traffic_manager.generateLoadTraffic(capture_duration=300)

# Check status
status = traffic_manager.getTrafficStatus()
print(f"Traffic running: {status['is_running']}")
