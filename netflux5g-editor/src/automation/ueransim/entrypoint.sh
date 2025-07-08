#!/bin/bash

set -e

_term() { 
    case "$command" in
    ue) 
        echo "Deleting ue: nr-ue -c ue.yaml"
        for x in $(./usr/local/bin/nr-cli -d); do 
            ./usr/local/bin/nr-cli $x --exec "deregister switch-off"
        done
        echo "UEs switched off"
        sleep 5
        ;;
    *) 
        echo "It isn't necessary to perform any cleanup"
        ;;
    esac
}

if [ $# -lt 1 ]
then
        echo "Usage : $0 [gnb|ue]"
        exit
fi

command=$1
trap _term SIGTERM
shift

case "$command" in

ue) 
    # GNB_IP=${GNB_IP:-"$(host -4 $GNB_HOSTNAME |awk '/has.*address/{print $NF; exit}')"}
    export GNB_IP
    echo "GNB_IP: $GNB_IP"
    envsubst < /etc/ueransim/ue.yaml > ue.yaml
    echo "Launching ue: nr-ue -c ue.yaml"
    nr-ue -c ue.yaml $@ &
    child=$!
    wait "$child"
    ;;
gnb)
    # Setup Access Point functionality if enabled
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Setting up Access Point functionality for gNB..."
        /usr/local/bin/ap-setup.sh
        if [ $? -ne 0 ]; then
            echo "WARNING: AP setup failed, continuing with gNB startup"
        fi
    fi
    
    N2_BIND_IP=${N2_BIND_IP:-"$(ip addr show ${N2_IFACE}  | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    N3_BIND_IP=${N3_BIND_IP:-"$(ip addr show ${N3_IFACE} | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    RADIO_BIND_IP=${RADIO_BIND_IP:-"$(ip addr show ${RADIO_IFACE} | grep -o 'inet [[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}'| cut -c 6-)"}
    # AMF_IP=${AMF_IP:-"$(host -4 $AMF_HOSTNAME |awk '/has.*address/{print $NF; exit}')"}
    export N2_BIND_IP N3_BIND_IP RADIO_BIND_IP AMF_IP
    echo "N2_BIND_IP: $N2_BIND_IP"
    echo "N3_BIND_IP: $N3_BIND_IP"
    echo "RADIO_BIND_IP: $RADIO_BIND_IP"
    echo "AMF_IP: $AMF_IP"
    envsubst < /etc/ueransim/gnb.yaml > gnb.yaml
    echo "Launching gnb: nr-gnb -c gnb.yaml"
    
    # Start gNB in background if AP is enabled to allow both services
    if [ "$AP_ENABLED" = "true" ]; then
        echo "Starting gNB in background mode (AP enabled)"
        nr-gnb -c gnb.yaml $@ &
        GNB_PID=$!
        
        # Keep container running and monitor both services
        while true; do
            sleep 10
            
            # Check if gNB is still running
            if ! kill -0 $GNB_PID 2>/dev/null; then
                echo "gNB process has stopped, restarting..."
                nr-gnb -c gnb.yaml $@ &
                GNB_PID=$!
            fi
            
            # Check if hostapd is still running (if AP enabled)
            if ! pgrep -f hostapd > /dev/null; then
                echo "Hostapd process has stopped, attempting restart..."
                /usr/local/bin/ap-setup.sh
            fi
        done
    else
        # Normal gNB operation without AP
        nr-gnb -c gnb.yaml $@
    fi
    ;;
*) echo "unknown component $1 is not a component (gnb or ue). Running $@ as command"
   $@
   ;;
esac
