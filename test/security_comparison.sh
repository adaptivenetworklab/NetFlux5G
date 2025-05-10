#!/bin/bash
# Security features comparison for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Security Comparison ==="

# Docker security check
echo "Docker security features:"
echo " - Default security profile: AppArmor/SELinux"
echo " - User namespace support: Limited by default"
echo " - Rootless mode: Experimental"
docker info | grep -E "Security|Rootless"

# Containerd security check
echo "Containerd security features:"
echo " - Default security profile: Based on runtime"
echo " - User namespace support: Via runtime"
echo " - Rootless mode: Via runtime"

# Podman security check
echo "Podman security features:"
echo " - Default security profile: AppArmor/SELinux"
echo " - User namespace support: Yes"
echo " - Rootless mode: Native support"
podman info | grep -E "security|rootless"

# LXD security check
echo "LXD security features:"
echo " - Default security profile: AppArmor + seccomp"
echo " - User namespace support: Yes"
echo " - Rootless mode: Via snap"
lxc info | grep -E "driver|security"
