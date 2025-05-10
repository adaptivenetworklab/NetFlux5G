#!/bin/bash
# Startup time and image size comparison for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Startup Time and Image Size Comparison ==="

# Function to check image size
get_image_size() {
  local container_type=$1
  local image_name=$2
  local command=$3
  echo "Checking $container_type image size for $image_name:"
  $command
}

# Function to measure startup time
measure_startup_time() {
  local container_type=$1
  local container_name=$2
  local command=$3
  local rm_command=$4
  echo "Measuring $container_type startup time:"
  local start_time=$(date +%s.%N)
  $command
  local end_time=$(date +%s.%N)
  local startup_time=$(echo "$end_time - $start_time" | bc)
  echo "$container_type startup time: $startup_time seconds"
  $rm_command
}

# Docker tests
get_image_size "Docker" "nginx:alpine" "docker image ls nginx:alpine"
measure_startup_time "Docker" "docker-startup" "docker run --name docker-startup -d nginx:alpine" "docker rm -f docker-startup"

# Containerd tests
get_image_size "Containerd" "nginx:alpine" "nerdctl image ls nginx:alpine"
measure_startup_time "Containerd" "containerd-startup" "nerdctl run --name containerd-startup -d nginx:alpine" "nerdctl rm -f containerd-startup"

# Podman tests
get_image_size "Podman" "nginx:alpine" "podman image ls nginx:alpine"
measure_startup_time "Podman" "podman-startup" "podman run --name podman-startup -d nginx:alpine" "podman rm -f podman-startup"

# LXD tests
get_image_size "LXD" "ubuntu:22.04" "lxc image info ubuntu:22.04"
measure_startup_time "LXD" "lxd-startup" "lxc launch ubuntu:22.04 lxd-startup" "lxc delete -f lxd-startup"
