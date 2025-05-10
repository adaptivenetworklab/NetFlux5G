#!/bin/bash
# Test script to evaluate resource isolation for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Resource Isolation Test ==="

# Docker with resource limits
echo "Docker with Resource Limits:"
docker run --name docker-limited -d --memory=512m --cpus=1 nginx:alpine
docker stats --no-stream docker-limited
docker rm -f docker-limited

# Containerd with resource limits
echo "Containerd with Resource Limits:"
nerdctl run --name containerd-limited -d --memory=512m --cpus=1 nginx:alpine
nerdctl stats --no-stream containerd-limited
nerdctl rm -f containerd-limited

# Podman with resource limits
echo "Podman with Resource Limits:"
podman run --name podman-limited -d --memory=512m --cpus=1 nginx:alpine
podman stats --no-stream podman-limited
podman rm -f podman-limited

# LXD with resource limits
echo "LXD with Resource Limits:"
lxc launch ubuntu:22.04 lxd-limited --config limits.memory=512MiB --config limits.cpu=1
sleep 5
lxc info lxd-limited --resources
lxc delete -f lxd-limited
