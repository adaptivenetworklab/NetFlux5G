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

RUN sed -i -e 's/http:\/\/archive\.ubuntu\.com\/ubuntu\//mirror:\/\/mirrors\.ubuntu\.com\/mirrors\.txt/' /etc/apt/sources.list

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    bash \
    curl \
    gettext \
    iperf3 iperf \
    iproute2 \
    libsctp-dev lksctp-tools \
    iw wireless-tools ethtool iproute2 net-tools iputils-ping traceroute tcpdump iptables dnsutils procps tshark speedtest-cli
    
ENV N2_IFACE=eth0
ENV N3_IFACE=eth0
ENV RADIO_IFACE=eth0
ENV AMF_HOSTNAME=amf
ENV GNB_HOSTNAME=localhost

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ue"]

