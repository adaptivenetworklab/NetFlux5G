#!/bin/bash
# Network performance test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Network Performance Test ==="

# Create network test script
cat > network_test.sh << 'EOF'
#!/bin/bash
apt-get update && apt-get install -y iperf3 iputils-ping curl
echo "Testing connectivity to google.com:"
ping -c 4 google.com
echo "Testing download speed:"
curl -o /dev/null http://speedtest.ftp.otenet.gr/files/test10Mb.db -s -w "Download speed: %{speed_download} bytes/sec\n"
EOF
chmod +x network_test.sh

# Run tests
echo "Docker network performance test:"
docker run --rm -v $(pwd)/network_test.sh:/network_test.sh ubuntu:22.04 /network_test.sh

echo "Containerd network performance test:"
nerdctl run --rm -v $(pwd)/network_test.sh:/network_test.sh ubuntu:22.04 /network_test.sh

echo "Podman network performance test:"
podman run --rm -v $(pwd)/network_test.sh:/network_test.sh ubuntu:22.04 /network_test.sh

echo "LXD network performance test:"
lxc launch ubuntu:22.04 lxd-net-perf
sleep 5
lxc file push network_test.sh lxd-net-perf/root/
lxc exec lxd-net-perf -- bash -c "chmod +x /root/network_test.sh && /root/network_test.sh"
lxc delete -f lxd-net-perf

# Clean up
rm network_test.sh
echo "Network performance tests completed"
