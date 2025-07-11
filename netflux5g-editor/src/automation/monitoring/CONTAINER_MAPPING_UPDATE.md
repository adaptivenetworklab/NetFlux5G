# Dashboard Configuration Update for Current Container Setup

## Summary

Dashboard telah disesuaikan untuk merefleksikan container yang sedang berjalan berdasarkan output `docker ps -a` pada sistem aktual.

## Container Mapping Changes

### Monitoring Stack (Unchanged)
- ✅ `netflux5g_prometheus` - Prometheus server
- ✅ `netflux5g_grafana` - Grafana dashboard
- ✅ `netflux5g_cadvisor` - Container metrics
- ✅ `netflux5g_node-exporter` - System metrics
- ✅ `netflux5g_blackbox-exporter` - Network probes

### 5G Core Components (Updated)
**Before (IP-based)** → **After (Container name-based)**
- `172.18.0.3` → `mn.amf1` (AMF)
- `172.18.0.4` → `mn.smf1` (SMF)
- `172.18.0.5` → `mn.upf1` (UPF1)
- Added: `mn.upf2` (UPF2)
- `172.18.0.6` → `mn.nrf1` (NRF)
- `172.18.0.7` → `mn.ausf1` (AUSF)
- `172.18.0.8` → `mn.udm1` (UDM)
- `172.18.0.10` → `mn.udr1` (UDR)
- `172.18.0.9` → `mn.pcf1` (PCF)
- `172.18.0.11` → `mn.bsf1` (BSF)
- `172.18.0.12` → `mn.nssf1` (NSSF)
- Added: `mn.scp1` (SCP)

### UERANSIM Components (Updated)
**Before** → **After**
- `172.18.0.15` → `mn.GNB__1` (gNB1)
- `172.18.0.16` → `mn.GNB__2` (gNB2)
- Added individual UEs:
  - `mn.UE__1` (UE1)
  - `mn.UE__2` (UE2)
  - `mn.UE__3` (UE3)
  - `mn.UE__4` (UE4)
  - `mn.UE__5` (UE5)
  - `mn.UE__6` (UE6)

### Infrastructure Services (Updated)
**Before** → **After**
- `172.25.0.2` → `netflux5g-mongodb` (MongoDB)
- `172.25.0.3` → `netflux5g-webui` (WebUI)
- Added: `netflux5g-onos-controller` (ONOS SDN Controller)

## Configuration Changes Made

### 1. Prometheus Configuration (`prometheus/prometheus.yml`)

#### Updated Scrape Configs:
```yaml
# ICMP Probes - Updated targets
- job_name: "icmp-probe"
  static_configs:
    - targets:
        - mn.amf1        # AMF
        - mn.smf1        # SMF
        - mn.upf1        # UPF1
        - mn.upf2        # UPF2
        - mn.nrf1        # NRF
        - mn.pcf1        # PCF
        - mn.GNB__1      # gNB1
        - mn.GNB__2      # gNB2
        - netflux5g-mongodb
        - netflux5g-webui
        - netflux5g-onos-controller

# 5G Core Containers - New job
- job_name: "5g-core-containers"
  static_configs:
    - targets:
        - mn.amf1:9090
        - mn.smf1:9090
        - mn.upf1:9090
        - mn.upf2:9090
        # ... all 5G core components

# UERANSIM Containers - New job
- job_name: "ueransim-containers"
  static_configs:
    - targets:
        - mn.GNB__1:9091
        - mn.GNB__2:9091
        - mn.UE__1:9091
        # ... all UE instances

# Infrastructure Services - New job
- job_name: "infrastructure-services"
  static_configs:
    - targets:
        - netflux5g-mongodb:27017
        - netflux5g-webui:9999
        - netflux5g-onos-controller:8181
```

### 2. Grafana Dashboard (`dashboard.json`)

#### Updated Variables:
```json
{
  "name": "pod",
  "query": "label_values(container_last_seen{name=~\"(mn\\\\.|netflux5g).*\"}, name)"
}
```
- Filter to show only containers starting with "mn." or "netflux5g"
- This excludes system containers and focuses on relevant components

#### Updated "5G Core Network Functions Status" Panel:
- **11 targets** instead of 5:
  - AMF, SMF, UPF1, UPF2, NRF, PCF (Core functions)
  - gNB1, gNB2 (Radio access)
  - MongoDB, WebUI, ONOS (Infrastructure)

#### New "UE Status Monitor" Panel:
- Added panel to show individual UE status
- Displays UP/DOWN status for all 6 UEs
- Uses container name-based monitoring
- Positioned above success rate panels

#### Updated Panel Layout:
- Adjusted Y positions to accommodate new UE status panel
- Maintained proper spacing between panels
- All panels now correctly aligned

## Benefits of This Update

### 1. **Accurate Monitoring**
- Monitors actual running containers
- No more monitoring of non-existent IP addresses
- Real-time status of current deployment

### 2. **Enhanced Visibility**
- Individual UE monitoring (6 UEs)
- Dual UPF monitoring (UPF1 and UPF2)
- ONOS SDN controller monitoring
- Complete 5G core function coverage

### 3. **Better Organization**
- Container name-based instead of IP-based
- Logical grouping by function type
- Easier identification and troubleshooting

### 4. **Scalability**
- Easy to add/remove UEs
- Support for multiple UPFs
- Flexible container naming convention

## Verification Steps

### 1. Check Prometheus Targets
```bash
# Access Prometheus web UI
http://localhost:9090/targets

# Verify all targets are discovered and UP
```

### 2. Test Dashboard Variables
```bash
# Open Grafana dashboard
http://localhost:3000

# Check pod dropdown shows:
# - mn.amf1, mn.smf1, mn.upf1, mn.upf2, etc.
# - mn.GNB__1, mn.GNB__2
# - mn.UE__1 through mn.UE__6
# - netflux5g-* containers
```

### 3. Validate Network Probes
- All probe targets should show GREEN in "5G Core Network Functions Status"
- Individual UE status should be visible in "UE Status Monitor"

### 4. Container Metrics
- CPU, Memory, Network I/O should show data for selected containers
- Filter by specific container types using $pod variable

## Troubleshooting

### If Targets Show as DOWN:
1. **Check container connectivity**:
   ```bash
   docker exec netflux5g_prometheus ping mn.amf1
   ```

2. **Verify container names**:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

3. **Check network configuration**:
   ```bash
   docker network ls
   docker network inspect <network_name>
   ```

### If Metrics Not Appearing:
1. **Verify container exports metrics**:
   ```bash
   # Check if container has metrics endpoint
   curl http://mn.amf1:9090/metrics
   ```

2. **Check Prometheus scrape errors**:
   - Go to Prometheus UI → Status → Targets
   - Look for error messages

### If UE Panel Empty:
1. **Verify UE containers are running**:
   ```bash
   docker ps | grep "mn.UE"
   ```

2. **Check if UEs export metrics**:
   ```bash
   curl http://mn.UE__1:9091/metrics
   ```

## Future Enhancements

### 1. **Dynamic Discovery**
- Implement service discovery for automatic container detection
- Reduce manual configuration updates

### 2. **Custom Metrics**
- Add Open5GS specific metrics if available
- UERANSIM performance metrics

### 3. **Alerting Rules**
- Update alert rules to use container names
- Add UE-specific alerts

### 4. **Dashboard Improvements**
- Add drill-down capabilities
- Container-specific detailed views
- Performance correlation analysis

This update ensures the monitoring system accurately reflects the actual container deployment and provides comprehensive visibility into the 5G network infrastructure.
