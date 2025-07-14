FROM debian:bullseye AS builder

ARG version
ARG branch=main
ENV VERSION=$version
ENV BRANCH=$branch

RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        ninja-build \
        build-essential \
        flex \
        bison \
        git \
        cmake \
        meson \
        libsctp-dev \
        libgnutls28-dev \
        libgcrypt-dev \
        libssl-dev \
        libidn11-dev \
        libmongoc-dev \
        libbson-dev \
        libyaml-dev \
        libmicrohttpd-dev \
        libcurl4-gnutls-dev \
        libnghttp2-dev \
        libtins-dev \
        libtalloc-dev \
        iproute2 \
        ca-certificates \
        netbase \
        pkg-config \
        wget && \
    apt-get clean

RUN	mkdir -p /opt/open5gs && cd /tmp && git clone https://github.com/open5gs/open5gs && \
	cd open5gs && \
    if [ "$VERSION" = "dev" ]; then \
      git checkout $BRANCH; \
      wget https://api.github.com/repos/open5gs/open5gs/git/refs/heads/$BRANCH -O /open5gs-ver.json; \
    else \
      git checkout v$VERSION; \
      wget https://api.github.com/repos/open5gs/open5gs/git/refs/tags/v$VERSION -O /open5gs-ver.json; \
    fi && \
    meson  build --prefix=/opt/open5gs && \
    ln -s /opt/open5gs/subprojects/ /opt/open5gs/../subprojects && \
    ninja -C build install

## Replace default config values to work in containers (use dev eth0 and reference other containers by name)
COPY configs/open5gs/* /opt/open5gs/etc/open5gs/
COPY configs/freeDiameter/* /opt/open5gs/etc/freeDiameter/

FROM debian:bullseye-slim

ARG version
ENV VERSION=$version

RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    libtalloc2 \
    libgnutls30 \
    libgcrypt20 \
    libssl1.1 \
    libbson-1.0-0 \
    libtins4.0 \
    libcurl4-gnutls-dev \
    libyaml-0-2 \
    libmongoc-1.0-0 \
    libsctp1 \
    libidn11 \
    libcurl4 \
    libmicrohttpd12 \
    libnghttp2-14 \
    wondershaper iproute2 iputils-ping procps net-tools iptables iperf iperf3 traceroute tcpdump iw wireless-tools ethtool procps tshark speedtest-cli dnsutils gettext-base \
    openvswitch-switch openvswitch-common \
    bridge-utils \
    python3 python3-pip \
    jq \
    nmap netcat-openbsd \
    vlan \
    supervisor && \
    rm -rf /var/lib/apt/lists/*

ENV APP_ROOT=/opt/open5gs
COPY --from=builder /opt/open5gs ${APP_ROOT}

RUN cd ${APP_ROOT}/lib && ln -s $(uname -m)-linux-gnu/freeDiameter .
ENV PATH=${APP_ROOT}/bin:${PATH} HOME=${APP_ROOT}
WORKDIR ${APP_ROOT}

# Copy scripts and make them executable
COPY entrypoint.sh /opt/open5gs/etc/open5gs/entrypoint.sh
COPY ovs-setup.sh /opt/open5gs/bin/ovs-setup.sh

RUN chmod +x /opt/open5gs/etc/open5gs/entrypoint.sh /opt/open5gs/bin/ovs-setup.sh

# Create required directories for OVS
RUN mkdir -p /var/run/openvswitch /var/log/openvswitch /var/log/supervisor /logging

#Run with non-root user
# RUN groupadd -r open5gs && useradd --no-log-init -r -g open5gs open5gs
# RUN chown -R open5gs:open5gs ${APP_ROOT}
# USER open5gs

#Default CONF values
ENV DB_URI=mongodb://mongo/open5gs

ENV ENABLE_NAT=true

# OpenFlow/SDN Controller Configuration
ENV OVS_ENABLED=false \
    OVS_CONTROLLER="" \
    OVS_BRIDGE_NAME="br-open5gs" \
    OVS_FAIL_MODE="standalone" \
    OPENFLOW_PROTOCOLS="OpenFlow14" \
    OVS_DATAPATH="kernel" \
    CONTROLLER_IP="" \
    CONTROLLER_PORT="6633" \
    BRIDGE_INTERFACES="" \
    OVS_AUTO_SETUP=true \
    MININET_WIFI_MODE=false

# Network interface configuration for mininet-wifi integration
ENV NETWORK_INTERFACE="eth0" \
    BRIDGE_PRIORITY="32768" \
    STP_ENABLED=false

CMD ["/bin/bash"]
ENTRYPOINT [ "/opt/open5gs/etc/open5gs/entrypoint.sh" ]
