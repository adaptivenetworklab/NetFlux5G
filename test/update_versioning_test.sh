#!/bin/bash
# Image updates and versioning test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Container Image Updates and Versioning Test ==="

# Create Dockerfiles
cat > Dockerfile.versioning << 'EOF'
FROM ubuntu:22.04
LABEL version="1.0"
RUN apt-get update && apt-get install -y nginx
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

cat > Dockerfile.versioning.update << 'EOF'
FROM ubuntu:22.04
LABEL version="2.0"
RUN apt-get update && apt-get install -y nginx curl
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

echo "1. DOCKER IMAGE VERSIONING"
echo "-------------------------"
docker build -t version-test:1.0 -f Dockerfile.versioning .
docker image inspect version-test:1.0 | grep -A 3 Labels
docker history version-test:1.0 --no-trunc | head -4
docker build -t version-test:2.0 -f Dockerfile.versioning.update .
docker image inspect version-test:2.0 | grep -A 3 Labels
docker history version-test:2.0 --no-trunc | head -4
echo "Docker image size comparison:"
docker images | grep version-test

echo -e "\n2. CONTAINERD IMAGE VERSIONING"
echo "------------------------------"
nerdctl build -t version-test:1.0-containerd -f Dockerfile.versioning .
nerdctl image inspect version-test:1.0-containerd | grep -A 3 Labels
nerdctl history version-test:1.0-containerd | head -4
nerdctl build -t version-test:2.0-containerd -f Dockerfile.versioning.update .
nerdctl image inspect version-test:2.0-containerd | grep -A 3 Labels
nerdctl history version-test:2.0-containerd | head -4
echo "Containerd image size comparison:"
nerdctl images | grep version-test

echo -e "\n3. PODMAN IMAGE VERSIONING"
echo "--------------------------"
podman build -t version-test:1.0-podman -f Dockerfile.versioning .
podman image inspect version-test:1.0-podman | grep -A 3 Labels
podman history version-test:1.0-podman | head -4
podman build -t version-test:2.0-podman -f Dockerfile.versioning.update .
podman image inspect version-test:2.0-podman | grep -A 3 Labels
podman history version-test:2.0-podman | head -4
echo "Podman image size comparison:"
podman images | grep version-test

echo -e "\n4. LXD IMAGE VERSIONING"
echo "-----------------------"
echo "LXD uses a different approach to image management and versioning:"
lxc launch ubuntu:22.04 version-test-lxd
lxc exec version-test-lxd -- apt-get update
lxc exec version-test-lxd -- apt-get install -y nginx
lxc snapshot version-test-lxd v1.0
lxc info version-test-lxd | grep -A 6 Snapshots
lxc exec version-test-lxd -- apt-get install -y curl
lxc snapshot version-test-lxd v2.0
lxc info version-test-lxd | grep -A 10 Snapshots
echo "LXD snapshot comparison:"
lxc info version-test-lxd | grep -A 10 Snapshots
lxc delete -f version-test-lxd

# Summary
echo -e "\nIMAGE UPDATE AND VERSIONING SUMMARY"
echo "-----------------------------------"
echo "Docker:"
echo "  - Layered image approach with cached layers between versions"
echo "  - Image tagging for version management"
echo "  - History and inspect commands for image metadata"
echo "Containerd:"
echo "  - Similar layered approach to Docker"
echo "  - OCI-compatible image format"
echo "  - Similar tagging and inspection capabilities via nerdctl"
echo "Podman:"
echo "  - Compatible with Docker images"
echo "  - Same layering and tagging approach"
echo "  - Similar history and inspect commands"
echo "LXD:"
echo "  - Image-based approach with VM-like snapshots"
echo "  - Different conceptual model for updates (snapshots vs layers)"
echo "  - Snapshots can be used to track versions of system containers"

# Clean up
rm Dockerfile.versioning Dockerfile.versioning.update
