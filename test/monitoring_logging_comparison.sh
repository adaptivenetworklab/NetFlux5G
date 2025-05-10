#!/bin/bash
# Monitoring and logging capabilities comparison for Docker, Containerd, Podman, and LXD

set -e

echo "=== Monitoring and Logging Capabilities Comparison ==="

# Create log generator script
cat > log_generator.sh << 'EOF'
#!/bin/bash
for i in {1..10}; do
  echo "INFO: Log message $i"
  echo "DEBUG: Detailed information for log $i" >&2
  sleep 1
done
EOF
chmod +x log_generator.sh

echo "1. DOCKER MONITORING AND LOGGING"
echo "--------------------------------"
echo "Docker container stats:"
docker run --name docker-mon -d ubuntu:22.04 sleep 60
docker stats --no-stream docker-mon
echo "Docker logging:"
docker run --name docker-log -v $(pwd)/log_generator.sh:/log_generator.sh ubuntu:22.04 /log_generator.sh
docker logs docker-log
echo "Docker logging drivers:"
docker info | grep "Logging Driver"
echo "Available logging drivers:"
docker info | grep -A 10 "Logging Driver"
docker rm -f docker-mon docker-log >/dev/null 2>&1

echo -e "\n2. CONTAINERD MONITORING AND LOGGING"
echo "------------------------------------"
echo "Containerd container stats:"
nerdctl run --name containerd-mon -d ubuntu:22.04 sleep 60
nerdctl stats --no-stream containerd-mon
echo "Containerd logging:"
nerdctl run --name containerd-log -v $(pwd)/log_generator.sh:/log_generator.sh ubuntu:22.04 /log_generator.sh
nerdctl logs containerd-log
nerdctl rm -f containerd-mon containerd-log >/dev/null 2>&1

echo -e "\n3. PODMAN MONITORING AND LOGGING"
echo "---------------------------------"
echo "Podman container stats:"
podman run --name podman-mon -d ubuntu:22.04 sleep 60
podman stats --no-stream podman-mon
echo "Podman logging:"
podman run --name podman-log -v $(pwd)/log_generator.sh:/log_generator.sh ubuntu:22.04 /log_generator.sh
podman logs podman-log
echo "Podman logging drivers:"
podman info | grep -A 10 "log driver"
podman rm -f podman-mon podman-log >/dev/null 2>&1

echo -e "\n4. LXD MONITORING AND LOGGING"
echo "------------------------------"
echo "LXD container stats:"
lxc launch ubuntu:22.04 lxd-mon
sleep 5
lxc info lxd-mon --resources
echo "LXD logging:"
lxc file push log_generator.sh lxd-mon/root/
lxc exec lxd-mon -- chmod +x /root/log_generator.sh
lxc exec lxd-mon -- /root/log_generator.sh
echo "LXD logging capabilities:"
echo "System logs can be viewed with: lxc console <container>"
echo "Container logs can be viewed with: lxc info <container>"
lxc delete -f lxd-mon >/dev/null 2>&1

# Summary
echo -e "\nMONITORING & LOGGING CAPABILITIES SUMMARY"
echo "------------------------------------------"
echo "Docker:"
echo "  - Rich stats via docker stats command"
echo "  - Multiple logging drivers (json-file, syslog, journald, etc.)"
echo "  - Easy log access via docker logs command"
echo "  - Integration with various monitoring tools"
echo "Containerd:"
echo "  - Basic stats via nerdctl stats command"
echo "  - Standard logging to stdout/stderr"
echo "  - Log access via nerdctl logs command"
echo "  - Focused on being a runtime rather than rich features"
echo "Podman:"
echo "  - Stats similar to Docker via podman stats"
echo "  - Various logging drivers (k8s-file, journald, etc.)"
echo "  - Log access via podman logs command"
echo "  - Daemonless design affects some monitoring approaches"
echo "LXD:"
echo "  - System-container focused metrics"
echo "  - Rich resource statistics (CPU, memory, network, disk)"
echo "  - Different logging approach (system logs within container)"
echo "  - Works more like traditional VMs for monitoring"

# Clean up
rm log_generator.sh
