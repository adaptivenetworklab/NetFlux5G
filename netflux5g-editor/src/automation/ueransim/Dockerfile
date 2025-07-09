FROM ubuntu:24.04 AS builder

ARG version=3.1.0
ARG commit=
ENV VERSION=$version
ENV COMMIT=$commit

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \  
      git \
      ca-certificates \
      build-essential \
      cmake \
      make \
      g++ \
      libsctp-dev  \ 
      lksctp-tools && \
      apt-get clean
  

RUN cd /tmp && git clone https://github.com/aligungr/UERANSIM.git
    
RUN cd /tmp/UERANSIM && echo "cmake --version" && make

FROM ubuntu:24.04 AS release 

# Update package list and install required packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \  
        bash \
        bind9-dnsutils \
        curl \
        wget \
        gettext \
        iproute2 \
        iputils-ping \
        libsctp1 \ 
        lksctp-tools \
        libstdc++6 \
        traceroute \
        iperf3 iperf \
        libsctp-dev \
        iw wireless-tools ethtool net-tools tcpdump iptables dnsutils procps \
        hostapd \
        wpasupplicant \
        bridge-utils \
        openvswitch-switch \
        openvswitch-common \
        sudo \
        rfkill \
        tshark speedtest-cli linux-firmware \
        netcat-openbsd \
        jq \
        python3 python3-pip \
        supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
  
COPY --from=builder /tmp/UERANSIM/build/* /usr/local/bin/
COPY /etc/ueransim /etc/ueransim
COPY entrypoint.sh /entrypoint.sh

# Copy OVS setup scripts and make them executable
COPY ueransim-ovs-setup.sh /usr/local/bin/ueransim-ovs-setup.sh
COPY ueransim-ovs-config.sh /usr/local/bin/ueransim-ovs-config.sh
COPY ap-setup.sh /usr/local/bin/ap-setup.sh
COPY supervisord.conf /etc/supervisor/conf.d/ueransim.conf
RUN chmod +x /usr/local/bin/ueransim-ovs-setup.sh /usr/local/bin/ueransim-ovs-config.sh /usr/local/bin/ap-setup.sh

# OpenFlow/SDN Controller Configuration Environment Variables
ENV OVS_ENABLED=false \
    OVS_CONTROLLER="" \
    OVS_BRIDGE_NAME="br-ueransim" \
    OVS_FAIL_MODE="standalone" \
    OPENFLOW_PROTOCOLS="OpenFlow14" \
    OVS_DATAPATH="kernel" \
    CONTROLLER_IP="" \
    CONTROLLER_PORT="6633" \
    BRIDGE_INTERFACES="" \
    OVS_AUTO_SETUP=true

# Network interface configuration for mininet-wifi integration
ENV NETWORK_INTERFACE="eth0" \
    BRIDGE_PRIORITY="32768" \
    STP_ENABLED=false \
    UERANSIM_COMPONENT=""

# Standard UERANSIM Environment Variables
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
RUN mkdir -p /var/run/openvswitch /var/log/openvswitch /etc/openvswitch /var/log/supervisor /logging
RUN systemctl disable hostapd || true
RUN systemctl disable wpa_supplicant || true

# Create startup script for AP functionality  
RUN chmod +x /usr/local/bin/ap-setup.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ue"]
