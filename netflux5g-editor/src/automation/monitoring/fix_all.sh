#!/bin/bash
# All-in-one script untuk memperbaiki dashboard auto-refresh

echo "🔧 NetFlux5G Dashboard Auto-Refresh Fix"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make scripts executable
chmod +x fix_dashboard_refresh.sh
chmod +x configure_grafana.sh
chmod +x verify_metrics.sh

echo "🔍 Step 1: Diagnosing current issues..."
./fix_dashboard_refresh.sh

echo ""
echo "🔧 Step 2: Configuring Grafana datasource..."
./configure_grafana.sh

echo ""
echo "✅ Step 3: Verifying final state..."
./verify_metrics.sh

echo ""
echo "🎯 Quick Manual Test:"
echo "1. Open Grafana: http://localhost:3000"
echo "2. Navigate to dashboard"
echo "3. Check if auto-refresh is working (top-right corner should show '5s')"
echo "4. Data should appear automatically without manual query execution"
echo ""
echo "💡 If still having issues:"
echo "   • Hard refresh browser (Ctrl+F5)"
echo "   • Clear browser cache"
echo "   • Check browser developer console for errors"
echo "   • Ensure 5G containers are running: docker ps --filter name=mn."
