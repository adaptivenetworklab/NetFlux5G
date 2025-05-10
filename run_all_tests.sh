#!/bin/bash
# Main script to run all container technology comparison tests
# Generates reports and stores results in results/ directory

set -e

echo "====================================================="
echo "COMPREHENSIVE CONTAINER TECHNOLOGY COMPARISON SCRIPT"
echo "====================================================="
echo "This script will run all tests to compare Docker, Containerd, Podman, and LXD on Ubuntu 22.04"
echo ""

# Create results directory
mkdir -p results/{raw,processed}
cd results

# Record system information
echo "Recording system information..."
{
  echo "===== SYSTEM INFORMATION ====="
  uname -a
  lsb_release -a 2>&1
  echo ""
  echo "CPU Information:"
  lscpu
  echo ""
  echo "Memory Information:"
  free -h
  echo ""
  echo "Disk Information:"
  df -h
} > raw/system_info.txt

# Record container technology versions
echo "Recording container technology versions..."
{
  echo "===== CONTAINER TECHNOLOGY VERSIONS ====="
  echo "Docker:"
  docker --version 2>&1
  echo ""
  echo "Containerd:"
  containerd --version 2>&1
  nerdctl --version 2>&1
  echo ""
  echo "Podman:"
  podman --version 2>&1
  echo ""
  echo "LXD:"
  lxd --version 2>&1
  lxc --version 2>&1
} > raw/versions.txt

# List of tests to run
TESTS=(
  "Basic Container Operations:container_operations.sh"
  "Resource Isolation:resource_isolation.sh"
  "Container Stress Test:container_stress_test.sh"
  "CPU Memory Performance:performance_test.sh"
  "IO Performance:io_performance_test.sh"
  "Network Performance:network_performance_test.sh"
  "Security Comparison:security_comparison.sh"
  "Startup Time Test:startup_time_test.sh"
  "Runtime Overhead:runtime_overhead_test.sh"
  "Multi-Container Test:multi_container_test.sh"
  "Build Performance:build_performance_test.sh"
  "Storage Driver:storage_driver_test.sh"
  "Advanced Sysbench Test:sysbench_stress_test.sh"
  "Application Deployment:application_deployment_test.sh"
  "Monitoring Logging:monitoring_logging_comparison.sh"
  "Versioning Test:update_versioning_test.sh"
)

# Run each test and capture output
for test in "${TESTS[@]}"; do
  test_name="${test%%:*}"
  test_script="${test##*:}"
  echo "Running $test_name test..."
  if bash "../tests/$test_script" > "raw/${test_name// /_}_results.txt" 2>&1; then
    echo "✓ $test_name test completed"
  else
    echo "✗ $test_name test failed"
  fi
  echo ""
  echo "Press Enter to continue to the next test..."
  read -r
done

# Generate reports
echo "Generating reports..."
bash ../utils/generate_report.sh

cd ..
echo "All tests completed. Results are available in the results/ directory."
echo "Open results/index.html in a browser to view the report."
