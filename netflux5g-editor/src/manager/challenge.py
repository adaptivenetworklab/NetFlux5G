"""
Challenge Manager for NetFlux5G Editor

This module manages the topology challenge system integration with the main application.
It provides the interface between the challenge system and the main GUI.
"""

import os
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import Qt
from utils.debug import debug_print, error_print, warning_print
from challenges.topology_challenge import TopologyChallengePanel

class ChallengeManager:
    """Manager for the topology challenge system."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.challenge_panel = None
        self.challenge_dock = None
        
        # Setup challenge system
        self.setupChallengeSystem()
    
    def setupChallengeSystem(self):
        """Setup the challenge system integration."""
        try:
            # Create challenge panel
            self.challenge_panel = TopologyChallengePanel(self.main_window)
            
            # Create dock widget
            self.challenge_dock = QDockWidget("Topology Challenges", self.main_window)
            self.challenge_dock.setWidget(self.challenge_panel)
            self.challenge_dock.setFeatures(
                QDockWidget.DockWidgetMovable | 
                QDockWidget.DockWidgetFloatable |
                QDockWidget.DockWidgetClosable
            )
            
            # Add to main window (initially hidden)
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.challenge_dock)
            self.challenge_dock.hide()
            
            # Add menu item
            self.addChallengeMenu()
            
            debug_print("Challenge system initialized successfully")
            
        except Exception as e:
            error_print(f"Failed to setup challenge system: {e}")
    
    def addChallengeMenu(self):
        """Connect challenge menu actions to their handlers."""
        try:
            # Connect the UI-defined actions to their handlers
            if hasattr(self.main_window, 'actionShowChallengePanel'):
                self.main_window.actionShowChallengePanel.triggered.connect(self.toggleChallengePanel)
                self.show_challenges_action = self.main_window.actionShowChallengePanel
                
            if hasattr(self.main_window, 'actionStartBasicChallenge'):
                self.main_window.actionStartBasicChallenge.triggered.connect(self.startBasicChallenge)
                
            if hasattr(self.main_window, 'actionCreateCustomChallenge'):
                self.main_window.actionCreateCustomChallenge.triggered.connect(self.createCustomChallenge)
                
            debug_print("Challenge menu actions connected successfully")
            
        except Exception as e:
            error_print(f"Failed to connect challenge menu actions: {e}")
    
    def toggleChallengePanel(self):
        """Toggle the challenge panel visibility."""
        try:
            if self.challenge_dock.isVisible():
                self.challenge_dock.hide()
                if hasattr(self, 'show_challenges_action') and self.show_challenges_action:
                    self.show_challenges_action.setChecked(False)
            else:
                self.challenge_dock.show()
                if hasattr(self, 'show_challenges_action') and self.show_challenges_action:
                    self.show_challenges_action.setChecked(True)
                
                # Bring to front and resize appropriately
                self.challenge_dock.raise_()
                self.challenge_dock.activateWindow()
                
        except Exception as e:
            error_print(f"Failed to toggle challenge panel: {e}")
    
    def showChallengePanel(self):
        """Show the challenge panel."""
        try:
            self.challenge_dock.show()
            if hasattr(self, 'show_challenges_action') and self.show_challenges_action:
                self.show_challenges_action.setChecked(True)
            self.challenge_dock.raise_()
            self.challenge_dock.activateWindow()
        except Exception as e:
            error_print(f"Failed to show challenge panel: {e}")
    
    def hideChallengePanel(self):
        """Hide the challenge panel."""
        try:
            self.challenge_dock.hide()
            if hasattr(self, 'show_challenges_action') and self.show_challenges_action:
                self.show_challenges_action.setChecked(False)
        except Exception as e:
            error_print(f"Failed to hide challenge panel: {e}")
    
    def startBasicChallenge(self):
        """Start the basic 5G core challenge."""
        try:
            # Show challenge panel
            self.showChallengePanel()
            
            # Find and start the basic challenge
            if self.challenge_panel:
                for i in range(self.challenge_panel.challenges_layout.count()):
                    widget = self.challenge_panel.challenges_layout.itemAt(i).widget()
                    if hasattr(widget, 'challenge') and widget.challenge.id == 'basic_5g_core':
                        widget.start_challenge()
                        break
                        
        except Exception as e:
            error_print(f"Failed to start basic challenge: {e}")
    
    def createCustomChallenge(self):
        """Open the custom challenge creator."""
        try:
            if self.challenge_panel:
                self.challenge_panel.open_challenge_creator()
        except Exception as e:
            error_print(f"Failed to open challenge creator: {e}")
    
    def getChallengeProgress(self):
        """Get the current challenge progress."""
        try:
            if self.challenge_panel and self.challenge_panel.active_challenge:
                # Return information about the active challenge
                return {
                    'active_challenge': self.challenge_panel.active_challenge,
                    'challenge_panel_visible': self.challenge_dock.isVisible()
                }
            return None
        except Exception as e:
            error_print(f"Failed to get challenge progress: {e}")
            return None
    
    def onTopologyLoaded(self):
        """Handle topology loaded event."""
        try:
            # Refresh challenge panel if visible
            if self.challenge_panel and self.challenge_dock.isVisible():
                debug_print("Topology loaded - challenges available for execution")
        except Exception as e:
            error_print(f"Error handling topology loaded event: {e}")
    
    def onTopologyRun(self):
        """Handle topology run event."""
        try:
            # If a challenge is active, the tracking will automatically update
            if self.challenge_panel and self.challenge_panel.active_challenge:
                debug_print(f"Topology running - monitoring challenge progress for {self.challenge_panel.active_challenge}")
        except Exception as e:
            error_print(f"Error handling topology run event: {e}")
    
    def onTopologyStop(self):
        """Handle topology stop event."""
        try:
            # Challenge tracking will handle the stop automatically
            if self.challenge_panel and self.challenge_panel.active_challenge:
                debug_print(f"Topology stopped - challenge tracking paused for {self.challenge_panel.active_challenge}")
        except Exception as e:
            error_print(f"Error handling topology stop event: {e}")
    
    def setupChallengeDirectories(self):
        """Setup challenge directories if they don't exist."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Create challenges directory structure
            challenges_dir = os.path.join(base_dir, 'challenges')
            topologies_dir = os.path.join(challenges_dir, 'topologies')
            
            os.makedirs(challenges_dir, exist_ok=True)
            os.makedirs(topologies_dir, exist_ok=True)
            
            # Copy basic-1.nf5g to challenges/topologies if it doesn't exist
            basic_topology_src = "/home/litfan/TA/testing/basic-1/basic-1.nf5g"
            basic_topology_dst = os.path.join(topologies_dir, "basic-1.nf5g")
            
            if os.path.exists(basic_topology_src) and not os.path.exists(basic_topology_dst):
                import shutil
                shutil.copy2(basic_topology_src, basic_topology_dst)
                debug_print(f"Copied basic challenge topology to {basic_topology_dst}")
            
            return True
            
        except Exception as e:
            error_print(f"Failed to setup challenge directories: {e}")
            return False
    
    def onTopologyDeployed(self):
        """Called when topology is successfully deployed."""
        try:
            if self.challenge_panel:
                self.challenge_panel.onTopologyDeployed()
        except Exception as e:
            error_print(f"Error notifying challenge panel of topology deployment: {e}")
    
    def onTopologyDeploymentFailed(self, error_message):
        """Called when topology deployment fails."""
        try:
            if self.challenge_panel:
                self.challenge_panel.onTopologyDeploymentFailed(error_message)
        except Exception as e:
            error_print(f"Error notifying challenge panel of deployment failure: {e}")
    
    def onTopologyStopped(self):
        """Called when topology is stopped."""
        try:
            if self.challenge_panel:
                self.challenge_panel.onTopologyStopped()
        except Exception as e:
            error_print(f"Error notifying challenge panel of topology stop: {e}")
