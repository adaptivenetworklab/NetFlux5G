"""
Analysis Example Example
"""

# Traffic Analysis Example
from utils.traffic_utils import NetworkAnalyzer

# Analyze captured traffic
capture_dir = "/path/to/captures"
analyzer = NetworkAnalyzer(capture_dir)

# Generate analysis report
report_file = analyzer.analyze_capture_files()
print(f"Analysis report saved to: {report_file}")
