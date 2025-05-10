#!/bin/bash
# Advanced stress testing with sysbench for Docker, Containerd, Podman, and LXD

set -e

echo "=== Advanced Container Stress Testing with sysbench ==="

# Function to run sysbench tests
run_sysbench_test() {
  local container_type=$1
  local container_name=$2
  local run_cmd=$3
  local exec_cmd=$4
  local rm_cmd=$5

  echo "Running sysbench tests for $container_type"
  $run_cmd
  sleep 5
  $exec_cmd "apt-get update && apt-get install -y sysbench"
  echo "Running CPU benchmark test..."
  $exec_cmd "sysbench --test=cpu --cpu-max-prime=20000 run" > "${container_type}_cpu_results.txt"
  echo "Running Memory benchmark test..."
  $exec_cmd "sysbench --test=memory --memory-block-size=1K --memory-total-size=1G run" > "${container_type}_memory_results.txt"
  echo "Running File I/O benchmark test..."
  $exec_cmd "sysbench --test=fileio --file-total-size=1G prepare"
  $exec_cmd "sysbench --test=fileio --file-total-size=1G --file-test-mode=rndrw run" > "${container_type}_fileio_results.txt"
  $exec_cmd "sysbench --test=fileio --file-total-size=1G cleanup"
  $rm_cmd
  echo "-----------------------------------"
}

# Run tests
run_sysbench_test "Docker" "docker-sysbench" \
  "docker run --name docker-sysbench -d ubuntu:22.04 sleep 3600" \
  "docker exec docker-sysbench" \
  "docker rm -f docker-sysbench"

run_sysbench_test "Containerd" "containerd-sysbench" \
  "nerdctl run --name containerd-sysbench -d ubuntu:22.04 sleep 3600" \
  "nerdctl exec containerd-sysbench" \
  "nerdctl rm -f containerd-sysbench"

run_sysbench_test "Podman" "podman-sysbench" \
  "podman run --name podman-sysbench -d ubuntu:22.04 sleep 3600" \
  "podman exec podman-sysbench" \
  "podman rm -f podman-sysbench"

run_sysbench_test "LXD" "lxd-sysbench" \
  "lxc launch ubuntu:22.04 lxd-sysbench" \
  "lxc exec lxd-sysbench --" \
  "lxc delete -f lxd-sysbench"

# Analyze results
echo "Analyzing sysbench results..."
extract_metric() {
  local file=$1
  local metric=$2
  grep "$metric" "$file" | awk '{print $NF}'
}
echo -e "\nCPU Performance Comparison:"
echo "Docker: $(extract_metric Docker_cpu_results.txt "events per second:") events/sec"
echo "Containerd: $(extract_metric Containerd_cpu_results.txt "events per second:") events/sec"
echo "Podman: $(extract_metric Podman_cpu_results.txt "events per second:") events/sec"
echo "LXD: $(extract_metric LXD_cpu_results.txt "events per second:") events/sec"
echo -e "\nMemory Performance Comparison:"
echo "Docker: $(extract_metric Docker_memory_results.txt "transferred") transferred at $(extract_metric Docker_memory_results.txt "MiB/sec")"
echo "Containerd: $(extract_metric Containerd_memory_results.txt "transferred") transferred at $(extract_metric Containerd_memory_results.txt "MiB/sec")"
echo "Podman: $(extract_metric Podman_memory_results.txt "transferred") transferred at $(extract_metric Podman_memory_results.txt "MiB/sec")"
echo "LXD: $(extract_metric LXD_memory_results.txt "transferred") transferred at $(extract_metric LXD_memory_results.txt "MiB/sec")"
echo -e "\nI/O Performance Comparison:"
echo "Docker: $(extract_metric Docker_fileio_results.txt "read, MiB/s:") read MiB/s, $(extract_metric Docker_fileio_results.txt "written, MiB/s:") written MiB/s"
echo "Containerd: $(extract_metric Containerd_fileio_results.txt "read, MiB/s:") read MiB/s, $(extract_metric Containerd_fileio_results.txt "written, MiB/s:") written MiB/s"
echo "Podman: $(extract_metric Podman_fileio_results.txt "read, MiB/s:") read MiB/s, $(extract_metric Podman_fileio_results.txt "written, MiB/s:") written MiB/s"
echo "LXD: $(extract_metric LXD_fileio_results.txt "read, MiB/s:") read MiB/s, $(extract_metric LXD_fileio_results.txt "written, MiB/s:") written MiB/s"

# Clean up
rm -f *_cpu_results.txt *_memory_results.txt *_fileio_results.txt
