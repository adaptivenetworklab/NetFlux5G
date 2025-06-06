import os
import sys
import json
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QPushButton, QDesktopWidget, QFileDialog, QFrame, QMenuBar, QMenu, QAction, QSplitter
from PyQt5.QtCore import Qt, QPoint, QMimeData, QTimer, QDateTime
from PyQt5.QtGui import QDrag, QPixmap, QIcon, QFont, QKeySequence, QCursor
from PyQt5 import uic
from gui.canvas import Canvas, MovableLabel
from gui.toolbar import ToolbarFunctions
from gui.links import NetworkLink
from export.compose_export import DockerComposeExporter
from export.mininet_export import MininetExporter
from manager.debug_manager import DebugManager, debug_print, error_print, warning_print, set_debug_enabled, is_debug_enabled
from automation.automation_runner import AutomationRunner

# Load the UI file
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "ui", "Main_Window.ui")

class NetFlux5GApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load the UI file
        uic.loadUi(UI_FILE, self)

        # Set application icon for window and taskbar
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "Icon", "logoSquare.png")
        self.setWindowIcon(QIcon(icon_path))

        # Get screen geometry for better initial sizing
        screen = QDesktopWidget().screenGeometry()
        
        # Set initial size to 80% of screen size
        initial_width = int(screen.width() * 0.8)
        initial_height = int(screen.height() * 0.8)
        self.resize(initial_width, initial_height)
        
        # Set window properties for better responsiveness
        self.setMinimumSize(1000, 700)
        
        # Center the window on the screen
        self.move(
            (screen.width() - initial_width) // 2,
            (screen.height() - initial_height) // 2
        )

        # Initialize the toolbar functions
        self.toolbar_functions = ToolbarFunctions(self)
        
        # Initialize exporters
        self.docker_compose_exporter = DockerComposeExporter(self)
        self.mininet_exporter = MininetExporter(self)
        
        # Initialize automation runner
        self.automation_runner = AutomationRunner(self)

        # Initialize grid attribute
        self.show_grid = False
        
        # Initialize component mapping for icons FIRST
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
        
        # Add Debug menu after loading UI
        self.setupDebugMenu()
        
        # Set up the canvas first
        self.setupCanvas()
        
        # Setup component panel responsiveness
        self.setupComponentPanel()
        
        # Optional: Add toggle button
        self.setupComponentPanelToggle()
        
        # Initialize attributes
        self.current_link_source = None
        self.current_file = None
        self.current_tool = "pick"
        self.selected_component = None
        
        # Setup all connections
        self.setupConnections()

        # Debug menu actions
        self.debugMenuActions()

        # Show helpful shortcut information
        self.showShortcutHelp()
        
        # Debug canvas setup
        self.debugCanvasSetup()
        
        # Force initial geometry update
        QTimer.singleShot(100, self.updateCanvasGeometry)

    def updateCanvasGeometry(self):
        """Update canvas geometry based on current window size and ObjectFrame position."""
        try:
            if not hasattr(self, 'canvas_view'):
                warning_print("Canvas view not found during geometry update")
                return

            window_size = self.size()

            # Get ObjectFrame width from the actual widget
            object_frame_width = self.ObjectFrame.width() if hasattr(self, 'ObjectFrame') else 71

            menubar_height = self.menubar.height() if hasattr(self, 'menubar') else 26
            toolbar_height = self.toolBar.height() if hasattr(self, 'toolBar') else 30
            statusbar_height = self.statusbar.height() if hasattr(self, 'statusbar') else 23

            available_width = window_size.width() - object_frame_width - 10
            available_height = window_size.height() - menubar_height - toolbar_height - statusbar_height - 10

            available_width = max(available_width, 400)
            available_height = max(available_height, 300)

            canvas_x = object_frame_width + 5
            canvas_y = 5

            self.canvas_view.setGeometry(canvas_x, canvas_y, available_width, available_height)
            self.canvas_view.setVisible(True)
            self.canvas_view.show()

            if hasattr(self.canvas_view, 'updateSceneSize'):
                self.canvas_view.updateSceneSize()

            debug_print(f"Canvas geometry updated - x:{canvas_x}, y:{canvas_y}, w:{available_width}, h:{available_height}")
            debug_print(f"Canvas visible: {self.canvas_view.isVisible()}")
            debug_print(f"Canvas accepts drops: {self.canvas_view.acceptDrops()}")

        except Exception as e:
            error_print(f"Failed to update canvas geometry: {e}")
            traceback.print_exc()

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
            "Debug: Ctrl+Shift+D=Toggle Debug"
        )
        # Show for 5 seconds, then return to ready state
        self.showCanvasStatus(help_message, 5000)

    def setupCanvas(self):
        """Set up the canvas with proper error handling and dynamic sizing."""
        try:
            # Remove the existing horizontalLayoutWidget if it exists
            if hasattr(self, 'horizontalLayoutWidget'):
                self.horizontalLayoutWidget.deleteLater()
            
            # Create a splitter to allow resizing between component panel and canvas
            self.main_splitter = QSplitter(Qt.Horizontal)
            
            # Set the ObjectFrame as the left widget in the splitter
            if hasattr(self, 'ObjectFrame'):
                # Remove ObjectFrame from its current parent
                self.ObjectFrame.setParent(None)
                self.main_splitter.addWidget(self.ObjectFrame)
                
                # Set minimum and maximum widths for the component panel
                self.ObjectFrame.setMinimumWidth(45)   # Minimum width to keep icons visible with minimal text
                self.ObjectFrame.setMaximumWidth(150)  # Maximum width to prevent it from taking too much space
            
            # Create the canvas view
            self.canvas_view = Canvas(self)
            self.canvas_view.setMinimumWidth(400)  # Ensure canvas has minimum space
            self.main_splitter.addWidget(self.canvas_view)
            
            # Set splitter proportions - component panel takes less space
            self.main_splitter.setSizes([80, 800])  # Roughly 1:10 ratio
            
            # Set the splitter as the central widget
            self.setCentralWidget(self.main_splitter)
            
            # Allow the component panel to be collapsible (optional)
            self.main_splitter.setCollapsible(0, True)  # Component panel can be collapsed
            self.main_splitter.setCollapsible(1, False)  # Canvas cannot be collapsed
            
            # Connect splitter resize events to update component sizes
            self.main_splitter.splitterMoved.connect(self.onSplitterMoved)
            
            # Set up canvas status bar with delay to ensure canvas is ready
            QTimer.singleShot(200, self.setupCanvasStatusBar)
            
            debug_print("DEBUG: Canvas and component panel setup with dynamic resizing")
            
        except Exception as e:
            error_print(f"ERROR: Failed to setup canvas: {e}")
            # Fallback to original setup if there's an error
            self.canvas_view = Canvas(self)
            self.setCentralWidget(self.canvas_view)

    def onSplitterMoved(self, pos, index):
        """Handle splitter movement to update component panel layout."""
        debug_print(f"DEBUG: Splitter moved to position {pos}, index {index}")
        
        # Update component button and label sizes when splitter moves
        QTimer.singleShot(50, self.updateComponentButtonSizes)

    def closeEvent(self, event):
        """Handle application close event to clean up resources."""
        try:
            # Stop any running automation
            if hasattr(self, 'automation_runner'):
                self.automation_runner.stop_all()
            
            # Clean up status timer
            if hasattr(self, '_status_timer') and self._status_timer:
                self._status_timer.stop()
                self._status_timer = None
            
            # Clean up status label
            if hasattr(self, 'canvas_status_label') and self.canvas_status_label:
                try:
                    self.canvas_status_label.hide()
                    self.canvas_status_label.deleteLater()
                except RuntimeError:
                    pass  # Already deleted
                finally:
                    self.canvas_status_label = None
            
            debug_print("Application cleanup completed")
            
        except Exception as e:
            error_print(f"Error during application cleanup: {e}")
        
        # Accept the close event
        event.accept()

    def setupComponentPanel(self):
        """Setup the component panel with responsive layout."""
        if not hasattr(self, 'ObjectFrame'):
            error_print("ERROR: ObjectFrame not found in UI")
            return
        
        # Store original layout widget reference
        if hasattr(self, 'verticalLayoutWidget'):
            self.original_layout_widget = self.verticalLayoutWidget
            self.original_layout = self.verticalLayoutWidget.layout()
        
        # Create a new responsive layout system
        self.createResponsiveComponentLayout()
        
        # Update button and label sizes to be responsive
        self.updateComponentButtonSizes()

    def toggleComponentPanel(self):
        """Toggle the visibility of the component panel."""
        if not hasattr(self, 'main_splitter') or not hasattr(self, 'ObjectFrame'):
            return
        
        if self.ObjectFrame.isVisible():
            # Hide the panel
            self.ObjectFrame.hide()
            if hasattr(self, 'panel_toggle_button'):
                self.panel_toggle_button.setText("▶")  # Right arrow when panel is hidden
            self.showCanvasStatus("Component panel hidden")
        else:
            # Show the panel
            self.ObjectFrame.show()
            if hasattr(self, 'panel_toggle_button'):
                self.panel_toggle_button.setText("◀")  # Left arrow when panel is visible
            # Update sizes after showing
            QTimer.singleShot(100, self.updateComponentButtonSizes)
            self.showCanvasStatus("Component panel shown")

    def setupComponentPanelToggle(self):
        """Add a toggle button to show/hide the component panel."""
        from PyQt5.QtWidgets import QToolButton
        
        # Create toggle button
        self.panel_toggle_button = QToolButton()
        self.panel_toggle_button.setText("◀")  # Left arrow when panel is visible
        self.panel_toggle_button.setToolTip("Toggle Component Panel")
        self.panel_toggle_button.setFixedSize(20, 30)
        self.panel_toggle_button.clicked.connect(self.toggleComponentPanel)
        
        # Add to the main splitter or toolbar
        if hasattr(self, 'toolBar'):
            self.toolBar.addWidget(self.panel_toggle_button)

    def createResponsiveComponentLayout(self):
        """Create a responsive layout that switches between 1 and 2 columns."""
        from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy
        
        # Create main container widget
        self.responsive_widget = QWidget(self.ObjectFrame)
        self.responsive_widget.setGeometry(0, 0, self.ObjectFrame.width(), self.ObjectFrame.height())
        
        # Create main vertical layout
        self.main_vertical_layout = QVBoxLayout(self.responsive_widget)
        self.main_vertical_layout.setContentsMargins(2, 2, 2, 2)
        self.main_vertical_layout.setSpacing(2)
        
        # Create grid layout for components
        self.component_grid_layout = QGridLayout()
        self.component_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.component_grid_layout.setSpacing(2)
        
        # Add grid layout to main layout
        self.main_vertical_layout.addLayout(self.component_grid_layout)
        self.main_vertical_layout.addStretch()  # Add stretch to push components to top
        
        # Store component data for responsive layout
        self.component_data = [
            ('Host', 'label', 'Host'),
            ('STA', 'label_2', 'Station'), 
            ('UE', 'label_3', 'User Equipment'),
            ('GNB', 'label_4', 'gNodeB'),
            ('DockerHost', 'label_5', 'Docker'),
            ('AP', 'label_6', 'Access Point'),
            ('VGcore', 'label_7', '5G Cores'),
            ('Router', 'label_8', 'Legacy Router'),
            ('Switch', 'label_9', 'SDN Switch'),
            ('Controller', 'label_11', 'Controller')
        ]
        
        # Create component widgets
        self.component_widgets = []
        for i, (button_name, label_name, display_text) in enumerate(self.component_data):
            widget_container = self.createComponentWidget(button_name, label_name, display_text)
            self.component_widgets.append(widget_container)
        
        # Initial layout arrangement
        self.arrangeComponentsInGrid()
        
        # Set size policy for responsive behavior
        self.responsive_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def createComponentWidget(self, button_name, label_name, display_text):
        """Create a single component widget (button + label)."""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap
        
        # Create container widget
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create vertical layout for button and label
        layout = QVBoxLayout(container)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        
        # Create button
        button = QPushButton()
        button.setObjectName(button_name)
        button.setFixedSize(40, 40)  # Initial size, will be updated
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Set button icon if available
        icon_path = self.component_icon_map.get(button_name)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            button.setIcon(QIcon(scaled_pixmap))
        
        # Connect button to drag function
        button.mousePressEvent = lambda event, comp_type=button_name: self.onComponentButtonPress(event, comp_type)
        
        # Create label
        label = QLabel(display_text)
        label.setObjectName(label_name)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setMaximumHeight(40)  # Limit label height
    
        # Set font size
        font = label.font()
        font.setPointSize(7)
        label.setFont(font)
        
        # Add to layout
        layout.addWidget(button, 0, Qt.AlignCenter)
        layout.addWidget(label, 0, Qt.AlignCenter)
        
        # Store references
        container.button = button
        container.label = label
        container.button_name = button_name
        container.label_name = label_name
        container.display_text = display_text
        
        return container

    def onComponentButtonPress(self, event, component_type):
        """Handle component button press to start drag operation."""
        from PyQt5.QtCore import Qt
        
        if event.button() == Qt.LeftButton:
            debug_print(f"DEBUG: Component button pressed: {component_type}")
            self.startDrag(component_type)

    def arrangeComponentsInGrid(self):
        """Arrange components in grid based on available width."""
        if not hasattr(self, 'component_widgets') or not hasattr(self, 'component_grid_layout'):
            return
        
        # Clear existing layout items
        for i in reversed(range(self.component_grid_layout.count())):
            item = self.component_grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.component_grid_layout.removeWidget(widget)
        
        # Calculate number of columns based on panel width
        panel_width = self.ObjectFrame.width()
        debug_print(f"DEBUG: Arranging components for panel width: {panel_width}")
        
        # Determine number of columns
        if panel_width >= 120:  # Wide enough for 2 columns
            num_columns = 2
            debug_print("DEBUG: Using 2-column layout")
        else:  # Too narrow, use 1 column
            num_columns = 1
            debug_print("DEBUG: Using 1-column layout")
        
        # Arrange widgets in grid
        for i, widget in enumerate(self.component_widgets):
            row = i // num_columns
            col = i % num_columns
            self.component_grid_layout.addWidget(widget, row, col)
            debug_print(f"DEBUG: Placed {widget.button_name} at row {row}, col {col}")
        
        # Update component sizes
        self.updateComponentSizesForLayout(num_columns, panel_width)

    def updateComponentSizesForLayout(self, num_columns, panel_width):
        """Update component button and label sizes based on layout."""
        if not hasattr(self, 'component_widgets'):
            return
        
        # Calculate button size based on available space
        available_width = panel_width - 20  # Account for margins and spacing
        if num_columns == 2:
            button_width = max(30, min(45, (available_width - 10) // 2))  # Split width, account for spacing
        else:
            button_width = max(35, min(50, available_width - 10))
        
        button_size = button_width  # Keep square buttons
        
        # Calculate font size
        if panel_width < 60:
            font_size = 6
            text_mode = 'minimal'
        elif panel_width < 100:
            font_size = 7
            text_mode = 'abbreviated'
        else:
            font_size = 8
            text_mode = 'full'
        
        debug_print(f"DEBUG: Updating sizes - button: {button_size}x{button_size}, font: {font_size}, text: {text_mode}")
        
        # Text mappings for different modes
        text_mappings = {
            'full': {
                'Host': 'Host', 'STA': 'Station', 'UE': 'User Equipment', 'GNB': 'gNodeB',
                'DockerHost': 'Docker', 'AP': 'Access Point', 'VGcore': '5G Cores',
                'Router': 'Legacy Router', 'Switch': 'SDN Switch', 'Controller': 'Controller'
            },
            'abbreviated': {
                'Host': 'Host', 'STA': 'STA', 'UE': 'UE', 'GNB': 'gNB',
                'DockerHost': 'Docker', 'AP': 'AP', 'VGcore': '5GC',
                'Router': 'Router', 'Switch': 'Switch', 'Controller': 'Control'
            },
            'minimal': {
                'Host': 'H', 'STA': 'S', 'UE': 'U', 'GNB': 'G',
                'DockerHost': 'D', 'AP': 'A', 'VGcore': '5G',
                'Router': 'R', 'Switch': 'Sw', 'Controller': 'C'
            }
        }
        
        # Update each component
        for widget in self.component_widgets:
            # Update button size
            widget.button.setFixedSize(button_size, button_size)
            
            # Update button icon
            icon_path = self.component_icon_map.get(widget.button_name)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                icon_size = max(16, button_size - 8)  # Leave some margin
                scaled_pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                widget.button.setIcon(QIcon(scaled_pixmap))
            
            # Update label text and font
            text = text_mappings[text_mode].get(widget.button_name, widget.display_text)
            widget.label.setText(text)
            
            font = widget.label.font()
            font.setPointSize(font_size)
            widget.label.setFont(font)

    def updateComponentButtonSizes(self):
        """Update component button sizes and label fonts based on panel width."""
        if not hasattr(self, 'ObjectFrame'):
            return
        
        # Use the new responsive layout system
        self.arrangeComponentsInGrid()

    def setupCanvasStatusBar(self):
        """Create a custom status bar that only appears over the canvas area."""
        try:
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import QTimer
            
            # Remove existing status label if it exists
            if hasattr(self, 'canvas_status_label'):
                try:
                    if self.canvas_status_label and not self.canvas_status_label.isHidden():
                        self.canvas_status_label.hide()
                    self.canvas_status_label.deleteLater()
                except RuntimeError:
                    pass  # Object already deleted
                finally:
                    self.canvas_status_label = None
            
            # Cancel any pending status timers
            if hasattr(self, '_status_timer'):
                self._status_timer.stop()
                self._status_timer = None
            
            # Create new status label
            if hasattr(self, 'canvas_view') and self.canvas_view:
                self.canvas_status_label = QLabel(self.canvas_view)
                self.canvas_status_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 200);
                        border: 1px solid gray;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 11px;
                        color: black;
                    }
                """)
                self.canvas_status_label.hide()  # Initially hidden
                
                # Position the status label
                self.updateCanvasStatusBarPosition()
                
                debug_print("Canvas status bar created successfully")
            
        except Exception as e:
            error_print(f"Failed to setup canvas status bar: {e}")

    def updateCanvasStatusBarPosition(self):
        """Update the position of the canvas status bar."""
        try:
            if (hasattr(self, 'canvas_status_label') and 
                self.canvas_status_label and 
                hasattr(self, 'canvas_view') and 
                self.canvas_view):
                
                # Check if the object is still valid
                try:
                    # Test if we can access the object
                    _ = self.canvas_status_label.isVisible()
                except RuntimeError:
                    # Object has been deleted, recreate it
                    self.setupCanvasStatusBar()
                    return
                
                # Get canvas view geometry
                canvas_rect = self.canvas_view.geometry()
                
                # Position at bottom-left of canvas view
                x = 10
                y = canvas_rect.height() - 30
                
                self.canvas_status_label.move(x, y)
                
        except Exception as e:
            error_print(f"Failed to update canvas status bar position: {e}")

    def showCanvasStatus(self, message, timeout=0):
        """Show a status message on the canvas status bar with better error handling."""
        try:
            # Check if we have a valid status label
            if not hasattr(self, 'canvas_status_label') or not self.canvas_status_label:
                self.setupCanvasStatusBar()
            
            # Verify the object is still valid
            if self.canvas_status_label:
                try:
                    # Test access to the object
                    _ = self.canvas_status_label.isVisible()
                    
                    # Set the message
                    self.canvas_status_label.setText(message)
                    self.canvas_status_label.adjustSize()
                    self.canvas_status_label.show()
                    
                    # Cancel any existing timer
                    if hasattr(self, '_status_timer') and self._status_timer:
                        self._status_timer.stop()
                    
                    # Set up auto-hide timer if timeout is specified
                    if timeout > 0:
                        self._status_timer = QTimer()
                        self._status_timer.setSingleShot(True)
                        self._status_timer.timeout.connect(self._hideCanvasStatus)
                        self._status_timer.start(timeout)
                    
                    debug_print(f"Canvas status updated: {message}")
                    
                except RuntimeError:
                    # Object was deleted, recreate and try again
                    self.setupCanvasStatusBar()
                    if self.canvas_status_label:
                        self.canvas_status_label.setText(message)
                        self.canvas_status_label.adjustSize()
                        self.canvas_status_label.show()
            
        except Exception as e:
            error_print(f"Failed to show canvas status: {e}")
            # Fallback to debug print
            debug_print(f"STATUS: {message}", force=True)

    def _hideCanvasStatus(self):
        """Hide the canvas status label safely."""
        try:
            if (hasattr(self, 'canvas_status_label') and 
                self.canvas_status_label):
                try:
                    self.canvas_status_label.hide()
                    self.canvas_status_label.setText("Ready")
                except RuntimeError:
                    # Object was deleted, ignore
                    pass
        except Exception as e:
            error_print(f"Failed to hide canvas status: {e}")

    def resizeEvent(self, event):
        """Handle window resize events to update canvas and component layout size."""
        super().resizeEvent(event)
        try:
            # Update canvas geometry
            QTimer.singleShot(50, self.updateCanvasGeometry)
            
            # Update component panel layout
            QTimer.singleShot(100, self.updateComponentPanelLayout)
            
            # Update canvas status bar position
            if hasattr(self, 'canvas_status_label'):
                QTimer.singleShot(150, self.updateCanvasStatusBarPosition)
            
        except Exception as e:
            error_print(f"ERROR in resizeEvent: {e}")

    def updateComponentPanelLayout(self):
        """Update component panel layout after resize."""
        if hasattr(self, 'ObjectFrame') and hasattr(self, 'responsive_widget'):
            # Update responsive widget size
            self.responsive_widget.setGeometry(0, 0, self.ObjectFrame.width(), self.ObjectFrame.height())
            
            # Rearrange components
            self.arrangeComponentsInGrid()
            
            debug_print(f"DEBUG: Component panel layout updated for width: {self.ObjectFrame.width()}")

    def setupConnections(self):
        """Set up all signal connections."""
        try:
            # Menu connections
            if hasattr(self, 'actionNew'):
                self.actionNew.triggered.connect(self.newTopology)
            if hasattr(self, 'actionOpen'):
                self.actionOpen.triggered.connect(self.openTopology)
            if hasattr(self, 'actionSave'):
                self.actionSave.triggered.connect(self.saveTopology)
            if hasattr(self, 'actionSaveAs'):
                self.actionSaveAs.triggered.connect(self.saveTopologyAs)
            if hasattr(self, 'actionExportToDockerCompose'):
                self.actionExportToDockerCompose.triggered.connect(self.exportToDockerCompose)
            if hasattr(self, 'actionExportToMininet'):
                self.actionExportToMininet.triggered.connect(self.exportToMininet)

            # Component button connections - use the new responsive layout
            if hasattr(self, 'component_widgets'):
                for widget in self.component_widgets:
                    if hasattr(widget, 'button') and hasattr(widget, 'button_name'):
                        button = widget.button
                        component_type = widget.button_name
                        
                        # Create a proper closure to capture the component_type
                        def make_mouse_press_handler(comp_type):
                            def handle_mouse_press(event):
                                self.onComponentButtonPress(event, comp_type)
                            return handle_mouse_press
                        
                        # Apply the handler to the button
                        button.mousePressEvent = make_mouse_press_handler(component_type)
                        debug_print(f"DEBUG: Connected {component_type} button")
            
            # Fallback: try to connect original UI buttons if they exist
            component_buttons = [
                ('Host', 'Host'),
                ('STA', 'STA'), 
                ('UE', 'UE'),
                ('GNB', 'GNB'),
                ('DockerHost', 'DockerHost'),
                ('AP', 'AP'),
                ('VGcore', 'VGcore'),
                ('Router', 'Router'),
                ('Switch', 'Switch'),
                ('Controller', 'Controller')
            ]
            
            for button_name, component_type in component_buttons:
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    if hasattr(button, 'mousePressEvent'):
                        def make_fallback_handler(comp_type):
                            def handle_fallback_mouse_press(event):
                                self.onComponentButtonPress(event, comp_type)
                            return handle_fallback_mouse_press
                        
                        button.mousePressEvent = make_fallback_handler(component_type)
                        debug_print(f"DEBUG: Connected fallback {component_type} button")

            # Keyboard shortcuts
            if hasattr(self, 'actionPickTool'):
                self.actionPickTool.setShortcut(QKeySequence('P'))
            if hasattr(self, 'actionLinkTool'):
                self.actionLinkTool.setShortcut(QKeySequence('L'))
            if hasattr(self, 'actionDelete'):
                self.actionDelete.setShortcut(QKeySequence('D'))
            if hasattr(self, 'actionShowGrid'):
                self.actionShowGrid.setShortcut(QKeySequence('G'))

            debug_print("DEBUG: All connections setup successfully")
            
        except Exception as e:
            error_print(f"ERROR: Failed to setup connections: {e}")
            # Continue execution even if some connections fail

    def debugCanvasSetup(self):
        """Debug method to verify canvas setup."""
        debug_print("=== CANVAS DEBUG INFO ===")
        debug_print(f"Canvas view exists: {hasattr(self, 'canvas_view')}")
        if hasattr(self, 'canvas_view'):
            debug_print(f"Canvas view size: {self.canvas_view.size()}")
            debug_print(f"Canvas view geometry: {self.canvas_view.geometry()}")
            debug_print(f"Canvas view visible: {self.canvas_view.isVisible()}")
            debug_print(f"Canvas view parent: {self.canvas_view.parent()}")
            debug_print(f"Canvas accepts drops: {self.canvas_view.acceptDrops()}")
            debug_print(f"Canvas viewport size: {self.canvas_view.viewport().size()}")
            debug_print(f"Scene exists: {hasattr(self.canvas_view, 'scene')}")
            if hasattr(self.canvas_view, 'scene'):
                debug_print(f"Scene rect: {self.canvas_view.scene.sceneRect()}")
                debug_print(f"Scene items count: {len(self.canvas_view.scene.items())}")
            
            # Check if ObjectFrame overlaps with canvas
            if hasattr(self, 'ObjectFrame'):
                obj_frame_geom = self.ObjectFrame.geometry()
                canvas_geom = self.canvas_view.geometry()
                debug_print(f"ObjectFrame geometry: {obj_frame_geom}")
                debug_print(f"Canvas geometry: {canvas_geom}")
                overlap = obj_frame_geom.intersects(canvas_geom)
                debug_print(f"ObjectFrame and Canvas overlap: {overlap}")
                
        debug_print("=== END CANVAS DEBUG ===")

    def startDrag(self, component_type):
        """Start drag action for components with enhanced debugging."""
        debug_print(f"DEBUG: Starting drag for component: {component_type}")
        
        # Exit link mode if active
        self.exitLinkMode()
        
        # Verify canvas exists and is ready
        if not hasattr(self, 'canvas_view'):
            error_print("ERROR: canvas_view not found!")
            self.showCanvasStatus("ERROR: Canvas not initialized")
            return
            
        if not self.canvas_view.acceptDrops():
            warning_print("WARNING: Canvas does not accept drops, enabling...")
            self.canvas_view.setAcceptDrops(True)

        # Create a drag object with component information
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(component_type)  # Pass the component type as text
        drag.setMimeData(mime_data)
        
        debug_print(f"DEBUG: Created drag with mime data: '{component_type}'")
        
        # Set a pixmap for the drag appearance
        icon_path = self.component_icon_map.get(component_type)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(20, 20))  # Set the drag hotspot to the center
            debug_print(f"DEBUG: Set drag pixmap from {icon_path}")
        else:
            error_print(f"ERROR: Icon not found for {component_type} at {icon_path}")
            # Create a simple text pixmap as fallback
            fallback_pixmap = QPixmap(40, 40)
            fallback_pixmap.fill(Qt.lightGray)
            drag.setPixmap(fallback_pixmap)
        
        # Update status
        self.showCanvasStatus(f"Dragging {component_type}... Drop on canvas to place")
        
        # Execute the drag
        result = drag.exec_(Qt.CopyAction)
        debug_print(f"DEBUG: Drag operation completed with result: {result}")
        
        # Reset status
        self.showCanvasStatus("Ready")
        
    def startLinkMode(self, component_type):
        """Activate link mode."""
        debug_print("DEBUG: Starting link mode")
        
        # Reset any previous source selection
        self.current_link_source = None
        
        # Set current tool to link
        self.current_tool = "link"
        
        # Enable link mode in canvas
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(True)
            self.canvas_view.setCursor(Qt.CrossCursor)
        
        # Update status bar
        self.showCanvasStatus("Link mode activated. Click on source object, then destination object.")

    def createLink(self, source, destination):
        """Create a link between two objects."""
        debug_print(f"DEBUG: Creating link between {source} and {destination}")
        
        # Create a new NetworkLink with cable visualization
        link = NetworkLink(source, destination)
        
        # Add the link to the scene
        self.canvas_view.scene.addItem(link)
        
        # Update the status bar
        source_name = getattr(source, 'object_type', getattr(source, 'component_type', 'object'))
        dest_name = getattr(destination, 'object_type', getattr(destination, 'component_type', 'object'))
        self.showCanvasStatus(f"Link created between {source_name} and {dest_name}")
        
        # Update view
        self.canvas_view.viewport().update()
        
        return link

    def exitLinkMode(self):
        """Exit link mode."""
        debug_print("DEBUG: Exiting link mode")
        
        # Remove highlight from source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setHighlighted'):
            self.current_link_source.setHighlighted(False)
        
        # Re-enable dragging for source if one was selected
        if self.current_link_source and hasattr(self.current_link_source, 'setFlag'):
            from PyQt5.QtWidgets import QGraphicsItem
            self.current_link_source.setFlag(QGraphicsItem.ItemIsMovable, True)
            
        self.current_link_source = None
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(False)
            # Reset cursor to default
            self.canvas_view.setCursor(QCursor(Qt.ArrowCursor))
            
        self.showCanvasStatus("Pick tool selected")

    def updateAllLinks(self):
        """Update all links in the scene."""
        if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
            for item in self.canvas_view.scene.items():
                if isinstance(item, NetworkLink):
                    item.updatePosition()

    def enablePickTool(self):
        """Restore the pick tool state."""
        debug_print("DEBUG: Enabling pick tool")
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "pick"
        self.selected_component = None  # Reset selected component
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(False)
            # Reset cursor to default arrow
            self.canvas_view.setCursor(QCursor(Qt.ArrowCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        self.showCanvasStatus("Pick tool selected")

    def enableLinkTool(self):
        """Enable the Link Tool from toolbar."""
        debug_print("DEBUG: Enabling link tool from toolbar")
        
        # Exit other modes
        self.current_tool = "link"
        
        # Reset any previous source selection
        self.current_link_source = None
        
        # Enable link mode in canvas
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(True)
            # Set cursor to plus sign for link mode
            self.canvas_view.setCursor(QCursor(Qt.CrossCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        # Update status bar
        self.showCanvasStatus("Link Tool active. Click on source component, then destination component.")

    def enableDeleteTool(self):
        """Enable the Delete Tool."""
        debug_print("DEBUG: Enabling delete tool")
        self.exitLinkMode()  # Exit link mode if active
        self.current_tool = "delete"
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setLinkMode(False)
            # Set cursor to a different cursor for delete mode (optional)
            self.canvas_view.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Update toolbar button states
        self.updateToolbarButtonStates()
        
        self.showCanvasStatus("Delete Tool selected. Click on items to delete them.")

    def updateToolbarButtonStates(self):
        """Update the checked state of toolbar buttons based on current tool."""
        if hasattr(self, 'actionPickTool'):
            self.actionPickTool.setChecked(self.current_tool == "pick")
        if hasattr(self, 'actionLinkTool'):
            self.actionLinkTool.setChecked(self.current_tool == "link")
        if hasattr(self, 'actionDelete'):
            self.actionDelete.setChecked(self.current_tool == "delete")

    def addTextBox(self):
        self.current_tool = "text"
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.showCanvasStatus("Text box tool selected. Click on canvas to add text.")
        
    def addDrawSquare(self):
        self.current_tool = "square"
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setDragMode(QGraphicsView.NoDrag)
        self.showCanvasStatus("Square tool selected. Click and drag to draw a square.")

    def zoomIn(self):
        """Zoom in the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.zoomIn()
            self.showCanvasStatus(f"Zoomed in (Level: {self.canvas_view.zoom_level:.1f}x)")

    def zoomOut(self):
        """Zoom out the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.zoomOut()
            self.showCanvasStatus(f"Zoomed out (Level: {self.canvas_view.zoom_level:.1f}x)")

    def resetZoom(self):
        """Reset the zoom level of the canvas."""
        if hasattr(self, 'canvas_view'):
            self.canvas_view.resetZoom()
            self.showCanvasStatus("Zoom reset to default level")
        
    def toggleGrid(self):
        """Toggle the visibility of the grid on the canvas with debouncing."""
        debug_print(f"DEBUG: toggleGrid called, current state: {self.show_grid}")
        
        # Add a small delay to prevent double-triggering
        if hasattr(self, '_grid_toggle_timer'):
            if self._grid_toggle_timer.isActive():
                return
        
        if not hasattr(self, '_grid_toggle_timer'):
            self._grid_toggle_timer = QTimer()
            self._grid_toggle_timer.setSingleShot(True)
            self._grid_toggle_timer.timeout.connect(self._performGridToggle)
        
        # Start timer with 100ms delay
        self._grid_toggle_timer.start(100)

    def _performGridToggle(self):
        """Actually perform the grid toggle after debouncing."""
        self.show_grid = not self.show_grid
        debug_print(f"DEBUG: Grid state changed to: {self.show_grid}")
        
        if hasattr(self, 'canvas_view'):
            self.canvas_view.setShowGrid(self.show_grid)
            debug_print(f"DEBUG: Canvas setShowGrid called with: {self.show_grid}")
        
        status = "shown" if self.show_grid else "hidden"
        self.showCanvasStatus(f"Grid {status}")
        
        # Update the action's checked state to match
        if hasattr(self, 'actionShowGrid'):
            self.actionShowGrid.setChecked(self.show_grid)

    def newTopology(self):
        if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
            self.canvas_view.scene.clear()
        self.current_file = None
        self.showCanvasStatus("New topology created")
            
    def saveTopology(self):
        """Save the current topology. If no file is set, prompt for save location."""
        if self.current_file:
            # Save to existing file
            self.saveTopologyToFile(self.current_file)
        else:
            # Prompt for save location
            self.saveTopologyAs()
    
    def saveTopologyToFile(self, filename):
        """Save topology data to file."""
        try:
            # Extract current topology
            nodes, links = self.extractTopology()
            
            # Create topology data structure
            topology_data = {
                "version": "1.0",
                "type": "NetFlux5G_Topology",
                "metadata": {
                    "created_with": "NetFlux5G Editor",
                    "created_date": QDateTime.currentDateTime().toString(),
                    "canvas_size": {
                        "width": self.canvas_view.size().width() if hasattr(self, 'canvas_view') else 1161,
                        "height": self.canvas_view.size().height() if hasattr(self, 'canvas_view') else 1151
                    }
                },
                "nodes": nodes,
                "links": links
            }
            
            # Save to JSON file
            import json
            with open(filename, 'w') as f:
                json.dump(topology_data, f, indent=2, ensure_ascii=False)
                
            self.current_file = filename
            self.showCanvasStatus(f"Topology saved to {os.path.basename(filename)}")
            debug_print(f"DEBUG: Topology saved successfully to {filename}")
            debug_print(f"DEBUG: Saved {len(nodes)} nodes and {len(links)} links")
            
        except Exception as e:
            error_msg = f"Error saving topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        
    def saveTopologyAs(self):
        """Prompt user to save topology with a new filename."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            self.saveTopologyToFile(filename)
            
    def openTopology(self):
        """Open a topology file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Topology", 
            "", 
            "NetFlux5G Files (*.nf5g);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            self.loadTopologyFromFile(filename)
            
    def loadTopologyFromFile(self, filename):
        """Load topology from file."""
        try:
            import json
            
            with open(filename, 'r') as f:
                topology_data = json.load(f)
            
            # Validate the file format
            if not isinstance(topology_data, dict) or 'nodes' not in topology_data:
                raise ValueError("Invalid topology file format")
            
            # Clear current canvas
            if hasattr(self, 'canvas_view') and hasattr(self.canvas_view, 'scene'):
                self.canvas_view.scene.clear()
            
            # Load nodes
            nodes = topology_data.get('nodes', [])
            node_map = {}  # Map to store created components for linking
            
            for node_data in nodes:
                component = self.createComponentFromData(node_data)
                if component:
                    node_map[node_data['name']] = component
            
            # Load links
            links = topology_data.get('links', [])
            for link_data in links:
                self.createLinkFromData(link_data, node_map)
            
            # Update canvas
            if hasattr(self, 'canvas_view'):
                self.canvas_view.scene.update()
                self.canvas_view.viewport().update()
            
            # Set current file
            self.current_file = filename
            
            self.showCanvasStatus(f"Topology loaded: {len(nodes)} components, {len(links)} links")
            debug_print(f"DEBUG: Topology loaded successfully from {filename}")
            
        except Exception as e:
            error_msg = f"Error loading topology: {str(e)}"
            self.showCanvasStatus(error_msg)
            error_print(f"ERROR: {error_msg}")
            traceback.print_exc()

    def createComponentFromData(self, node_data):
        """Create a component from saved node data."""
        try:
            component_type = node_data.get('type')
            name = node_data.get('name')
            x = node_data.get('x', 0)
            y = node_data.get('y', 0)
            properties = node_data.get('properties', {})
            
            # Get the icon path for this component type
            icon_path = self.component_icon_map.get(component_type)
            if not icon_path or not os.path.exists(icon_path):
                warning_print(f"WARNING: Icon not found for {component_type}")
                return None
            
            # Create the component
            from .gui.components import NetworkComponent
            component = NetworkComponent(component_type, icon_path)
            
            # Set position
            component.setPosition(x, y)
            
            # Set display name
            component.display_name = name
            
            # Set properties (this will include all 5G configurations)
            component.setProperties(properties)
            
            # Add to scene
            self.canvas_view.scene.addItem(component)
            
            debug_print(f"DEBUG: Created component {name} of type {component_type} at ({x}, {y})")
            return component
            
        except Exception as e:
            error_print(f"ERROR: Failed to create component from data: {e}")
            return None

    def createLinkFromData(self, link_data, node_map):
        """Create a link from saved link data."""
        try:
            source_name = link_data.get('source')
            dest_name = link_data.get('destination')
            link_type = link_data.get('type', 'ethernet')
            properties = link_data.get('properties', {})
            
            # Find source and destination components
            source_component = node_map.get(source_name)
            dest_component = node_map.get(dest_name)
            
            if not source_component or not dest_component:
                warning_print(f"WARNING: Could not find components for link {source_name} -> {dest_name}")
                return None
            
            # Create the link
            from gui.links import NetworkLink
            link = NetworkLink(source_component, dest_component)
            link.link_type = link_type
            link.properties = properties
            
            # Add to scene
            self.canvas_view.scene.addItem(link)
            
            debug_print(f"DEBUG: Created link from {source_name} to {dest_name}")
            return link
            
        except Exception as e:
            error_print(f"ERROR: Failed to create link from data: {e}")
            return None

    def keyPressEvent(self, event):
        """Handle key press events with improved shortcuts."""
        
        # ESC key - return to pick tool
        if event.key() == Qt.Key_Escape:
            self.enablePickTool()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoomIn()
        elif event.key() == Qt.Key_Minus:
            self.zoomOut()
        elif event.key() == Qt.Key_0:
            self.resetZoom()
        elif event.key() == Qt.Key_G:
            self.toggleGrid()
        elif event.key() == Qt.Key_P:
            self.enablePickTool()
        elif event.key() == Qt.Key_D:
            if event.modifiers() & Qt.ShiftModifier and event.modifiers() & Qt.ControlModifier:
                # Ctrl+Shift+D for debug toggle
                self.toggleDebugMode()
            else:
                # Just D for delete tool
                self.enableDeleteTool()
        elif event.key() == Qt.Key_L: 
            self.enableLinkTool()
        elif event.key() == Qt.Key_T:
            self.addTextBox()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.saveTopology()
            elif event.key() == Qt.Key_N:
                self.newTopology()
            elif event.key() == Qt.Key_O:
                self.openTopology()
        # Add shortcuts for RunAll and StopAll
        elif event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            if hasattr(self, 'actionRunAll') and self.actionRunAll.isEnabled():
                self.runAllComponents()
        elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
            if hasattr(self, 'actionStopAll') and self.actionStopAll.isEnabled():
                self.stopAllComponents()
        
        # Call parent implementation for other keys
        super().keyPressEvent(event)

    def exportToDockerCompose(self):
        """Export 5G Core components to docker-compose.yaml and configuration files."""
        self.docker_compose_exporter.export_to_docker_compose()

    def exportToMininet(self):
        """Export the current topology to a Mininet script."""
        self.mininet_exporter.export_to_mininet()

    def extractTopology(self):
        """Extract all nodes and links from the canvas, including properties and positions."""
        nodes = []
        links = []
        
        if not hasattr(self, 'canvas_view') or not hasattr(self.canvas_view, 'scene'):
            return nodes, links
        
        for item in self.canvas_view.scene.items():
            if hasattr(item, 'component_type'):  # NetworkComponent
                # Extract component information including properties
                node_data = {
                    'name': getattr(item, 'display_name', item.component_type),
                    'type': item.component_type,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'properties': item.getProperties() if hasattr(item, 'getProperties') else {}
                }
                nodes.append(node_data)
                
            elif isinstance(item, NetworkLink):  # NetworkLink
                # Extract link information
                source_name = getattr(item.source_node, 'display_name', 
                                    getattr(item.source_node, 'component_type', 'Unknown'))
                dest_name = getattr(item.dest_node, 'display_name', 
                                  getattr(item.dest_node, 'component_type', 'Unknown'))
                
                link_data = {
                    'source': source_name,
                    'destination': dest_name,
                    'type': getattr(item, 'link_type', 'ethernet')
                }
                links.append(link_data)
        
        debug_print(f"DEBUG: Total extracted - {len(nodes)} nodes, {len(links)} links")
        return nodes, links
    
    def runAllComponents(self):
        """Run All - Deploy and start all components"""
        debug_print("DEBUG: RunAll triggered")
        
        # Check if already running
        if self.automation_runner.is_deployment_running():
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Already Running",
                "Deployment is already running. Do you want to stop it first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stopAllComponents()
                # Wait a moment for cleanup
                QTimer.singleShot(2000, self.automation_runner.run_all)
            return
        
        # Start the automation
        self.automation_runner.run_all()
        
        # Update UI state
        if hasattr(self, 'actionRunAll'):
            self.actionRunAll.setEnabled(False)
        if hasattr(self, 'actionStopAll'):
            self.actionStopAll.setEnabled(True)

    def stopAllComponents(self):
        """Stop All - Stop all running services"""
        debug_print("DEBUG: StopAll triggered")
        
        if not self.automation_runner.is_deployment_running():
            self.showCanvasStatus("No services are currently running")
            return
        
        # Show confirmation dialog
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Stop All Services",
            "Are you sure you want to stop all running services?\n\nThis will:\n- Stop Docker containers\n- Clean up Mininet\n- Terminate all processes",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.automation_runner.stop_all()
            
            # Update UI state
            if hasattr(self, 'actionRunAll'):
                self.actionRunAll.setEnabled(True)
            if hasattr(self, 'actionStopAll'):
                self.actionStopAll.setEnabled(False)    

    def onAutomationFinished(self, success, message):
        """Handle automation completion."""
        if success:
            from PyQt5.QtWidgets import QMessageBox
            
            deployment_info = self.automation_runner.get_deployment_info()
            info_text = f"Deployment completed successfully!\n\n"
            
            if deployment_info:
                info_text += f"Working directory: {deployment_info['export_dir']}\n"
                info_text += f"Docker Compose: {os.path.basename(deployment_info['docker_compose_file'])}\n"
                info_text += f"Mininet Script: {os.path.basename(deployment_info['mininet_script'])}\n\n"
            
            info_text += "Services are now running. Use 'Stop All' to terminate when done."
            
            QMessageBox.information(self, "Deployment Successful", info_text)
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Deployment Failed", f"Deployment failed:\n\n{message}")
            
            # Re-enable RunAll button
            if hasattr(self, 'actionRunAll'):
                self.actionRunAll.setEnabled(True)
            if hasattr(self, 'actionStopAll'):
                self.actionStopAll.setEnabled(False)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application-wide icon
    icon_path = os.path.join(os.path.dirname(__file__), "gui", "Icon", "logoSquare.png")
    app.setWindowIcon(QIcon(icon_path))

    window = NetFlux5GApp()
    window.show()
    
    # Debug window after showing
    debug_print("=== WINDOW SHOWN DEBUG ===")
    window.debugCanvasSetup()
    debug_print("=== END WINDOW DEBUG ===")
    
    sys.exit(app.exec_())