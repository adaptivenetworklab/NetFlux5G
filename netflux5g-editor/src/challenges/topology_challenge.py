"""
Topology Challenge System for NetFlux5G Editor

This module provides a learning system where users complete topology configuration
challenges and receive real-time progress feedback based on component status and
connections. The system integrates with the deployment monitor to track successful
connections and configurations.

Features:
- Predefined challenges with specific objectives
- Real-time progress tracking based on deployment status
- Component configuration validation
- Connection status monitoring
- Success/failure feedback
- Challenge completion scoring
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QProgressBar, QFrame, QScrollArea,
                           QMessageBox, QDialog, QTextEdit, QComboBox,
                           QSpinBox, QCheckBox, QGroupBox, QGridLayout,
                           QLineEdit, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor, QPalette
from utils.debug import debug_print, error_print, warning_print
from utils.docker_utils import DockerUtils
from manager.deployment_monitor import ComponentStatusWorker

@dataclass
class ChallengeObjective:
    """Represents a single objective within a challenge."""
    id: str
    description: str
    component_type: str
    component_name: Optional[str] = None
    config_requirements: Dict[str, Any] = None
    connection_requirements: List[str] = None
    weight: float = 1.0  # Weight for scoring
    completed: bool = False

@dataclass
class TopologyChallenge:
    """Represents a complete topology challenge."""
    id: str
    name: str
    description: str
    difficulty: str  # "beginner", "intermediate", "advanced"
    topology_file: str
    objectives: List[ChallengeObjective]
    total_score: int = 100
    time_limit: Optional[int] = None  # seconds
    hints: List[str] = None

class ChallengeProgressTracker(QThread):
    """Background thread to track challenge progress."""
    
    progress_updated = pyqtSignal(dict)  # {objective_id: progress_data}
    challenge_completed = pyqtSignal(bool, int)  # success, score
    
    def __init__(self, challenge: TopologyChallenge, main_window):
        super().__init__()
        self.challenge = challenge
        self.main_window = main_window
        self.running = True
        self.deployed_components = {}
        self.objective_status = {}
        
        # Initialize objective status
        for obj in self.challenge.objectives:
            self.objective_status[obj.id] = {
                'completed': False,
                'progress': 0.0,
                'details': 'Not started'
            }
    
    def stop(self):
        """Stop the tracking thread."""
        self.running = False
    
    def run(self):
        """Main tracking loop."""
        while self.running:
            try:
                # Get deployed components status
                self._update_deployed_components()
                
                # Check each objective
                total_progress = 0.0
                completed_objectives = 0
                
                for objective in self.challenge.objectives:
                    progress = self._check_objective_progress(objective)
                    self.objective_status[objective.id] = progress
                    
                    if progress['completed']:
                        completed_objectives += 1
                    
                    total_progress += progress['progress'] * objective.weight
                
                # Emit progress update
                self.progress_updated.emit(self.objective_status.copy())
                
                # Check if challenge is completed
                if completed_objectives == len(self.challenge.objectives):
                    score = int(total_progress / len(self.challenge.objectives))
                    self.challenge_completed.emit(True, score)
                    break
                
                # Wait before next check
                for _ in range(20):  # 2 seconds
                    if not self.running:
                        break
                    self.msleep(100)
                    
            except Exception as e:
                error_print(f"Error in challenge tracking: {e}")
                self.msleep(1000)
    
    def _update_deployed_components(self):
        """Update the status of deployed components."""
        try:
            # Get all deployed components similar to deployment monitor
            from gui.widgets.LogViewer import DeployedComponentsExtractor
            self.deployed_components = DeployedComponentsExtractor.extractDeployedComponents()
        except Exception as e:
            debug_print(f"Failed to get deployed components: {e}")
            self.deployed_components = {}
    
    def _check_objective_progress(self, objective: ChallengeObjective) -> Dict[str, Any]:
        """Check progress for a specific objective."""
        progress_data = {
            'completed': False,
            'progress': 0.0,
            'details': 'Checking...'
        }
        
        try:
            # Get components from the current topology
            topology_components = self._get_topology_components()
            
            # Find matching component(s)
            matching_components = []
            for comp in topology_components:
                if comp['type'] == objective.component_type:
                    if objective.component_name is None or comp['name'] == objective.component_name:
                        matching_components.append(comp)
            
            if not matching_components:
                progress_data['details'] = f"No {objective.component_type} components found in topology"
                return progress_data
            
            # Check each matching component
            total_progress = 0.0
            for comp in matching_components:
                comp_progress = self._check_component_objective(comp, objective)
                total_progress += comp_progress
            
            # Average progress across components
            if matching_components:
                avg_progress = total_progress / len(matching_components)
                progress_data['progress'] = avg_progress
                progress_data['completed'] = avg_progress >= 95.0  # 95% threshold for completion
                
                if progress_data['completed']:
                    progress_data['details'] = f"✅ {objective.description}"
                elif avg_progress > 0:
                    progress_data['details'] = f"🔄 {objective.description} ({avg_progress:.1f}%)"
                else:
                    progress_data['details'] = f"❌ {objective.description}"
            
        except Exception as e:
            error_print(f"Error checking objective {objective.id}: {e}")
            progress_data['details'] = f"Error: {str(e)}"
        
        return progress_data
    
    def _get_topology_components(self) -> List[Dict[str, Any]]:
        """Get all components from the current topology."""
        components = []
        
        try:
            if (hasattr(self.main_window, 'canvas_view') and 
                hasattr(self.main_window.canvas_view, 'scene')):
                
                from gui.components import NetworkComponent
                for item in self.main_window.canvas_view.scene.items():
                    if isinstance(item, NetworkComponent):
                        components.append({
                            'name': item.display_name,
                            'type': item.component_type,
                            'properties': item.getProperties(),
                            'component': item
                        })
        except Exception as e:
            error_print(f"Failed to get topology components: {e}")
        
        return components
    
    def _check_component_objective(self, component: Dict[str, Any], objective: ChallengeObjective) -> float:
        """Check progress for a specific component against an objective."""
        progress = 0.0
        
        try:
            # Check configuration requirements
            if objective.config_requirements:
                config_progress = self._check_config_requirements(component, objective.config_requirements)
                progress += config_progress * 0.6  # 60% for config
            else:
                progress += 60.0  # If no config requirements, give full config score
            
            # Check connection/deployment status
            if objective.connection_requirements:
                connection_progress = self._check_connection_requirements(component, objective.connection_requirements)
                progress += connection_progress * 0.4  # 40% for connections
            else:
                # Check basic deployment status
                deployment_progress = self._check_deployment_status(component)
                progress += deployment_progress * 0.4
                
        except Exception as e:
            error_print(f"Error checking component objective: {e}")
        
        return min(100.0, progress)
    
    def _check_config_requirements(self, component: Dict[str, Any], requirements: Dict[str, Any]) -> float:
        """Check if component configuration meets requirements."""
        if not requirements:
            return 100.0
        
        total_requirements = len(requirements)
        met_requirements = 0
        
        component_props = component.get('properties', {})
        
        for key, expected_value in requirements.items():
            actual_value = component_props.get(key)
            
            if actual_value is not None:
                # Handle different value types
                if isinstance(expected_value, str):
                    if str(actual_value).lower() == expected_value.lower():
                        met_requirements += 1
                elif isinstance(expected_value, (int, float)):
                    if abs(float(actual_value) - float(expected_value)) < 0.001:
                        met_requirements += 1
                elif isinstance(expected_value, bool):
                    if bool(actual_value) == expected_value:
                        met_requirements += 1
                elif actual_value == expected_value:
                    met_requirements += 1
        
        return (met_requirements / total_requirements) * 100.0
    
    def _check_connection_requirements(self, component: Dict[str, Any], requirements: List[str]) -> float:
        """Check if component meets connection requirements."""
        if not requirements:
            return 100.0
        
        # Get container name for this component
        container_name = self._get_component_container_name(component)
        if not container_name:
            return 0.0
        
        # Check if container is running and connected
        if not DockerUtils.container_exists(container_name):
            return 0.0
        
        if not DockerUtils.is_container_running(container_name):
            return 20.0  # Container exists but not running
        
        # Check specific connection requirements
        connection_score = 40.0  # Base score for running container
        
        try:
            # Use the same logic as deployment monitor
            component_type = component['type']
            
            if component_type in ['AMF', 'SMF', 'UPF', 'NRF', 'UDR', 'UDM', 'AUSF', 'PCF', 'NSSF', 'BSF', 'SCP']:
                connection_score += self._check_5g_core_connections(container_name, component_type)
            elif component_type == 'GNB':
                connection_score += self._check_gnb_connections(container_name)
            elif component_type == 'UE':
                connection_score += self._check_ue_connections(container_name)
            else:
                connection_score += 60.0  # Full score for other components if running
                
        except Exception as e:
            debug_print(f"Error checking connections for {container_name}: {e}")
        
        return min(100.0, connection_score)
    
    def _check_deployment_status(self, component: Dict[str, Any]) -> float:
        """Check basic deployment status of a component."""
        container_name = self._get_component_container_name(component)
        if not container_name:
            return 0.0
        
        if not DockerUtils.container_exists(container_name):
            return 0.0
        
        if DockerUtils.is_container_running(container_name):
            return 100.0
        else:
            return 50.0  # Container exists but not running
    
    def _get_component_container_name(self, component: Dict[str, Any]) -> Optional[str]:
        """Get the container name for a component."""
        try:
            # Use the same logic as NetworkComponent._getContainerName()
            comp_obj = component.get('component')
            if comp_obj and hasattr(comp_obj, '_getContainerName'):
                return comp_obj._getContainerName()
            
            # Fallback logic
            name = component['name'].lower().replace(' ', '').replace('#', '')
            return f"mn.{name}"
        except Exception:
            return None
    
    def _check_5g_core_connections(self, container_name: str, component_type: str) -> float:
        """Check 5G core component connections."""
        # Simplified connection check - look for common success patterns in logs
        try:
            import subprocess
            cmd = ['docker', 'exec', container_name, 'tail', '-50', f'/logging/{container_name.replace("mn.", "")}.log']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                log_content = result.stdout.lower()
                
                # Look for successful connection patterns
                success_patterns = [
                    'registration complete',
                    'connection established',
                    'successfully registered',
                    'service started',
                    'ready to serve'
                ]
                
                for pattern in success_patterns:
                    if pattern in log_content:
                        return 60.0
                
                return 30.0  # Running but no clear connection success
            
            return 10.0
        except Exception:
            return 0.0
    
    def _check_gnb_connections(self, container_name: str) -> float:
        """Check gNB connections."""
        try:
            import subprocess
            cmd = ['docker', 'exec', container_name, 'tail', '-50', f'/logging/{container_name.replace("mn.", "")}.log']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                log_content = result.stdout.lower()
                
                # Look for gNB connection patterns
                if 'ng setup response' in log_content or 'connected to amf' in log_content:
                    return 60.0
                elif 'connecting' in log_content:
                    return 30.0
                
            return 10.0
        except Exception:
            return 0.0
    
    def _check_ue_connections(self, container_name: str) -> float:
        """Check UE connections."""
        try:
            import subprocess
            cmd = ['docker', 'exec', container_name, 'tail', '-50', f'/logging/{container_name.replace("mn.", "")}.log']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                log_content = result.stdout.lower()
                
                # Look for UE connection patterns
                if 'pdu session establishment accept' in log_content or 'registration complete' in log_content:
                    return 60.0
                elif 'registering' in log_content or 'connecting' in log_content:
                    return 30.0
                
            return 10.0
        except Exception:
            return 0.0

class ChallengeWidget(QFrame):
    """Widget displaying a single challenge with progress tracking."""
    
    challenge_started = pyqtSignal(str)  # challenge_id
    challenge_stopped = pyqtSignal(str)  # challenge_id
    
    def __init__(self, challenge: TopologyChallenge, main_window, parent=None):
        super().__init__(parent)
        self.challenge = challenge
        self.main_window = main_window
        self.progress_tracker = None
        self.is_active = False
        
        self.setupUI()
        
    def setupUI(self):
        """Setup the challenge widget UI."""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        
        # Header with challenge info
        header_layout = QHBoxLayout()
        
        # Challenge name and difficulty
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.challenge.name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(name_label)
        
        difficulty_label = QLabel(f"Difficulty: {self.challenge.difficulty.title()}")
        difficulty_color = {
            'beginner': 'green',
            'intermediate': 'orange', 
            'advanced': 'red'
        }
        difficulty_label.setStyleSheet(f"color: {difficulty_color.get(self.challenge.difficulty, 'black')};")
        info_layout.addWidget(difficulty_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        # Control buttons
        self.start_button = QPushButton("Start Challenge")
        self.start_button.clicked.connect(self.start_challenge)
        header_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_challenge)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(self.challenge.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; margin: 5px 0px;")
        layout.addWidget(desc_label)
        
        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setTextVisible(True)
        self.overall_progress.setFormat("Overall Progress: %p%")
        layout.addWidget(self.overall_progress)
        
        # Objectives list
        objectives_label = QLabel("Objectives:")
        objectives_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(objectives_label)
        
        # Scrollable objectives area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        objectives_widget = QWidget()
        self.objectives_layout = QVBoxLayout(objectives_widget)
        
        # Create objective widgets
        self.objective_widgets = {}
        for objective in self.challenge.objectives:
            obj_widget = self.create_objective_widget(objective)
            self.objective_widgets[objective.id] = obj_widget
            self.objectives_layout.addWidget(obj_widget)
        
        scroll_area.setWidget(objectives_widget)
        layout.addWidget(scroll_area)
        
        # Set initial style
        self.update_style(False)
    
    def create_objective_widget(self, objective: ChallengeObjective) -> QFrame:
        """Create widget for a single objective."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        
        layout = QHBoxLayout(frame)
        
        # Status icon
        status_label = QLabel("⏸️")
        status_label.setFixedWidth(30)
        layout.addWidget(status_label)
        
        # Description
        desc_label = QLabel(objective.description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setMaximumWidth(100)
        progress_bar.setTextVisible(False)
        layout.addWidget(progress_bar)
        
        # Store references for updates
        frame.status_label = status_label
        frame.progress_bar = progress_bar
        frame.desc_label = desc_label
        
        return frame
    
    def start_challenge(self):
        """Start the challenge."""
        # Load challenge topology
        if not self.load_challenge_topology():
            return
        
        # Start progress tracking
        self.progress_tracker = ChallengeProgressTracker(self.challenge, self.main_window)
        self.progress_tracker.progress_updated.connect(self.update_progress)
        self.progress_tracker.challenge_completed.connect(self.on_challenge_completed)
        self.progress_tracker.start()
        
        # Update UI
        self.is_active = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_style(True)
        
        # Emit signal
        self.challenge_started.emit(self.challenge.id)
        
        # Show start message
        QMessageBox.information(
            self,
            "Challenge Started",
            f"Challenge '{self.challenge.name}' has been started!\n\n"
            f"Configure the topology components according to the objectives and run the topology to see your progress."
        )
    
    def stop_challenge(self):
        """Stop the challenge."""
        if self.progress_tracker:
            self.progress_tracker.stop()
            self.progress_tracker.wait()
            self.progress_tracker = None
        
        # Update UI
        self.is_active = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_style(False)
        
        # Reset progress
        self.overall_progress.setValue(0)
        for obj_widget in self.objective_widgets.values():
            obj_widget.status_label.setText("⏸️")
            obj_widget.progress_bar.setValue(0)
        
        # Emit signal
        self.challenge_stopped.emit(self.challenge.id)
    
    def load_challenge_topology(self) -> bool:
        """Load the challenge topology file."""
        try:
            topology_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'challenges', 'topologies', self.challenge.topology_file
            )
            
            if not os.path.exists(topology_path):
                QMessageBox.warning(
                    self,
                    "Topology Not Found",
                    f"Challenge topology file not found:\n{topology_path}"
                )
                return False
            
            # Load topology using file manager
            self.main_window.file_manager.loadTopologyFromFile(topology_path)
            return True
            
        except Exception as e:
            error_print(f"Failed to load challenge topology: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load challenge topology:\n{str(e)}"
            )
            return False
    
    def update_progress(self, objective_status: Dict[str, Any]):
        """Update progress display."""
        total_progress = 0.0
        completed_count = 0
        
        for obj_id, status in objective_status.items():
            if obj_id in self.objective_widgets:
                widget = self.objective_widgets[obj_id]
                
                # Update status icon
                if status['completed']:
                    widget.status_label.setText("✅")
                    completed_count += 1
                elif status['progress'] > 0:
                    widget.status_label.setText("🔄")
                else:
                    widget.status_label.setText("❌")
                
                # Update progress bar
                widget.progress_bar.setValue(int(status['progress']))
                
                # Update description with details
                objective = next(obj for obj in self.challenge.objectives if obj.id == obj_id)
                widget.desc_label.setText(f"{objective.description}\n{status['details']}")
                
                total_progress += status['progress']
        
        # Update overall progress
        if self.challenge.objectives:
            overall = total_progress / len(self.challenge.objectives)
            self.overall_progress.setValue(int(overall))
            self.overall_progress.setFormat(f"Overall Progress: {overall:.1f}% ({completed_count}/{len(self.challenge.objectives)} objectives)")
    
    def on_challenge_completed(self, success: bool, score: int):
        """Handle challenge completion."""
        if success:
            QMessageBox.information(
                self,
                "Challenge Completed!",
                f"Congratulations! You have successfully completed the challenge '{self.challenge.name}'!\n\n"
                f"Final Score: {score}%\n"
                f"All objectives have been met."
            )
        
        # Stop the challenge
        self.stop_challenge()
    
    def update_style(self, active: bool):
        """Update widget style based on active state."""
        if active:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    background-color: #E8F5E8;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #CCC;
                    border-radius: 5px;
                    background-color: #F9F9F9;
                }
            """)
    
    def onTopologyDeployed(self):
        """Called when topology is successfully deployed."""
        if self.progress_tracker and not self.progress_tracker.isRunning():
            # Restart progress tracking when topology is deployed
            self.start_challenge()
    
    def onTopologyDeploymentFailed(self, error_message):
        """Called when topology deployment fails."""
        if self.progress_tracker and self.progress_tracker.isRunning():
            # Stop progress tracking when deployment fails
            self.stop_challenge()
            QMessageBox.warning(
                self,
                "Deployment Failed",
                f"Topology deployment failed: {error_message}\n\nChallenge progress tracking has been stopped."
            )
    
    def onTopologyStopped(self):
        """Called when topology is stopped."""
        if self.progress_tracker and self.progress_tracker.isRunning():
            # Pause progress tracking when topology is stopped
            self.stop_challenge()

class TopologyChallengePanel(QWidget):
    """Main panel for topology challenges."""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.challenges = []
        self.active_challenge = None
        
        self.setupUI()
        self.load_default_challenges()
    
    def setupUI(self):
        """Setup the main panel UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Topology Challenges")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Challenge management buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh Challenges")
        refresh_button.clicked.connect(self.load_default_challenges)
        button_layout.addWidget(refresh_button)
        
        create_button = QPushButton("Create Challenge")
        create_button.clicked.connect(self.open_challenge_creator)
        button_layout.addWidget(create_button)
        
        layout.addLayout(button_layout)
        
        # Challenges scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.challenges_widget = QWidget()
        self.challenges_layout = QVBoxLayout(self.challenges_widget)
        
        scroll_area.setWidget(self.challenges_widget)
        layout.addWidget(scroll_area)
    
    def load_default_challenges(self):
        """Load default challenges."""
        # Clear existing challenges
        for i in reversed(range(self.challenges_layout.count())):
            child = self.challenges_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.challenges.clear()
        
        # Load challenge definitions
        challenge_definitions = self.get_default_challenge_definitions()
        
        for challenge_def in challenge_definitions:
            # Convert objective dictionaries to ChallengeObjective objects
            objectives = []
            for obj_def in challenge_def.get('objectives', []):
                objective = ChallengeObjective(
                    id=obj_def['id'],
                    description=obj_def['description'],
                    component_type=obj_def['component_type'],
                    component_name=obj_def.get('component_name'),
                    config_requirements=obj_def.get('config_requirements'),
                    connection_requirements=obj_def.get('connection_requirements'),
                    weight=obj_def.get('weight', 1.0)
                )
                objectives.append(objective)
            
            # Create TopologyChallenge with proper objectives
            challenge = TopologyChallenge(
                id=challenge_def['id'],
                name=challenge_def['name'],
                description=challenge_def['description'],
                difficulty=challenge_def['difficulty'],
                topology_file=challenge_def['topology_file'],
                objectives=objectives,
                total_score=challenge_def.get('total_score', 100),
                time_limit=challenge_def.get('time_limit'),
                hints=challenge_def.get('hints')
            )
            self.challenges.append(challenge)
            
            # Create and add challenge widget
            challenge_widget = ChallengeWidget(challenge, self.main_window, self)
            challenge_widget.challenge_started.connect(self.on_challenge_started)
            challenge_widget.challenge_stopped.connect(self.on_challenge_stopped)
            
            self.challenges_layout.addWidget(challenge_widget)
        
        # Add stretch to push challenges to top
        self.challenges_layout.addStretch()
    
    def get_default_challenge_definitions(self) -> List[Dict[str, Any]]:
        """Get default challenge definitions."""
        return [
            {
                'id': 'basic_5g_core',
                'name': 'Basic 5G Core Setup',
                'description': 'Set up a basic 5G core network with UE, gNB, and core components. Configure the UE to connect to the network successfully.',
                'difficulty': 'beginner',
                'topology_file': 'basic-1.nf5g',
                'objectives': [
                    {
                        'id': 'ue_config',
                        'description': 'Configure UE with correct MCC/MNC (999/70)',
                        'component_type': 'UE',
                        'config_requirements': {
                            'UE_MCC': '999',
                            'UE_MNC': '70',
                            'UE_APN': 'internet'
                        },
                        'weight': 1.0
                    },
                    {
                        'id': 'gnb_config',
                        'description': 'Configure gNB with correct parameters',
                        'component_type': 'GNB',
                        'config_requirements': {
                            'ueransim_component': 'gnb'
                        },
                        'weight': 1.0
                    },
                    {
                        'id': 'ue_connection',
                        'description': 'UE successfully connects to the 5G network',
                        'component_type': 'UE',
                        'connection_requirements': ['registration_complete', 'pdu_session_established'],
                        'weight': 2.0
                    },
                    {
                        'id': 'gnb_connection',
                        'description': 'gNB successfully connects to AMF',
                        'component_type': 'GNB',
                        'connection_requirements': ['ng_setup_response', 'amf_connected'],
                        'weight': 1.5
                    },
                    {
                        'id': 'core_running',
                        'description': 'All 5G core components are running',
                        'component_type': 'VGcore',
                        'connection_requirements': ['services_running'],
                        'weight': 1.0
                    }
                ],
                'total_score': 100,
                'hints': [
                    'Make sure the UE and gNB have matching MCC/MNC values',
                    'Check that the VGcore component includes all necessary 5G services',
                    'Run the topology to see connection status',
                    'Use the deployment monitor to check component health'
                ]
            },
            {
                'id': 'multi_ue_challenge',
                'name': 'Multiple UE Connection',
                'description': 'Configure multiple UEs to connect to the same gNB and ensure they all register successfully.',
                'difficulty': 'intermediate',
                'topology_file': 'basic-1.nf5g',  # Will be modified by challenge
                'objectives': [
                    {
                        'id': 'ue1_connection',
                        'description': 'First UE connects successfully',
                        'component_type': 'UE',
                        'component_name': 'UE #1',
                        'connection_requirements': ['registration_complete'],
                        'weight': 1.0
                    },
                    {
                        'id': 'ue2_connection',
                        'description': 'Second UE connects successfully',
                        'component_type': 'UE',
                        'component_name': 'UE #2',
                        'connection_requirements': ['registration_complete'],
                        'weight': 1.0
                    },
                    {
                        'id': 'ue3_connection',
                        'description': 'Third UE connects successfully',
                        'component_type': 'UE',
                        'component_name': 'UE #3',
                        'connection_requirements': ['registration_complete'],
                        'weight': 1.0
                    }
                ],
                'total_score': 100,
                'hints': [
                    'Each UE needs unique IMSI and MSISDN values',
                    'All UEs should use the same APN',
                    'Check that the core network can handle multiple UE registrations'
                ]
            }
        ]
    
    def on_challenge_started(self, challenge_id: str):
        """Handle challenge start."""
        if self.active_challenge:
            QMessageBox.warning(
                self,
                "Challenge Active",
                f"Please stop the current challenge '{self.active_challenge}' before starting a new one."
            )
            return
        
        self.active_challenge = challenge_id
        debug_print(f"Challenge started: {challenge_id}")
    
    def on_challenge_stopped(self, challenge_id: str):
        """Handle challenge stop."""
        if self.active_challenge == challenge_id:
            self.active_challenge = None
        debug_print(f"Challenge stopped: {challenge_id}")
    
    def open_challenge_creator(self):
        """Open the challenge creator dialog."""
        dialog = ChallengeCreatorDialog(self.main_window, self)
        if dialog.exec_() == QDialog.Accepted:
            # Reload challenges
            self.load_default_challenges()
    
    def onTopologyDeployed(self):
        """Called when topology is successfully deployed."""
        debug_print("Topology deployed - updating challenge progress tracking")
        # Notify all active challenge widgets
        for i in range(self.challenges_layout.count()):
            widget = self.challenges_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'onTopologyDeployed'):
                widget.onTopologyDeployed()
    
    def onTopologyDeploymentFailed(self, error_message):
        """Called when topology deployment fails."""
        debug_print(f"Topology deployment failed: {error_message}")
        # Notify all active challenge widgets
        for i in range(self.challenges_layout.count()):
            widget = self.challenges_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'onTopologyDeploymentFailed'):
                widget.onTopologyDeploymentFailed(error_message)
    
    def onTopologyStopped(self):
        """Called when topology is stopped."""
        debug_print("Topology stopped - pausing challenge progress tracking")
        # Notify all active challenge widgets
        for i in range(self.challenges_layout.count()):
            widget = self.challenges_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'onTopologyStopped'):
                widget.onTopologyStopped()

