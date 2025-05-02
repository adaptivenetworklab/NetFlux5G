#!/bin/bash

# Create directories if they don't exist
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/config/datasources
mkdir -p monitoring/grafana/config/dashboards

# Ensure all required configuration files are in place

# Start monitoring stack
echo "Starting monitoring stack..."
docker compose -f monitoring.yaml up -d

echo "Monitoring stack deployment complete!"
echo "Grafana is accessible at http://localhost:3000 (username: admin, password: admin)"
echo "Prometheus is accessible at http://localhost:9090"

Make the script executable:

chmod +x deploy-monitoring.sh
