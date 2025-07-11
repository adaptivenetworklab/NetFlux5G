#!/bin/bash
# Script untuk debug dan fix dashboard auto-refresh issues

echo "🔍 Debugging Dashboard Auto-Refresh Issues..."
echo ""

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:$port"
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $service_name (port $port) - Running"
        return 0
    else
        echo "❌ $service_name (port $port) - Not responding"
        return 1
    fi
}

# Check monitoring stack
echo "📊 Checking monitoring services:"
check_service "Prometheus" 9090
prometheus_status=$?
check_service "Grafana" 3000  
grafana_status=$?
check_service "Blackbox Exporter" 9115
blackbox_status=$?

echo ""

# Check Prometheus targets if available
if [ $prometheus_status -eq 0 ]; then
    echo "🎯 Checking Prometheus targets:"
    targets_response=$(curl -s "http://localhost:9090/api/v1/targets")
    
    if echo "$targets_response" | grep -q '"health":"up"'; then
        echo "✅ Some targets are healthy"
    else
        echo "⚠️  No healthy targets found"
    fi
    
    # Check specific probe targets
    echo ""
    echo "🔍 Testing specific queries:"
    
    # Test UE probe query
    ue_query_response=$(curl -s "http://localhost:9090/api/v1/query?query=probe_success%7Binstance%3D~%22mn%5C%5C.UE__%2E%2A%22%7D")
    if echo "$ue_query_response" | grep -q '"status":"success"'; then
        echo "✅ UE probe query works"
        ue_count=$(echo "$ue_query_response" | grep -o '"value":\[[^]]*\]' | grep -o '"1"' | wc -l)
        echo "   Active UE probes: $ue_count"
    else
        echo "❌ UE probe query failed"
    fi
    
    # Test gNB probe query
    gnb_query_response=$(curl -s "http://localhost:9090/api/v1/query?query=probe_success%7Binstance%3D~%22mn%5C%5C.GNB__%2E%2A%22%7D")
    if echo "$gnb_query_response" | grep -q '"status":"success"'; then
        echo "✅ gNB probe query works"
        gnb_count=$(echo "$gnb_query_response" | grep -o '"value":\[[^]]*\]' | grep -o '"1"' | wc -l)
        echo "   Active gNB probes: $gnb_count"
    else
        echo "❌ gNB probe query failed"
    fi
else
    echo "❌ Cannot test queries - Prometheus not available"
fi

echo ""

# Check containers
echo "📦 Checking relevant containers:"
ue_containers=$(docker ps --filter "name=mn.UE__" --filter "status=running" --format "{{.Names}}" | wc -l)
gnb_containers=$(docker ps --filter "name=mn.GNB__" --filter "status=running" --format "{{.Names}}" | wc -l)
core_containers=$(docker ps --filter "name=mn." --filter "status=running" --format "{{.Names}}" | grep -v "UE__\|GNB__" | wc -l)

echo "   UE containers running: $ue_containers"
echo "   gNB containers running: $gnb_containers"  
echo "   Core containers running: $core_containers"

if [ $ue_containers -eq 0 ] && [ $gnb_containers -eq 0 ]; then
    echo ""
    echo "⚠️  No UE/gNB containers detected!"
    echo "   This is why dashboard shows 'No data'"
    echo ""
    echo "🚀 To fix this, start your 5G topology:"
    echo "   1. Navigate to your topology script"
    echo "   2. Run: python your_topology.py"
    echo "   3. Wait for containers to start"
    echo "   4. Refresh Grafana dashboard"
fi

echo ""

# Fix dashboard refresh issues
echo "🔧 Applying dashboard fixes..."

# Restart Grafana to reload dashboard
echo "   Restarting Grafana..."
docker-compose restart grafana

# Wait for Grafana
echo "   Waiting for Grafana to restart..."
sleep 15

# Check if Grafana is back up
if check_service "Grafana" 3000; then
    echo ""
    echo "✅ Dashboard fixes applied!"
    echo ""
    echo "📋 What was fixed:"
    echo "   • Added proper interval and step to queries"
    echo "   • Fixed time range (now-5m to now)"
    echo "   • Enhanced refresh configuration"
    echo "   • Restarted Grafana service"
    echo ""
    echo "🌐 Access dashboard: http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: admin"
    echo ""
    echo "🔄 Dashboard should now auto-refresh every 5 seconds"
    echo ""
    if [ $ue_containers -gt 0 ] || [ $gnb_containers -gt 0 ]; then
        echo "✅ Containers detected - dashboard should show data"
    else
        echo "⚠️  Start your 5G topology for data to appear"
    fi
else
    echo "❌ Grafana restart failed"
    echo "Check logs: docker-compose logs grafana"
fi
