#!/bin/bash
# Simple test untuk memastikan query bekerja

echo "🧪 Testing Prometheus Queries for Dashboard"
echo "==========================================="
echo ""

# Test connectivity
echo "🔗 Testing Prometheus connectivity..."
if curl -s -f "http://localhost:9090" > /dev/null 2>&1; then
    echo "✅ Prometheus is accessible"
else
    echo "❌ Prometheus not accessible at localhost:9090"
    echo "   Make sure monitoring stack is running: docker-compose up -d"
    exit 1
fi

echo ""

# Test basic up metric
echo "📊 Testing basic 'up' metric..."
up_response=$(curl -s "http://localhost:9090/api/v1/query?query=up")
if echo "$up_response" | grep -q '"status":"success"'; then
    echo "✅ Basic metrics are working"
    # Count how many targets are up
    up_count=$(echo "$up_response" | grep -o '"value":\["[^"]*","1"\]' | wc -l)
    echo "   Targets up: $up_count"
else
    echo "❌ Basic metrics test failed"
fi

echo ""

# Test probe_success metric
echo "🎯 Testing probe_success metric..."
probe_response=$(curl -s "http://localhost:9090/api/v1/query?query=probe_success")
if echo "$probe_response" | grep -q '"status":"success"'; then
    echo "✅ Probe metrics are available"
    # Show available probe targets
    echo "   Available probe targets:"
    echo "$probe_response" | grep -o '"instance":"[^"]*"' | cut -d'"' -f4 | sort | uniq | sed 's/^/     - /'
else
    echo "❌ Probe metrics not available"
    echo "   This means blackbox exporter is not working properly"
fi

echo ""

# Test UE query specifically
echo "🔍 Testing UE count query..."
ue_query="count(probe_success{instance=~\"mn\\\\.UE__.*\"} == 1)"
ue_response=$(curl -s "http://localhost:9090/api/v1/query?query=$(printf '%s' "$ue_query" | sed 's/ /%20/g; s/{/%7B/g; s/}/%7D/g; s/=/%3D/g; s/~/%7E/g; s/"/%22/g; s/\\\\/\%5C/g')")

if echo "$ue_response" | grep -q '"status":"success"'; then
    echo "✅ UE query is working"
    # Extract the count value
    ue_count=$(echo "$ue_response" | grep -o '"value":\["[^"]*","[^"]*"\]' | grep -o ',"[^"]*"' | sed 's/,"//; s/"//')
    echo "   UE count result: ${ue_count:-0}"
else
    echo "❌ UE query failed"
    echo "   Query: $ue_query"
    echo "   Response: $ue_response"
fi

echo ""

# Test gNB query
echo "📡 Testing gNB count query..."
gnb_query="count(probe_success{instance=~\"mn\\\\.GNB__.*\"} == 1)"
gnb_response=$(curl -s "http://localhost:9090/api/v1/query?query=$(printf '%s' "$gnb_query" | sed 's/ /%20/g; s/{/%7B/g; s/}/%7D/g; s/=/%3D/g; s/~/%7E/g; s/"/%22/g; s/\\\\/\%5C/g')")

if echo "$gnb_response" | grep -q '"status":"success"'; then
    echo "✅ gNB query is working"
    gnb_count=$(echo "$gnb_response" | grep -o '"value":\["[^"]*","[^"]*"\]' | grep -o ',"[^"]*"' | sed 's/,"//; s/"//')
    echo "   gNB count result: ${gnb_count:-0}"
else
    echo "❌ gNB query failed"
    echo "   Query: $gnb_query"
fi

echo ""

# Check containers
echo "📦 Checking actual containers..."
ue_containers=$(docker ps --filter "name=mn.UE__" --filter "status=running" --quiet | wc -l)
gnb_containers=$(docker ps --filter "name=mn.GNB__" --filter "status=running" --quiet | wc -l)

echo "   UE containers running: $ue_containers"
echo "   gNB containers running: $gnb_containers"

echo ""

# Final recommendation
if [ "${ue_count:-0}" -gt 0 ] || [ "${gnb_count:-0}" -gt 0 ]; then
    echo "✅ Queries are working! Dashboard should display data."
    echo ""
    echo "🔧 If dashboard still shows 'No data':"
    echo "   1. Hard refresh Grafana page (Ctrl+F5)"
    echo "   2. Check time range (set to 'Last 5 minutes')"
    echo "   3. Verify auto-refresh is enabled (top-right corner)"
    echo "   4. Import the updated dashboard file"
else
    echo "⚠️  Queries work but no data available."
    echo ""
    if [ $ue_containers -eq 0 ] && [ $gnb_containers -eq 0 ]; then
        echo "🚀 Start your 5G topology to see data:"
        echo "   python your_topology_script.py"
    else
        echo "🔧 Containers exist but probes are failing:"
        echo "   1. Check if containers are accessible"
        echo "   2. Verify blackbox exporter configuration"
        echo "   3. Check Prometheus targets: http://localhost:9090/targets"
    fi
fi

echo ""
echo "🌐 Direct links for testing:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000"
echo "   Targets: http://localhost:9090/targets"
