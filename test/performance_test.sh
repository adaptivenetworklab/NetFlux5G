#!/bin/bash
# CPU and memory performance test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Performance Test ==="

# Create CPU-intensive workload script
cat > cpu_test.sh << 'EOF'
#!/bin/bash
start=$(date +%s.%N)
for i in {1..1000}; do
  echo "Scale test $i"
  for j in {1..50000}; do
    echo $i $j | bc > /dev/null
  done
done
end=$(date +%s.%N)
runtime=$(echo "$end - $start" | bc)
echo "Total runtime: $runtime seconds"
EOF
chmod +x cpu_test.sh

# Run tests
echo "Docker performance test:"
docker run --rm -v $(pwd)/cpu_test.sh:/cpu_test.sh alpine:latest /cpu_test.sh

echo "Containerd performance test:"
nerdctl run --rm -v $(pwd)/cpu_test.sh:/cpu_test.sh alpine:latest /cpu_test.sh

echo "Podman performance test:"
podman run --rm -v $(pwd)/cpu_test.sh:/cpu_test.sh alpine:latest /cpu_test.sh

echo "LXD performance test:"
lxc launch ubuntu:22.04 lxd-perf
sleep 5
lxc file push cpu_test.sh lxd-perf/root/
lxc exec lxd-perf -- bash -c "chmod +x /root/cpu_test.sh && /root/cpu_test.sh"
lxc delete -f lxd-perf

# Clean up
rm cpu_test.sh
echo "Performance tests completed"
