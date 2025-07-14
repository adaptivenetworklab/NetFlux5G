FROM debian:bullseye as builder

ARG version=3.2.6

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    git \
    gcc \
    make \
    g++ \
    libsctp-dev lksctp-tools \
    iproute2 \
    libssl-dev

RUN cd /tmp && git clone https://github.com/Kitware/CMake.git
RUN cd /tmp/CMake && ./bootstrap && make && make install

RUN cd /tmp && git clone https://github.com/aligungr/UERANSIM.git
RUN cd /tmp/UERANSIM && make

FROM debian:bullseye

COPY --from=builder /tmp/UERANSIM/build/* /usr/local/bin/

# Install base packages
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    bash \
    curl \
    gettext \
    iperf3 iperf \
    iproute2 \
    libsctp-dev lksctp-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install wireless and networking tools for mininet-wifi integration
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    iw wireless-tools ethtool net-tools \
    iputils-ping traceroute tcpdump iptables \
    dnsutils procps \
    hostapd wpasupplicant \
    bridge-utils \
    openvswitch-switch openvswitch-common \
    sudo rfkill crda \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install additional packages for enhanced functionality
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    tshark speedtest-cli firmware-iwlwifi \
    netcat-openbsd \
    vim nano \
    htop \
    || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG N2_IFACE
ARG N3_IFACE
ARG RADIO_IFACE
ARG AMF_HOSTNAME
ARG GNB_HOSTNAME
ARG NETWORK_INTERFACE
ARG WIRELESS_INTERFACE
ARG ENABLE_MONITORING
ARG AP_ENABLED
ARG AP_SSID
ARG AP_CHANNEL
ARG AP_MODE
ARG AP_PASSWD
ARG AP_BRIDGE_NAME
ARG AP_FAILMODE
ARG OVS_ENABLED
ARG OVS_BRIDGE_NAME
ARG OVS_FAIL_MODE
ARG OVS_AUTO_SETUP
ARG OVS_CONTROLLER
ARG CONTROLLER_IP
ARG CONTROLLER_PORT
ARG OPENFLOW_PROTOCOLS
ARG BRIDGE_INTERFACES
ARG BRIDGE_PRIORITY
ARG STP_ENABLED
ARG MININET_WIFI_MODE
ARG UERANSIM_COMPONENT
ARG MCC
ARG MNC
ARG SST
ARG SD
ARG TAC
ARG GNB_ID
ARG APN
ARG MSISDN
ARG KEY
ARG OP_TYPE
ARG OP
ARG IMEI
ARG IMEISV
ARG TUNNEL_IFACE
ARG SESSION_TYPE
ARG PDU_SESSIONS
ARG MOBILITY_ENABLED

# Set up environment variables for UERANSIM configuration
ENV N2_IFACE=eth0
ENV N3_IFACE=eth0
ENV RADIO_IFACE=eth0
ENV AMF_HOSTNAME=amf
ENV GNB_HOSTNAME=localhost
ENV NETWORK_INTERFACE=eth0

# Wireless and mininet-wifi integration environment variables
ENV WIRELESS_INTERFACE=""
ENV ENABLE_MONITORING=false

# AP Configuration Environment Variables
ENV AP_ENABLED=false
ENV AP_SSID=gnb-hotspot
ENV AP_CHANNEL=6
ENV AP_MODE=g
ENV AP_PASSWD=""
ENV AP_BRIDGE_NAME=br-gnb
ENV AP_FAILMODE=standalone

# OVS Configuration Environment Variables  
ENV OVS_ENABLED=false
ENV OVS_BRIDGE_NAME=br-ueransim
ENV OVS_FAIL_MODE=standalone
ENV OVS_AUTO_SETUP=false
ENV OVS_CONTROLLER=""
ENV CONTROLLER_IP=""
ENV CONTROLLER_PORT=6633
ENV OPENFLOW_PROTOCOLS=OpenFlow14
ENV BRIDGE_INTERFACES=""
ENV BRIDGE_PRIORITY=32768
ENV STP_ENABLED=false
ENV MININET_WIFI_MODE=false

# UERANSIM component configuration
ENV UERANSIM_COMPONENT=gnb
ENV MCC=999
ENV MNC=70
ENV SST=1
ENV SD=0xffffff
ENV TAC=1
ENV GNB_ID=1

# UE specific configuration
ENV APN=internet
ENV MSISDN=0000000001
ENV KEY=465B5CE8B199B49FAA5F0A2EE238A6BC
ENV OP_TYPE=OPC
ENV OP=E8ED289DEBA952E4283B54E88E6183CA
ENV IMEI=356938035643803
ENV IMEISV=4370816125816151
ENV TUNNEL_IFACE=uesimtun0
ENV SESSION_TYPE=IPv4
ENV PDU_SESSIONS=1
ENV MOBILITY_ENABLED=false

# Create necessary directories
RUN mkdir -p /var/run/openvswitch /var/log/openvswitch /etc/openvswitch /logging
RUN mkdir -p /var/log/ueransim /tmp/ueransim
RUN mkdir -p /etc/ueransim

# Create OVS database directory
RUN mkdir -p /etc/openvswitch

# Disable conflicting services (they interfere with mininet-wifi)
RUN systemctl disable hostapd 2>/dev/null || true
RUN systemctl disable wpa_supplicant 2>/dev/null || true

# Copy enhanced setup scripts
COPY ueransim-ovs-setup.sh /usr/local/bin/ueransim-ovs-setup.sh

# Copy UERANSIM configuration templates
COPY etc/ueransim /etc/ueransim

# Copy enhanced entrypoint
COPY entrypoint.sh /entrypoint.sh

# Make scripts executable
RUN chmod +x /usr/local/bin/ueransim-ovs-setup.sh  
RUN chmod +x /entrypoint.sh

# Create user for running UERANSIM (optional, can run as root in container)
RUN useradd -m -s /bin/bash ueransim || true

# Set proper permissions
RUN chown -R root:root /usr/local/bin/
RUN chown -R root:root /etc/ueransim/

# Expose common ports for 5G communication
EXPOSE 4997 9487 38412 38472 2152

# Health check to verify container functionality
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep nr-gnb || pgrep nr-ue || exit 1

ENTRYPOINT ["/entrypoint.sh"]
