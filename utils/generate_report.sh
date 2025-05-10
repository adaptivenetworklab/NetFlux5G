#!/bin/bash
# Generates HTML and Markdown reports from test results

set -e

echo "Generating summary reports..."

# Ensure results directory exists
mkdir -p results/{raw,processed}

# Generate Markdown summary report
cat > results/summary_report.md << EOF
# Container Technology Comparison: Summary Report

## Test Environment
- **OS**: Ubuntu 22.04
- **Test Date**: $(date)
- **Hardware**: See system_info.txt for details

## Container Technologies Tested
- Docker
- Containerd (with nerdctl)
- Podman
- LXD

## Key Findings

### Performance Metrics

| Metric | Docker | Containerd | Podman | LXD |
|--------|--------|------------|--------|-----|
| Startup Time | See startup_time_test_results.txt | See startup_time_test_results.txt | See startup_time_test_results.txt | See startup_time_test_results.txt |
| Memory Usage | See runtime_overhead_test_results.txt | See runtime_overhead_test_results.txt | See runtime_overhead_test_results.txt | See runtime_overhead_test_results.txt |
| I/O Performance | See io_performance_test_results.txt | See io_performance_test_results.txt | See io_performance_test_results.txt | See io_performance_test_results.txt |
| CPU Performance | See cpu_memory_performance_results.txt | See cpu_memory_performance_results.txt | See cpu_memory_performance_results.txt | See cpu_memory_performance_results.txt |
| Build Speed | See build_performance_test_results.txt | See build_performance_test_results.txt | See build_performance_test_results.txt | N/A |

### Feature Comparison

| Feature | Docker | Containerd | Podman | LXD |
|---------|--------|------------|--------|-----|
| Daemon Required | Yes | Yes | No | Yes |
| Rootless Support | Limited | Via runtime | Native | Via snap |
| Image Format | OCI | OCI | OCI | Custom |
| Networking Options | Bridge, host, overlay, macvlan | Similar to Docker | Similar to Docker | Bridge, macvlan, physical, OVN |
| Pod Support | Via Compose | Native | Native | No (system containers) |
| Security Features | See security_comparison_results.txt | See security_comparison_results.txt | See security_comparison_results.txt | See security_comparison_results.txt |

### Use Case Recommendations

**Docker** is well-suited for:
- Development environments
- CI/CD pipelines
- Applications requiring extensive Docker ecosystem integration

**Containerd** is well-suited for:
- Kubernetes environments
- Low-level container runtime needs
- When minimal runtime overhead is required

**Podman** is well-suited for:
- Security-conscious environments requiring rootless containers
- When daemon-less operation is preferred
- When Docker compatibility is needed without the Docker daemon

**LXD** is well-suited for:
- System containers (closer to VMs)
- Long-running server workloads
- When stronger isolation is required
- When VM-like features are needed in containers

## Detailed Results
See individual test result files in results/raw/ for detailed analysis.
EOF

# Generate HTML report
cat > results/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Container Technology Comparison Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 30px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .result-link {
            display: block;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Container Technology Comparison Results</h1>
        <p>This report compares Docker, Containerd, Podman, and LXD on Ubuntu 22.04.</p>

        <h2>System Information</h2>
        <p><a href="raw/system_info.txt" class="result-link">System Information</a></p>
        <p><a href="raw/versions.txt" class="result-link">Container Technology Versions</a></p>

        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Category</th>
                <th>Description</th>
                <th>Results</th>
            </tr>
            <tr>
                <td>Basic Operations</td>
                <td>Measures basic container operations like creation, starting, stopping</td>
                <td><a href="raw/Basic_Container_Operations_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Resource Isolation</td>
                <td>Tests container resource limits and isolation</td>
                <td><a href="raw/Resource_Isolation_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Stress Testing</td>
                <td>Tests container performance under load</td>
                <td><a href="raw/Container_Stress_Test_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>CPU/Memory Performance</td>
                <td>Compares CPU and memory performance</td>
                <td><a href="raw/CPU_Memory_Performance_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>I/O Performance</td>
                <td>Measures I/O operations performance</td>
                <td><a href="raw/IO_Performance_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Network Performance</td>
                <td>Tests network connectivity and performance</td>
                <td><a href="raw/Network_Performance_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Security Comparison</td>
                <td>Compares security features</td>
                <td><a href="raw/Security_Comparison_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Startup Time</td>
                <td>Measures container startup times</td>
                <td><a href="raw/Startup_Time_Test_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Runtime Overhead</td>
                <td>Measures daemon and runtime overhead</td>
                <td><a href="raw/Runtime_Overhead_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Multi-Container Testing</td>
                <td>Tests performance with multiple containers</td>
                <td><a href="raw/Multi-Container_Test_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Build Performance</td>
                <td>Compares image build performance</td>
                <td><a href="raw/Build_Performance_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Storage Driver</td>
                <td>Compares storage drivers and performance</td>
                <td><a href="raw/Storage_Driver_results.txt" class="result-link">View Results</a></td>
            </tr>
            <tr>
                <td>Advanced Benchmarks</td>
                <td>Detailed sysbench performance tests</td>
                <td><a href="
