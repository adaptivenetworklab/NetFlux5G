#!/bin/bash
# I/O performance test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container I/O Performance Test ==="

# Create I/O test script
cat > io_test.sh << 'EOF'
#!/bin/bash
echo "Testing write performance..."
time dd if=/dev/zero of=/tmp/test_file bs=1M count=1024 oflag=direct
echo "Testing read performance..."
time dd if=/tmp/test_file of=/dev/null bs=1M iflag=direct
rm /tmp/test_file
EOF
chmod +x io_test.sh

# Run tests
echo "Docker I/O performance test:"
docker run --rm -v $(pwd)/io_test.sh:/io_test.sh ubuntu:22.04 /io_test.sh

echo "Containerd I/O performance test:"
nerdctl run --rm -v $(pwd)/io_test.sh:/io_test.sh ubuntu:22.04 /io_test.sh

echo "Podman I/O performance test:"
podman run --rm -v $(pwd)/io_test.sh:/io_test.sh ubuntu:22.04 /io_test.sh

echo "LXD I/O performance test:"
lxc launch ubuntu:22.04 lxd-io-perf
sleep 5
lxc file push io_test.sh lxd-io-perf/root/
lxc exec lxd-io-perf -- bash -c "chmod +x /root/io_test.sh && /root/io_test.sh"
lxc delete -f lxd-io-perf

# Clean up
rm io_test.sh
echo "I/O performance tests completed"
