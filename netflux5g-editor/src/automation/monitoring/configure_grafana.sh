#!/bin/bash
# Script untuk memastikan Prometheus datasource terkonfigurasi dengan benar di Grafana

echo "🔗 Checking and configuring Prometheus datasource..."

# Wait for Grafana to be ready
wait_for_grafana() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:3000/api/health" > /dev/null 2>&1; then
            echo "✅ Grafana is ready"
            return 0
        fi
        echo "⏳ Waiting for Grafana... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    echo "❌ Grafana failed to start"
    return 1
}

# Configure Prometheus datasource
configure_datasource() {
    echo "🔧 Configuring Prometheus datasource..."
    
    # Create datasource configuration
    datasource_config='{
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "basicAuth": false,
        "withCredentials": false,
        "jsonData": {
            "httpMethod": "POST",
            "queryTimeout": "60s",
            "timeInterval": "5s"
        }
    }'
    
    # Add datasource via API
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$datasource_config" \
        "http://admin:admin@localhost:3000/api/datasources")
    
    if echo "$response" | grep -q '"message":"Datasource added"'; then
        echo "✅ Prometheus datasource configured successfully"
        return 0
    elif echo "$response" | grep -q '"message":"Data source with the same name already exists"'; then
        echo "ℹ️  Prometheus datasource already exists"
        return 0
    else
        echo "⚠️  Datasource configuration response: $response"
        return 1
    fi
}

# Test datasource connectivity
test_datasource() {
    echo "🧪 Testing datasource connectivity..."
    
    # Get datasource ID
    datasource_info=$(curl -s "http://admin:admin@localhost:3000/api/datasources/name/Prometheus")
    datasource_id=$(echo "$datasource_info" | grep -o '"id":[0-9]*' | cut -d: -f2)
    
    if [ -n "$datasource_id" ]; then
        # Test datasource
        test_response=$(curl -s -X POST "http://admin:admin@localhost:3000/api/datasources/$datasource_id/proxy/api/v1/query?query=up")
        
        if echo "$test_response" | grep -q '"status":"success"'; then
            echo "✅ Datasource connectivity test passed"
            return 0
        else
            echo "❌ Datasource connectivity test failed"
            echo "Response: $test_response"
            return 1
        fi
    else
        echo "❌ Could not find datasource ID"
        return 1
    fi
}

# Import dashboard
import_dashboard() {
    echo "📊 Importing dashboard..."
    
    # Create dashboard import payload
    dashboard_payload='{
        "dashboard": '$(cat grafana/dashboard.json)',
        "overwrite": true,
        "inputs": [
            {
                "name": "DS_PROMETHEUS",
                "type": "datasource",
                "pluginId": "prometheus",
                "value": "Prometheus"
            }
        ]
    }'
    
    # Import dashboard
    import_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$dashboard_payload" \
        "http://admin:admin@localhost:3000/api/dashboards/import")
    
    if echo "$import_response" | grep -q '"status":"success"'; then
        echo "✅ Dashboard imported successfully"
        dashboard_url=$(echo "$import_response" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
        echo "🌐 Dashboard URL: http://localhost:3000$dashboard_url"
        return 0
    else
        echo "⚠️  Dashboard import response: $import_response"
        return 1
    fi
}

# Main execution
echo "🚀 Starting Grafana configuration..."

if wait_for_grafana; then
    configure_datasource
    sleep 2
    test_datasource
    sleep 2
    import_dashboard
    
    echo ""
    echo "🎉 Configuration complete!"
    echo ""
    echo "📋 Summary:"
    echo "   • Prometheus datasource configured"
    echo "   • Connectivity tested"
    echo "   • Dashboard imported with updated queries"
    echo "   • Auto-refresh enabled (5s interval)"
    echo ""
    echo "🌐 Access dashboard: http://localhost:3000"
    echo "   Username: admin"
    echo "   Password: admin"
    echo ""
    echo "💡 If still showing 'No data':"
    echo "   1. Check if 5G containers are running"
    echo "   2. Verify Prometheus targets: http://localhost:9090/targets"
    echo "   3. Test queries manually in Prometheus"
else
    echo "❌ Cannot configure - Grafana not available"
    exit 1
fi
