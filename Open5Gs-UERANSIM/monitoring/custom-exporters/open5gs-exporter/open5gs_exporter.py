#!/usr/bin/env python3
import time
import os
import socket
import psutil
import re
from prometheus_client import start_http_server, Counter, Gauge, Summary

# Open5GS metrics
subscribers_gauge = Gauge('open5gs_subscribers_total', 'Total number of subscribers')
active_sessions_gauge = Gauge('open5gs_active_sessions', 'Number of active sessions')
cpu_usage_gauge = Gauge('open5gs_cpu_usage_percent', 'CPU usage percentage')
memory_usage_gauge = Gauge('open5gs_memory_usage_bytes', 'Memory usage in bytes')
uptime_gauge = Gauge('open5gs_uptime_seconds', 'Uptime in seconds')

# Counters for various events
pdu_sessions_counter = Counter('open5gs_pdu_sessions_total', 'Total PDU sessions established')
authentication_counter = Counter('open5gs_authentication_total', 'Total authentication procedures')
registration_counter = Counter('open5gs_registration_total', 'Total registration procedures')
service_request_counter = Counter('open5gs_service_request_total', 'Total service requests')

# Performance metrics
request_latency = Summary('open5gs_request_latency_seconds', 'Request latency in seconds')

def collect_metrics():
    # Example: collect CPU and memory usage
    cpu_usage_gauge.set(psutil.cpu_percent())
    memory_usage_gauge.set(psutil.virtual_memory().used)

    # Example: collect uptime
    uptime_gauge.set(time.time() - psutil.boot_time())

    # In a real scenario, you would parse logs or query an API to get these metrics
    # This is a placeholder for demonstration
    subscribers_gauge.set(100)  # Example value
    active_sessions_gauge.set(50)  # Example value

def main():
    # Get port from environment or use default
    port = int(os.environ.get('OPEN5GS_METRICS_PORT', 9090))

    # Start up the server to expose the metrics
    start_http_server(port)
    print(f"Metrics server started on port {port}")

    # Generate some metrics every 15 seconds
    while True:
        collect_metrics()
        time.sleep(15)

if __name__ == '__main__':
    main()
