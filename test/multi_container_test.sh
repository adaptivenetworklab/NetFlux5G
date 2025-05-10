#!/bin/bash
# Multi-container application test for Docker, Containerd, Podman, and LXD

set -e

echo "=== Multi-Container Application Test ==="

# Create Docker Compose file
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    depends_on:
      - db
  db:
    image: postgres:alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_USER: user
      POSTGRES_DB: testdb
EOF

# Create Podman pod YAML
cat > podman-pod.yml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: multi-app
spec:
  containers:
  - name: web
    image: nginx:alpine
    ports:
    - containerPort: 80
      hostPort: 8081
  - name: db
    image: postgres:alpine
    env:
    - name: POSTGRES_PASSWORD
      value: password
    - name: POSTGRES_USER
      value: user
    - name: POSTGRES_DB
      value: testdb
EOF

# Test Docker Compose
echo "Testing Docker Compose multi-container deployment:"
time docker-compose up -d
sleep 5
docker-compose ps
curl -s http://localhost:8080 > /dev/null && echo "Docker Compose web container accessible"
time docker-compose down -v

# Test Containerd with nerdctl compose
echo "Testing Nerdctl compose multi-container deployment:"
time nerdctl compose up -d
sleep 5
nerdctl compose ps
curl -s http://localhost:8080 > /dev/null && echo "Nerdctl compose web container accessible"
time nerdctl compose down -v

# Test Podman pod
echo "Testing Podman pod deployment:"
time podman play kube podman-pod.yml
sleep 5
podman pod ps
curl -s http://localhost:8081 > /dev/null && echo "Podman pod web container accessible"
time podman pod rm -f multi-app

# Test LXD
echo "Testing LXD deployment:"
lxc profile create web-profile
lxc profile device add web-profile proxy0 proxy listen=tcp:0.0.0.0:8082 connect=tcp:127.0.0.1:80
time lxc launch ubuntu:22.04 lxd-web --profile web-profile
time lxc launch ubuntu:22.04 lxd-db
lxc exec lxd-web -- bash -c "apt-get update && apt-get install -y nginx && systemctl start nginx"
lxc exec lxd-db -- bash -c "apt-get update && apt-get install -y postgresql && systemctl start postgresql"
sleep 5
lxc list
curl -s http://localhost:8082 > /dev/null && echo "LXD web container accessible"
time lxc delete -f lxd-web lxd-db
lxc profile delete web-profile

# Clean up
rm docker-compose.yml podman-pod.yml
