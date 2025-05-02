#!/usr/bin/env python3
import time
import os
import socket
import psutil
from prometheus_client import start_http_server, Counter, Gauge, Summary

# UERANSIM metrics
connection_status_gauge = Gauge('ueransim_connection_status', 'Connection status (1=connected, 0=disconnected)')
signal_strength_gauge = Gauge('ueransim_signal_strength_dbm', 'Signal strength in dBm')
bandwidth_gauge = Gauge('ueransim_bandwidth_kbps', 'Bandwidth in Kbps')
latency_gauge = Gauge('ueransim_latency_ms', 'Network latency in milliseconds')
cpu_usage_gauge = Gauge('ueransim_cpu_usage_percent', 'CPU usage percentage')
memory_usage_gauge = Gauge('ueransim_memory_usage_bytes', 'Memory usage in bytes')

# Counters for PDU sessions and RRC connections
pdu_session_counter = Counter('ueransim_pdu_sessions_total', 'Total PDU sessions established')
rrc_connection_counter = Counter('ueransim_rrc_connections_total', 'Total RRC connections established')
registration_counter = Counter('ueransim_registrations_total', 'Total registrations')
authentication_counter = Counter('ueransim_authentications_total', 'Total authentications')

# Packet statistics
tx_packets_counter = Counter('ueransim_tx_packets_total', 'Total transmitted packets')
rx_packets_counter = Counter('ueransim_rx_packets_total', 'Total received packets')
tx_bytes_counter = Counter('ueransim_tx_bytes_total', 'Total transmitted bytes')
rx_bytes_counter = Counter('ueransim_rx_bytes_total', 'Total received bytes')

def collect_metrics():
    # Example: collect CPU and memory usage
    cpu_usage_gauge.set(psutil.cpu_percent())
    memory_usage_gauge.set(psutil.virtual_memory().used)

    # In a real scenario, you would parse logs or query an API to get these metrics
    # This is a placeholder for demonstration
    connection_status_gauge.set(1)  # Example: connected
    signal_strength_gauge.set(-80)  # Example: -80 dBm
    bandwidth_gauge.set(20000)      # Example: 20 Mbps
    latency_gauge.set(20)           # Example: 20 ms

    # Simulate packet statistics (in a real scenario, you would get this from network interfaces)
    for nic, stats in psutil.net_io_counters(pernic=True).items():
        if nic.startswith('uesim'):
            tx_bytes_counter._value.set(stats.bytes_sent)
            rx_bytes_counter._value.set(stats.bytes_recv)
            tx_packets_counter._value.set(stats.packets_sent)
            rx_packets_counter._value.set(stats.packets_recv)

def main():
    # Get port from environment or use default
    port = int(os.environ.get('UERANSIM_METRICS_PORT', 9090))

    # Start up the server to expose the metrics
    start_http_server(port)
    print(f"UERANSIM metrics server started on port {port}")

    # Generate some metrics every 15 seconds
    while True:
        collect_metrics()
        time.sleep(15)

if __name__ == '__main__':
    main()
