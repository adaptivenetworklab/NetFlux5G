#!/bin/bash
# Stress test script for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Stress Test ==="

# Function to run stress test and collect metrics
run_stress_test() {
  local container_type=$1
  local container_name=$2
  local run_cmd=$3
  local exec_cmd=$4
  local rm_cmd=$5

  echo "Running stress test for $container_type"
  $run_cmd
  sleep 5
  $exec_cmd "apt-get update && apt-get install -y stress-ng"
  local start_time=$(date +%s)
  $exec_cmd "stress-ng --cpu 1 --vm 1 --vm-bytes 256M --io 1 --timeout 30s"
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  echo "$container_type stress test completed in $duration seconds"
  $rm_cmd
  echo "-----------------------------------"
}

# Docker stress test
run_stress_test "Docker" "docker-stress" \
  "docker run --name docker-stress -d ubuntu:22.04 sleep 3600" \
  "docker exec docker-stress" \
  "docker rm -f docker-stress"

# Containerd stress test
run_stress_test "Containerd" "containerd-stress" \
  "nerdctl run --name containerd-stress -d ubuntu:22.04 sleep 3600" \
  "nerdctl exec containerd-stress" \
  "nerdctl rm -f containerd-stress"

# Podman stress test
run_stress_test "Podman" "podman-stress" \
  "podman run --name podman-stress -d ubuntu:22.04 sleep 3600" \
  "podman exec podman-stress" \
  "podman rm -f podman-stress"

# LXD stress test
run_stress_test "LXD" "lxd-stress" \
  "lxc launch ubuntu:22.04 lxd-stress" \
  "lxc exec lxd-stress --" \
  "lxc delete -f lxd-stress"
