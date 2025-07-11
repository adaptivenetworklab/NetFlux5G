# Enhanced 5G Core Network Monitoring System

## Overview

Sistem monitoring ini telah dimodifikasi untuk memberikan visibilitas yang komprehensif terhadap infrastruktur 5G Core Network. Sistem ini menggunakan stack monitoring modern dengan Prometheus, Grafana, dan Alertmanager.

## Components

### 1. Prometheus
- **Port**: 9090
- **Function**: Metrics collection dan storage
- **Config**: `prometheus/prometheus.yml`
- **Alert Rules**: `prometheus/alert_rules.yml`

### 2. Grafana
- **Port**: 3000
- **Function**: Data visualization dan dashboards
- **Dashboard**: `grafana/dashboard.json`
- **Guide**: `grafana/DASHBOARD_GUIDE.md`

### 3. Alertmanager
- **Port**: 9093
- **Function**: Alert routing dan notifications
- **Config**: `prometheus/alertmanager.yml`

### 4. Node Exporter
- **Port**: 9100
- **Function**: System metrics collection

### 5. cAdvisor
- **Port**: 8080
- **Function**: Container metrics collection

### 6. Blackbox Exporter
- **Port**: 9115
- **Function**: Network connectivity probes

## Key Monitoring Features

### Infrastructure Monitoring
- ✅ CPU, Memory, Disk, Network usage per container
- ✅ System load average dan resource utilization
- ✅ Container restart tracking
- ✅ Network connectivity probes

### 5G Core Specific Monitoring
- ✅ Connected UEs count
- ✅ Connected gNodeBs count
- ✅ PDU Sessions monitoring
- ✅ Registration success rates
- ✅ Session establishment success rates
- ✅ UPF packet processing dan throughput

### Alerting System
- ✅ Multi-tier alerting (Warning/Critical)
- ✅ Email notifications
- ✅ Slack integration (configurable)
- ✅ Webhook support
- ✅ Alert grouping dan deduplication

## Quick Start

### 1. Start Monitoring Stack

```bash
# Navigate to monitoring directory
cd netflux5g-editor/src/automation/monitoring

# Start monitoring services
./run.sh
```

### 2. Access Dashboards

- **Grafana**: <http://localhost:3000>
  - Username: admin
  - Password: admin (change on first login)
- **Prometheus**: <http://localhost:9090>
- **Alertmanager**: <http://localhost:9093>

### 3. Import Dashboard

1. Login to Grafana
2. Go to Dashboards → Import
3. Upload `grafana/dashboard.json`
4. Configure Prometheus data source if needed

**Note**: Dashboard has been configured for current container setup:
- 5G Core: mn.amf1, mn.smf1, mn.upf1, mn.upf2, mn.nrf1, mn.pcf1, etc.
- UERANSIM: mn.GNB__1, mn.GNB__2, mn.UE__1 through mn.UE__6
- Infrastructure: netflux5g-mongodb, netflux5g-webui, netflux5g-onos-controller

## Configuration

### Prometheus Targets

Edit `prometheus/prometheus.yml` untuk menambah atau mengubah monitoring targets:

```yaml
scrape_configs:
  - job_name: 'your-service'
    static_configs:
      - targets: ['your-service:port']
```

### Alert Rules

Modify `prometheus/alert_rules.yml` untuk customization alert thresholds:

```yaml
- alert: YourAlert
  expr: your_metric > threshold
  for: duration
  labels:
    severity: warning|critical
  annotations:
    summary: "Alert description"
```

### Notification Channels

Update `prometheus/alertmanager.yml` untuk konfigurasi notifications:

- Email SMTP settings
- Slack webhook URLs
- Custom webhook endpoints

## Dashboard Customization

### Adding New Panels

1. Open Grafana dashboard
2. Click "Add Panel"
3. Configure query menggunakan Prometheus metrics
4. Set visualization type dan styling
5. Save dashboard

### Modifying Thresholds

1. Edit panel settings
2. Go to "Field" → "Thresholds"
3. Adjust warning dan critical values
4. Update colors accordingly

## Troubleshooting

### Common Issues

1. **No Data in Grafana**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Verify data source configuration in Grafana
   ```

2. **Alerts Not Firing**
   ```bash
   # Check Prometheus rules
   curl http://localhost:9090/api/v1/rules
   
   # Verify alertmanager configuration
   curl http://localhost:9093/api/v1/status
   ```

3. **High Resource Usage**
   ```bash
   # Check metrics retention
   # Adjust scrape intervals
   # Monitor Prometheus storage
   ```

### Log Locations

- Prometheus: `/var/log/prometheus/`
- Grafana: `/var/log/grafana/`
- Alertmanager: `/var/log/alertmanager/`

## Metrics Reference

### Container Metrics (cAdvisor)
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage
- `container_network_receive_bytes_total`: Network RX
- `container_network_transmit_bytes_total`: Network TX
- `container_start_time_seconds`: Container start time

### System Metrics (Node Exporter)
- `node_load1`, `node_load5`, `node_load15`: System load
- `node_memory_MemAvailable_bytes`: Available memory
- `node_filesystem_avail_bytes`: Disk space available
- `node_cpu_seconds_total`: CPU time

### 5G Core Metrics (Custom)
- `open5gs_amf_connected_ues`: Connected UEs
- `open5gs_amf_connected_gnbs`: Connected gNodeBs
- `open5gs_smf_pdu_sessions`: Active PDU sessions
- `open5gs_amf_registration_success_total`: Registration successes
- `open5gs_smf_pdu_session_establishment_success_total`: Session successes
- `open5gs_upf_ingress_packets_total`: UPF ingress packets
- `open5gs_upf_egress_packets_total`: UPF egress packets

### Network Probe Metrics (Blackbox)
- `probe_success`: Service reachability
- `probe_duration_seconds`: Response time
- `probe_http_status_code`: HTTP status (if applicable)

## Best Practices

### 1. Regular Maintenance
- Monitor disk space untuk metrics storage
- Regular backup dari Grafana dashboards
- Update thresholds berdasarkan historical data

### 2. Alert Management
- Tune alert thresholds untuk mengurangi false positives
- Implement escalation procedures
- Document common incident responses

### 3. Performance Optimization
- Adjust scrape intervals berdasarkan requirements
- Use recording rules untuk complex queries
- Implement metrics retention policies

### 4. Security
- Change default passwords
- Enable authentication untuk external access
- Secure inter-service communication

## Support

Untuk support atau questions:
1. Check `DASHBOARD_GUIDE.md` untuk dashboard usage
2. Review Prometheus documentation untuk metrics queries
3. Consult Grafana documentation untuk visualization options

## Contributing

Untuk contribute ke monitoring system:
1. Test changes di development environment
2. Document new metrics atau panels
3. Update alert thresholds appropriately
4. Validate dashboard export/import functionality
