import os
import subprocess
import threading
import time
import signal
import yaml
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from export.compose_export import DockerComposeExporter
from export.mininet_export import MininetExporter
from manager.debug import debug_print, error_print, warning_print
from prerequisites.checker import PrerequisitesChecker

class AutomationRunner(QObject):
    """Handler for running automated deployment of Docker Compose and Mininet scripts."""
    
    # Signals for status updates
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    execution_finished = pyqtSignal(bool, str)  # success, message
    test_results_ready = pyqtSignal(dict)  # test results
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.docker_compose_exporter = DockerComposeExporter(main_window)
        self.mininet_exporter = MininetExporter(main_window)
        
        # Process tracking
        self.docker_process = None
        self.mininet_process = None
        self.is_running = False
        self.export_dir = None
        self.mininet_script_path = None
        self.test_mode = False
        self.docker_compose_cmd = None  # Store the correct Docker Compose command
        
        # Connect signals
        self.status_updated.connect(self.main_window.showCanvasStatus)

    def _get_docker_compose_command(self):
        """Get the correct Docker Compose command."""
        if self.docker_compose_cmd is None:
            self.docker_compose_cmd = PrerequisitesChecker.get_docker_compose_command()
        return self.docker_compose_cmd

    def run_all(self):
        """Main entry point for RunAll functionality."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "Automation is already running. Please stop it first."
            )
            return
        
        all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
        if not all_ok:
            missing = [tool for tool, ok in checks.items() if not ok]
            instructions = PrerequisitesChecker.get_installation_instructions()
            
            error_msg = f"Missing prerequisites: {', '.join(missing)}\n\n"
            for tool in missing:
                error_msg += f"{tool.upper()}:\n{instructions[tool]}\n"
            
            QMessageBox.critical(
                self.main_window,
                "Missing Prerequisites",
                error_msg
            )
            return

        # Check if we have components to export
        nodes, links = self.main_window.extractTopology()
        core5g_components = [n for n in nodes if n['type'] == 'VGcore']
        
        if not core5g_components and not any(n['type'] in ['GNB', 'UE', 'Host', 'STA'] for n in nodes):
            QMessageBox.information(
                self.main_window,
                "No Components",
                "No 5G components or network elements found to deploy."
            )
            return
            
        # Show progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing deployment...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("NetFlux5G Automation")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self.stop_all)
        self.progress_dialog.show()
        
        # Connect progress signal
        self.progress_updated.connect(self.progress_dialog.setValue)
        
        # Start the automation in a separate thread
        self.automation_thread = threading.Thread(target=self._run_automation_sequence)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
    def _run_automation_sequence(self):
        """Run the complete automation sequence."""
        try:
            self.is_running = True
            
            # Step 1: Create working directory
            self.status_updated.emit("Creating working directory...")
            self.progress_updated.emit(10)
            self.export_dir = self._create_working_directory()
            
            # Step 2: Generate Docker Compose
            self.status_updated.emit("Generating Docker Compose configuration...")
            self.progress_updated.emit(25)
            self._generate_docker_compose()
            
            # Step 3: Generate Mininet script
            self.status_updated.emit("Generating Mininet script...")
            self.progress_updated.emit(40)
            self._generate_mininet_script()
            
            # Step 4: Start Docker Compose
            self.status_updated.emit("Starting Docker Compose services...")
            self.progress_updated.emit(60)
            self._start_docker_compose()
            
            # Step 5: Wait for services to be ready
            self.status_updated.emit("Waiting for services to initialize...")
            self.progress_updated.emit(75)
            self._wait_for_services()
            
            # Step 6: Start Mininet
            self.status_updated.emit("Starting Mininet network...")
            self.progress_updated.emit(90)
            self._start_mininet()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Deployment completed successfully!")
            self.execution_finished.emit(True, "All services started successfully")
            
        except Exception as e:
            error_msg = f"Automation failed: {str(e)}"
            error_print(f"ERROR: {error_msg}")
            self.status_updated.emit(error_msg)
            self.execution_finished.emit(False, error_msg)
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def _create_working_directory(self):
        """Create a working directory for the deployment."""
        import tempfile
        from datetime import datetime
        
        # Create a timestamped directory in the project root or temp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        export_dir = os.path.join(base_dir, "..", "export", "started", f"netflux5g_deploy_{timestamp}")
        
        os.makedirs(export_dir, exist_ok=True)
        debug_print(f"Created working directory: {export_dir}")
        return export_dir
    
    def _generate_docker_compose(self):
        """Generate Docker Compose files."""
        self.docker_compose_exporter.export_docker_compose_files(self.export_dir)
        
        # Verify the docker-compose.yaml was created
        compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
        if not os.path.exists(compose_file):
            raise Exception("Docker Compose file was not generated")
            
        debug_print(f"Docker Compose generated at: {compose_file}")
    
    def _generate_mininet_script(self):
        """Generate Mininet script."""
        script_name = "netflux5g_topology.py"
        self.mininet_script_path = os.path.join(self.export_dir, script_name)
        self.mininet_exporter.export_to_mininet_script(self.mininet_script_path)
        
        # Verify the script was created
        if not os.path.exists(self.mininet_script_path):
            raise Exception("Mininet script was not generated")
            
        # Make the script executable
        os.chmod(self.mininet_script_path, 0o755)
        debug_print(f"Mininet script generated at: {self.mininet_script_path}")

    def extractTopology(self):
        """Extract topology from main window."""
        return self.main_window.file_manager.extractTopology()
    
    def _start_docker_compose(self):
        """Start Docker Compose services."""
        compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
        
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Docker is not installed or not accessible")
        
        # Get the correct Docker Compose command
        compose_cmd = self._get_docker_compose_command()
        if not compose_cmd:
            raise Exception("Docker Compose is not installed or not accessible. Please install Docker Compose or use Docker Desktop.")
        
        # Start Docker Compose services
        cmd = compose_cmd + ["-f", compose_file, "up", "-d"]
        debug_print(f"Starting Docker Compose with command: {' '.join(cmd)}")
        
        self.docker_process = subprocess.Popen(
            cmd,
            cwd=self.export_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the process to complete
        stdout, stderr = self.docker_process.communicate()
        
        if self.docker_process.returncode != 0:
            raise Exception(f"Docker Compose failed: {stderr}")
            
        debug_print(f"Docker Compose started successfully: {stdout}")

    def _wait_for_services(self):
        """Wait for Docker services to be ready."""
        # Simple wait - in a real implementation, you might want to check service health
        time.sleep(10)
        
        # Check if services are running
        try:
            compose_cmd = self._get_docker_compose_command()
            if compose_cmd:
                result = subprocess.run(
                    compose_cmd + ["-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
                    capture_output=True,
                    text=True,
                    cwd=self.export_dir
                )
                debug_print(f"Docker services status: {result.stdout}")
        except Exception as e:
            warning_print(f"Could not check service status: {e}")

    def _start_mininet(self):
        """Start Mininet in a new terminal."""
        if not self.mininet_script_path:
            raise Exception("Mininet script path not set")
        
        # Check if mininet is available
        try:
            subprocess.run(["mn", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("Mininet is not installed or not accessible")
        
        # Create a script to run Mininet in a new terminal
        terminal_script = os.path.join(self.export_dir, "run_mininet.sh")
        with open(terminal_script, 'w') as f:
            f.write(f"""#!/bin/bash
