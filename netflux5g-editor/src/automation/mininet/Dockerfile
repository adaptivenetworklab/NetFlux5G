FROM ubuntu:20.04

ENV TZ=Asia/Jakarta
ENV DEBIAN_FRONTEND=noninteractive

# Install base packages and dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
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
    wireless-tools \
    rfkill \
    iw \
    wpasupplicant \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/netflux5g

# Clone required repositories
RUN git clone https://github.com/intrig-unicamp/mininet-wifi.git \
    && git clone https://github.com/containernet/containernet.git

# Copy custom install script
COPY ./install.sh /app/netflux5g/mininet-wifi/util/install.sh
RUN chmod +x /app/netflux5g/mininet-wifi/util/install.sh

# Install Containernet first
WORKDIR /app/netflux5g/containernet/ansible
RUN pip3 install --upgrade pip ansible \
    && ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml

WORKDIR /app/netflux5g/containernet
RUN make install

# Set containernet environment variable
ENV CONTAINERNET_NESTED=1

# Install Mininet-WiFi
WORKDIR /app/netflux5g/mininet-wifi
RUN util/install.sh -Wlnfv6

# Clone NetFlux5G project
WORKDIR /app/netflux5g
RUN git clone https://github.com/adaptivenetworklab/Riset_23-24_SDN.git NetFlux5G

# Create working directories
RUN mkdir -p /app/netflux5g/workspace \
    && mkdir -p /app/netflux5g/logs \
    && mkdir -p /app/netflux5g/captures

# Set up entrypoint
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user for security
RUN useradd -m -s /bin/bash netflux \
    && echo "netflux ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && chown -R netflux:netflux /app/netflux5g

# Set default user
USER netflux
WORKDIR /app/netflux5g

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
