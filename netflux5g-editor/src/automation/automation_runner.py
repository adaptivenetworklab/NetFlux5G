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
        
        # Connect signals
        self.status_updated.connect(self.main_window.showCanvasStatus)
        
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
        
        # Check if docker-compose is available
        try:
            subprocess.run(["docker-compose", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try docker compose (newer syntax)
            try:
                subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise Exception("Docker Compose is not installed or not accessible")
        
        # Start Docker Compose services
        cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
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
            result = subprocess.run(
                ["docker-compose", "-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
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
                    subprocess.run(
                        ["docker-compose", "-f", compose_file, "down"],
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
# NetFlux5G Connectivity Test Script

echo "=== NetFlux5G Connectivity Test ==="
echo "Testing UE connectivity through 5G network..."

# Test UE 1 connectivity
echo "Testing UE 1..."
docker exec mn.ue_test_1 ping -c 3 -I uesimtun0 8.8.8.8 > /logs/ue1_ping.log 2>&1
UE1_RESULT=$?

# Test UE 2 connectivity  
echo "Testing UE 2..."
docker exec mn.ue_test_2 ping -c 3 -I uesimtun0 8.8.8.8 > /logs/ue2_ping.log 2>&1
UE2_RESULT=$?

# Test UE 3 connectivity
echo "Testing UE 3..."
docker exec mn.ue_test_3 ping -c 3 -I uesimtun0 8.8.8.8 > /logs/ue3_ping.log 2>&1
UE3_RESULT=$?

# Report results
if [ $UE1_RESULT -eq 0 ] && [ $UE2_RESULT -eq 0 ] && [ $UE3_RESULT -eq 0 ]; then
    echo "SUCCESS: All UEs have connectivity"
    exit 0
else
    echo "FAILED: Some UEs failed connectivity test"
    exit 1
fi
''')
        os.chmod(connectivity_script, 0o755)
        
        # Create data transfer test script
        data_test_script = os.path.join(scripts_dir, "test_data_transfer.sh")
        with open(data_test_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G Data Transfer Test Script

echo "=== NetFlux5G Data Transfer Test ==="

# Start iperf3 server on UPF
docker exec mn.upf1 iperf3 -s -p 5201 -D

# Test data transfer from UE 1
echo "Testing data transfer from UE 1..."
docker exec mn.ue_test_1 iperf3 -c 10.100.0.1 -p 5201 -t 10 -J > /logs/ue1_iperf.json

# Test data transfer from UE 2
echo "Testing data transfer from UE 2..."
docker exec mn.ue_test_2 iperf3 -c 10.100.0.1 -p 5201 -t 10 -J > /logs/ue2_iperf.json

echo "Data transfer tests completed"
exit 0
''')
        os.chmod(data_test_script, 0o755)
        
        # Create registration test script
        registration_script = os.path.join(scripts_dir, "test_registration.sh")
        with open(registration_script, 'w') as f:
            f.write('''#!/bin/bash
# NetFlux5G UE Registration Test Script

echo "=== NetFlux5G UE Registration Test ==="

# Check UE registration status
echo "Checking UE registration status..."

# Check if uesimtun interfaces are created (indicates successful registration)
UE1_TUN=$(docker exec mn.ue_test_1 ip link show uesimtun0 2>/dev/null)
UE2_TUN=$(docker exec mn.ue_test_2 ip link show uesimtun0 2>/dev/null)
UE3_TUN=$(docker exec mn.ue_test_3 ip link show uesimtun0 2>/dev/null)

REGISTERED=0
if [ ! -z "$UE1_TUN" ]; then
    echo "UE 1: REGISTERED"
    ((REGISTERED++))
fi

if [ ! -z "$UE2_TUN" ]; then
    echo "UE 2: REGISTERED"
    ((REGISTERED++))
fi

if [ ! -z "$UE3_TUN" ]; then
    echo "UE 3: REGISTERED"
    ((REGISTERED++))
fi

echo "Registered UEs: $REGISTERED/3"

if [ $REGISTERED -eq 3 ]; then
    echo "SUCCESS: All UEs registered"
    exit 0
else
    echo "FAILED: Not all UEs registered"
    exit 1
fi
''')
        os.chmod(registration_script, 0o755)
    
    def _generate_test_configurations(self):
        """Generate test-specific configurations."""
        # Generate Docker Compose for testing
        self.docker_compose_exporter.export_docker_compose_files(self.export_dir)
        
        # Generate Mininet script for testing
        script_name = "test_topology.py"
        self.mininet_script_path = os.path.join(self.export_dir, script_name)
        self.mininet_exporter.export_to_mininet_script(self.mininet_script_path)
        
        # Make scripts executable
        if os.path.exists(self.mininet_script_path):
            os.chmod(self.mininet_script_path, 0o755)
    
    def _deploy_test_infrastructure(self):
        """Deploy test infrastructure."""
        try:
            # Start Docker Compose services
            compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
            
            cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
            debug_print(f"Starting test infrastructure: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_print(f"Docker Compose failed: {result.stderr}")
                return False
            
            # Start Mininet (in background for testing)
            mininet_log = os.path.join(self.export_dir, "logs", "mininet.log")
            self.mininet_process = subprocess.Popen(
                ["sudo", "python3", self.mininet_script_path],
                cwd=self.export_dir,
                stdout=open(mininet_log, 'w'),
                stderr=subprocess.STDOUT
            )
            
            return True
            
        except Exception as e:
            error_print(f"Infrastructure deployment failed: {e}")
            return False
    
    def _wait_for_services_ready(self):
        """Wait for all services to be ready."""
        # Wait for Docker services
        max_wait = 60
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                result = subprocess.run(
                    ["docker-compose", "-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
                    capture_output=True,
                    text=True,
                    cwd=self.export_dir
                )
                
                # Check if all services are running
                if "Up" in result.stdout:
                    debug_print("Docker services are ready")
                    break
                    
            except Exception as e:
                debug_print(f"Waiting for services: {e}")
            
            time.sleep(5)
            wait_time += 5
        
        # Additional wait for 5G components to initialize
        time.sleep(30)
    
    def _test_ue_registration(self):
        """Test UE registration with the network."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_registration.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            debug_print(f"UE registration test result: {success}")
            debug_print(f"Registration output: {result.stdout}")
            
            return success
            
        except Exception as e:
            error_print(f"UE registration test failed: {e}")
            return False
    
    def _test_connectivity(self):
        """Test network connectivity."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_connectivity.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            success = result.returncode == 0
            
            # Parse connectivity metrics
            metrics = {
                'connectivity_success': success,
                'ue_count_tested': 3,
                'ping_response_time': 'N/A'
            }
            
            return {
                'success': success,
                'metrics': metrics
            }
            
        except Exception as e:
            error_print(f"Connectivity test failed: {e}")
            return {
                'success': False,
                'metrics': {'error': str(e)}
            }
    
    def _test_data_transfer(self):
        """Test data transfer performance."""
        try:
            script_path = os.path.join(self.export_dir, "scripts", "test_data_transfer.sh")
            result = subprocess.run(
                ["bash", script_path],
                cwd=self.export_dir,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            success = result.returncode == 0
            
            # Parse performance metrics from iperf results
            metrics = {
                'data_transfer_success': success,
                'average_throughput': 'N/A',
                'total_data_transferred': 'N/A'
            }
            
            # Try to parse iperf JSON results
            try:
                import json
                ue1_log = os.path.join(self.export_dir, "logs", "ue1_iperf.json")
                if os.path.exists(ue1_log):
                    with open(ue1_log, 'r') as f:
                        iperf_data = json.load(f)
                        if 'end' in iperf_data:
                            metrics['average_throughput'] = f"{iperf_data['end']['sum_received']['bits_per_second'] / 1e6:.2f} Mbps"
                            metrics['total_data_transferred'] = f"{iperf_data['end']['sum_received']['bytes'] / 1e6:.2f} MB"
            except:
                pass
            
            return {
                'success': success,
                'metrics': metrics
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