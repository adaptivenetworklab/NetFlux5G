#!/bin/bash
#
# NetFlux5G - 5G Network Connectivity Test Script
# Tests end-to-end connectivity between 5G network components
#

# Text formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Paths and settings
LOG_DIR="/tmp/netflux5g/logs"
mkdir -p $LOG_DIR

echo -e "${BOLD}===== NetFlux5G Network Connectivity Test =====${NC}"
echo "Test started at: $(date)"
echo "This script will verify connectivity between all 5G components"
echo

# Function to test if component is reachable
test_component() {
    local component=$1
    local ip=$2
    echo -e "${BLUE}Testing connectivity to ${component}${NC} (${ip})..."
    
    if ping -c 3 -W 2 $ip > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${component} is reachable"
        return 0
    else
        echo -e "  ${RED}✗${NC} Cannot reach ${component}"
        return 1
    fi
}

# Function to check if container/service is running
check_service() {
    local service=$1
    echo -e "${BLUE}Checking if ${service} is running...${NC}"
    
    if docker ps | grep -q $service; then
        echo -e "  ${GREEN}✓${NC} ${service} is running"
        return 0
    else
        echo -e "  ${RED}✗${NC} ${service} is not running"
        return 1
    fi
}

# Test Core Network components
echo -e "\n${BOLD}1. Testing Core Network Components${NC}"
check_service "amf"
check_service "upf"
check_service "smf"

# Test AMF to SMF connectivity
echo -e "\n${BOLD}2. Testing AMF to SMF connectivity${NC}"
AMF_IP=$(docker exec -it amf hostname -I | awk '{print $1}')
SMF_IP=$(docker exec -it smf hostname -I | awk '{print $1}')

if [[ -n "$AMF_IP" && -n "$SMF_IP" ]]; then
    docker exec -it amf ping -c 3 $SMF_IP > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} AMF can reach SMF"
    else
        echo -e "  ${RED}✗${NC} AMF cannot reach SMF"
    fi
else
    echo -e "  ${RED}✗${NC} Could not determine AMF or SMF IP address"
fi

# Test gNB registration
echo -e "\n${BOLD}3. Testing gNB Registration${NC}"
if docker exec -it gnb tail -n 50 /tmp/gnb.log 2>/dev/null | grep -q "ng_setup_response"; then
    echo -e "  ${GREEN}✓${NC} gNB successfully registered with AMF"
else
    echo -e "  ${RED}✗${NC} No gNB registration with AMF found"
    echo "      Check AMF configuration and gNB logs"
fi

# Test UE connectivity
echo -e "\n${BOLD}4. Testing UE Registration and PDU Session${NC}"
UE_CONTAINER=$(docker ps | grep ue | awk '{print $NF}' | head -1)

if [ -n "$UE_CONTAINER" ]; then
    # Check if UE is connected
    if docker exec -it $UE_CONTAINER ip a | grep -q uesimtun0; then
        echo -e "  ${GREEN}✓${NC} UE interface uesimtun0 is created"
        
        # Get the IP address
        UE_IP=$(docker exec -it $UE_CONTAINER ip a show uesimtun0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
        echo -e "  ${GREEN}✓${NC} UE IP address: ${UE_IP}"
        
        # Test internet connectivity from UE
        echo -e "${BLUE}    Testing UE internet connectivity...${NC}"
        if docker exec -it $UE_CONTAINER ping -I uesimtun0 -c 3 8.8.8.8 > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} UE has internet connectivity"
        else
            echo -e "  ${RED}✗${NC} UE has no internet connectivity"
            echo "      Check UPF configuration and routing"
        fi
    else
        echo -e "  ${RED}✗${NC} UE interface uesimtun0 not found"
        echo "      UE might not be registered or PDU session failed"
        echo -e "${BLUE}    Checking UE logs for errors...${NC}"
        docker exec -it $UE_CONTAINER tail -n 50 /tmp/ue.log 2>/dev/null | grep -i error | head -5
    fi
else
    echo -e "  ${RED}✗${NC} No UE containers found"
fi

# Display packet capture suggestion
echo -e "\n${BOLD}Additional Diagnostic Steps:${NC}"
echo -e "1. To capture traffic for debugging, run:"
echo "   docker exec -it upf tcpdump -i any -n port 2152 -v"
echo "2. To view AMF logs, run:"
echo "   docker exec -it amf tail -f /opt/open5gs/var/log/open5gs/amf.log"
echo "3. To verify UE status, run:"
echo "   docker exec -it ue1 nr-cli imsi-999700000000001 -e status"

echo -e "\n${BOLD}===== Test Completed at $(date) =====${NC}"

# Determine overall status
if docker exec -it $UE_CONTAINER ip a | grep -q uesimtun0 && \
   docker exec -it $UE_CONTAINER ping -I uesimtun0 -c 1 8.8.8.8 > /dev/null 2>&1 && \
   docker exec -it gnb tail -n 50 /tmp/gnb.log 2>/dev/null | grep -q "ng_setup_response"; then
    echo -e "\n${GREEN}${BOLD}Overall Test Result: PASSED${NC}"
    echo "5G network is functioning correctly!"
else
    echo -e "\n${RED}${BOLD}Overall Test Result: FAILED${NC}"
    echo "There are issues with the 5G network configuration."
    echo "Review the test results above for specific problems."
fi
