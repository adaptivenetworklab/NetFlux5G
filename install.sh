#!/bin/bash

# Check if the script is running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi

# Git configurations
git config --global url."https://github.com/".insteadOf git@github.com:
git config --global url."https://".insteadOf git://

# Install packages
apt update
apt install -y python3-pip git

# Upgrade pip and install Docker
pip3 install -U pip
pip3 install docker

# Clone Mininet-WiFi repository dan install
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv
