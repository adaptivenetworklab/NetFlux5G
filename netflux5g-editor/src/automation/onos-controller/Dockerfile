FROM ubuntu:20.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt install wget git zip curl unzip openjdk-11-jdk=11.0.7+10-3ubuntu1 openjdk-11-jre=11.0.7+10-3ubuntu1 openjdk-11-jdk-headless=11.0.7+10-3ubuntu1 openjdk-11-jre-headless=11.0.7+10-3ubuntu1 -y

ENV ONOS_VERSION=2.7.0
ARG ONOS_VERSION

WORKDIR /opt/

RUN adduser sdn --system --group 

RUN wget -c https://repo1.maven.org/maven2/org/onosproject/onos-releases/$ONOS_VERSION/onos-$ONOS_VERSION.tar.gz && \
    tar xzf onos-$ONOS_VERSION.tar.gz && \
    mv onos-$ONOS_VERSION onos && \
    chown -R sdn:sdn onos

# Copy the startup scripts and configuration
ENV ONOS_APPS=org.onosproject.gui2,org.onosproject.drivers,org.onosproject.proxyarp,org.onosproject.fwd,org.onosproject.hostprovider,org.onosproject.lldpprovider,org.onosproject.optical-model,org.onosproject.openflow

USER sdn

# Set environment variables to avoid port conflicts
ENV ONOS_CLUSTER_PORT=9876
ENV ONOS_NODE_ID=127.0.0.1

EXPOSE 6653 6640 8181 8101 9876

CMD ["/opt/onos/bin/onos-service", "start"]