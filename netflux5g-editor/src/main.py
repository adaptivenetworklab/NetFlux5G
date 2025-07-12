import os
import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QMenuBar, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QCursor
from PyQt5 import uic

# Import managers
from manager.window import WindowManager
from manager.status import StatusManager
from manager.component_panel import ComponentPanelManager
from manager.file import FileManager
from manager.tool import ToolManager
from manager.canvas import CanvasManager
from manager.automation import AutomationManager
from manager.keyboard import KeyboardManager
from manager.component_operations import ComponentOperationsManager
from manager.debug import DebugManager, debug_print, error_print, warning_print, set_debug_enabled, is_debug_enabled
from manager.welcome import WelcomeScreenManager
from manager.docker_network import DockerNetworkManager
from manager.database import DatabaseManager
from manager.monitoring import MonitoringManager
from manager.controller import ControllerManager
from manager.template_updater import TemplateUpdater

# Import existing modules
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from export.mininet_export import MininetExporter
from automation.automation_runner import AutomationRunner

# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "ui", "Main_Window.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self, show_welcome=True):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)

        # Initialize component mapping for icons FIRST
        self.setupComponentIconMap()
        
        # Initialize managers
        self.window_manager = WindowManager(self)
        self.status_manager = StatusManager(self)
        self.component_panel_manager = ComponentPanelManager(self)
        self.file_manager = FileManager(self)
        self.tool_manager = ToolManager(self)
        self.canvas_manager = CanvasManager(self)
        self.automation_manager = AutomationManager(self)
        self.keyboard_manager = KeyboardManager(self)
        self.component_operations_manager = ComponentOperationsManager(self)
        self.welcome_manager = WelcomeScreenManager(self)
        self.docker_network_manager = DockerNetworkManager(self)
        self.database_manager = DatabaseManager(self)
        self.monitoring_manager = MonitoringManager(self)
        self.controller_manager = ControllerManager(self)
        self.template_updater = TemplateUpdater(self)
        
        # Initialize other components
        self.toolbar_functions = ToolbarFunctions(self)
        self.mininet_exporter = MininetExporter(self)
        self.automation_runner = AutomationRunner(self)

        # Initialize grid attribute
        self.show_grid = False
        
        # Setup window
        self.window_manager.setupWindow()
        
        # Add Debug menu
        self.setupDebugMenu()
        
        # Set up the canvas and component panel
        self.setupCanvas()
        self.component_panel_manager.setupComponentPanel()
        self.component_panel_manager.setupComponentPanelToggle()
        
        # Initialize attributes
        self.current_link_source = None
        self.current_file = None
        self.is_template_loaded = False  # Flag to track if a template is loaded
        self.template_name = None  # Name of the loaded template
        self.current_tool = "pick"
        self.selected_component = None
        self.has_unsaved_changes = False  # Track if there are unsaved changes
        self.placement_mode = False
        self.placement_component_type = None
        
        # Setup all connections
        self.setupConnections()

        # Setup initial UI states
        self.setupInitialUIStates()

        # Debug menu actions
        self.debugMenuActions()

        # Update template files with correct config paths
        debug_print("Updating template configuration paths...")
        if self.template_updater.update_all_templates():
            debug_print("Template configuration paths updated successfully")
        else:
            warning_print("Failed to update some template configuration paths")

        # Initialize window title
        self.updateWindowTitle()

        # Show helpful shortcut information
        self.showShortcutHelp()

        # Don't show main window immediately if showing welcome screen
        if show_welcome:
            # Hide main window initially
            self.hide()
        
        # Force initial geometry update
        QTimer.singleShot(100, self.window_manager.updateCanvasGeometry)

    def setupComponentIconMap(self):
        """Initialize component icon mapping."""
        icon_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon")
        self.component_icon_map = {
            "Host": os.path.join(icon_base_path, "host.png"),
            "STA": os.path.join(icon_base_path, "sta.png"),
            "UE": os.path.join(icon_base_path, "ue.png"),
            "GNB": os.path.join(icon_base_path, "gNB.png"),
            "DockerHost": os.path.join(icon_base_path, "docker.png"),
            "AP": os.path.join(icon_base_path, "AP.png"),
            "VGcore": os.path.join(icon_base_path, "5G core.png"),
            "Router": os.path.join(icon_base_path, "Router.png"),
            "Switch": os.path.join(icon_base_path, "switch.png"),
            "LinkCable": os.path.join(icon_base_path, "link cable.png"),
            "Controller": os.path.join(icon_base_path, "controller.png")
        }

    def setupCanvas(self):
        """Set up the canvas with proper error handling and let splitter manage sizing."""
        try:
            if hasattr(self, 'horizontalLayoutWidget'):
                self.horizontalLayoutWidget.deleteLater()
            self.main_splitter = QSplitter(Qt.Horizontal)
            if hasattr(self, 'ObjectFrame'):
                self.ObjectFrame.setParent(None)
                self.main_splitter.addWidget(self.ObjectFrame)
                self.ObjectFrame.setMinimumWidth(240)
                self.ObjectFrame.setMaximumWidth(240)
            self.canvas_view = Canvas(self)
            self.main_splitter.addWidget(self.canvas_view)
            self.main_splitter.setSizes([240, 1000])
            self.main_splitter.setStretchFactor(0, 0)
            self.main_splitter.setStretchFactor(1, 1)
            self.setCentralWidget(self.main_splitter)
            self.main_splitter.setCollapsible(0, True)
            self.main_splitter.setCollapsible(1, False)
            self.main_splitter.splitterMoved.connect(self.onSplitterMoved)
            QTimer.singleShot(200, self.status_manager.setupCanvasStatusBar)
            debug_print("DEBUG: Canvas and component panel setup with dynamic resizing (no manual geometry)")
        except Exception as e:
            error_print(f"ERROR: Failed to setup canvas: {e}")
            self.canvas_view = Canvas(self)
            self.setCentralWidget(self.canvas_view)

    def onSplitterMoved(self, pos, index):
        """Handle splitter movement."""
        debug_print(f"DEBUG: Splitter moved to position {pos}, index {index}")
        
        if hasattr(self, '_splitter_timer'):
            self._splitter_timer.stop()
        else:
            self._splitter_timer = QTimer()
            self._splitter_timer.setSingleShot(True)
            self._splitter_timer.timeout.connect(self.component_panel_manager.updateComponentButtonSizes)
        
        self._splitter_timer.start(150)

        # Update canvas geometry when the splitter is moved
        if hasattr(self, 'window_manager'):
            self.window_manager.updateCanvasGeometry()

    def setupConnections(self):
        """Set up all signal connections."""
        try:
            # Menu connections
            if hasattr(self, 'actionNew'):
                self.actionNew.triggered.connect(self.file_manager.newTopology)
            if hasattr(self, 'actionOpen'):
                self.actionOpen.triggered.connect(self.file_manager.openTopology)
            if hasattr(self, 'actionSave'):
                self.actionSave.triggered.connect(self.file_manager.saveTopology)
            if hasattr(self, 'actionSave_As'):
                self.actionSave_As.triggered.connect(self.file_manager.saveTopologyAs)
            if hasattr(self, 'actionExport_to_Level_2_Script'):
                self.actionExport_to_Level_2_Script.triggered.connect(self.automation_manager.exportToMininet)

            # Edit menu connections - Cut, Copy, Paste
            if hasattr(self, 'actionCut'):
                self.actionCut.triggered.connect(self.component_operations_manager.cutComponent)
            if hasattr(self, 'actionCopy'):
                self.actionCopy.triggered.connect(self.component_operations_manager.copyComponent)
            if hasattr(self, 'actionPaste'):
                self.actionPaste.triggered.connect(self.component_operations_manager.pasteComponent)

            # Tool connections
            if hasattr(self, 'actionPickTool'):
                self.actionPickTool.triggered.connect(self.tool_manager.enablePickTool)
            if hasattr(self, 'actionLinkTool'):
                self.actionLinkTool.triggered.connect(self.tool_manager.enableLinkTool)
            if hasattr(self, 'actionDelete'):
                self.actionDelete.triggered.connect(self.tool_manager.enableDeleteTool)

            # Canvas connections
            if hasattr(self, 'actionShowGrid'):
                self.actionShowGrid.triggered.connect(self.canvas_manager.toggleGrid)

            # Automation connections
            if hasattr(self, 'actionRun_All'):
                self.actionRun_All.triggered.connect(self.automation_manager.runAllComponents)
            if hasattr(self, 'actionStop_All'):
                self.actionStop_All.triggered.connect(self.automation_manager.stopAllComponents)
            if hasattr(self, 'actionRunAll'):
                self.actionRunAll.triggered.connect(self.automation_manager.runAllComponents)
            if hasattr(self, 'actionStopAll'):
                self.actionStopAll.triggered.connect(self.automation_manager.stopAllComponents)
            if hasattr(self, 'actionRun'):
                self.actionRun.triggered.connect(self.automation_manager.runTopology)
            if hasattr(self, 'actionStop'):
                self.actionStop.triggered.connect(self.automation_manager.stopTopology)

            # Docker network connections
            if hasattr(self, 'actionCreate_Docker_Network'):
                self.actionCreate_Docker_Network.triggered.connect(self.docker_network_manager.create_docker_network)
            if hasattr(self, 'actionDelete_Docker_Network'):
                self.actionDelete_Docker_Network.triggered.connect(self.docker_network_manager.delete_docker_network)

            # Database connections
            if hasattr(self, 'actionDeploy_Database'):
                self.actionDeploy_Database.triggered.connect(self.database_manager.deployDatabase)
            if hasattr(self, 'actionStop_Database'):
                self.actionStop_Database.triggered.connect(self.database_manager.stopDatabase)

            # Web UI connections
            if hasattr(self, 'actionDeploy_User_Manager'):
                self.actionDeploy_User_Manager.triggered.connect(self.database_manager.deployWebUI)
            if hasattr(self, 'actionStop_User_Manager'):
                self.actionStop_User_Manager.triggered.connect(self.database_manager.stopWebUI)

            # Monitoring connections
            if hasattr(self, 'actionDeploy_Monitoring'):
                self.actionDeploy_Monitoring.triggered.connect(self.monitoring_manager.deployMonitoring)
            if hasattr(self, 'actionStop_Monitoring'):
                self.actionStop_Monitoring.triggered.connect(self.monitoring_manager.stopMonitoring)

            # Controller connections
            if hasattr(self, 'actionDeploy_Ryu_Controller'):
                self.actionDeploy_Ryu_Controller.triggered.connect(self.controller_manager.deployController)
            if hasattr(self, 'actionStop_Ryu_Controller'):
                self.actionStop_Ryu_Controller.triggered.connect(self.controller_manager.stopController)
            
            # ONOS Controller connections
            if hasattr(self, 'actionDeploy_ONOS_Controller'):
                self.actionDeploy_ONOS_Controller.triggered.connect(self.controller_manager.deployOnosController)
            if hasattr(self, 'actionStop_ONOS_Controller'):
                self.actionStop_ONOS_Controller.triggered.connect(self.controller_manager.stopOnosController)

            # Component button connections
            if hasattr(self.component_panel_manager, 'component_widgets'):
                for widget in self.component_panel_manager.component_widgets:
                    if hasattr(widget, 'button') and hasattr(widget, 'button_name'):
                        button = widget.button
                        component_type = widget.button_name
                        
                        def make_mouse_press_handler(comp_type):
                            def handle_mouse_press(event):
                                self.onComponentButtonPress(event, comp_type)
                            return handle_mouse_press
                        
                        button.mousePressEvent = make_mouse_press_handler(component_type)
                        debug_print(f"DEBUG: Connected {component_type} button")

            # Keyboard shortcuts
            if hasattr(self, 'actionPickTool'):
                self.actionPickTool.setShortcut(QKeySequence('P'))
            if hasattr(self, 'actionLinkTool'):
                self.actionLinkTool.setShortcut(QKeySequence('L'))
            if hasattr(self, 'actionDelete'):
                self.actionDelete.setShortcut(QKeySequence('D'))
            if hasattr(self, 'actionShowGrid'):
                self.actionShowGrid.setShortcut(QKeySequence('G'))
            if hasattr(self, 'actionRun'):
                self.actionRun.setShortcut(QKeySequence('F5'))
            if hasattr(self, 'actionStop'):
                self.actionStop.setShortcut(QKeySequence('F6'))
            if hasattr(self, 'actionRun_All'):
                self.actionRun_All.setShortcut(QKeySequence('Ctrl+F5'))
            if hasattr(self, 'actionStop_All'):
                self.actionStop_All.setShortcut(QKeySequence('Ctrl+F6'))

            # Connect splitter moved signal to handler
            if hasattr(self, 'splitter'):
                self.splitter.splitterMoved.connect(self.onSplitterMoved)

            # Connect automation runner signals
            self.automation_runner.execution_finished.connect(self.automation_manager.onAutomationFinished)

            debug_print("DEBUG: All connections setup successfully")
            
        except Exception as e:
            error_print(f"ERROR: Failed to setup connections: {e}")

    def onComponentButtonPress(self, event, component_type):
        """Handle component button press to start drag operation."""
        from PyQt5.QtCore import Qt
        
        if event.button() == Qt.LeftButton:
            debug_print(f"DEBUG: Component button pressed: {component_type}")
            self.tool_manager.startDrag(component_type)

    def keyPressEvent(self, event):
        """Handle key press events."""
        # Allow ESC to cancel placement mode
        if self.placement_mode and event.key() == Qt.Key_Escape:
            self.exitPlacementMode()
            return
        
        # Delegate to keyboard manager for other shortcuts
        if hasattr(self, 'keyboard_manager'):
            handled = self.keyboard_manager.handleKeyPress(event)
            if handled:
                return
        
        super().keyPressEvent(event)

    # Delegate methods to managers
    def startDrag(self, component_type):
        """Delegate to tool manager."""
        self.tool_manager.startDrag(component_type)

    def createLink(self, source, destination):
        """Delegate to tool manager."""
        return self.tool_manager.createLink(source, destination)

    def exitLinkMode(self):
        """Delegate to tool manager."""
        self.tool_manager.exitLinkMode()

    def zoomIn(self):
        """Delegate to canvas manager."""
        self.canvas_manager.zoomIn()

    def zoomOut(self):
        """Delegate to canvas manager."""
        self.canvas_manager.zoomOut()

    def resetZoom(self):
        """Delegate to canvas manager."""
        self.canvas_manager.resetZoom()

    def toggleGrid(self):
        """Delegate to canvas manager."""
        self.canvas_manager.toggleGrid()

    # Component operations delegates
    def cutComponent(self):
        """Delegate to component operations manager."""
        self.component_operations_manager.cutComponent()

    def copyComponent(self):
        """Delegate to component operations manager."""
        self.component_operations_manager.copyComponent()

    def pasteComponent(self):
        """Delegate to component operations manager."""
        self.component_operations_manager.pasteComponent()

    def setupDebugMenu(self):
        """Create and setup the Debug menu"""
        try:
            # Check if menubar exists, if not create it
            if not hasattr(self, 'menubar') or self.menubar is None:
                self.menubar = QMenuBar(self)
                self.setMenuBar(self.menubar)
            
            # Create Debug menu
            self.menuDebug = QMenu('Debug', self)
            self.menubar.addMenu(self.menuDebug)
            
            # Create debug mode toggle action
            self.actionToggleDebug = QAction('Enable Debug Mode', self)
            self.actionToggleDebug.setCheckable(True)
            self.actionToggleDebug.setChecked(is_debug_enabled())
            self.actionToggleDebug.setShortcut(QKeySequence('Ctrl+Shift+D'))
            self.actionToggleDebug.setStatusTip('Toggle debug mode on/off')
            self.actionToggleDebug.triggered.connect(self.toggleDebugMode)
            
            # Create clear debug output action
            self.actionClearDebug = QAction('Clear Debug Output', self)
            self.actionClearDebug.setShortcut(QKeySequence('Ctrl+Shift+C'))
            self.actionClearDebug.setStatusTip('Clear debug output in console')
            self.actionClearDebug.triggered.connect(self.clearDebugOutput)
            
            # Create show debug info action
            self.actionShowDebugInfo = QAction('Show Debug Info', self)
            self.actionShowDebugInfo.setShortcut(QKeySequence('Ctrl+Shift+I'))
            self.actionShowDebugInfo.setStatusTip('Show current debug information')
            self.actionShowDebugInfo.triggered.connect(self.showDebugInfo)
            
            # Add actions to menu
            self.menuDebug.addAction(self.actionToggleDebug)
            self.menuDebug.addSeparator()
            self.menuDebug.addAction(self.actionClearDebug)
            self.menuDebug.addAction(self.actionShowDebugInfo)
            
            debug_print("Debug menu created successfully")
            
        except Exception as e:
            error_print(f"Failed to setup debug menu: {e}")
            
    def toggleDebugMode(self):
        """Toggle debug mode on/off"""
        current_state = is_debug_enabled()
        new_state = not current_state
        
        set_debug_enabled(new_state)
        
        # Update action text and status
        if new_state:
            self.actionToggleDebug.setText('Disable Debug Mode')
            self.showCanvasStatus("Debug mode enabled - Debug messages will now be shown")
        else:
            self.actionToggleDebug.setText('Enable Debug Mode')
            self.showCanvasStatus("Debug mode disabled - Debug messages will be hidden")
        
        # Update checked state
        self.actionToggleDebug.setChecked(new_state)
        
        debug_print(f"Debug mode toggled to: {new_state}", force=True)

    def clearDebugOutput(self):
        """Clear the debug output in console (if possible)"""
        try:
            # For Windows
            if os.name == 'nt':
                os.system('cls')
            # For Unix/Linux/MacOS
            else:
                os.system('clear')
            
            debug_print("Debug output cleared", force=True)
            self.showCanvasStatus("Debug output cleared")
            
        except Exception as e:
            error_print(f"Could not clear console: {e}")
            self.showCanvasStatus("Could not clear console output")

    def showDebugInfo(self):
        """Show current debug information"""
        debug_info = []
        debug_info.append(f"Debug Mode: {'Enabled' if is_debug_enabled() else 'Disabled'}")
        debug_info.append(f"Current Tool: {self.current_tool}")
        debug_info.append(f"Canvas Size: {self.canvas_view.size() if hasattr(self, 'canvas_view') else 'N/A'}")
        debug_info.append(f"Scene Items: {len(self.canvas_view.scene.items()) if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene') else 'N/A'}")
        debug_info.append(f"Current File: {self.current_file if self.current_file else 'None'}")
        debug_info.append(f"Link Source: {self.current_link_source if self.current_link_source else 'None'}")
        
        info_text = "\n".join(debug_info)
        debug_print("=== DEBUG INFO ===", force=True)
        debug_print(info_text, force=True)
        debug_print("=== END DEBUG INFO ===", force=True)
        
        self.showCanvasStatus("Debug info printed to console")

    def showShortcutHelp(self):
        """Show a brief help message about shortcuts."""
        help_message = (
            "Mouse Navigation: Middle-click + drag to pan | Ctrl + Mouse wheel to zoom | "
            "Keyboard: P=Pick, D=Delete, L=Link, G=Grid, +/-=Zoom, 0=Reset Zoom, ESC=Pick Tool | "
            "Edit: Ctrl+X=Cut, Ctrl+C=Copy, Ctrl+V=Paste | "
            "Debug: Ctrl+Shift+D=Toggle Debug"
        )
        # Show for 5 seconds, then return to ready state
        self.showCanvasStatus(help_message, 5000)

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Check for unsaved changes
            if self.has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes in your topology.\n\n"
                    "Do you want to save your changes before exiting?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                
                if reply == QMessageBox.Save:
                    # Try to save the file
                    self.file_manager.saveTopology()
                    # Check if save was successful (user didn't cancel save dialog)
                    if self.has_unsaved_changes:
                        # Save was cancelled, so don't close
                        event.ignore()
                        return
                elif reply == QMessageBox.Cancel:
                    # User cancelled, don't close
                    event.ignore()
                    return
                # If Discard was chosen, continue with closing
            
            # Stop any running automation
            if hasattr(self, 'automation_runner'):
                self.automation_runner.stop_all()
            
            # Clear component operations clipboard
            if hasattr(self, 'component_operations_manager'):
                self.component_operations_manager.clearClipboard()
            
            # Clean up status timer
            if hasattr(self.status_manager, '_status_timer') and self.status_manager._status_timer:
                self.status_manager._status_timer.stop()
                self.status_manager._status_timer = None
            
            # Clean up status label
            if hasattr(self.status_manager, 'canvas_status_label') and self.status_manager.canvas_status_label:
                try:
                    self.status_manager.canvas_status_label.hide()
                    self.status_manager.canvas_status_label.deleteLater()
                except RuntimeError:
                    pass  # Already deleted
                finally:
                    self.status_manager.canvas_status_label = None
            
            debug_print("Application cleanup completed")
            
        except Exception as e:
            error_print(f"Error during application cleanup: {e}")
        
        event.accept()

    def showCanvasStatus(self, message, timeout=0):
        """Wrapper method for status manager."""
        self.status_manager.showCanvasStatus(message, timeout)

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        try:
            if hasattr(self, '_resize_timer'):
                self._resize_timer.stop()
            else:
                self._resize_timer = QTimer()
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self._performResizeUpdate)
            
            self._resize_timer.start(200)
            
        except Exception as e:
            error_print(f"ERROR in resizeEvent: {e}")

    def _performResizeUpdate(self):
        """Perform the actual resize updates after debouncing."""
        try:
            self.window_manager.updateCanvasGeometry()
            self.component_panel_manager.updateComponentButtonSizes()
            
            if hasattr(self.status_manager, 'canvas_status_label'):
                self.status_manager.updateCanvasStatusBarPosition()
                
        except Exception as e:
            error_print(f"ERROR in _performResizeUpdate: {e}")

    def debugMenuActions(self):
        """Debug method to check available menu actions."""
        debug_print("=== DEBUG: Menu Actions ===")
        
        # Check if File menu exists
        if hasattr(self, 'menuFile'):
            debug_print(f"menuFile found: {self.menuFile}")
            debug_print("Actions in File menu:")
            for action in self.menuFile.actions():
                debug_print(f"  - {action.objectName()}: {action.text()}")
        
        # Check specific actions
        menu_actions = ['actionNew', 'actionSave', 'actionOpen', 'actionSave_As', 'actionQuit']
        for action_name in menu_actions:
            if hasattr(self, action_name):
                action = getattr(self, action_name)
                debug_print(f"{action_name}: Found - {action.text()}")
            else:
                debug_print(f"{action_name}: NOT FOUND")
        
        debug_print("=== END DEBUG ===")

    def enterPlacementMode(self, component_type, icon_path=None):
        """Enter placement mode for the selected component and set cursor to its icon. Always reset cursor first."""
        from PyQt5.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()  # Prevent cursor stacking
        self.placement_mode = True
        self.placement_component_type = component_type
        self.placement_icon_path = icon_path
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                cursor = QCursor(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                QApplication.setOverrideCursor(cursor)
        self.showCanvasStatus(f"Selected: {component_type}. Click on canvas to place. Press ESC to cancel.")

    def exitPlacementMode(self):
        """Exit placement mode and restore default cursor."""
        self.placement_mode = False
        self.placement_component_type = None
        self.placement_icon_path = None
        QApplication.restoreOverrideCursor()
        self.showCanvasStatus("Ready")

    def extractTopology(self):
        """Delegate topology extraction to the file manager."""
        if hasattr(self, 'file_manager'):
            return self.file_manager.extractTopology()
        return [], []

    def markAsModified(self):
        """Mark the current topology as having unsaved changes."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.updateWindowTitle()
            debug_print("Topology marked as modified")
    
    def markAsSaved(self):
        """Mark the current topology as saved (no unsaved changes)."""
        if self.has_unsaved_changes:
            self.has_unsaved_changes = False
            self.updateWindowTitle()
            debug_print("Topology marked as saved")
    
    def updateWindowTitle(self):
        """Update the window title to reflect current file and modification status."""
        title = "NetFlux 5G Editor"
        
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title += f" - {filename}"
        elif self.is_template_loaded and self.template_name:
            title += f" - {self.template_name} (Template)"
        else:
            title += " - Untitled"
        
        if self.has_unsaved_changes:
            title += " *"
        
        self.setWindowTitle(title)

    def onTopologyChanged(self):
        """Called when the topology is changed (components added/removed/modified)."""
        self.markAsModified()

    def setupInitialUIStates(self):
        """Setup initial UI button states."""
        try:
            # Initially disable stop actions since nothing is running
            if hasattr(self, 'actionStop_All'):
                self.actionStop_All.setEnabled(False)
            if hasattr(self, 'actionStopAll'):
                self.actionStopAll.setEnabled(False)
            if hasattr(self, 'actionStop'):
                self.actionStop.setEnabled(False)
                
            # Enable run actions initially
            if hasattr(self, 'actionRun_All'):
                self.actionRun_All.setEnabled(True)
            if hasattr(self, 'actionRunAll'):
                self.actionRunAll.setEnabled(True)
            if hasattr(self, 'actionRun'):
                self.actionRun.setEnabled(True)
                
            # Setup tooltips for automation actions
            if hasattr(self, 'actionRun_All'):
                self.actionRun_All.setToolTip("Deploy and start all components: controller, database, monitoring, and topology (Ctrl+F5)")
            if hasattr(self, 'actionStop_All'):
                self.actionStop_All.setToolTip("Stop all running services and clean up Mininet (Ctrl+F6)")
            if hasattr(self, 'actionRun'):
                self.actionRun.setToolTip("Run the current topology in Mininet (F5)")
            if hasattr(self, 'actionStop'):
                self.actionStop.setToolTip("Stop and clean up the current topology with 'sudo mn -c' (F6)")
            if hasattr(self, 'actionRunAll'):
                self.actionRunAll.setToolTip("Deploy and run all 5G components with Docker")
            if hasattr(self, 'actionStopAll'):
                self.actionStopAll.setToolTip("Stop all running 5G services and Docker containers")
                
            debug_print("DEBUG: Initial UI states setup successfully")
        except Exception as e:
            error_print(f"ERROR: Failed to setup initial UI states: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(__file__), "gui", "Icon", "logoSquare.png")
    app.setWindowIcon(QIcon(icon_path))

    # Check for command line arguments
    show_welcome = "--no-welcome" not in sys.argv
    update_templates_only = "--update-templates" in sys.argv
    
    # If only updating templates, do that and exit
    if update_templates_only:
        debug_print("Running template update only...")
        updater = TemplateUpdater()
        if updater.update_all_templates():
            print("Template configuration paths updated successfully")
            sys.exit(0)
        else:
            print("Failed to update template configuration paths")
            sys.exit(1)
    
    window = NetFlux5GApp(show_welcome)
    
    if show_welcome:
        # Show welcome screen first
        if not window.welcome_manager.showWelcomeScreen():
            # If welcome screen fails, show main window directly
            window.show()
    else:
        # Show main window directly
        window.show()
    
    sys.exit(app.exec_())