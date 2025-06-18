import os
import subprocess
import tempfile
import time
from PyQt5.QtWidgets import QMessageBox
from manager.debug import debug_print, error_print

class ComponentUtils:
    """Utility class for handling component operations like terminals, logs, etc."""
    
    @staticmethod
    def open_terminal_for_component(main_window, component_id):
        """Open a terminal for the specified component."""
        try:
            nodes, _ = main_window.file_manager.extractTopology()
            
            # Find the component by ID
            component = None
            for node in nodes:
                if node.get('component_id') == component_id:
                    component = node
                    break
                    
            if not component:
                QMessageBox.warning(main_window, "Component Not Found", 
                                    f"Component with ID {component_id} not found in the topology.")
                return
            
            # Check if we have a running environment
            if not main_window.automation_runner.is_running:
                QMessageBox.information(main_window, "Environment Not Running", 
                                       "Please start the topology using 'Run All' before opening a terminal.")
                return
            
            # Get component name and type
            component_name = component.get('properties', {}).get('name', f"Component {component_id}")
            component_type = component.get('type', 'Unknown')
            sanitized_name = component_name.lower().replace(' ', '_')
            
            # Check container name based on component type and name
            container_name = None
            if component_type == 'UE':
                container_name = f"ue_{sanitized_name}"
            elif component_type == 'GNB':
                container_name = f"gnb_{sanitized_name}"
            elif component_type == 'VGcore':
                core_type = component.get('properties', {}).get('Component5G_Type', 'amf')
                container_name = f"{core_type.lower()}_{sanitized_name}"
            else:
                container_name = sanitized_name
                
            # Try to find the matching container
            result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                  capture_output=True, text=True)
            
            container_list = result.stdout.strip().split('\n')
            if not container_list or not container_list[0]:
                # Try with netflux5g_deploy prefix
                export_dir = main_window.automation_runner.export_dir
                if export_dir:
                    dir_name = os.path.basename(export_dir)
                    container_name = f"{dir_name}_{sanitized_name}_1"
                    result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                          capture_output=True, text=True)
                    container_list = result.stdout.strip().split('\n')
            
            if not container_list or not container_list[0]:
                QMessageBox.warning(main_window, "Container Not Found", 
                                   f"Could not find a running container for {component_name}. Make sure the topology is running.")
                return
                
            # Use the first matching container
            container_name = container_list[0]
            
            # Create terminal script
            fd, temp_script = tempfile.mkstemp(suffix='.sh')
            with os.fdopen(fd, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"echo 'Opening terminal for {component_name} ({container_name})...'\n")
                f.write(f"docker exec -it {container_name} /bin/bash\n")
                f.write("echo 'Terminal session ended. Press Enter to close...'\n")
                f.write("read\n")
            
            os.chmod(temp_script, 0o755)
            
            # Try to open terminal window
            terminal_commands = [
                ["gnome-terminal", "--", "bash", temp_script],
                ["xterm", "-e", f"bash {temp_script}"],
                ["konsole", "-e", f"bash {temp_script}"],
                ["lxterminal", "-e", f"bash {temp_script}"]
            ]
            
            launched = False
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd)
                    launched = True
                    break
                except FileNotFoundError:
                    continue
                    
            if not launched:
                QMessageBox.warning(main_window, "Terminal Not Available", 
                                   "Could not find a suitable terminal emulator. Please install xterm, gnome-terminal, konsole, or lxterminal.")
                
            debug_print(f"Opened terminal for component {component_name} ({container_name})")
                
        except Exception as e:
            error_print(f"Error opening terminal: {e}")
            QMessageBox.critical(main_window, "Error", f"Failed to open terminal: {str(e)}")
    
    @staticmethod
    def view_logs_for_component(main_window, component_id):
        """View logs for the specified component."""
        try:
            nodes, _ = main_window.file_manager.extractTopology()
            
            # Find the component by ID
            component = None
            for node in nodes:
                if node.get('component_id') == component_id:
                    component = node
                    break
                    
            if not component:
                QMessageBox.warning(main_window, "Component Not Found", 
                                    f"Component with ID {component_id} not found in the topology.")
                return
            
            # Check if we have a running environment
            if not main_window.automation_runner.is_running:
                QMessageBox.information(main_window, "Environment Not Running", 
                                       "Please start the topology using 'Run All' before viewing logs.")
                return
            
            # Get component name and type
            component_name = component.get('properties', {}).get('name', f"Component {component_id}")
            component_type = component.get('type', 'Unknown')
            sanitized_name = component_name.lower().replace(' ', '_')
            
            # Check container name based on component type and name
            container_name = None
            if component_type == 'UE':
                container_name = f"ue_{sanitized_name}"
            elif component_type == 'GNB':
                container_name = f"gnb_{sanitized_name}"
            elif component_type == 'VGcore':
                core_type = component.get('properties', {}).get('Component5G_Type', 'amf')
                container_name = f"{core_type.lower()}_{sanitized_name}"
            else:
                container_name = sanitized_name
                
            # Try to find the matching container
            result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                  capture_output=True, text=True)
            
            container_list = result.stdout.strip().split('\n')
            if not container_list or not container_list[0]:
                # Try with netflux5g_deploy prefix
                export_dir = main_window.automation_runner.export_dir
                if export_dir:
                    dir_name = os.path.basename(export_dir)
                    container_name = f"{dir_name}_{sanitized_name}_1"
                    result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                          capture_output=True, text=True)
                    container_list = result.stdout.strip().split('\n')
            
            if not container_list or not container_list[0]:
                QMessageBox.warning(main_window, "Container Not Found", 
                                   f"Could not find a running container for {component_name}. Make sure the topology is running.")
                return
                
            # Use the first matching container
            container_name = container_list[0]
            
            # Create log viewing script
            fd, temp_script = tempfile.mkstemp(suffix='.sh')
            with os.fdopen(fd, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"echo 'Viewing logs for {component_name} ({container_name})...'\n")
                
                # Determine appropriate log command based on component type
                if component_type == 'VGcore':
                    core_type = component.get('properties', {}).get('Component5G_Type', '').lower()
                    f.write(f"docker exec {container_name} tail -f /opt/open5gs/var/log/open5gs/{core_type}.log 2>/dev/null || \\\n")
                    f.write(f"docker exec {container_name} journalctl -u open5gs-{core_type}d -f || \\\n")
                    f.write(f"docker logs -f {container_name}\n")
                elif component_type == 'GNB' or component_type == 'UE':
                    f.write(f"docker logs -f {container_name}\n")
                else:
                    f.write(f"docker logs -f {container_name}\n")
                    
                f.write("echo 'Log session ended. Press Enter to close...'\n")
                f.write("read\n")
            
            os.chmod(temp_script, 0o755)
            
            # Try to open terminal window with logs
            terminal_commands = [
                ["gnome-terminal", "--", "bash", temp_script],
                ["xterm", "-e", f"bash {temp_script}"],
                ["konsole", "-e", f"bash {temp_script}"],
                ["lxterminal", "-e", f"bash {temp_script}"]
            ]
            
            launched = False
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd)
                    launched = True
                    break
                except FileNotFoundError:
                    continue
                    
            if not launched:
                QMessageBox.warning(main_window, "Terminal Not Available", 
                                   "Could not find a suitable terminal emulator. Please install xterm, gnome-terminal, konsole, or lxterminal.")
                
            debug_print(f"Viewing logs for component {component_name} ({container_name})")
                
        except Exception as e:
            error_print(f"Error viewing logs: {e}")
            QMessageBox.critical(main_window, "Error", f"Failed to view logs: {str(e)}")
    
    @staticmethod
    def restart_component(main_window, component_id):
        """Restart the specified component."""
        try:
            nodes, _ = main_window.file_manager.extractTopology()
            
            # Find the component by ID
            component = None
            for node in nodes:
                if node.get('component_id') == component_id:
                    component = node
                    break
                    
            if not component:
                QMessageBox.warning(main_window, "Component Not Found", 
                                    f"Component with ID {component_id} not found in the topology.")
                return
            
            # Check if we have a running environment
            if not main_window.automation_runner.is_running:
                QMessageBox.information(main_window, "Environment Not Running", 
                                       "Please start the topology using 'Run All' before restarting components.")
                return
            
            # Get component name and type
            component_name = component.get('properties', {}).get('name', f"Component {component_id}")
            component_type = component.get('type', 'Unknown')
            sanitized_name = component_name.lower().replace(' ', '_')
            
            # Check container name based on component type and name
            container_name = None
            if component_type == 'UE':
                container_name = f"ue_{sanitized_name}"
            elif component_type == 'GNB':
                container_name = f"gnb_{sanitized_name}"
            elif component_type == 'VGcore':
                core_type = component.get('properties', {}).get('Component5G_Type', 'amf')
                container_name = f"{core_type.lower()}_{sanitized_name}"
            else:
                container_name = sanitized_name
                
            # Try to find the matching container
            result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                  capture_output=True, text=True)
            
            container_list = result.stdout.strip().split('\n')
            if not container_list or not container_list[0]:
                # Try with netflux5g_deploy prefix
                export_dir = main_window.automation_runner.export_dir
                if export_dir:
                    dir_name = os.path.basename(export_dir)
                    container_name = f"{dir_name}_{sanitized_name}_1"
                    result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                                          capture_output=True, text=True)
                    container_list = result.stdout.strip().split('\n')
            
            if not container_list or not container_list[0]:
                QMessageBox.warning(main_window, "Container Not Found", 
                                   f"Could not find a running container for {component_name}. Make sure the topology is running.")
                return
                
            # Use the first matching container
            container_name = container_list[0]
            
            # Restart the container
            restart_cmd = ["docker", "restart", container_name]
            result = subprocess.run(restart_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                QMessageBox.information(main_window, "Component Restarted", 
                                       f"Component {component_name} ({container_name}) has been restarted successfully.")
            else:
                QMessageBox.warning(main_window, "Restart Failed", 
                                   f"Failed to restart {component_name} ({container_name}): {result.stderr}")
            
            debug_print(f"Restarted component {component_name} ({container_name})")
                
        except Exception as e:
            error_print(f"Error restarting component: {e}")
            QMessageBox.critical(main_window, "Error", f"Failed to restart component: {str(e)}")
