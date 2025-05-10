#!/bin/bash
# Installation script for container technologies on Ubuntu 22.04
# Installs Docker, Containerd, Podman, LXD, and testing tools

set -e

# Update package list
echo "Updating package list..."
sudo apt update

# Install Docker
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install the Docker packages.
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install Containerd and nerdctl
echo "Installing Containerd and nerdctl..."
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo systemctl restart containerd
NERDCTL_VERSION="1.0.0"
wget -q "https://github.com/containerd/nerdctl/releases/download/v${NERDCTL_VERSION}/nerdctl-${NERDCTL_VERSION}-linux-amd64.tar.gz"
sudo tar -xzf "nerdctl-${NERDCTL_VERSION}-linux-amd64.tar.gz" -C /usr/local/bin
rm "nerdctl-${NERDCTL_VERSION}-linux-amd64.tar.gz"

# Install Podman
echo "Installing Podman..."
sudo apt install -y podman

# Install LXD
echo "Installing LXD..."
sudo snap install lxd
sudo usermod -aG lxd "$USER"
sudo lxd init --auto

# Install additional tools needed for testing
echo "Installing testing tools..."
sudo apt install -y jq bc stress-ng sysbench iperf3 postgresql-client

echo "Installation completed successfully."
echo "Please log out and log back in for group memberships to take effect."
