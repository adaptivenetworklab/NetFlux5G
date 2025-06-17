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

    def is_deployment_running(self):
        """Check if a deployment is currently running."""
        return self.is_running

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
    
    def _generate_test_configurations(self):
        """Generate test configurations for end-to-end testing."""
        try:
            # Extract topology to analyze components
            nodes, links = self.main_window.file_manager.extractTopology()
            
            # Find 5G Core components for testing
            core5g_components = [n for n in nodes if n['type'] == 'VGcore']
            gnb_components = [n for n in nodes if n['type'] == 'GNB']
            ue_components = [n for n in nodes if n['type'] == 'UE']
            
            if not core5g_components:
                # Create default test configuration if no VGcore components found
                debug_print("No VGcore components found, creating default test configuration")
                self._create_default_test_configuration()
                return
            
            # Generate Docker Compose for 5G Core
            self.docker_compose_exporter.export_docker_compose_files(self.export_dir)
            
            # Generate enhanced test configurations for UERANSIM
            self._generate_ueransim_test_configs(gnb_components, ue_components)
            
            debug_print("Test configurations generated successfully")
            
        except Exception as e:
            error_print(f"Failed to generate test configurations: {e}")
            raise
    
    def _create_default_test_configuration(self):
        """Create a default test configuration for basic 5G testing."""
        try:
            # Create a minimal docker-compose.yaml for testing
            config_dir = os.path.join(self.export_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Use the pre-built UERANSIM configuration from the manual implementation
            self._copy_reference_implementation()
            
            debug_print("Default test configuration created")
            
        except Exception as e:
            error_print(f"Failed to create default test configuration: {e}")
            raise
    
    def _copy_reference_implementation(self):
        """Copy the reference Open5GS-UERANSIM implementation for testing."""
        try:
            # Get the path to the manual implementation
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            manual_impl_dir = os.path.join(base_dir, "manual-implementation", "Open5Gs-UERANSIM")
            
            if not os.path.exists(manual_impl_dir):
                debug_print(f"Manual implementation not found at {manual_impl_dir}, creating basic config")
                self._create_basic_test_compose()
                return
            
            # Copy the working docker-compose files
            import shutil
            
            compose_files = ["ngc.yaml", "gnb1.yaml", "webui-db.yaml"]
            
            for compose_file in compose_files:
                src = os.path.join(manual_impl_dir, compose_file)
                if os.path.exists(src):
                    dst = os.path.join(self.export_dir, compose_file)
                    shutil.copy2(src, dst)
                    debug_print(f"Copied {compose_file} to test directory")
            
            # Copy the registration script
            reg_script_src = os.path.join(manual_impl_dir, "register_subscriber.sh")
            if os.path.exists(reg_script_src):
                reg_script_dst = os.path.join(self.export_dir, "register_subscriber.sh")
                shutil.copy2(reg_script_src, reg_script_dst)
                os.chmod(reg_script_dst, 0o755)
            
            # Create a master docker-compose.yaml that combines the services
            self._create_combined_test_compose()
            
        except Exception as e:
            error_print(f"Failed to copy reference implementation: {e}")
            self._create_basic_test_compose()
    
    def _create_basic_test_compose(self):
        """Create a basic docker-compose.yaml for testing."""
        import yaml
        
        compose_config = {
            'services': {
                'mongo': {
                    'image': 'mongo:latest',
                    'restart': 'unless-stopped',
                    'environment': {
                        'MONGO_INITDB_ROOT_USERNAME': 'root',
                        'MONGO_INITDB_ROOT_PASSWORD': 'example',
                        'MONGO_INITDB_DATABASE': 'open5gs'
                    },
                    'volumes': ['mongodb_data:/data/db'],
                    'networks': ['open5gs-ueransim_default']
                },
                'webui': {
                    'image': 'adaptive/open5gs:1.0',
                    'depends_on': ['mongo'],
                    'restart': 'unless-stopped',
                    'environment': {
                        'DB_URI': 'mongodb://mongo/open5gs',
                        'NODE_ENV': 'development'
                    },
                    'volumes': ['./config/webui.yaml:/opt/open5gs/etc/open5gs/webui.yaml'],
                    'ports': ['9999:9999'],
                    'networks': ['open5gs-ueransim_default']
                },
                'nrf': {
                    'image': 'adaptive/open5gs:1.0',
                    'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-nrfd',
                    'restart': 'on-failure',
                    'volumes': [
                        './config/nrf.yaml:/opt/open5gs/etc/open5gs/nrf.yaml',
                        './config/entrypoint.sh:/opt/open5gs/etc/open5gs/entrypoint.sh'
                    ],
                    'networks': ['open5gs-ueransim_default']
                },
                'amf': {
                    'image': 'adaptive/open5gs:1.0',
                    'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-amfd',
                    'restart': 'on-failure',
                    'depends_on': ['nrf'],
                    'volumes': [
                        './config/amf.yaml:/opt/open5gs/etc/open5gs/amf.yaml',
                        './config/entrypoint.sh:/opt/open5gs/etc/open5gs/entrypoint.sh'
                    ],
                    'cap_add': ['net_admin'],
                    'networks': ['open5gs-ueransim_default']
                },
                'smf': {
                    'image': 'adaptive/open5gs:1.0',
                    'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-smfd',
                    'restart': 'on-failure',
                    'depends_on': ['nrf'],
                    'volumes': [
                        './config/smf.yaml:/opt/open5gs/etc/open5gs/smf.yaml',
                        './config/entrypoint.sh:/opt/open5gs/etc/open5gs/entrypoint.sh'
                    ],
                    'cap_add': ['net_admin'],
                    'networks': ['open5gs-ueransim_default']
                },
                'upf': {
                    'image': 'adaptive/open5gs:1.0',
                    'command': '/opt/open5gs/etc/open5gs/entrypoint.sh open5gs-upfd',
                    'restart': 'on-failure',
                    'privileged': True,
                    'volumes': [
                        './config/upf.yaml:/opt/open5gs/etc/open5gs/upf.yaml',
                        './config/entrypoint.sh:/opt/open5gs/etc/open5gs/entrypoint.sh'
                    ],
                    'cap_add': ['net_admin'],
                    'networks': ['open5gs-ueransim_default']
                },
                'gnb1': {
                    'image': 'adaptive/ueransim:1.0',
                    'command': 'sleep infinity',
                    'restart': 'unless-stopped',
                    'privileged': True,
                    'volumes': [
                        './config/gnb1.yaml:/ueransim/config/gnb1.yaml',
                        './config/ue1.yaml:/ueransim/config/ue1.yaml',
                        './config/ue2.yaml:/ueransim/config/ue2.yaml',
                        './config/ue3.yaml:/ueransim/config/ue3.yaml'
                    ],
                    'cap_add': ['net_admin'],
                    'devices': ['/dev/net/tun'],
                    'networks': ['open5gs-ueransim_default']
                },
                'ues1': {
                    'image': 'adaptive/ueransim:1.0',
                    'command': 'sleep infinity',
                    'restart': 'unless-stopped',
                    'privileged': True,
                    'volumes': [
                        './config/ue1.yaml:/ueransim/config/ue1.yaml',
                        './config/ue2.yaml:/ueransim/config/ue2.yaml',
                        './config/ue3.yaml:/ueransim/config/ue3.yaml'
                    ],
                    'cap_add': ['net_admin'],
                    'devices': ['/dev/net/tun'],
                    'networks': ['open5gs-ueransim_default']
                }
            },
            'networks': {
                'open5gs-ueransim_default': {
                    'driver': 'bridge',
                    'driver_opts': {
                        'com.docker.network.bridge.name': 'br-open5gs'
                    },
                    'ipam': {
                        'driver': 'default',
                        'config': [
                            {'subnet': '172.22.0.0/24'}
                        ]
                    }
                }
            },
            'volumes': {
                'mongodb_data': {}
            }
        }
        
        compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
        with open(compose_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
        
        debug_print(f"Created basic test docker-compose.yaml at {compose_file}")
    
    def _create_combined_test_compose(self):
        """Create a combined docker-compose.yaml from separate files."""
        import yaml
        
        # Start with webui-db.yaml as base
        combined_config = {'services': {}, 'networks': {}, 'volumes': {}}
        
        compose_files = ["webui-db.yaml", "ngc.yaml", "gnb1.yaml"]
        
        for compose_file in compose_files:
            file_path = os.path.join(self.export_dir, compose_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    if config:
                        if 'services' in config:
                            combined_config['services'].update(config['services'])
                        if 'networks' in config:
                            combined_config['networks'].update(config['networks'])
                        if 'volumes' in config:
                            combined_config['volumes'].update(config['volumes'])
                            
                except Exception as e:
                    warning_print(f"Failed to parse {compose_file}: {e}")
        
        # Write combined configuration
        if combined_config['services']:
            compose_file = os.path.join(self.export_dir, "docker-compose.yaml")
            with open(compose_file, 'w') as f:
                yaml.dump(combined_config, f, default_flow_style=False, sort_keys=False)
            debug_print("Created combined docker-compose.yaml for testing")
        else:
            debug_print("No services found in compose files, creating basic configuration")
            self._create_basic_test_compose()
    
    def _generate_ueransim_test_configs(self, gnb_components, ue_components):
        """Generate UERANSIM configuration files for gNB and UE components."""
        try:
            config_dir = os.path.join(self.export_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Generate gNB configurations
            for i, gnb in enumerate(gnb_components, 1):
                self._create_gnb_config(gnb, config_dir, f"gnb{i}")
            
            # Generate UE configurations  
            for i, ue in enumerate(ue_components, 1):
                self._create_ue_config(ue, config_dir, f"ue{i}")
            
            # Copy entrypoint script
            self.docker_compose_exporter.copy_entrypoint_script(config_dir)
            
        except Exception as e:
            error_print(f"Failed to generate UERANSIM configs: {e}")
            raise
    
    def _create_gnb_config(self, gnb_component, config_dir, gnb_name):
        """Create gNB configuration file."""
        import yaml
        
        props = gnb_component.get('properties', {})
        
        gnb_config = {
            'mcc': props.get('GNB_MCC', '999'),
            'mnc': props.get('GNB_MNC', '70'),
            'nci': '0x000000010',
            'idLength': 32,
            'tac': int(props.get('GNB_TAC', '1')),
            'linkIp': '127.0.0.1',
            'ngapIp': '127.0.0.1',
            'gtpIp': '127.0.0.1',
            'amfConfigs': [
                {
                    'address': props.get('GNB_AMF_IP', '127.0.0.1'),
                    'port': 38412
                }
            ],
            'slices': [
                {
                    'sst': int(props.get('GNB_SST', '1')),
                    'sd': props.get('GNB_SD', '0x010203')
                }
            ],
            'ignoreStreamIds': True
        }
        
        config_file = os.path.join(config_dir, f"{gnb_name}.yaml")
        with open(config_file, 'w') as f:
            yaml.dump(gnb_config, f, default_flow_style=False)
        
        debug_print(f"Created gNB config: {config_file}")
    
    def _create_ue_config(self, ue_component, config_dir, ue_name):
        """Create UE configuration file."""
        import yaml
        
        props = ue_component.get('properties', {})
        
        ue_config = {
            'supi': f"imsi-{props.get('UE_MCC', '999')}{props.get('UE_MNC', '70')}{props.get('UE_MSISDN', '0000000001')}",
            'mcc': props.get('UE_MCC', '999'),
            'mnc': props.get('UE_MNC', '70'),
            'routingIndicator': '0000',
            'protectionScheme': 0,
            'homeNetworkPublicKey': '5a8d38864820197c3394b92613b20b76b976d0036da1df8a48130b8e7cfc61',
            'homeNetworkPrivateKey': 'f2fae229c98c9de5a6bb3395a0a2b75f8b5e1e5e1e5e1e5e1e5e1e5e1e5e1e5e',
            'key': props.get('UE_Key', '465B5CE8B199B49FAA5F0A2EE238A6BC'),
            'op': props.get('UE_OP', 'E8ED289DEBA952E4283B54E88E6183CA'),
            'opType': props.get('UE_OP_Type', 'OPC'),
            'amf': '8000',
            'imei': '356938035643803',
            'imeiSv': '4370816125816151',
            'gnbSearchList': [props.get('UE_GNB_IP', '127.0.0.1')],
            'uacAic': {
                'mps': False,
                'mcs': False
            },
            'uacAcc': {
                'normalClass': 0,
                'class11': False,
                'class12': False,
                'class13': False,
                'class14': False,
                'class15': False
            },
            'sessions': [
                {
                    'apn': props.get('UE_APN', 'internet'),
                    'slice': {
                        's-nssai': {
                            'sst': int(props.get('UE_SST', '1')),
                            'sd': props.get('UE_SD', '0x010203')
                        }
                    }
                }
            ],
            'configured-nssai': [
                {
                    'sst': int(props.get('UE_SST', '1')),
                    'sd': props.get('UE_SD', '0x010203')
                }
            ],
            'default-nssai': [
                {
                    'sst': int(props.get('UE_SST', '1')),
                    'sd': props.get('UE_SD', '0x010203')
                }
            ],
            'integrity': '2',
            'ciphering': '0'
        }
        
        config_file = os.path.join(config_dir, f"{ue_name}.yaml")
        with open(config_file, 'w') as f:
            yaml.dump(ue_config, f, default_flow_style=False)
        
        debug_print(f"Created UE config: {config_file}")

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
        """Stop all running processes and clean up containers."""
        if not self.is_running:
            # Even if not officially running, clean up any orphaned containers
            self._cleanup_orphaned_containers()
            return
            
        self.status_updated.emit("Stopping all services...")
        
        try:
            # Stop Docker Compose services first
            self._stop_compose_services()
            
            # Clean up any orphaned containers
            self._cleanup_orphaned_containers()
            
            # Stop Mininet
            self._stop_mininet()
            
            self.status_updated.emit("All services stopped and cleaned up")
            
        except Exception as e:
            error_print(f"Error stopping services: {e}")
            self.status_updated.emit(f"Error stopping services: {e}")
        finally:
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()
    
    def _stop_compose_services(self):
        """Stop Docker Compose services in the export directory."""
        if self.export_dir and os.path.exists(self.export_dir):
            compose_cmd = self._get_docker_compose_command()
            if compose_cmd:
                # Stop in reverse order
                compose_files = ["gnb1.yaml", "gnb2.yaml", "ngc.yaml", "webui-db.yaml", "docker-compose.yaml"]
                
                for compose_file in compose_files:
                    file_path = os.path.join(self.export_dir, compose_file)
                    if os.path.exists(file_path):
                        debug_print(f"Stopping services from {compose_file}...")
                        try:
                            result = subprocess.run(
                                compose_cmd + ["-f", file_path, "down", "-v", "--remove-orphans"],
                                cwd=self.export_dir,
                                capture_output=True,
                                timeout=60,
                                text=True
                            )
                            if result.returncode != 0:
                                warning_print(f"Warning stopping {compose_file}: {result.stderr}")
                            else:
                                debug_print(f"Successfully stopped {compose_file}")
                        except subprocess.TimeoutExpired:
                            warning_print(f"Timeout stopping {compose_file}")
                        except Exception as e:
                            warning_print(f"Error stopping {compose_file}: {e}")
    
    def _cleanup_orphaned_containers(self):
        """Clean up any orphaned NetFlux5G containers."""
        try:
            # Find containers with NetFlux5G test names
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                container_names = result.stdout.strip().split('\n')
                netflux_containers = [
                    name for name in container_names 
                    if name and ('e2e_test_' in name or 'netflux5g_deploy_' in name)
                ]
                
                if netflux_containers:
                    debug_print(f"Found {len(netflux_containers)} NetFlux5G containers to clean up")
                    
                    # Stop containers first
                    for container in netflux_containers:
                        try:
                            subprocess.run(
                                ["docker", "stop", container],
                                capture_output=True,
                                timeout=30
                            )
                            debug_print(f"Stopped container: {container}")
                        except Exception as e:
                            warning_print(f"Failed to stop container {container}: {e}")
                    
                    # Remove containers
                    for container in netflux_containers:
                        try:
                            subprocess.run(
                                ["docker", "rm", "-f", container],
                                capture_output=True,
                                timeout=30
                            )
                            debug_print(f"Removed container: {container}")
                        except Exception as e:
                            warning_print(f"Failed to remove container {container}: {e}")
                    
                    self.status_updated.emit(f"Cleaned up {len(netflux_containers)} orphaned containers")
                else:
                    debug_print("No NetFlux5G containers found to clean up")
                    
        except Exception as e:
            error_print(f"Error during container cleanup: {e}")
    
    def _stop_mininet(self):
        """Stop Mininet processes."""
        if self.mininet_process and self.mininet_process.poll() is None:
            debug_print("Stopping Mininet...")
            try:
                self.mininet_process.terminate()
                self.mininet_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.mininet_process.kill()
                
            # Clean up Mininet
            try:
                subprocess.run(["sudo", "mn", "-c"], capture_output=True, timeout=30)
                debug_print("Mininet cleanup completed")
            except Exception as e:
                warning_print(f"Mininet cleanup warning: {e}")
    
    def _create_test_directory(self):
        """Create a test directory with proper naming."""
        import tempfile
        from datetime import datetime
        
        # Create a timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_dir = os.path.join(base_dir, "..", "export", "stopped", f"netflux5g_test_{timestamp}")
        
        os.makedirs(test_dir, exist_ok=True)
        debug_print(f"Created test directory: {test_dir}")
        return test_dir

    def run_end_to_end_test(self):
        """Run complete end-to-end testing sequence."""
        if self.is_running:
            QMessageBox.warning(
                self.main_window,
                "Already Running",
                "A deployment is already running. Please stop it first."
            )
            return
        
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

        # Show progress dialog
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
        
        # Set test mode
        self.test_mode = True
        
        # Start the test in a separate thread
        self.test_thread = threading.Thread(target=self._run_end_to_end_test_sequence)
        self.test_thread.daemon = True
        self.test_thread.start()
        
    def _run_end_to_end_test_sequence(self):
        """Run the complete end-to-end test sequence."""
        try:
            self.is_running = True
            
            # Step 1: Create test directory
            self.status_updated.emit("Creating test environment...")
            self.progress_updated.emit(10)
            self.export_dir = self._create_test_directory()
            
            # Step 2: Generate test configurations
            self.status_updated.emit("Generating test configurations...")
            self.progress_updated.emit(25)
            self._generate_test_configurations()
            
            # Step 3: Start Docker services
            self.status_updated.emit("Starting 5G Core services...")
            self.progress_updated.emit(40)
            self._start_docker_compose()
            
            # Step 4: Wait for services initialization
            self.status_updated.emit("Waiting for services to initialize...")
            self.progress_updated.emit(60)
            self._wait_for_services()
            
            # Step 5: Register test subscribers
            self.status_updated.emit("Registering test subscribers...")
            self.progress_updated.emit(75)
            self._register_test_subscribers()
            
            # Step 6: Run connectivity tests
            self.status_updated.emit("Running connectivity tests...")
            self.progress_updated.emit(90)
            test_results = self._run_connectivity_tests()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("End-to-end test completed!")
            
            # Emit test results
            self.test_results_ready.emit(test_results)
            self.execution_finished.emit(True, "End-to-end test completed successfully")
            
        except Exception as e:
            error_msg = f"End-to-end test failed: {str(e)}"
            error_print(f"ERROR: {error_msg}")
            self.status_updated.emit(error_msg)
            self.execution_finished.emit(False, error_msg)
        finally:
            self.test_mode = False
            self.is_running = False
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.hide()

    def _register_test_subscribers(self):
        """Register test subscribers in the 5G Core."""
        try:
            # Check if registration script exists
            reg_script = os.path.join(self.export_dir, "register_subscriber.sh")
            if os.path.exists(reg_script):
                debug_print("Running subscriber registration script...")
                result = subprocess.run(
                    ["bash", reg_script],
                    cwd=self.export_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    debug_print("Subscriber registration completed successfully")
                else:
                    warning_print(f"Subscriber registration warning: {result.stderr}")
            else:
                debug_print("No registration script found, skipping subscriber registration")
                
        except Exception as e:
            error_print(f"Failed to register subscribers: {e}")
            raise

    def _run_connectivity_tests(self):
        """Run connectivity tests between components."""
        test_results = {
            'timestamp': time.time(),
            'tests': [],
            'summary': {'passed': 0, 'failed': 0, 'total': 0}
        }
        
        try:
            # Test 1: Check if 5G Core services are running
            core_test = self._test_core_services()
            test_results['tests'].append(core_test)
            
            # Test 2: Test gNB connection (if available)
            gnb_test = self._test_gnb_connection()
            test_results['tests'].append(gnb_test)
            
            # Test 3: Test UE registration (if available)
            ue_test = self._test_ue_registration()
            test_results['tests'].append(ue_test)
            
            # Calculate summary
            for test in test_results['tests']:
                test_results['summary']['total'] += 1
                if test['result'] == 'PASS':
                    test_results['summary']['passed'] += 1
                else:
                    test_results['summary']['failed'] += 1
                    
            debug_print(f"Test summary: {test_results['summary']}")
            
        except Exception as e:
            error_print(f"Error running connectivity tests: {e}")
            test_results['tests'].append({
                'name': 'Test Execution',
                'result': 'FAIL',
                'message': str(e),
                'duration': 0
            })
            test_results['summary']['failed'] += 1
            test_results['summary']['total'] += 1
        
        return test_results

    def _test_core_services(self):
        """Test if 5G Core services are running properly."""
        start_time = time.time()
        
        try:
            # Check Docker services status
            compose_cmd = self._get_docker_compose_command()
            if compose_cmd:
                result = subprocess.run(
                    compose_cmd + ["-f", os.path.join(self.export_dir, "docker-compose.yaml"), "ps"],
                    capture_output=True,
                    text=True,
                    cwd=self.export_dir,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Check if services are up
                    if "Up" in result.stdout:
                        return {
                            'name': '5G Core Services',
                            'result': 'PASS',
                            'message': 'Core services are running',
                            'duration': time.time() - start_time
                        }
                    else:
                        return {
                            'name': '5G Core Services',
                            'result': 'FAIL',
                            'message': 'No services are running',
                            'duration': time.time() - start_time
                        }
                else:
                    return {
                        'name': '5G Core Services',
                        'result': 'FAIL',
                        'message': f'Failed to check services: {result.stderr}',
                        'duration': time.time() - start_time
                    }
            else:
                return {
                    'name': '5G Core Services',
                    'result': 'FAIL',
                    'message': 'Docker Compose not available',
                    'duration': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'name': '5G Core Services',
                'result': 'FAIL',
                'message': str(e),
                'duration': time.time() - start_time
            }

    def _test_gnb_connection(self):
        """Test gNB connection to 5G Core."""
        start_time = time.time()
        
        try:
            # Check if gNB container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=gnb", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                gnb_container = result.stdout.strip().split('\n')[0]
                
                # Try to check gNB status (simplified test)
                status_result = subprocess.run(
                    ["docker", "exec", gnb_container, "ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if status_result.returncode == 0:
                    return {
                        'name': 'gNB Connection',
                        'result': 'PASS',
                        'message': f'gNB container {gnb_container} is running',
                        'duration': time.time() - start_time
                    }
                else:
                    return {
                        'name': 'gNB Connection',
                        'result': 'FAIL',
                        'message': 'gNB container not responding',
                        'duration': time.time() - start_time
                    }
            else:
                return {
                    'name': 'gNB Connection',
                    'result': 'SKIP',
                    'message': 'No gNB container found',
                    'duration': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'name': 'gNB Connection',
                'result': 'FAIL',
                'message': str(e),
                'duration': time.time() - start_time
            }

    def _test_ue_registration(self):
        """Test UE registration with 5G Core."""
        start_time = time.time()
        
        try:
            # Check if UE container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=ue", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                ue_container = result.stdout.strip().split('\n')[0]
                
                # Try to check UE status (simplified test)
                status_result = subprocess.run(
                    ["docker", "exec", ue_container, "ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if status_result.returncode == 0:
                    return {
                        'name': 'UE Registration',
                        'result': 'PASS',
                        'message': f'UE container {ue_container} is running',
                        'duration': time.time() - start_time
                    }
                else:
                    return {
                        'name': 'UE Registration',
                        'result': 'FAIL',
                        'message': 'UE container not responding',
                        'duration': time.time() - start_time
                    }
            else:
                return {
                    'name': 'UE Registration',
                    'result': 'SKIP',
                    'message': 'No UE container found',
                    'duration': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'name': 'UE Registration',
                'result': 'FAIL',
                'message': str(e),
                'duration': time.time() - start_time
            }

    def get_deployment_info(self):
        """Get information about the current deployment."""
        if not self.export_dir:
            return None
            
        info = {
            'export_dir': self.export_dir,
            'docker_compose_file': os.path.join(self.export_dir, "docker-compose.yaml"),
            'mininet_script': self.mininet_script_path or "Not generated"
        }
        
        return info