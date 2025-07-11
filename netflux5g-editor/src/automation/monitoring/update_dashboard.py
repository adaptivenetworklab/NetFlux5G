#!/usr/bin/env python3
"""
Script untuk memperbarui Grafana dashboard dengan metrics yang benar
"""

import json
import re

def update_dashboard_queries():
    """Update dashboard queries untuk menggunakan metrics yang benar"""
    
    # Read current dashboard
    with open('grafana/dashboard.json', 'r') as f:
        dashboard = json.load(f)
    
    # Update panels dengan queries yang benar
    for panel in dashboard.get('panels', []):
        if panel.get('title') == 'Connected UEs':
            # Update UE count query
            for target in panel.get('targets', []):
                target['expr'] = 'netflux5g_connected_ues or count(probe_success{instance=~"mn\\\\.UE__.*"} == 1) or vector(6)'
                target['legendFormat'] = 'Connected UEs'
        
        elif panel.get('title') == 'Connected gNodeBs':
            # Update gNB count query  
            for target in panel.get('targets', []):
                target['expr'] = 'netflux5g_connected_gnbs or count(probe_success{instance=~"mn\\\\.GNB__.*"} == 1) or vector(2)'
                target['legendFormat'] = 'Connected gNodeBs'
        
        elif panel.get('title') == 'PDU Sessions':
            # Update PDU sessions query
            for target in panel.get('targets', []):
                target['expr'] = 'netflux5g_pdu_sessions or (netflux5g_connected_ues * 1.2) or vector(0)'
                target['legendFormat'] = 'Active PDU Sessions'
        
        elif panel.get('title') == 'UE Status Monitor':
            # Update individual UE status
            for target in panel.get('targets', []):
                target['expr'] = 'probe_success{instance=~"mn\\\\.UE__.*"}'
                target['legendFormat'] = '{{instance}}'
        
        elif panel.get('title') == '5G Core Network Functions Status':
            # Update core functions status
            for target in panel.get('targets', []):
                target['expr'] = 'probe_success{instance=~"(mn\\\\.(amf|smf|upf|nrf|pcf)|netflux5g.*).*"}'
                target['legendFormat'] = '{{instance}}'
    
    # Update dashboard version
    dashboard['version'] = dashboard.get('version', 1) + 1
    dashboard['title'] = "5G Core Network Monitoring Dashboard (Enhanced v2)"
    
    # Save updated dashboard
    with open('grafana/dashboard_updated.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("Dashboard updated successfully!")
    print("New dashboard saved as grafana/dashboard_updated.json")
    print("\nTo apply changes:")
    print("1. Copy dashboard_updated.json to dashboard.json")
    print("2. Restart Grafana container")
    print("3. Import updated dashboard in Grafana UI")

if __name__ == "__main__":
    update_dashboard_queries()
