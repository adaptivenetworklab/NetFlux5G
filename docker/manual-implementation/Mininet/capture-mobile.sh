sh tshark -i ap1-wlan1 -w /root/hasil_test/ap1-fixed -F pcapng -a duration:180 &
sh tshark -i ap2-wlan1 -w /root/hasil_test/ap2-fixed -F pcapng -a duration:180 &
sh tshark -i ap3-wlan1 -w /root/hasil_test/ap3-fixed -F pcapng -a duration:180 &
