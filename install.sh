#!/bin/bash

USERNAME=$(whoami)
echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/$USERNAME > /dev/null

sudo apt-get update \
    && sudo apt-get upgrade -y \
    && sudo apt-get install -y \
        git \
        make \
        help2man \
        net-tools \
        aptitude \
        build-essential \
        python3 \
        python3-setuptools \
        python3-dev \
        python3-pip \
        python3-venv \
        pyflakes3 \
        tcpdump \
        wpan-tools \
        software-properties-common \
        ansible \
        curl \
        iptables \
        iputils-ping \
        traceroute \
        nano \
        sudo \
        x11-apps \
        xauth \
        xorg \
        openbox \
        libx11-xcb1 \
        libxcb1 \
        libxcb-xinerama0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-sync1 \
        libxcb-xfixes0 \
        libxcb-xkb1 \
        libxrender1 \
        libgl1 \
        libglx0 \
        libgl1-mesa-glx \
        libqt5gui5 \
        qtbase5-dev \
        qt5-qmake \
        libqt5core5a \
        libqt5dbus5 \
        dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

echo "Cloning Mininet-WiFi and Containernet repositories..."

cd ..
git clone https://github.com/intrig-unicamp/mininet-wifi.git
git clone https://github.com/ramonfontes/containernet.git

echo "Installing Mininet-WiFi and Containernet..."

cd mininet-wifi 
git checkout 69c6251
util/install.sh -Wlnfv6

cd ../containernet

sed -i 's/--depth=1//g' util/install.sh
sed -i '183a \
    cd mininet-wifi \
    sudo git checkout 69c6251 \
    cd ..\
' util/install.sh

util/install.sh -W

echo "Installing pip packages..."

cd ../NetFlux5G
pip3 install -r netflux5g-editor/requirements.txt