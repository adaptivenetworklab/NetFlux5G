FROM tip-research/build-open5gs:1.0 AS builder

FROM debian:bullseye-slim

ARG version
ENV VERSION=$version

LABEL org.opencontainers.image.authors="Carlos Giraldo <cgiraldo@gradiant.org>" \
      org.opencontainers.image.vendor="Gradiant" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="$version"

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
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
    wondershaper iproute2 iputils-ping procps net-tools iptables iperf iperf3 traceroute tcpdump iw wireless-tools ethtool procps tshark speedtest-cli && \
    rm -rf /var/lib/apt/lists/*

ENV APP_ROOT=/opt/open5gs
COPY --from=builder /opt/open5gs ${APP_ROOT}

RUN cd ${APP_ROOT}/lib && ln -s $(uname -m)-linux-gnu/freeDiameter .
ENV PATH=${APP_ROOT}/bin:${PATH} HOME=${APP_ROOT}
WORKDIR ${APP_ROOT}
COPY entrypoint.sh /opt/open5gs/etc/open5gs/entrypoint.sh

#Run with non-root user
RUN groupadd -r open5gs && useradd --no-log-init -r -g open5gs open5gs
RUN chown -R open5gs:open5gs ${APP_ROOT}
USER open5gs

#Default CONF values
ENV DB_URI=mongodb://mongo/open5gs

# ENV IPV4_TUN_SUBNET="10.45.0.0/16" \
#     IPV4_TUN_ADDR="10.45.0.1/16" \
#     IPV6_TUN_ADDR="cafe::1/64" \
#     ENABLE_NAT=true

ENV ENABLE_NAT=true

CMD ["/bin/bash"]
ENTRYPOINT [ "/opt/open5gs/etc/open5gs/entrypoint.sh" ]
