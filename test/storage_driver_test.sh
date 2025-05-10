#!/bin/bash
# Storage driver comparison for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Storage Driver Comparison ==="

# Check storage drivers
echo "Docker storage driver:"
docker info | grep "Storage Driver"

echo "Containerd storage driver:"
containerd config dump | grep -A 5 plugins.\"io.containerd.grpc.v1.cri\".containerd.runtimes

echo "Podman storage driver:"
podman info | grep -A 5 "storage:"

echo "LXD storage driver:"
lxc storage list
lxc storage show default

# Test volume performance
echo "Testing Docker volume performance:"
docker volume create docker-vol
time docker run --rm -v docker-vol:/data ubuntu:22.04 dd if=/dev/zero of=/data/testfile bs=1M count=100
docker volume rm docker-vol

echo "Testing Containerd volume performance:"
nerdctl volume create containerd-vol
time nerdctl run --rm -v containerd-vol:/data ubuntu:22.04 dd if=/dev/zero of=/data/testfile bs=1M count=100
nerdctl volume rm containerd-vol

echo "Testing Podman volume performance:"
podman volume create podman-vol
time podman run --rm -v podman-vol:/data ubuntu:22.04 dd if=/dev/zero of=/data/testfile bs=1M count=100
podman volume rm podman-vol

echo "Testing LXD storage performance:"
lxc storage volume create default lxd-vol
lxc launch ubuntu:22.04 lxd-storage-test
lxc storage volume attach default lxd-vol lxd-storage-test /data
lxc exec lxd-storage-test -- dd if=/dev/zero of=/data/testfile bs=1M count=100
lxc delete -f lxd-storage-test
lxc storage volume delete default lxd-vol
