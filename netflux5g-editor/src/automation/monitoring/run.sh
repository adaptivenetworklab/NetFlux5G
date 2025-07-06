#!/bin/bash

# Navigasi ke direktori monitoring (jika belum berada di sana)
cd "$(dirname "$0")"

echo "Menjalankan stack monitoring (Prometheus, Grafana, Node Exporter, cAdvisor)..."
docker compose up -d

echo "Monitoring stack telah dijalankan."
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo "Gunakan login default Grafana: admin / admin"

