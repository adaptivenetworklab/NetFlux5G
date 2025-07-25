"""
Docker utility functions for NetFlux5G Editor
Consolidates common Docker operations used across multiple managers
"""
import os
import subprocess
import time
from PyQt5.QtWidgets import QMessageBox
from utils.debug import debug_print, error_print, warning_print


class DockerUtils:
    """Utility class for common Docker operations."""
    
    @staticmethod
    def check_docker_available(main_window=None, show_error=True):
        """
        Check if Docker is available and running.
        
        Args:
            main_window: Main window instance for showing error dialogs
            show_error: Whether to show error dialog on failure
            
        Returns:
            bool: True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, 'docker --version')
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            if show_error and main_window:
                QMessageBox.critical(
                    main_window,
                    "Docker Not Available",
                    "Docker is not installed or not accessible.\n\n"
                    "Please install Docker and ensure it's running:\n"
                    "https://docs.docker.com/desktop/setup/install/linux/"
                )
            return False
    
    @staticmethod
    def is_container_running(container_name):
        """
        Check if a specific container is currently running.
        
        Args:
            container_name (str): Name of the container to check
            
        Returns:
            bool: True if container is running, False otherwise
        """
        try:
            cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
    
    @staticmethod
    def container_exists(container_name):
        """
        Check if a container exists (running or stopped).
        
        Args:
            container_name (str): Name of the container to check
            
        Returns:
            bool: True if container exists, False otherwise
        """
        try:
            cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return container_name in result.stdout
        except Exception:
            return False
    
    @staticmethod
    def network_exists(network_name):
        """
        Check if a Docker network exists.
        
        Args:
            network_name (str): Name of the network to check
            
        Returns:
            bool: True if network exists, False otherwise
        """
        if not network_name:
            return False
            
        try:
            result = subprocess.run(
                ['docker', 'network', 'ls', '--filter', f'name={network_name}', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return network_name in result.stdout
        except Exception:
            return False
    
    @staticmethod
    def volume_exists(volume_name):
        """
        Check if a Docker volume exists.
        
        Args:
            volume_name (str): Name of the volume to check
            
        Returns:
            bool: True if volume exists, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', 'volume', 'ls', '--filter', f'name={volume_name}', '--format', '{{.Name}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return volume_name in result.stdout
        except Exception:
            return False
    
    @staticmethod
    def stop_container(container_name, timeout=30):
        """
        Stop and remove a Docker container.
        
        Args:
            container_name (str): Name of the container to stop
            timeout (int): Timeout in seconds for the operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if container exists
            if not DockerUtils.container_exists(container_name):
                return True, f"Container {container_name} does not exist"
            
            # Stop the container if running
            if DockerUtils.is_container_running(container_name):
                debug_print(f"Stopping container {container_name}...")
                stop_result = subprocess.run(
                    ['docker', 'stop', container_name],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if stop_result.returncode != 0:
                    return False, f"Failed to stop container: {stop_result.stderr}"
            
            # Remove the container
            debug_print(f"Removing container {container_name}...")
            remove_result = subprocess.run(
                ['docker', 'rm', '-f', container_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if remove_result.returncode != 0:
                return False, f"Failed to remove container: {remove_result.stderr}"
            
            return True, f"Container {container_name} stopped and removed successfully"
            
        except subprocess.TimeoutExpired:
            return False, f"Operation timed out for container {container_name}"
        except Exception as e:
            return False, f"Error stopping container {container_name}: {str(e)}"
    
    @staticmethod
    def get_container_status(container_name):
        """
        Get the status of a container.
        
        Args:
            container_name (str): Name of the container
            
        Returns:
            str: Container status or error message
        """
        try:
            # Check if running
            if DockerUtils.is_container_running(container_name):
                cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return f"Running: {result.stdout.strip()}" if result.stdout.strip() else "Running"
            
            # Check if exists but stopped
            if DockerUtils.container_exists(container_name):
                cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return f"Stopped: {result.stdout.strip()}" if result.stdout.strip() else "Stopped"
            
            return "Container does not exist"
            
        except Exception as e:
            return f"Error checking status: {str(e)}"
    
    @staticmethod
    def wait_for_container_ready(container_name, max_wait_time=60, check_interval=2):
        """
        Wait for a container to be ready and running.
        
        Args:
            container_name (str): Name of the container
            max_wait_time (int): Maximum time to wait in seconds
            check_interval (int): Time between checks in seconds
            
        Returns:
            bool: True if container is ready, False if timeout
        """
        elapsed_time = 0
        while elapsed_time < max_wait_time:
            if DockerUtils.is_container_running(container_name):
                debug_print(f"Container {container_name} is ready after {elapsed_time} seconds")
                return True
            
            time.sleep(check_interval)
            elapsed_time += check_interval
            debug_print(f"Waiting for {container_name} to be ready... ({elapsed_time}s)")
        
        error_print(f"Container {container_name} did not become ready within {max_wait_time} seconds")
        return False
    
    @staticmethod
    def create_network(network_name):
        """
        Create a Docker network if it doesn't exist.
        
        Args:
            network_name (str): Name of the network to create
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if DockerUtils.network_exists(network_name):
                return True, f"Network {network_name} already exists"
            
            result = subprocess.run(
                ['docker', 'network', 'create', '--driver', 'bridge', network_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Network {network_name} created successfully"
            else:
                return False, f"Failed to create network: {result.stderr}"
                
        except Exception as e:
            return False, f"Error creating network {network_name}: {str(e)}"
    
    @staticmethod
    def remove_network(network_name):
        """
        Remove a Docker network.
        
        Args:
            network_name (str): Name of the network to remove
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not DockerUtils.network_exists(network_name):
                return True, f"Network {network_name} does not exist"
            
            result = subprocess.run(
                ['docker', 'network', 'rm', network_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Network {network_name} removed successfully"
            else:
                return False, f"Failed to remove network: {result.stderr}"
                
        except Exception as e:
            return False, f"Error removing network {network_name}: {str(e)}"
    
    @staticmethod
    def image_exists(image_name):
        """
        Check if a Docker image exists locally.
        
        Args:
            image_name (str): Name of the image to check (e.g., 'mongo:latest')
            
        Returns:
            bool: True if image exists locally, False otherwise
        """
        try:
            check_cmd = ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}', image_name]
            result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
            return image_name in result.stdout
        except Exception:
            return False
    
    @staticmethod
    def pull_image(image_name, timeout=300):
        """
        Pull a Docker image from registry.
        
        Args:
            image_name (str): Name of the image to pull
            timeout (int): Timeout in seconds for the pull operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            debug_print(f"Pulling Docker image: {image_name}")
            pull_cmd = ['docker', 'pull', image_name]
            result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                debug_print(f"Successfully pulled image: {image_name}")
                return True, f"Successfully pulled {image_name}"
            else:
                error_print(f"Failed to pull image {image_name}: {result.stderr}")
                return False, f"Failed to pull {image_name}: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while pulling image {image_name}"
            error_print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error pulling image {image_name}: {e}"
            error_print(error_msg)
            return False, error_msg
    
    @staticmethod
    def ensure_image_available(image_name, timeout=300):
        """
        Ensure Docker image is available locally, pull if necessary.
        
        Args:
            image_name (str): Name of the image to ensure is available
            timeout (int): Timeout in seconds for pull operation if needed
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if DockerUtils.image_exists(image_name):
            debug_print(f"Image {image_name} already exists locally")
            return True, f"Image {image_name} is available"
        else:
            debug_print(f"Image {image_name} not found locally, pulling...")
            return DockerUtils.pull_image(image_name, timeout)
    
    @staticmethod
    def build_image(image_name, dockerfile_dir, timeout=600):
        """
        Build a Docker image from a Dockerfile directory.
        
        Args:
            image_name (str): Name for the built image (e.g., 'myimage:latest')
            dockerfile_dir (str): Path to the directory containing the Dockerfile
            timeout (int): Timeout in seconds for the build operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            debug_print(f"Building Docker image: {image_name} from {dockerfile_dir}")
            build_cmd = ['docker', 'build', '-t', image_name, dockerfile_dir]
            result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                debug_print(f"Successfully built image: {image_name}")
                return True, f"Successfully built {image_name}"
            else:
                error_print(f"Failed to build image {image_name}: {result.stderr}")
                return False, f"Failed to build {image_name}: {result.stderr}"
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while building image {image_name}"
            error_print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error building image {image_name}: {e}"
            error_print(error_msg)
            return False, error_msg

    @staticmethod
    def remove_container(container_name, timeout=30):
        """
        Remove a Docker container (force remove, does not stop if running).
        
        Args:
            container_name (str): Name of the container to remove
            timeout (int): Timeout in seconds for the operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not DockerUtils.container_exists(container_name):
                return True, f"Container {container_name} does not exist"
            result = subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True, f"Container {container_name} removed successfully"
            else:
                return False, f"Failed to remove container: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, f"Operation timed out for container {container_name}"
        except Exception as e:
            return False, f"Error removing container {container_name}: {str(e)}"

    @staticmethod
    def remove_volume(volume_name, timeout=30):
        """
        Remove a Docker volume.
        
        Args:
            volume_name (str): Name of the volume to remove
            timeout (int): Timeout in seconds for the operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not DockerUtils.volume_exists(volume_name):
                return True, f"Volume {volume_name} does not exist"
            result = subprocess.run(['docker', 'volume', 'rm', volume_name], capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True, f"Volume {volume_name} removed successfully"
            else:
                return False, f"Failed to remove volume: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, f"Operation timed out for volume {volume_name}"
        except Exception as e:
            return False, f"Error removing volume {volume_name}: {str(e)}"

    @staticmethod
    def start_container(container_name, timeout=30):
        """
        Start a stopped Docker container.
        
        Args:
            container_name (str): Name of the container to start
            timeout (int): Timeout in seconds for the operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not DockerUtils.container_exists(container_name):
                return False, f"Container {container_name} does not exist"
            result = subprocess.run(['docker', 'start', container_name], capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True, f"Container {container_name} started successfully"
            else:
                return False, f"Failed to start container: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, f"Operation timed out for container {container_name}"
        except Exception as e:
            return False, f"Error starting container {container_name}: {str(e)}"

    @staticmethod
    def get_container_ip(container_name):
        """
        Get the IP address of a running container (first network).
        
        Args:
            container_name (str): Name of the container
            
        Returns:
            str: IP address or 'unknown'
        """
        try:
            cmd = ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip() or 'unknown'
            return 'unknown'
        except Exception:
            return 'unknown'
    
    @staticmethod
    def create_volume(volume_name, timeout=30):
        """
        Create a Docker volume if it does not exist.
        
        Args:
            volume_name (str): Name of the volume to create
            timeout (int): Timeout in seconds for the operation
            
        Returns:
            bool: True if volume exists or was created, False otherwise
        """
        try:
            if DockerUtils.volume_exists(volume_name):
                return True
            result = subprocess.run(['docker', 'volume', 'create', volume_name], capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def exec_in_container(container_name, cmd_list, timeout=15):
        """
        Execute a command inside a running container.
        
        Args:
            container_name (str): Name of the container
            cmd_list (list): Command and arguments as list
            timeout (int): Timeout in seconds
            
        Returns:
            dict: { 'returncode': int, 'stdout': str, 'stderr': str }
        """
        try:
            full_cmd = ['docker', 'exec', container_name] + cmd_list
            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': str(e)
            }
        

class DockerContainerBuilder:
    """Helper class for building Docker run commands with consistent patterns."""
    
    def __init__(self, image, container_name):
        self.image = image
        self.container_name = container_name
        self.ports = []
        self.volumes = []
        self.env_vars = []
        self.network = None
        self.extra_args = []
        self.command_args = []  # <-- Add this for arguments after image name
    
    def add_port(self, port_mapping):
        """Add port mapping (e.g., '8080:80')."""
        self.ports.append(port_mapping)
        return self
    
    def add_volume(self, volume_mapping):
        """Add volume mapping (e.g., '/host/path:/container/path')."""
        self.volumes.append(volume_mapping)
        return self
    
    def add_env(self, env_var):
        """Add environment variable (e.g., 'KEY=value')."""
        self.env_vars.append(env_var)
        return self
    
    def set_network(self, network_name):
        """Set the Docker network."""
        self.network = network_name
        return self
    
    def add_extra_arg(self, arg):
        """Add extra Docker run argument."""
        self.extra_args.append(arg)
        return self

    def add_command_arg(self, arg):
        """Add command arguments after image name."""
        self.command_args.append(arg)
        return self
    
    def build_command(self):
        """Build the complete Docker run command."""
        cmd = [
            'docker', 'run', '-d',
            '--name', self.container_name,
            '--restart', 'unless-stopped'
        ]
        
        # Add network
        if self.network:
            cmd.extend(['--network', self.network])
        
        # Add port mappings
        for port in self.ports:
            cmd.extend(['-p', port])
        
        # Add volume mappings
        for volume in self.volumes:
            cmd.extend(['-v', volume])
        
        # Add environment variables
        for env_var in self.env_vars:
            cmd.extend(['-e', env_var])
        
        # Add extra arguments
        cmd.extend(self.extra_args)
        
        # Add image
        cmd.append(self.image)
        
        # Add command arguments
        cmd.extend(self.command_args)
        
        return cmd
    
    def run(self, timeout=60):
        """
        Execute the Docker run command.
        
        Args:
            timeout (int): Timeout for the operation
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            cmd = self.build_command()
            debug_print(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                debug_print(f"Container {self.container_name} started successfully")
                return True, f"Container {self.container_name} started successfully"
            else:
                error_print(f"Failed to start container: {result.stderr}")
                return False, f"Failed to start container: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, f"Container start operation timed out"
        except Exception as e:
            return False, f"Error starting container: {str(e)}"
