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
    def check_mininet():
        """Check if Mininet is available."""
        try:
            result = subprocess.run(
                ["sudo", "mn", "--version"], 
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
Please visit: https://docs.docker.com/desktop/setup/install/linux/
""",
            'mininet': """
Install Mininet-Wifi:
Please visit: https://github.com/intrig-unicamp/mininet-wifi
""",
            'python3': """
Install Python 3:
Ubuntu/Debian: sudo apt-get install python3
""",
            'sudo': """
sudo should be available on most Linux systems.
If not available, run as root or install sudo package.

When using container, ensure using a user with sudo privileges or execute as root user.
"""
        }