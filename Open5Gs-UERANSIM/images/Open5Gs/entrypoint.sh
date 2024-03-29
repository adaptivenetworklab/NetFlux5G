#!/bin/bash

set -eo pipefail


# tun iface create
function tun_create {
    echo -e "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    if ! grep "ogstun" /proc/net/dev > /dev/null; then
        echo "Creating ogstun device"
        ip tuntap add name ogstun mode tun
    fi

    if ! grep "ogstun2" /proc/net/dev > /dev/null; then
        echo "Creating ogstun2 device"
        ip tuntap add name ogstun2 mode tun
    fi

    ip addr del 10.45.0.1/16 dev ogstun 2> /dev/null || true
    ip addr add 10.45.0.1/16 dev ogstun

    ip addr del 10.46.0.1/16 dev ogstun 2> /dev/null || true
    ip addr add 10.46.0.1/16 dev ogstun2
    
    ip link set ogstun up
    ip link set ogstun2 up
    sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward";
    if [ "$ENABLE_NAT" = true ] ; then
      iptables -t nat -A POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE
      iptables -t nat -A POSTROUTING -s 10.46.0.0/16 ! -o ogstun2 -j MASQUERADE
    fi
}
 
 COMMAND=$1
if [[ "$COMMAND"  == *"open5gs-pgwd" ]] || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
tun_create
fi

# Temporary patch to solve the case of docker internal dns not resolving "not running" container names.
# Just wait 10 seconds to be "running" and resolvable
if [[ "$COMMAND"  == *"open5gs-pcrfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-mmed" ]] \
    || [[ "$COMMAND"  == *"open5gs-nrfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-scpd" ]] \
    || [[ "$COMMAND"  == *"open5gs-sgwcd" ]] \
    || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
sleep 10
fi

$@

exit 1
