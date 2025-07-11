#!/bin/bash
# Script untuk deploy monitoring dengan UE counting yang benar

echo "=== NetFlux5G Enhanced Monitoring Deployment ==="
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Navigate to monitoring directory
cd "$(dirname "$0")"
MONITORING_DIR=$(pwd)
echo "📁 Working directory: $MONITORING_DIR"

# Build custom metrics exporter
echo ""
echo "🔨 Building custom metrics exporter..."
docker build -f Dockerfile.metrics -t netflux5g-metrics-exporter .

if [ $? -eq 0 ]; then
    echo "✅ Metrics exporter built successfully"
else
    echo "❌ Failed to build metrics exporter"
    exit 1
fi

# Start monitoring stack
echo ""
echo "🚀 Starting monitoring stack..."
docker-compose down 2>/dev/null  # Stop any existing containers
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ Monitoring stack started successfully"
else
    echo "❌ Failed to start monitoring stack"
    exit 1
fi

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Checking service status..."

services=("prometheus:9090" "grafana:3000" "metrics_exporter:8000" "blackbox-exporter:9115")
all_healthy=true

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -s -f "http://localhost:$port" > /dev/null 2>&1; then
        echo "✅ $name is healthy (port $port)"
    else
        echo "❌ $name is not responding (port $port)"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo "🎉 All services are healthy!"
    echo ""
    echo "📋 Access points:"
    echo "   • Grafana:     http://localhost:3000 (admin/admin)"
    echo "   • Prometheus:  http://localhost:9090"
    echo "   • Metrics:     http://localhost:8000/metrics"
    echo "   • Blackbox:    http://localhost:9115"
    echo ""
    echo "📈 Custom metrics available:"
    echo "   • netflux5g_connected_ues - Number of connected UEs"
    echo "   • netflux5g_connected_gnbs - Number of connected gNodeBs"
    echo "   • netflux5g_pdu_sessions - Number of active PDU sessions"
    echo ""
    echo "🔧 To check UE count manually:"
    echo "   curl http://localhost:8000/metrics | grep netflux5g_connected_ues"
    echo ""
    echo "⚠️  Note: Make sure your 5G containers are running for accurate metrics"
else
    echo "⚠️  Some services are not healthy. Check logs with:"
    echo "   docker-compose logs <service_name>"
fi

echo ""
echo "🏁 Deployment complete!"
