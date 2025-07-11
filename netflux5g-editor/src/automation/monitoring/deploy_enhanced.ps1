# PowerShell script untuk deploy monitoring dengan UE counting yang benar

Write-Host "=== NetFlux5G Enhanced Monitoring Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Check if docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Navigate to monitoring directory
$MONITORING_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $MONITORING_DIR
Write-Host "📁 Working directory: $MONITORING_DIR" -ForegroundColor Yellow

# Build custom metrics exporter
Write-Host ""
Write-Host "🔨 Building custom metrics exporter..." -ForegroundColor Cyan
docker build -f Dockerfile.metrics -t netflux5g-metrics-exporter .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Metrics exporter built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to build metrics exporter" -ForegroundColor Red
    exit 1
}

# Start monitoring stack
Write-Host ""
Write-Host "🚀 Starting monitoring stack..." -ForegroundColor Cyan
docker-compose down 2>$null  # Stop any existing containers
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Monitoring stack started successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start monitoring stack" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host ""
Write-Host "📊 Checking service status..." -ForegroundColor Cyan

$services = @(
    @{name="prometheus"; port=9090},
    @{name="grafana"; port=3000},
    @{name="metrics_exporter"; port=8000},
    @{name="blackbox-exporter"; port=9115}
)

$all_healthy = $true

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.port)" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✅ $($service.name) is healthy (port $($service.port))" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($service.name) is not responding (port $($service.port))" -ForegroundColor Red
        $all_healthy = $false
    }
}

Write-Host ""
if ($all_healthy) {
    Write-Host "🎉 All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Access points:" -ForegroundColor Cyan
    Write-Host "   • Grafana:     http://localhost:3000 (admin/admin)" -ForegroundColor White
    Write-Host "   • Prometheus:  http://localhost:9090" -ForegroundColor White
    Write-Host "   • Metrics:     http://localhost:8000/metrics" -ForegroundColor White
    Write-Host "   • Blackbox:    http://localhost:9115" -ForegroundColor White
    Write-Host ""
    Write-Host "📈 Custom metrics available:" -ForegroundColor Cyan
    Write-Host "   • netflux5g_connected_ues - Number of connected UEs" -ForegroundColor White
    Write-Host "   • netflux5g_connected_gnbs - Number of connected gNodeBs" -ForegroundColor White
    Write-Host "   • netflux5g_pdu_sessions - Number of active PDU sessions" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 To check UE count manually:" -ForegroundColor Cyan
    Write-Host "   Invoke-WebRequest http://localhost:8000/metrics | Select-String 'netflux5g_connected_ues'" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Note: Make sure your 5G containers are running for accurate metrics" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Some services are not healthy. Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs <service_name>" -ForegroundColor White
}

Write-Host ""
Write-Host "🏁 Deployment complete!" -ForegroundColor Green
