#!/bin/bash
# Test script to measure basic container operations for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Basic Operations Benchmark ==="

# Docker test
echo "Docker:"
time (docker run --name docker-test -d nginx:alpine)
time (docker stop docker-test)
time (docker start docker-test)
time (docker exec docker-test ls -la)
time (docker rm -f docker-test)

# Containerd test (using nerdctl)
echo "Containerd (nerdctl):"
time (nerdctl run --name containerd-test -d nginx:alpine)
time (nerdctl stop containerd-test)
time (nerdctl start containerd-test)
time (nerdctl exec containerd-test ls -la)
time (nerdctl rm -f containerd-test)

# Podman test
echo "Podman:"
time (podman run --name podman-test -d nginx:alpine)
time (podman stop podman-test)
time (podman start podman-test)
time (podman exec podman-test ls -la)
time (podman rm -f podman-test)

# LXD test
echo "LXD:"
time (lxc launch ubuntu:22.04 lxd-test)
time (lxc stop lxd-test)
time (lxc start lxd-test)
time (lxc exec lxd-test -- ls -la)
time (lxc delete -f lxd-test)
