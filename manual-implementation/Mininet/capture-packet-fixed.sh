upf1 tshark -i ogstun -i ogstun2 -w /upf1-packet -F pcapng -a duration:25 &
ue1 tshark -i uesimtun0 -w /ue1-packet -F pcapng -a duration:25 &
ue2 tshark -i uesimtun0 -w /ue2-packet -F pcapng -a duration:25 &
ue3 tshark -i uesimtun0 -w /ue3-packet -F pcapng -a duration:25 &
ue4 tshark -i uesimtun0 -w /ue4-packet -F pcapng -a duration:25 &
ue5 tshark -i uesimtun0 -w /ue5-packet -F pcapng -a duration:25 &
ue6 tshark -i uesimtun0 -w /ue6-packet -F pcapng -a duration:25 &

sh docker exec mn.upf1 iperf3 -s -B $(docker exec mn.upf1 ip -f inet addr show ogstun | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f m 2>&1 | tee /iperfs-upf1-ogstun &
sh docker exec mn.ue1 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue1 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15  2>&1 | tee /iperfc-ue1-up.log & 
sh docker exec mn.ue2 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue2 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15  2>&1 | tee /iperfc-ue2-up.log &
sh docker exec mn.ue4 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue4 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15  2>&1 | tee /iperfc-ue3-up.log &
sh docker exec mn.ue1 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue1 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15 -R  2>&1 | tee /iperfc-ue1-down.log & 
sh docker exec mn.ue2 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue2 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15 -R  2>&1 | tee /iperfc-ue2-down.log &
sh docker exec mn.ue4 iperf3 -c 10.45.0.1 -B $(docker exec mn.ue4 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5001 -f M -b 138M -t 15 -R  2>&1 | tee /iperfc-ue3-down.log &

sh docker exec mn.upf1 iperf3 -s -B $(docker exec mn.upf1 ip -f inet addr show ogstun2 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f m 2>&1 | tee /iperfs-upf1-ogstun2 &
sh docker exec mn.ue3 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue3 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 2>&1 | tee /iperfc-ue4-up.log &
sh docker exec mn.ue5 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue5 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 2>&1 | tee /iperfc-ue5-up.log &
sh docker exec mn.ue6 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue6 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 2>&1 | tee /iperfc-ue6-up.log &
sh docker exec mn.ue3 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue3 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 -R 2>&1 | tee /iperfc-ue4-down.log &
sh docker exec mn.ue5 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue5 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 -R 2>&1 | tee /iperfc-ue5-down.log &
sh docker exec mn.ue6 iperf3 -c 10.46.0.1 -B $(docker exec mn.ue6 ip -f inet addr show uesimtun0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p') -i 1 -p 5002 -f M -b 138M -t 15 -R 2>&1 | tee /iperfc-ue6-down.log &

sh sleep 30

sh docker cp mn.upf1:/upf1-packet /root/hasil_test/
sh docker cp mn.upf1:/upf1-init /root/hasil_test/

sh docker cp mn.amf1:/amf1-init /root/hasil_test/
sh docker cp mn.gnb1:/gnb1-init /root/hasil_test/
sh docker cp mn.gnb2:/gnb2-init /root/hasil_test/

sh docker cp mn.ue1:/ue1-packet /root/hasil_test/
sh docker cp mn.ue1:/ue1-init /root/hasil_test/

sh docker cp mn.ue2:/ue2-packet /root/hasil_test/
sh docker cp mn.ue2:/ue2-init /root/hasil_test/

sh docker cp mn.ue3:/ue3-packet /root/hasil_test/
sh docker cp mn.ue3:/ue3-init /root/hasil_test/

sh docker cp mn.ue4:/ue4-packet /root/hasil_test/
sh docker cp mn.ue4:/ue4-init /root/hasil_test/

sh docker cp mn.ue5:/ue5-packet /root/hasil_test/
sh docker cp mn.ue5:/ue5-init /root/hasil_test/

sh docker cp mn.ue6:/ue6-packet /root/hasil_test/
sh docker cp mn.ue6:/ue6-init /root/hasil_test/