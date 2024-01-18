#!/bin/bash

set -eo pipefail


# tun iface create
function tun_create {
    if ! grep "ogstun" /proc/net/dev > /dev/null; then
        echo "Creating ogstun device"
        ip tuntap add name ogstun mode tun
        ip tuntap add name ogstun2 mode tun
        ip tuntap add name ogstun3 mode tun
    fi

    ip addr del 10.45.0.1/16 dev ogstun 2> /dev/null
    ip addr add 10.45.0.1/16 dev ogstun
    ip addr del 2001:db8:cafe::1/48 dev ogstun 2> /dev/null
    ip addr add 2001:db8:cafe::1/48 dev ogstun
    ip addr del 10.46.0.1/16 dev ogstun2 2> /dev/null
    ip addr add 10.46.0.1/16 dev ogstun2
    ip addr del 2001:db8:babe::1/48 dev ogstun2 2> /dev/null
    ip addr add 2001:db8:babe::1/48 dev ogstun2
    ip addr del 10.47.0.1/16 dev ogstun3 2> /dev/null
    ip addr add 10.47.0.1/16 dev ogstun3
    ip addr del 2001:db8:face::1/48 dev ogstun3 2> /dev/null
    ip addr add 2001:db8:face::1/48 dev ogstun3

    sysctl -w net.ipv6.conf.all.disable_ipv6=0;         
    
    ip link set ogstun up
    ip link set ogstun2 up
    ip link set ogstun3 up

    sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward";


    iptables -t nat -A POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE
    iptables -t nat -A POSTROUTING -s 10.46.0.0/16 ! -o ogstun2 -j MASQUERADE
    iptables -t nat -A POSTROUTING -s 10.47.0.0/16 ! -o ogstun3 -j MASQUERADE
}
 
 COMMAND=$1
if [[ "$COMMAND"  == *"open5gs-pgwd" ]] || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
tun_create
fi

# Temporary patch to solve the case of docker internal dns not resolving "not running" container names.
# Just wait 10 seconds to be "running" and resolvable
if [[ "$COMMAND"  == *"open5gs-pcrfd" ]] \
    || [[ "$COMMAND"  == *"open5gs-mmed" ]] \
    || [[ "$COMMAND"  == *"open5gs-sgwcd" ]] \
    || [[ "$COMMAND"  == *"open5gs-upfd" ]]; then
sleep 10
fi

$@

exit 1