echo "Starting Mininet topology..."
echo "Working directory: {self.export_dir}"
cd "{self.export_dir}"
sudo python3 "{self.mininet_script_path}"
echo "Mininet session ended. Press Enter to close..."
read
""")
        
        os.chmod(terminal_script, 0o755)
        
        # Launch in a new terminal window
        try:
            # Try different terminal emulators
            terminal_commands = [
                ["gnome-terminal", "--", "bash", terminal_script],
                ["xterm", "-e", f"bash {terminal_script}"],
                ["konsole", "-e", f"bash {terminal_script}"],
                ["lxterminal", "-e", f"bash {terminal_script}"]
            ]
            
            launched = False
            for cmd in terminal_commands:
                try:
                    self.mininet_process = subprocess.Popen(cmd)
                    launched = True
                    debug_print(f"Mininet launched with: {' '.join(cmd)}")
                    break
                except FileNotFoundError:
                    continue
            
            if not launched:
                # Fallback: run in background and log to file
                log_file = os.path.join(self.export_dir, "mininet.log")
                self.mininet_process = subprocess.Popen(
                    ["sudo", "python3", self.mininet_script_path],
                    cwd=self.export_dir,
                    stdout=open(log_file, 'w'),
                    stderr=subprocess.STDOUT
                )
                debug_print(f"Mininet started in background, logging to: {log_file}")
        
        except Exception as e:
            raise Exception(f"Failed to start Mininet: {str(e)}")
    
    def stop_all(self):
        """Stop all running processes."""
        if not self.is_running:
            return
            
        self.status_updated.emit("Stopping all services...")
        
        try:
            # Stop Mininet
            if self.mininet_process and self.mininet_process.poll() is None:
                debug_print("Stopping Mininet...")
                try:
                    # Try graceful shutdown first
                    self.mininet_process.terminate()
                    self.mininet_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    self.mininet_process.kill()
                    
                # Clean up Mininet
                try:
                    subprocess.run(["sudo", "mn", "-c"], capture_output=True)
                except:
                    pass
            
            # Stop Docker Compose
            if self.export_dir:
                compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
                if os.path.exists(compose_file):
                    debug_print("Stopping Docker Compose...")
                    compose_cmd = self._get_docker_compose_command()
                    if compose_cmd:
                        subprocess.run(
                            compose_cmd + ["-f", compose_file, "down"],
                            cwd=self.export_dir,
                            capture_output=True
                        )
            
            self.status_updated.emit("All services stopped")
            
        except Exception as e:
            error_print(f"Error stopping services: {e}")
            self.status_updated.emit(f"Error stopping services: {e}")
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def is_deployment_running(self):
        """Check if deployment is currently running."""
        return self.is_running
    
    def get_deployment_info(self):
        """Get information about the current deployment."""
        if not self.export_dir:
            return None
            
        return {
            'export_dir': self.export_dir,
            'docker_compose_file': os.path.join(self.export_dir, "docker-compose.yaml"),
            'mininet_script': self.mininet_script_path,
            'is_running': self.is_running
        }
    
    def run_end_to_end_test(self):
        """Run complete end-to-end test sequence."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "Testing is already running. Please wait for completion."
            )
            return
        
        # Check prerequisites
        all_ok, checks = PrerequisitesChecker.check_all_prerequisites()
        if not all_ok:
            missing = [tool for tool, ok in checks.items() if not ok]
            instructions = PrerequisitesChecker.get_installation_instructions()
            
            error_msg = f"Missing prerequisites for testing: {', '.join(missing)}\n\n"
            for tool in missing:
                error_msg += f"{tool.upper()}:\n{instructions[tool]}\n"
            
            QMessageBox.critical(
                self.main_window,
                "Missing Prerequisites",
                error_msg
            )
            return
        
        # Set test mode
        self.test_mode = True
        
        # Show test progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing end-to-end test...", 
            "Cancel", 
            0, 
            100, 
            self.main_window
        )
        self.progress_dialog.setWindowTitle("NetFlux5G End-to-End Test")
        self.progress_dialog.setModal(True)
        self.progress_dialog.canceled.connect(self.stop_all)
        self.progress_dialog.show()
        
        # Connect progress signal
        self.progress_updated.connect(self.progress_dialog.setValue)
        
        # Start the test automation in a separate thread
        self.automation_thread = threading.Thread(target=self._run_test_sequence)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
    def _run_test_sequence(self):
        """Run the complete end-to-end test sequence."""
        try:
            self.is_running = True
            test_results = {
                'deployment': False,
                'connectivity': False,
                'registration': False,
                'data_transfer': False,
                'performance': {},
                'errors': [],
                'duration': 0
            }
            
            start_time = time.time()
            
            # Step 1: Create test environment
            self.status_updated.emit("Creating test environment...")
            self.progress_updated.emit(5)
            self.export_dir = self._create_test_directory()
            
            # Step 2: Generate configurations
            self.status_updated.emit("Generating 5G configurations...")
            self.progress_updated.emit(15)
            self._generate_test_configurations()
            
            # Step 3: Deploy infrastructure
            self.status_updated.emit("Deploying network infrastructure...")
            self.progress_updated.emit(30)
            deployment_success = self._deploy_test_infrastructure()
            test_results['deployment'] = deployment_success
            
            if not deployment_success:
                raise Exception("Infrastructure deployment failed")
            
            # Step 4: Wait for services initialization
            self.status_updated.emit("Waiting for services to initialize...")
            self.progress_updated.emit(45)
            self._wait_for_services_ready()
            
            # Step 5: Test UE registration
            self.status_updated.emit("Testing UE registration...")
            self.progress_updated.emit(60)
            registration_success = self._test_ue_registration()
            test_results['registration'] = registration_success
            
            # Step 6: Test connectivity
            self.status_updated.emit("Testing network connectivity...")
            self.progress_updated.emit(75)
            connectivity_results = self._test_connectivity()
            test_results['connectivity'] = connectivity_results['success']
            test_results['performance'].update(connectivity_results['metrics'])
            
            # Step 7: Test data transfer
            self.status_updated.emit("Testing data transfer...")
            self.progress_updated.emit(85)
            data_results = self._test_data_transfer()
            test_results['data_transfer'] = data_results['success']
            test_results['performance'].update(data_results['metrics'])
            
            # Step 8: Generate test report
            self.status_updated.emit("Generating test report...")
            self.progress_updated.emit(95)
            test_results['duration'] = time.time() - start_time
            self._generate_test_report(test_results)
            
            self.progress_updated.emit(100)
            
            # Determine overall success
            overall_success = (
                test_results['deployment'] and 
                test_results['connectivity'] and 
                test_results['registration']
            )
            
            if overall_success:
                self.status_updated.emit("End-to-end test completed successfully!")
                self.execution_finished.emit(True, "All tests passed")
            else:
                failed_tests = []
                if not test_results['deployment']: failed_tests.append("Deployment")
                if not test_results['connectivity']: failed_tests.append("Connectivity")
                if not test_results['registration']: failed_tests.append("Registration")
                
                message = f"Some tests failed: {', '.join(failed_tests)}"
                self.status_updated.emit(f"Test completed with failures: {message}")
                self.execution_finished.emit(False, message)
            
            # Emit test results
            self.test_results_ready.emit(test_results)
            
        except Exception as e:
            test_results['errors'].append(str(e))
            test_results['duration'] = time.time() - start_time if 'start_time' in locals() else 0
            
            error_msg = f"End-to-end test failed: {str(e)}"
            error_print(f"ERROR: {error_msg}")
            self.status_updated.emit(error_msg)
            self.execution_finished.emit(False, error_msg)
            self.test_results_ready.emit(test_results)
        finally:
            self.is_running = False
            self.test_mode = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def _create_test_directory(self):
        """Create a test directory with all necessary test scripts."""
        import tempfile
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        test_dir = os.path.join(base_dir, "..", "test_results", f"e2e_test_{timestamp}")
        
        os.makedirs(test_dir, exist_ok=True)
        os.makedirs(os.path.join(test_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(test_dir, "config"), exist_ok=True)
        os.makedirs(os.path.join(test_dir, "scripts"), exist_ok=True)
        
        # Create test scripts
        self._create_test_scripts(test_dir)
        
        debug_print(f"Created test directory: {test_dir}")
        return test_dir
    
    def _create_test_scripts(self, test_dir):
        """Create testing scripts for validation."""
        scripts_dir = os.path.join(test_dir, "scripts")
        
        # Create connectivity test script
        connectivity_script = os.path.join(scripts_dir, "test_connectivity.sh")
        with open(connectivity_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G Connectivity Test Script for Open5GS-UERANSIM

echo "=== NetFlux5G Connectivity Test ==="
echo "Testing UE connectivity through Open5GS 5G network..."

# Check if containers are running
echo "Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(ues|gnb|open5gs)"

# Test UE connectivity - Open5GS-UERANSIM uses different container names
echo "Testing UE connectivity..."

# Find UE containers
UE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "ues[0-9]+" | head -3)
SUCCESS_COUNT=0
TOTAL_COUNT=0

for container in $UE_CONTAINERS; do
    echo "Testing connectivity for $container..."
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    # Check if uesimtun interfaces exist
    TUNNELS=$(docker exec $container ip link show 2>/dev/null | grep uesimtun | wc -l)
    
    if [ $TUNNELS -gt 0 ]; then
        echo "  Found $TUNNELS tunnel interface(s)"
        
        # Test connectivity on first available tunnel
        for i in {0..2}; do
            if docker exec $container ip link show uesimtun$i >/dev/null 2>&1; then
                echo "  Testing ping through uesimtun$i..."
                if docker exec $container ping -c 3 -W 5 -I uesimtun$i 8.8.8.8 >/dev/null 2>&1; then
                    echo "  SUCCESS: $container has connectivity through uesimtun$i"
                    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                    break
                else
                    echo "  FAILED: Ping failed on uesimtun$i"
                fi
            fi
        done
    else
        echo "  FAILED: No tunnel interfaces found in $container"
    fi
done

echo "Connectivity test results: $SUCCESS_COUNT/$TOTAL_COUNT UE containers have connectivity"

# Log results
mkdir -p /tmp/test_logs
echo "Connectivity: $SUCCESS_COUNT/$TOTAL_COUNT" > /tmp/test_logs/connectivity_results.txt

if [ $SUCCESS_COUNT -gt 0 ] && [ $TOTAL_COUNT -gt 0 ]; then
    echo "SUCCESS: At least one UE has connectivity"
    exit 0
else
    echo "FAILED: No UEs have connectivity"
    exit 1
fi
''')
        os.chmod(connectivity_script, 0o755)
        
        # Create data transfer test script
        data_test_script = os.path.join(scripts_dir, "test_data_transfer.sh")
        with open(data_test_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G Data Transfer Test Script for Open5GS-UERANSIM

echo "=== NetFlux5G Data Transfer Test ==="

# Find UE containers
UE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "ues[0-9]+" | head -3)

if [ -z "$UE_CONTAINERS" ]; then
    echo "FAILED: No UE containers found"
    exit 1
fi

# Start a simple HTTP server in one UE container for testing
UE_SERVER=$(echo $UE_CONTAINERS | cut -d' ' -f1)
echo "Starting HTTP server in $UE_SERVER..."

# Get the IP of the first tunnel interface
SERVER_IP=$(docker exec $UE_SERVER ip addr show uesimtun0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)

if [ -z "$SERVER_IP" ]; then
    echo "FAILED: Could not get server IP from tunnel interface"
    exit 1
fi

# Start simple HTTP server in background
docker exec -d $UE_SERVER python3 -m http.server 8080 --bind $SERVER_IP

sleep 5

# Test data transfer from other UE containers
SUCCESS_COUNT=0
TEST_COUNT=0

for container in $UE_CONTAINERS; do
    if [ "$container" != "$UE_SERVER" ]; then
        echo "Testing data transfer from $container to $UE_SERVER ($SERVER_IP)..."
        TEST_COUNT=$((TEST_COUNT + 1))
        
        # Check if we can reach the HTTP server
        if docker exec $container wget -q --timeout=10 --tries=3 -O /dev/null http://$SERVER_IP:8080/ 2>/dev/null; then
            echo "  SUCCESS: Data transfer working from $container"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "  FAILED: Data transfer failed from $container"
        fi
    fi
done

# Log results
mkdir -p /tmp/test_logs
echo "Data Transfer: $SUCCESS_COUNT/$TEST_COUNT" > /tmp/test_logs/data_transfer_results.txt

echo "Data transfer test results: $SUCCESS_COUNT/$TEST_COUNT"

if [ $SUCCESS_COUNT -gt 0 ]; then
    echo "SUCCESS: Data transfer working"
    exit 0
else
    echo "FAILED: No successful data transfers"
    exit 1
fi
''')
        os.chmod(data_test_script, 0o755)
        
        # Create registration test script
        registration_script = os.path.join(scripts_dir, "test_registration.sh")
        with open(registration_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G UE Registration Test Script for Open5GS-UERANSIM

echo "=== NetFlux5G UE Registration Test ==="

# Find UE containers
UE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "ues[0-9]+" | head -3)

