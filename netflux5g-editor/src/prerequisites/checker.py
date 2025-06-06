import subprocess
import shutil
from manager.debug import debug_print, error_print, warning_print

class PrerequisitesChecker:
    """Check if all required tools are installed and accessible."""
    
    @staticmethod
    def check_all_prerequisites():
        """Check all prerequisites and return a report."""
        checks = {
            'docker': PrerequisitesChecker.check_docker(),
            'docker_compose': PrerequisitesChecker.check_docker_compose(),
            'mininet': PrerequisitesChecker.check_mininet(),
            'python3': PrerequisitesChecker.check_python3(),
            'sudo': PrerequisitesChecker.check_sudo()
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
        # Check for docker-compose command
        if shutil.which("docker-compose"):
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Check for docker compose (newer syntax)
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
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
    def get_installation_instructions():
        """Get installation instructions for missing prerequisites."""
        return {
            'docker': """
Install Docker:
Ubuntu/Debian: sudo apt-get install docker.io
CentOS/RHEL: sudo yum install docker
Or visit: https://docs.docker.com/get-docker/
""",
            'docker_compose': """
Install Docker Compose:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
Or visit: https://docs.docker.com/compose/install/
""",
            'mininet': """
Install Mininet:
Ubuntu/Debian: sudo apt-get install mininet
Or visit: http://mininet.org/download/
""",
            'python3': """
Install Python 3:
Ubuntu/Debian: sudo apt-get install python3
CentOS/RHEL: sudo yum install python3
""",
            'sudo': """
sudo should be available on most Linux systems.
If not available, run as root or install sudo package.
"""
        }