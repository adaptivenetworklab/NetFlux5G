import subprocess
import shutil
import sys
import importlib.util
import os

class PrerequisitesChecker:
    """Check if all required tools are installed and accessible."""
    
    @staticmethod
    def check_all_prerequisites():
        """Check all prerequisites and return a tuple (all_ok, checks)."""
        checks = {
            'docker': PrerequisitesChecker.check_docker(),
            'docker_compose': PrerequisitesChecker.check_docker_compose(),
            'mininet': PrerequisitesChecker.check_mininet(),
            'mininet_wifi': PrerequisitesChecker.check_mininet_wifi(),
            'containernet': PrerequisitesChecker.check_containernet(),
            'python3': PrerequisitesChecker.check_python3(),
            'sudo': PrerequisitesChecker.check_sudo(),
            'wireless_tools': PrerequisitesChecker.check_wireless_tools(),
            'kernel_modules': PrerequisitesChecker.check_kernel_modules(),
            'x11': PrerequisitesChecker.check_x11()
        }
        
        all_ok = all(checks.values())
        return all_ok, checks
    
    @staticmethod
    def check_critical_prerequisites():
        """Check only critical prerequisites needed for basic operation."""
        checks = {
            'python3': PrerequisitesChecker.check_python3(),
            'docker': PrerequisitesChecker.check_docker(),
            'docker_compose': PrerequisitesChecker.check_docker_compose(),
        }
        return all(checks.values()), checks
    
    @staticmethod
    def check_docker():
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                # Also check if Docker daemon is running
                daemon_check = subprocess.run(
                    ["docker", "info"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                return daemon_check.returncode == 0
            return False
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def check_docker_compose():
        """Check if Docker Compose is available."""
        command = PrerequisitesChecker.get_docker_compose_command()
        if command is None:
            return False
        
        try:
            if isinstance(command, list):
                result = subprocess.run(
                    command + ["--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
            else:
                result = subprocess.run(
                    [command, "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def get_docker_compose_command():
        """Get the appropriate docker-compose command."""
        # Check for docker-compose (older version)
        if shutil.which("docker-compose"):
            return "docker-compose"
        
        # Check for docker compose (newer syntax)
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                return ["docker", "compose"]
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return None

    @staticmethod
    def check_mininet():
        """Check if Mininet is available."""
        try:
            result = subprocess.run(
                ["mn", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def check_mininet_wifi():
        """Check if Mininet-WiFi Python modules are available."""
        try:
            import mn_wifi.net
            import mn_wifi.node
            import mn_wifi.link
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_containernet():
        """Check if Containernet Python modules are available."""
        try:
            import containernet.cli
            import containernet.node
            return True
        except ImportError:
            return False
    
    @staticmethod
    def check_python3():
        """Check if Python 3 is available."""
        try:
            result = subprocess.run(
                ["python3", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def check_sudo():
        """Check if sudo is available."""
        return shutil.which("sudo") is not None
    
    @staticmethod
    def check_wireless_tools():
        """Check if wireless tools are available."""
        tools = ["iw", "iwconfig"]
        for tool in tools:
            if shutil.which(tool):
                return True
        return False
    
    @staticmethod
    def check_kernel_modules():
        """Check if required kernel modules are available."""
        try:
            # Check if mac80211_hwsim module is loaded or available
            result = subprocess.run(
                ["lsmod"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0 and "mac80211_hwsim" in result.stdout:
                return True
            
            # Check if module file exists
            if os.path.exists("/lib/modules/" + os.uname().release + "/kernel/drivers/net/wireless/mac80211_hwsim.ko"):
                return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def check_x11():
        """Check if X11 is available for GUI applications."""
        return os.environ.get('DISPLAY') is not None
    
    @staticmethod
    def get_installation_instructions():
        """Get installation instructions for missing prerequisites."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        instructions = []
        
        if not status["python3"]:
            instructions.append("# Install Python 3:")
            instructions.append("sudo apt-get update")
            instructions.append("sudo apt-get install -y python3 python3-pip python3-venv python3-tk")
        
        if not status["sudo"]:
            instructions.append("# Install sudo:")
            instructions.append("apt-get install sudo")
        
        if not status["docker"]:
            instructions.append("# Install Docker:")
            instructions.append("sudo apt-get install -y docker.io")
            instructions.append("sudo systemctl start docker")
            instructions.append("sudo systemctl enable docker")
            instructions.append("sudo usermod -aG docker $USER")
            instructions.append("# Note: You need to logout and login again after adding user to docker group")
        
        if not status["docker_compose"]:
            instructions.append("# Install Docker Compose:")
            instructions.append("sudo apt-get install -y docker-compose")
            instructions.append("# Or for newer systems:")
            instructions.append("sudo apt-get install -y docker-compose-plugin")
        
        if not status["wireless_tools"]:
            instructions.append("# Install wireless tools:")
            instructions.append("sudo apt-get install -y wireless-tools wpasupplicant iw rfkill")
        
        if not status["kernel_modules"]:
            instructions.append("# Load wireless simulation kernel module:")
            instructions.append("sudo modprobe mac80211_hwsim radios=10")
            instructions.append("# To make it persistent:")
            instructions.append("echo 'mac80211_hwsim' | sudo tee -a /etc/modules")
        
        if not status["x11"]:
            instructions.append("# For GUI applications in Docker containers:")
            instructions.append("xhost +local:root")
        
        if not status["mininet"]:
            instructions.append("# Install Mininet (optional):")
            instructions.append("sudo apt-get install -y mininet python3-mininet")
        
        if not status["mininet_wifi"] or not status["containernet"]:
            instructions.append("# For Mininet-WiFi and Containernet, use Docker (recommended):")
            instructions.append("cd netflux5g-editor/src/automation/mininet")
            instructions.append("docker build -t mn-wifi:v1 .")
            instructions.append("")
            instructions.append("# Or install natively (advanced):")
            instructions.append("# Mininet-WiFi: https://github.com/intrig-unicamp/mininet-wifi")
            instructions.append("# Containernet: https://github.com/containernet/containernet")
        
        return instructions
    
    @staticmethod
    def get_missing_prerequisites():
        """Get a list of missing prerequisites."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        missing = []
        
        for prereq, available in status.items():
            if not available:
                missing.append(prereq.replace("_", "-"))
        
        return missing
    
    @staticmethod
    def is_system_ready():
        """Check if the system has all required prerequisites."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        
        # Critical prerequisites that must be available
        critical = ["python3", "docker"]
        
        # Check critical prerequisites
        for prereq in critical:
            if not status.get(prereq, False):
                return False
        
        return True
    
    @staticmethod
    def is_docker_ready():
        """Check if Docker-based functionality is ready."""
        critical_ok, critical_status = PrerequisitesChecker.check_critical_prerequisites()
        return critical_ok
    
    @staticmethod
    def is_mininet_ready():
        """Check if Mininet functionality is ready."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        
        # Either native Mininet or Docker-based Mininet
        has_native = status["mininet"] and status["mininet_wifi"] and status["containernet"]
        has_docker = status["docker"] and status["docker_compose"]
        
        return has_native or has_docker
    
    @staticmethod
    def get_recommendation():
        """Get recommendation for what the user can do with current setup."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        
        if PrerequisitesChecker.is_mininet_ready():
            return "FULL", "All features available - you can run complete end-to-end tests"
        elif PrerequisitesChecker.is_docker_ready():
            return "DOCKER", "Docker-based 5G simulation available - network simulation limited"
        elif status["python3"]:
            return "DESIGN", "GUI design mode only - no simulation capabilities"
        else:
            return "NONE", "Please install basic prerequisites to use NetFlux5G"
    
    @staticmethod
    def print_status_report():
        """Print a comprehensive status report."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        level, message = PrerequisitesChecker.get_recommendation()
        
        print("=" * 60)
        print("NetFlux5G Prerequisites Status Report")
        print("=" * 60)
        
        print(f"\nOverall Status: {message}")
        print(f"Capability Level: {level}")
        
        print("\nDetailed Status:")
        for prereq, available in status.items():
            status_icon = "✓" if available else "✗"
            print(f"  {status_icon} {prereq.replace('_', ' ').title()}")
        
        if not all_ok:
            print("\nInstallation Instructions:")
            instructions = PrerequisitesChecker.get_installation_instructions()
            for instruction in instructions:
                print(instruction)
        
        print("\n" + "=" * 60)