if [ -z "$UE_CONTAINERS" ]; then
    echo "FAILED: No UE containers found"
    exit 1
fi

echo "Found UE containers: $UE_CONTAINERS"

REGISTERED=0
TOTAL=0

for container in $UE_CONTAINERS; do
    echo "Checking registration status for $container..."
    TOTAL=$((TOTAL + 1))
    
    # Check if uesimtun interfaces are created (indicates successful registration)
    TUNNEL_COUNT=$(docker exec $container ip link show 2>/dev/null | grep uesimtun | wc -l)
    
    if [ $TUNNEL_COUNT -gt 0 ]; then
        echo "  Found $TUNNEL_COUNT tunnel interface(s)"
        
        # Check if interfaces have IP addresses
        for i in {0..2}; do
            if docker exec $container ip addr show uesimtun$i 2>/dev/null | grep -q 'inet '; then
                IP=$(docker exec $container ip addr show uesimtun$i 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
                echo "  uesimtun$i has IP: $IP"
                REGISTERED=$((REGISTERED + 1))
                break
            fi
        done
        
        if [ $TUNNEL_COUNT -gt 0 ] && [ -z "$IP" ]; then
            echo "  WARNING: Tunnel interfaces exist but no IP assigned"
        fi
    else
        echo "  FAILED: No tunnel interfaces found"
    fi
done

# Also check gNB logs for registration messages
echo "Checking gNB logs for registration events..."
GNB_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "gnb[0-9]*" | head -1)

