#!/bin/bash

# Enhanced 5G Core Network Monitoring Stack
# Navigasi ke direktori monitoring (jika belum berada di sana)
cd "$(dirname "$0")"

echo "=================================================="
echo "Starting Enhanced 5G Core Monitoring Stack..."
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p prometheus/data
mkdir -p grafana/data
mkdir -p alertmanager/data

# Set proper permissions
echo "🔧 Setting permissions..."
chmod 755 prometheus/data
chmod 755 grafana/data
chmod 755 alertmanager/data

# Start monitoring stack
echo "🚀 Starting monitoring services..."
echo "   - Prometheus (metrics collection)"
echo "   - Grafana (dashboards)"
echo "   - Alertmanager (alerting)"
echo "   - Node Exporter (system metrics)"
echo "   - cAdvisor (container metrics)"
echo "   - Blackbox Exporter (network probes)"

docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
if docker compose ps | grep -q "Up"; then
    echo "✅ Services are starting up..."
else
    echo "❌ Some services may have failed to start. Check with 'docker compose logs'"
fi

echo ""
echo "=================================================="
echo "🎉 Enhanced 5G Core Monitoring Stack Started!"
echo "=================================================="
echo ""
echo "📊 Access your monitoring tools:"
echo "   • Grafana Dashboard:    http://localhost:3000"
echo "     Login: admin / admin (change on first login)"
echo ""
echo "   • Prometheus:           http://localhost:9090"
echo "     - Metrics query interface"
echo "     - Target status check"
echo ""
echo "   • Alertmanager:         http://localhost:9093"
echo "     - Alert management"
echo "     - Notification routing"
echo ""
echo "📈 Key Features Enabled:"
echo "   ✅ Real-time infrastructure monitoring"
echo "   ✅ 5G Core network functions monitoring"
echo "   ✅ Container and system resource tracking"
echo "   ✅ Network connectivity probes"
echo "   ✅ Automated alerting system"
echo "   ✅ Success rate monitoring"
echo ""
echo "📚 Documentation:"
echo "   • Dashboard Guide: grafana/DASHBOARD_GUIDE.md"
echo "   • Full Documentation: README_ENHANCED.md"
echo ""
echo "🚨 To view logs: docker compose logs [service-name]"
echo "🛑 To stop: docker compose down"
echo "=================================================="

