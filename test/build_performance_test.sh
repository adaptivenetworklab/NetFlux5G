#!/bin/bash
# Image build performance test for Docker, Containerd, and Podman

set -e

echo "=== Container Build Performance Test ==="

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y nginx
RUN mkdir -p /var/www/html
COPY . /var/www/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create sample content
mkdir -p html
for i in {1..10}; do
  echo "<h1>Test page $i</h1>" > html/page$i.html
done

# Run tests
echo "Testing Docker build performance:"
time docker build -t docker-test-image .

echo "Testing Containerd (nerdctl) build performance:"
time nerdctl build -t containerd-test-image .

echo "Testing Podman build performance:"
time podman build -t podman-test-image .

echo "LXD doesn't have a native build capability like Dockerfile"

# Clean up
docker rmi docker-test-image
nerdctl rmi containerd-test-image
podman rmi podman-test-image
rm -rf Dockerfile html
