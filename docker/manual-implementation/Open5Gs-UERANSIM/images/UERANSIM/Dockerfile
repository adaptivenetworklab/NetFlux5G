FROM debian:bullseye as builder

ARG version=3.2.6

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    git \
    gcc \
    make \
    g++ \
    libsctp-dev lksctp-tools \
    iproute2

RUN  DEBIAN_FRONTEND=noninteractive apt-get install -y libssl-dev

RUN cd /tmp && git clone https://github.com/Kitware/CMake.git

RUN cd /tmp/CMake && ./bootstrap && make && make install

RUN cd /tmp && git clone https://github.com/aligungr/UERANSIM.git

RUN cd /tmp/UERANSIM && echo "cmake --version" && make

FROM debian:bullseye

COPY --from=builder /tmp/UERANSIM/build/* /usr/local/bin/

COPY /etc/ueransim /etc/ueransim
COPY entrypoint.sh /entrypoint.sh

# Fix apt sources for Debian (the previous sed command was for Ubuntu)
# RUN sed -i -e 's/http:\/\/archive\.ubuntu\.com\/ubuntu\//mirror:\/\/mirrors\.ubuntu\.com\/mirrors\.txt/' /etc/apt/sources.list

# Update package list and install required packages
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    bash \
    curl \
    gettext \
    iperf3 iperf \
    iproute2 \
    libsctp-dev lksctp-tools \
    iw wireless-tools ethtool net-tools iputils-ping traceroute tcpdump iptables dnsutils procps \
    && apt-get install -y \
    hostapd \
    wpasupplicant \
    bridge-utils \
    openvswitch-switch \
    openvswitch-common \
    sudo \
    rfkill \
    crda \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install additional packages that might fail
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    tshark speedtest-cli firmware-iwlwifi || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
ENV N2_IFACE=eth0
ENV N3_IFACE=eth0
ENV RADIO_IFACE=eth0
ENV AMF_HOSTNAME=amf
ENV GNB_HOSTNAME=localhost

# AP Configuration Environment Variables
ENV AP_ENABLED=false
ENV AP_SSID=gnb-hotspot
ENV AP_CHANNEL=6
ENV AP_MODE=g
ENV AP_PASSWD=""
ENV AP_BRIDGE_NAME=br-gnb
ENV OVS_CONTROLLER=""
ENV AP_FAILMODE=standalone
ENV OPENFLOW_PROTOCOLS=OpenFlow14

# Additional OVS and wireless configuration
RUN mkdir -p /var/run/openvswitch /var/log/openvswitch /etc/openvswitch
RUN systemctl disable hostapd || true
RUN systemctl disable wpa_supplicant || true

# Create startup script for AP functionality  
COPY ap-setup.sh /usr/local/bin/ap-setup.sh
RUN chmod +x /usr/local/bin/ap-setup.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ue"]

