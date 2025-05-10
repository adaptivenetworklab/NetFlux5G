#!/bin/bash
# Runtime overhead test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Runtime Overhead Test ==="

echo "Checking Docker daemon overhead:"
ps aux | grep -i docker | grep -v grep
docker info | grep "daemon:"
systemctl status docker | grep Memory

echo "Checking Containerd daemon overhead:"
ps aux | grep containerd | grep -v grep
systemctl status containerd | grep Memory

echo "Checking Podman overhead (should be minimal as it's daemonless):"
ps aux | grep podman | grep -v grep

echo "Checking LXD daemon overhead:"
ps aux | grep lxd | grep -v grep
systemctl status snap.lxd.daemon | grep Memory

echo "Overall system resources before running containers:"
free -h
echo "CPU load:"
uptime

# Run containers
docker run -d --name docker-overhead nginx:alpine
nerdctl run -d --name containerd-overhead nginx:alpine
podman run -d --name podman-overhead nginx:alpine
lxc launch ubuntu:22.04 lxd-overhead

echo "System resources after running containers:"
sleep 5
free -h
echo "CPU load:"
uptime

# Clean up
docker rm -f docker-overhead
nerdctl rm -f containerd-overhead
podman rm -f podman-overhead
lxc delete -f lxd-overhead