class ChallengeCreatorDialog(QDialog):
    """Dialog for creating custom challenges."""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.objectives = []
        
        self.setWindowTitle("Create Topology Challenge")
        self.setModal(True)
        self.resize(600, 700)
        
        self.setupUI()
    
    def setupUI(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Basic challenge info
        info_group = QGroupBox("Challenge Information")
        info_layout = QGridLayout(info_group)
        
        # Challenge ID
        info_layout.addWidget(QLabel("Challenge ID:"), 0, 0)
        self.id_edit = QLineEdit()
        info_layout.addWidget(self.id_edit, 0, 1)
        
        # Challenge name
        info_layout.addWidget(QLabel("Name:"), 1, 0)
        self.name_edit = QLineEdit()
        info_layout.addWidget(self.name_edit, 1, 1)
        
        # Difficulty
        info_layout.addWidget(QLabel("Difficulty:"), 2, 0)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(['beginner', 'intermediate', 'advanced'])
        info_layout.addWidget(self.difficulty_combo, 2, 1)
        
        # Topology file
        info_layout.addWidget(QLabel("Topology File:"), 3, 0)
        topology_layout = QHBoxLayout()
        self.topology_edit = QLineEdit()
        topology_browse_btn = QPushButton("Browse")
        topology_browse_btn.clicked.connect(self.browse_topology_file)
        topology_layout.addWidget(self.topology_edit)
        topology_layout.addWidget(topology_browse_btn)
        info_layout.addLayout(topology_layout, 3, 1)
        
        # Description
        info_layout.addWidget(QLabel("Description:"), 4, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        info_layout.addWidget(self.description_edit, 4, 1)
        
        layout.addWidget(info_group)
        
        # Objectives section
        objectives_group = QGroupBox("Objectives")
        objectives_layout = QVBoxLayout(objectives_group)
        
        # Objectives controls
        obj_controls_layout = QHBoxLayout()
        add_obj_btn = QPushButton("Add Objective")
        add_obj_btn.clicked.connect(self.add_objective)
        obj_controls_layout.addWidget(add_obj_btn)
        obj_controls_layout.addStretch()
        objectives_layout.addLayout(obj_controls_layout)
        
        # Objectives list
        self.objectives_scroll = QScrollArea()
        self.objectives_scroll.setWidgetResizable(True)
        self.objectives_scroll.setMaximumHeight(300)
        
        self.objectives_widget = QWidget()
        self.objectives_layout = QVBoxLayout(self.objectives_widget)
        
        self.objectives_scroll.setWidget(self.objectives_widget)
        objectives_layout.addWidget(self.objectives_scroll)
        
        layout.addWidget(objectives_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Challenge")
        save_btn.clicked.connect(self.save_challenge)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def browse_topology_file(self):
        """Browse for topology file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Topology File",
            "",
            "NetFlux5G Files (*.nf5g);;All Files (*)"
        )
        
        if file_path:
            # Convert to relative path if possible
            try:
                base_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'challenges', 'topologies'
                )
                rel_path = os.path.relpath(file_path, base_path)
                self.topology_edit.setText(rel_path)
            except:
                self.topology_edit.setText(file_path)
    
    def add_objective(self):
        """Add a new objective."""
        dialog = ObjectiveEditorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            objective = dialog.get_objective()
            self.objectives.append(objective)
            self.update_objectives_display()
    
    def update_objectives_display(self):
        """Update the objectives display."""
        # Clear existing widgets
        for i in reversed(range(self.objectives_layout.count())):
            child = self.objectives_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add objective widgets
        for i, objective in enumerate(self.objectives):
            obj_widget = self.create_objective_display_widget(objective, i)
            self.objectives_layout.addWidget(obj_widget)
        
        self.objectives_layout.addStretch()
    
    def create_objective_display_widget(self, objective: ChallengeObjective, index: int) -> QWidget:
        """Create display widget for an objective."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        
        layout = QHBoxLayout(widget)
        
        # Objective info
        info_label = QLabel(f"{index + 1}. {objective.description}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_objective(index))
        layout.addWidget(edit_btn)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_objective(index))
        layout.addWidget(remove_btn)
        
        return widget
    
    def edit_objective(self, index: int):
        """Edit an objective."""
        if 0 <= index < len(self.objectives):
            dialog = ObjectiveEditorDialog(self, self.objectives[index])
            if dialog.exec_() == QDialog.Accepted:
                self.objectives[index] = dialog.get_objective()
                self.update_objectives_display()
    
    def remove_objective(self, index: int):
        """Remove an objective."""
        if 0 <= index < len(self.objectives):
            del self.objectives[index]
            self.update_objectives_display()
    
    def save_challenge(self):
        """Save the challenge."""
        try:
            # Validate inputs
            if not self.id_edit.text():
                QMessageBox.warning(self, "Validation Error", "Challenge ID is required.")
                return
            
            if not self.name_edit.text():
                QMessageBox.warning(self, "Validation Error", "Challenge name is required.")
                return
            
            if not self.topology_edit.text():
                QMessageBox.warning(self, "Validation Error", "Topology file is required.")
                return
            
            if not self.objectives:
                QMessageBox.warning(self, "Validation Error", "At least one objective is required.")
                return
            
            # Create challenge data
            challenge_data = {
                'id': self.id_edit.text(),
                'name': self.name_edit.text(),
                'description': self.description_edit.toPlainText(),
                'difficulty': self.difficulty_combo.currentText(),
                'topology_file': self.topology_edit.text(),
                'objectives': [asdict(obj) for obj in self.objectives],
                'total_score': 100,
                'hints': []
            }
            
            # Save to file
            challenges_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'challenges'
            )
            os.makedirs(challenges_dir, exist_ok=True)
            
            file_path = os.path.join(challenges_dir, f"{challenge_data['id']}.json")
            
            with open(file_path, 'w') as f:
                json.dump(challenge_data, f, indent=2)
            
            QMessageBox.information(
                self,
                "Challenge Saved",
                f"Challenge '{challenge_data['name']}' has been saved successfully!"
            )
            
            self.accept()
            
        except Exception as e:
            error_print(f"Failed to save challenge: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save challenge:\n{str(e)}"
            )

class ObjectiveEditorDialog(QDialog):
    """Dialog for editing challenge objectives."""
    
    def __init__(self, parent=None, objective: ChallengeObjective = None):
        super().__init__(parent)
        self.objective = objective
        
        self.setWindowTitle("Edit Objective")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setupUI()
        
        if self.objective:
            self.load_objective_data()
    
    def setupUI(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Basic objective info
        info_layout = QGridLayout()
        
        # Objective ID
        info_layout.addWidget(QLabel("Objective ID:"), 0, 0)
        self.id_edit = QLineEdit()
        info_layout.addWidget(self.id_edit, 0, 1)
        
        # Description
        info_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_edit = QLineEdit()
        info_layout.addWidget(self.description_edit, 1, 1)
        
        # Component type
        info_layout.addWidget(QLabel("Component Type:"), 2, 0)
        self.component_type_combo = QComboBox()
        self.component_type_combo.addItems(['UE', 'GNB', 'VGcore', 'AP', 'Host', 'STA'])
        info_layout.addWidget(self.component_type_combo, 2, 1)
        
        # Component name (optional)
        info_layout.addWidget(QLabel("Component Name:"), 3, 0)
        self.component_name_edit = QLineEdit()
        self.component_name_edit.setPlaceholderText("Leave empty for any component of this type")
        info_layout.addWidget(self.component_name_edit, 3, 1)
        
        # Weight
        info_layout.addWidget(QLabel("Weight:"), 4, 0)
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(1, 10)
        self.weight_spin.setValue(1)
        info_layout.addWidget(self.weight_spin, 4, 1)
        
        layout.addLayout(info_layout)
        
        # Configuration requirements
        config_group = QGroupBox("Configuration Requirements")
        config_layout = QVBoxLayout(config_group)
        
        config_help = QLabel("Enter configuration requirements as key=value pairs, one per line:")
        config_help.setStyleSheet("color: #666; font-style: italic;")
        config_layout.addWidget(config_help)
        
        self.config_edit = QTextEdit()
        self.config_edit.setMaximumHeight(100)
        self.config_edit.setPlaceholderText("UE_MCC=999\nUE_MNC=70\nUE_APN=internet")
        config_layout.addWidget(self.config_edit)
        
        layout.addWidget(config_group)
        
        # Connection requirements
        conn_group = QGroupBox("Connection Requirements")
        conn_layout = QVBoxLayout(conn_group)
        
        conn_help = QLabel("Enter connection requirements, one per line:")
        conn_help.setStyleSheet("color: #666; font-style: italic;")
        conn_layout.addWidget(conn_help)
        
        self.connection_edit = QTextEdit()
        self.connection_edit.setMaximumHeight(80)
        self.connection_edit.setPlaceholderText("registration_complete\npdu_session_established")
        conn_layout.addWidget(self.connection_edit)
        
        layout.addWidget(conn_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def load_objective_data(self):
        """Load objective data into the form."""
        if not self.objective:
            return
        
        self.id_edit.setText(self.objective.id)
        self.description_edit.setText(self.objective.description)
        self.component_type_combo.setCurrentText(self.objective.component_type)
        
        if self.objective.component_name:
            self.component_name_edit.setText(self.objective.component_name)
        
        self.weight_spin.setValue(int(self.objective.weight))
        
        # Load config requirements
        if self.objective.config_requirements:
            config_lines = []
            for key, value in self.objective.config_requirements.items():
                config_lines.append(f"{key}={value}")
            self.config_edit.setPlainText("\n".join(config_lines))
        
        # Load connection requirements
        if self.objective.connection_requirements:
            self.connection_edit.setPlainText("\n".join(self.objective.connection_requirements))
    
    def get_objective(self) -> ChallengeObjective:
        """Get the objective from the form."""
        # Parse config requirements
        config_requirements = {}
        config_text = self.config_edit.toPlainText().strip()
        if config_text:
            for line in config_text.split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    config_requirements[key.strip()] = value.strip()
        
        # Parse connection requirements
        connection_requirements = []
        conn_text = self.connection_edit.toPlainText().strip()
        if conn_text:
            connection_requirements = [line.strip() for line in conn_text.split('\n') if line.strip()]
        
        return ChallengeObjective(
            id=self.id_edit.text(),
            description=self.description_edit.text(),
            component_type=self.component_type_combo.currentText(),
            component_name=self.component_name_edit.text() or None,
            config_requirements=config_requirements if config_requirements else None,
            connection_requirements=connection_requirements if connection_requirements else None,
            weight=float(self.weight_spin.value())
        )