if [ ! -z "$GNB_CONTAINERS" ]; then
    GNB_CONTAINER=$(echo $GNB_CONTAINERS | cut -d' ' -f1)
    REG_MESSAGES=$(docker logs $GNB_CONTAINER 2>&1 | grep -i -c "registration\|attach\|connected" || echo "0")
    echo "Found $REG_MESSAGES registration-related messages in gNB logs"
fi

# Log results
mkdir -p /tmp/test_logs
echo "Registration: $REGISTERED tunnel interfaces with IPs" > /tmp/test_logs/registration_results.txt
echo "Total UE containers: $TOTAL" >> /tmp/test_logs/registration_results.txt

echo "Registration test results: $REGISTERED UE tunnel interfaces with IP addresses"
echo "Total UE containers checked: $TOTAL"

if [ $REGISTERED -gt 0 ]; then
    echo "SUCCESS: At least one UE is registered (has tunnel interface with IP)"
    exit 0
else
    echo "FAILED: No UEs appear to be registered"
    exit 1
fi
''')
        os.chmod(registration_script, 0o755)
        
        # Create comprehensive status check script
        status_script = os.path.join(scripts_dir, "check_status.sh")
        with open(status_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G Status Check Script

echo "=== NetFlux5G Deployment Status ==="

echo "Docker containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(open5gs|ues|gnb|mongo|webui)"

echo -e "\nUE Tunnel Interfaces:"
UE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "ues[0-9]+")
for container in $UE_CONTAINERS; do
    echo "=== $container ==="
    docker exec $container ip addr show 2>/dev/null | grep -A 3 uesimtun || echo "No tunnel interfaces"
done

echo -e "\ngNB Status:"
GNB_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E "gnb[0-9]*")
for container in $GNB_CONTAINERS; do
    echo "=== $container ==="
    docker exec $container ps aux | grep nr-gnb || echo "gNB process not found"
done

echo -e "\nOpen5GS Core Status:"
CORE_CONTAINERS=$(docker ps --format "{{.Names}}" | grep open5gs)
for container in $CORE_CONTAINERS; do
    echo "=== $container ==="
    docker exec $container ps aux | grep open5gs || echo "Open5GS processes not found"
done
''')
        os.chmod(status_script, 0o755)

    def _wait_for_services_ready(self):
        """Wait for all services to be ready with improved timing."""
        # Wait for Docker services
        max_wait = 120  # Increased wait time for 5G services
        wait_time = 0
        
        self.status_updated.emit("Waiting for Docker containers to start...")
        
        while wait_time < max_wait:
            try:
                compose_cmd = self._get_docker_compose_command()
                if compose_cmd:
                    result = subprocess.run(
                        compose_cmd + ["-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
                        capture_output=True,
                        text=True,
                        cwd=self.export_dir
                    )
                    
                    # Check if all services are running
                    running_services = result.stdout.count("Up")
                    total_services = len([line for line in result.stdout.split('\n') if line.strip() and not line.startswith('NAME')])
                    
                    if running_services > 0 and "Up" in result.stdout:
                        debug_print(f"Docker services ready: {running_services}/{total_services}")
                        break
                        
            except Exception as e:
                debug_print(f"Waiting for services: {e}")
            
            time.sleep(10)
            wait_time += 10
        
        # Wait for 5G core to initialize
        self.status_updated.emit("Waiting for 5G core to initialize...")
        time.sleep(30)
        
        # Wait for UE registration
        self.status_updated.emit("Waiting for UE registration...")
        time.sleep(45)  # Give more time for UE registration
        
        # Run status check
        try:
            script_path = os.path.join(self.export_dir, "scripts", "check_status.sh")
            if os.path.exists(script_path):
                result = subprocess.run(
                    ["bash", script_path],
                    cwd=self.export_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                debug_print(f"Status check output: {result.stdout}")
            else:
                debug_print("Status check script not found")
        except Exception as e:
            debug_print(f"Status check failed: {e}")

    def _test_ue_registration(self):
        """Test UE registration with improved error handling."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_registration.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=90
            )
            
            success = result.returncode == 0
            debug_print(f"UE registration test result: {success}")
            debug_print(f"Registration output: {result.stdout}")
            
            if result.stderr:
                debug_print(f"Registration errors: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            error_print("UE registration test timed out")
            return False
        except Exception as e:
            error_print(f"UE registration test failed: {e}")
            return False
    
    def _test_connectivity(self):
        """Test network connectivity with improved error handling."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_connectivity.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            success = result.returncode == 0
            
            # Try to parse connectivity results
            metrics = {
                'connectivity_success': success,
                'test_output': result.stdout[-500:] if result.stdout else 'No output'  # Last 500 chars
            }
            
            # Check for specific success indicators
            if result.stdout:
                if "SUCCESS:" in result.stdout:
                    success = True
                elif "FAILED:" in result.stdout and "No UEs have connectivity" in result.stdout:
                    success = False
            
            debug_print(f"Connectivity test result: {success}")
            debug_print(f"Connectivity output: {result.stdout}")
            
            if result.stderr:
                debug_print(f"Connectivity errors: {result.stderr}")
                metrics['errors'] = result.stderr
            
            return {
                'success': success,
                'metrics': metrics
            }
            
        except subprocess.TimeoutExpired:
            error_print("Connectivity test timed out")
            return {
                'success': False,
                'metrics': {'error': 'Test timed out'}
            }
        except Exception as e:
            error_print(f"Connectivity test failed: {e}")
            return {
                'success': False,
                'metrics': {'error': str(e)}
            }
    
    def _test_data_transfer(self):
        """Test data transfer performance with improved error handling."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_data_transfer.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=240
            )
            
            success = result.returncode == 0
            
            metrics = {
                'data_transfer_success': success,
                'test_output': result.stdout[-500:] if result.stdout else 'No output'
            }
            
            debug_print(f"Data transfer test result: {success}")
            debug_print(f"Data transfer output: {result.stdout}")
            
            if result.stderr:
                debug_print(f"Data transfer errors: {result.stderr}")
                metrics['errors'] = result.stderr
            
            return {
                'success': success,
                'metrics': metrics
            }
            
        except subprocess.TimeoutExpired:
            error_print("Data transfer test timed out")
            return {
                'success': False,
                'metrics': {'error': 'Test timed out'}
            }
        except Exception as e:
            error_print(f"Data transfer test failed: {e}")
            return {
                'success': False,
                'metrics': {'error': str(e)}
            }
    
    def _generate_test_report(self, test_results):
        """Generate comprehensive test report."""
        report_file = os.path.join(self.export_dir, "test_report.html")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NetFlux5G End-to-End Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background: #d4edda; border-color: #c3e6cb; }}
        .failure {{ background: #f8d7da; border-color: #f5c6cb; }}
        .metric {{ margin: 5px 0; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>NetFlux5G End-to-End Test Report</h1>
        <p class="timestamp">Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Test Summary</h2>
        <div class="metric">Duration: {test_results['duration']:.2f} seconds</div>
        <div class="metric">Overall Result: {'PASS' if all([test_results['deployment'], test_results['connectivity'], test_results['registration']]) else 'FAIL'}</div>
    </div>
    
    <div class="section {'success' if test_results['deployment'] else 'failure'}">
        <h3>Deployment Test</h3>
        <p>Status: {'PASS' if test_results['deployment'] else 'FAIL'}</p>
        <p>All network components deployed and started successfully.</p>
    </div>
    
    <div class="section {'success' if test_results['registration'] else 'failure'}">
        <h3>UE Registration Test</h3>
        <p>Status: {'PASS' if test_results['registration'] else 'FAIL'}</p>
        <p>User Equipment registration with the 5G core network.</p>
    </div>
    
    <div class="section {'success' if test_results['connectivity'] else 'failure'}">
        <h3>Connectivity Test</h3>
        <p>Status: {'PASS' if test_results['connectivity'] else 'FAIL'}</p>
        <p>End-to-end connectivity through the 5G network.</p>
    </div>
    
    <div class="section {'success' if test_results['data_transfer'] else 'failure'}">
        <h3>Data Transfer Test</h3>
        <p>Status: {'PASS' if test_results['data_transfer'] else 'FAIL'}</p>
        <p>Data transfer performance testing.</p>
    </div>
    
    <div class="section">
        <h3>Performance Metrics</h3>
        {self._format_metrics(test_results['performance'])}
    </div>
    
    {'<div class="section failure"><h3>Errors</h3>' + '<br>'.join(test_results['errors']) + '</div>' if test_results['errors'] else ''}
</body>
</html>
"""
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        debug_print(f"Test report generated: {report_file}")
    
    def _format_metrics(self, metrics):
        """Format performance metrics for HTML report."""
        if not metrics:
            return "<p>No metrics available</p>"
        
        html = ""
        for key, value in metrics.items():
            html += f'<div class="metric">{key.replace("_", " ").title()}: {value}</div>'
        
        return html