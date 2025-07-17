"""
Advanced Usage Example
"""

# Advanced Traffic Generation
from utils.advanced_traffic_generator import AdvancedTrafficGenerator

# Create advanced generator
generator = AdvancedTrafficGenerator(main_window)

# Connect signals for status updates
generator.status_updated.connect(lambda msg: print(f"Status: {msg}"))
generator.progress_updated.connect(lambda p: print(f"Progress: {p}%"))
generator.traffic_completed.connect(lambda success, msg: print(f"Complete: {msg}"))

# Start comprehensive traffic generation
generator.start_comprehensive_traffic_generation()
