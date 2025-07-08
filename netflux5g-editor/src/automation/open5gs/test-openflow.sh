#!/bin/bash

# Test script to verify OpenFlow version compatibility
# This script helps debug OpenFlow version mismatches in OVS

set -e

BRIDGE_NAME=${OVS_BRIDGE_NAME:-"br-open5gs"}

echo "=== OpenFlow Version Compatibility Test ==="
echo "Testing bridge: $BRIDGE_NAME"
echo ""

# Check if bridge exists
if ! ovs-vsctl br-exists $BRIDGE_NAME; then
    echo "ERROR: Bridge $BRIDGE_NAME does not exist"
    exit 1
fi

# Get bridge protocols
echo "1. Bridge Protocol Configuration:"
protocols=$(ovs-vsctl get bridge $BRIDGE_NAME protocols 2>/dev/null | tr -d '[]"' | tr ',' ' ')
echo "   Configured protocols: $protocols"
echo ""

# Test different OpenFlow versions
echo "2. Testing OpenFlow Version Compatibility:"

versions=("OpenFlow10" "OpenFlow13" "OpenFlow14")
working_versions=()

for version in "${versions[@]}"; do
    echo -n "   Testing $version... "
    if ovs-ofctl -O $version show $BRIDGE_NAME >/dev/null 2>&1; then
        echo "✓ WORKING"
        working_versions+=($version)
    else
        echo "✗ FAILED"
    fi
done

echo ""

if [ ${#working_versions[@]} -eq 0 ]; then
    echo "ERROR: No OpenFlow versions are working!"
    echo "This indicates a serious OpenFlow configuration issue."
    exit 1
else
    echo "3. Working OpenFlow versions: ${working_versions[*]}"
    preferred_version=${working_versions[0]}
    echo "   Recommended version to use: $preferred_version"
fi

echo ""

# Test flow dumping with working version
echo "4. Testing Flow Operations:"
echo "   Dumping flows with $preferred_version:"
if ovs-ofctl -O $preferred_version dump-flows $BRIDGE_NAME; then
    echo "   ✓ Flow dump successful"
else
    echo "   ✗ Flow dump failed"
fi

echo ""

# Controller connection test
echo "5. Controller Connection Status:"
controller=$(ovs-vsctl get-controller $BRIDGE_NAME 2>/dev/null || echo "none")
if [ "$controller" != "none" ] && [ -n "$controller" ]; then
    echo "   Controller: $controller"
    echo "   Connection status:"
    ovs-vsctl show | grep -A5 "Controller $controller" || echo "   No detailed status available"
else
    echo "   No controller configured"
fi

echo ""
echo "=== Test Complete ==="
