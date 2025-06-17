import subprocess
import shutil
import sys
import importlib.util

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
            'wireless_tools': PrerequisitesChecker.check_wireless_tools()
        }
        
        all_ok = all(checks.values())
        return all_ok, checks
    
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
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def check_docker_compose():
        """Check if Docker Compose is available."""
        command = PrerequisitesChecker.get_docker_compose_command()
        if command is None:
            return False
        
        try:
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
                return "docker compose"
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
        tools = ["iw", "iwconfig", "wpa_supplicant"]
        for tool in tools:
            if not shutil.which(tool):
                return False
        return True
    
    @staticmethod
    def get_installation_instructions():
        """Get installation instructions for missing prerequisites."""
        all_ok, status = PrerequisitesChecker.check_all_prerequisites()
        instructions = []
        
        if not status["python3"]:
            instructions.append("Install Python 3: sudo apt-get install python3 python3-pip")
        
        if not status["sudo"]:
            instructions.append("Install sudo: apt-get install sudo")
        
        if not status["docker"]:
            instructions.append("Install Docker: sudo apt-get install docker.io")
            instructions.append("Add user to docker group: sudo usermod -aG docker $USER")
        
        if not status["docker_compose"]:
            instructions.append("Install Docker Compose: sudo apt-get install docker-compose")
        
        if not status["mininet"]:
            instructions.append("Install Mininet: sudo apt-get install mininet")
        
        if not status["wireless_tools"]:
            instructions.append("Install wireless tools: sudo apt-get install wireless-tools wpasupplicant iw")
        
        if not status["mininet_wifi"] or not status["containernet"]:
            instructions.append("For Mininet-WiFi and Containernet, use the provided Docker container:")
            instructions.append("cd netflux5g-editor/src/automation/mininet")
            instructions.append("docker build -t mn-wifi:v1 .")
            instructions.append("Or install manually following the README.md instructions")
        
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
        # Mininet-WiFi and Containernet are optional if Docker is available
        critical = ["python3", "sudo"]
        recommended = ["docker", "docker_compose", "mininet", "wireless_tools"]
        
        # Check critical prerequisites
        for prereq in critical:
            if not status[prereq]:
                return False
        
        # Check if we have either native installation or Docker
        has_native = status["mininet_wifi"] and status["containernet"]
        has_docker = status["docker"] and status["docker_compose"]
        
        return has_native or has_docker