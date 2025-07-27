# CAPTURE_DURATION=100     # Capture duration (longer than test)

# # Get all UE devices
# UE_LIST=($(seq 1 10 | sed 's/^/UE__/'))

# echo "Found ${#UE_LIST[@]} UE devices"

# # Start aggressive packet capture
# echo "Starting packet capture on all devices..."
# for ue in "${UE_LIST[@]}"; do
#     ${ue} tshark -i any -w /captures/${ue}-maxload -F pcapng -a duration:100 &
# done

# Start captures on all devices
UE__1 tshark -i any -w /captures/ue1-maxload -F pcapng -a duration:100 &
UE__2 tshark -i any -w /captures/ue2-maxload -F pcapng -a duration:100 &
UE__3 tshark -i any -w /captures/ue3-maxload -F pcapng -a duration:100 &
UE__4 tshark -i any -w /captures/ue4-maxload -F pcapng -a duration:100 &
UE__5 tshark -i any -w /captures/ue5-maxload -F pcapng -a duration:100 &
UE__6 tshark -i any -w /captures/ue6-maxload -F pcapng -a duration:100 &
UE__7 tshark -i any -w /captures/ue7-maxload -F pcapng -a duration:100 &
GNB__1 tshark -i any -w /captures/gnb1-maxload -F pcapng -a duration:100 &
GNB__2 tshark -i any -w /captures/gnb2-maxload -F pcapng -a duration:100 &
upf1 tshark -i any -w /captures/upf1-maxload -F pcapng -a duration:100 &
upf2 tshark -i any -w /captures/upf2-maxload -F pcapng -a duration:100 &
amf1 tshark -i any -w /captures/amf1-maxload -F pcapng -a duration:100 &
smf1 tshark -i any -w /captures/smf1-maxload -F pcapng -a duration:100 &
scp1 tshark -i any -w /captures/scp1-maxload -F pcapng -a duration:100 &
pcf1 tshark -i any -w /captures/pcf1-maxload -F pcapng -a duration:100 &
