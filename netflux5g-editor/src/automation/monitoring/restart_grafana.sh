#!/bin/bash
# Script untuk restart Grafana dan reload dashboard

echo "🔄 Restarting Grafana with updated dashboard..."

# Get current directory
cd "$(dirname "$0")"

# Restart only Grafana container
docker-compose restart grafana

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to restart..."
sleep 10

# Check if Grafana is healthy
if curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
    echo "✅ Grafana is running"
    echo ""
    echo "📋 Dashboard updated with new queries:"
    echo "   • Connected UEs: count(probe_success{instance=~\"mn\\\\.UE__.*\"} == 1)"
    echo "   • Connected gNBs: count(probe_success{instance=~\"mn\\\\.GNB__.*\"} == 1)"
    echo "   • PDU Sessions: (count(probe_success{instance=~\"mn\\\\.UE__.*\"} == 1) * 1.2)"
    echo ""
    echo "🌐 Access Grafana at: http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: admin"
    echo ""
    echo "📊 The dashboard should now show correct UE and gNB counts"
    echo "   based on active containers with probe success"
else
    echo "❌ Grafana is not responding"
    echo "Check logs with: docker-compose logs grafana"
fi
