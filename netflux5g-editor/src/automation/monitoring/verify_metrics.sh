#!/bin/bash
# Script untuk verifikasi metrics dan query

echo "🔍 Verifying UE count metrics..."
echo ""

# Check if containers are running
echo "📦 Checking active containers:"
UE_CONTAINERS=$(docker ps --filter "name=mn.UE__" --filter "status=running" --format "{{.Names}}" | wc -l)
GNB_CONTAINERS=$(docker ps --filter "name=mn.GNB__" --filter "status=running" --format "{{.Names}}" | wc -l)

echo "   UE containers: $UE_CONTAINERS"
echo "   gNB containers: $GNB_CONTAINERS"
echo ""

# Check if monitoring services are running
echo "🔧 Checking monitoring services:"
PROMETHEUS_STATUS=$(curl -s -f "http://localhost:9090" > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Not running")
GRAFANA_STATUS=$(curl -s -f "http://localhost:3000" > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Not running")
BLACKBOX_STATUS=$(curl -s -f "http://localhost:9115" > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Not running")

echo "   Prometheus: $PROMETHEUS_STATUS"
echo "   Grafana: $GRAFANA_STATUS" 
echo "   Blackbox: $BLACKBOX_STATUS"
echo ""

# Test Prometheus queries
if curl -s -f "http://localhost:9090" > /dev/null 2>&1; then
    echo "📊 Testing Prometheus queries:"
    
    # Test UE probe query
    UE_PROBE_RESULT=$(curl -s "http://localhost:9090/api/v1/query?query=count(probe_success{instance=~%22mn\\.UE__.*%22}%20==%201)" | grep -o '"result":\[.*\]' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*' | tail -1)
    echo "   UE probe count: ${UE_PROBE_RESULT:-0}"
    
    # Test gNB probe query  
    GNB_PROBE_RESULT=$(curl -s "http://localhost:9090/api/v1/query?query=count(probe_success{instance=~%22mn\\.GNB__.*%22}%20==%201)" | grep -o '"result":\[.*\]' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*' | tail -1)
    echo "   gNB probe count: ${GNB_PROBE_RESULT:-0}"
    
    echo ""
    
    if [ "${UE_PROBE_RESULT:-0}" -gt 0 ] || [ "${GNB_PROBE_RESULT:-0}" -gt 0 ]; then
        echo "✅ Probe metrics are working!"
        echo "   Dashboard should now display correct counts"
    else
        echo "⚠️  No probe success detected"
        echo "   Make sure your 5G containers are running and accessible"
        echo ""
        echo "💡 To start your 5G network, run the topology script first:"
        echo "   python /path/to/your/topology.py"
    fi
else
    echo "❌ Cannot connect to Prometheus"
fi

echo ""
echo "🌐 Dashboard URLs:"
echo "   Grafana: http://localhost:3000"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "🔧 Manual verification commands:"
echo "   docker ps --filter name=mn.UE__"
echo "   curl 'http://localhost:9090/api/v1/query?query=probe_success'"
