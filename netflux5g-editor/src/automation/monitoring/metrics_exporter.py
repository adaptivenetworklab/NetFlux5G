#!/usr/bin/env python3
"""
Custom metrics exporter untuk 5G network simulation
Menghitung UE dan gNB berdasarkan container aktif
"""

import time
import subprocess
import re
import sys
from prometheus_client import start_http_server, Gauge, Counter, Info
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define metrics
connected_ues = Gauge('netflux5g_connected_ues', 'Number of connected UEs')
connected_gnbs = Gauge('netflux5g_connected_gnbs', 'Number of connected gNodeBs')
active_containers = Gauge('netflux5g_active_containers', 'Number of active containers', ['type'])
pdu_sessions = Gauge('netflux5g_pdu_sessions', 'Number of active PDU sessions')
registration_attempts = Counter('netflux5g_registration_attempts_total', 'Total registration attempts')
registration_success = Counter('netflux5g_registration_success_total', 'Total successful registrations')
network_info = Info('netflux5g_network_info', 'Network deployment information')

def get_active_containers():
    """Get active containers from docker"""
    try:
        # Get UE containers
        ue_result = subprocess.run([
            'docker', 'ps', '--filter', 'name=mn.UE__', 
            '--filter', 'status=running', '--format', '{{.Names}}'
        ], capture_output=True, text=True, timeout=10)
        
        ue_containers = [line.strip() for line in ue_result.stdout.split('\n') if 'mn.UE__' in line]
        ue_count = len(ue_containers)
        
        # Get gNB containers
        gnb_result = subprocess.run([
            'docker', 'ps', '--filter', 'name=mn.GNB__',
            '--filter', 'status=running', '--format', '{{.Names}}'
        ], capture_output=True, text=True, timeout=10)
        
        gnb_containers = [line.strip() for line in gnb_result.stdout.split('\n') if 'mn.GNB__' in line]
        gnb_count = len(gnb_containers)
        
        # Get 5G core containers
        core_result = subprocess.run([
            'docker', 'ps', '--filter', 'name=mn.', 
            '--filter', 'status=running', '--format', '{{.Names}}'
        ], capture_output=True, text=True, timeout=10)
        
        core_containers = [line.strip() for line in core_result.stdout.split('\n') 
                          if line.strip() and 'mn.' in line and 'UE__' not in line and 'GNB__' not in line]
        core_count = len(core_containers)
        
        logger.info(f"Found containers - UEs: {ue_count}, gNBs: {gnb_count}, Core: {core_count}")
        logger.debug(f"UE containers: {ue_containers}")
        logger.debug(f"gNB containers: {gnb_containers}")
        logger.debug(f"Core containers: {core_containers}")
        
        return ue_count, gnb_count, core_count
        
    except subprocess.TimeoutExpired:
        logger.error("Docker command timed out")
        return 0, 0, 0
    except Exception as e:
        logger.error(f"Error getting containers: {e}")
        return 0, 0, 0

def simulate_network_metrics(ue_count, gnb_count):
    """Simulate realistic network metrics based on active containers"""
    try:
        # Simulate PDU sessions (1-2 per UE)
        pdu_count = int(ue_count * 1.2) if ue_count > 0 else 0
        
        # Simulate registration activity
        if ue_count > 0:
            # Simulate periodic registration attempts
            attempts = max(1, ue_count * 0.1)
            success = attempts * 0.95  # 95% success rate
            
            registration_attempts.inc(attempts)
            registration_success.inc(success)
        
        return pdu_count
        
    except Exception as e:
        logger.error(f"Error simulating metrics: {e}")
        return 0

def update_network_info(ue_count, gnb_count, core_count):
    """Update network deployment information"""
    try:
        network_info.info({
            'deployment_type': '5g_simulation',
            'ue_nodes': str(ue_count),
            'gnb_nodes': str(gnb_count),
            'core_functions': str(core_count),
            'last_update': str(int(time.time()))
        })
    except Exception as e:
        logger.error(f"Error updating network info: {e}")

def collect_metrics():
    """Main metrics collection loop"""
    logger.info("Starting metrics collection...")
    
    while True:
        try:
            # Get container counts
            ue_count, gnb_count, core_count = get_active_containers()
            
            # Update basic metrics
            connected_ues.set(ue_count)
            connected_gnbs.set(gnb_count)
            active_containers.labels(type='ue').set(ue_count)
            active_containers.labels(type='gnb').set(gnb_count)
            active_containers.labels(type='core').set(core_count)
            
            # Simulate network metrics
            pdu_count = simulate_network_metrics(ue_count, gnb_count)
            pdu_sessions.set(pdu_count)
            
            # Update network info
            update_network_info(ue_count, gnb_count, core_count)
            
            logger.info(f"Metrics updated - UEs: {ue_count}, gNBs: {gnb_count}, PDU Sessions: {pdu_count}")
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
        
        time.sleep(10)  # Update every 10 seconds

def health_check():
    """Simple health check endpoint"""
    try:
        # Test docker connection
        result = subprocess.run(['docker', 'version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

if __name__ == '__main__':
    try:
        # Health check
        if not health_check():
            logger.error("Docker not available or not accessible")
            sys.exit(1)
        
        # Start metrics server
        start_http_server(8000)
        logger.info("NetFlux5G Metrics Exporter started on port 8000")
        logger.info("Metrics available at http://localhost:8000/metrics")
        
        # Start collecting metrics
        collect_metrics()
        
    except KeyboardInterrupt:
        logger.info("Shutting down metrics exporter...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
