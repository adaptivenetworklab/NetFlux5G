# 5G Core Network Monitoring Dashboard Guide

## Dashboard Overview

Dashboard telah dimodifikasi untuk memberikan monitoring yang lebih komprehensif terhadap infrastruktur 5G Core Network. Dashboard ini menyediakan visibilitas real-time terhadap performance, status, dan health dari semua komponen sistem.

## Key Features

### 1. System Overview Panel
- **Total Containers**: Jumlah total container yang berjalan
- **Prometheus Status**: Status monitoring service
- **cAdvisor Status**: Status container monitoring
- **Node Exporter Status**: Status system metrics exporter

### 2. 5G Core Network Functions Status
Panel ini menampilkan status real-time dari komponen-komponen utama:
- **AMF (Access and Mobility Management Function)**: 172.18.0.3
- **PCF (Policy Control Function)**: 172.18.0.9
- **gNB1 (gNodeB)**: 172.18.0.15
- **MongoDB**: 172.25.0.2
- **WebUI**: 172.25.0.3

Status ditampilkan dengan color coding:
- 🟢 **Green (UP)**: Service berjalan normal
- 🔴 **Red (DOWN)**: Service tidak responsif

### 3. Resource Monitoring

#### CPU Usage (%)
- Real-time CPU utilization per container
- Threshold warnings:
  - 🟡 Yellow: >70%
  - 🔴 Red: >90%

#### Memory Usage
- Memory consumption dan limits per container
- Menampilkan both used memory dan memory limits

#### Network I/O
- Incoming (RX) dan outgoing (TX) network traffic
- Rate per second untuk monitoring bandwidth usage

#### Disk I/O
- Read dan write operations per container
- Performance monitoring untuk storage operations

### 4. 5G Core KPIs

#### Connected UEs (User Equipment)
- Gauge menampilkan jumlah UE yang terhubung
- Threshold: Warning di 50+, Critical di 80+

#### Connected gNodeBs
- Jumlah base station yang terhubung ke core network
- Threshold: Warning di 7+, Critical di 9+

#### PDU Sessions
- Active Protocol Data Unit sessions
- Indikator kapasitas session management

#### Network Response Time
- Average round-trip time untuk network probes
- Threshold:
  - 🟡 Yellow: >100ms
  - 🔴 Red: >500ms

### 5. Success Rate Metrics

#### Registration Success Rate
- Persentase keberhasilan registrasi UE
- Threshold:
  - 🔴 Red: <80%
  - 🟡 Yellow: 80-95%
  - 🟢 Green: >95%

#### PDU Session Establishment Success Rate
- Keberhasilan pembentukan session data
- Same threshold sebagai registration

### 6. Advanced Monitoring

#### Container Restart Count
- Monitoring container yang restart (indikator masalah)
- Threshold:
  - 🟡 Yellow: 1+ restart
  - 🔴 Red: 5+ restarts

#### UPF Packet Processing Rate
- Ingress dan egress packet processing per second
- Critical untuk monitoring data plane performance

#### UPF Throughput
- Bytes per second untuk data transfer monitoring
- Bandwidth utilization tracking

#### System Load Average
- Host system load (1m, 5m, 15m averages)
- Threshold:
  - 🟡 Yellow: >1.0
  - 🔴 Red: >2.0

#### Error Rate & Alerts
- Prometheus notifications dan container restart events
- Log-based monitoring untuk troubleshooting

## Dashboard Variables

### Pod Selection ($pod)
- Filter untuk memilih container/pod tertentu
- Support multi-selection dan "All" option
- Auto-refresh setiap 30 detik

### Target Selection ($target)
- Filter untuk probe targets (IP addresses)
- Useful untuk network connectivity monitoring

### Interval ($interval)
- Customizable time interval untuk rate calculations
- Options: 1m, 5m, 10m, 30m, 1h
- Default: 5m

## Time Range Settings

- **Default Range**: Last 1 hour
- **Auto Refresh**: 30 seconds
- **Refresh Intervals**: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d

## Alert Thresholds

### Critical Alerts (Red)
- CPU usage >90%
- Memory usage >90%
- Network response time >500ms
- Success rate <80%
- Container restarts >5
- System load >2.0

### Warning Alerts (Yellow)
- CPU usage >70%
- Memory usage >70%
- Network response time >100ms
- Success rate 80-95%
- Container restarts ≥1
- System load >1.0

## Best Practices

1. **Regular Monitoring**: Check dashboard setiap 15-30 menit
2. **Alert Response**: Investigate immediately ketika ada red alerts
3. **Trending**: Monitor trends untuk capacity planning
4. **Documentation**: Log significant events dan responses

## Troubleshooting Common Issues

### No Data Appearing
1. Check Prometheus data source configuration
2. Verify container metrics are being collected
3. Ensure network connectivity to monitoring targets

### High Resource Usage
1. Check individual container resource consumption
2. Monitor for memory leaks atau CPU spikes
3. Scale resources jika diperlukan

### Low Success Rates
1. Check network connectivity antar services
2. Verify 5G Core configuration
3. Monitor untuk error messages di logs

## Customization

Dashboard dapat disesuaikan dengan:
- Menambah panel untuk metrics tambahan
- Modifikasi threshold values sesuai environment
- Tambah annotation untuk deployment events
- Custom alerting rules
