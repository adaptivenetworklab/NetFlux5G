from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QCursor
from PyQt5 import uic
from manager.debug import debug_print, error_print, warning_print
import os
import webbrowser 

class WelcomeScreenManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.welcome_window = None
        
    def showWelcomeScreen(self):
        """Show the welcome screen before the main application."""
        try:
            self.welcome_window = WelcomeScreen(self.main_window)
            self.welcome_window.action_selected.connect(self.handleWelcomeAction)
            self.welcome_window.show()
            debug_print("Welcome screen displayed")
            return True
        except Exception as e:
            error_print(f"Failed to show welcome screen: {e}")
            return False
    
    def handleWelcomeAction(self, action, data=None):
        """Handle actions from the welcome screen."""
        debug_print(f"Welcome action received: {action}")
        
        if action == "new_topology":
            self.welcome_window.close()
            self.main_window.show()
            self.main_window.file_manager.newTopology()
            
        elif action == "open_topology":
            self.welcome_window.close()
            self.main_window.show()
            self.main_window.file_manager.openTopology()
            
        elif action == "load_example":
            self.welcome_window.close()
            self.main_window.show()
            self.loadExampleTopology(data)
        
        elif action == "open_link":  
            self.openWebLink(data) 
            
        elif action == "close":
            self.welcome_window.close()
            # Don't show main window, just exit

    def openWebLink(self, url):
        """Open web link in default browser."""
        try:
            if url:
                webbrowser.open(url)
                debug_print(f"Opened web link: {url}")
        except Exception as e:
            error_print(f"Failed to open web link: {e}")
            
    def loadExampleTopology(self, example_name):
        """Load a specific example topology."""
        try:
            # Map example names to template names
            example_mapping = {
                "basic_gnb_core": "basic_5g_topology",
                "multi_ran": "multi_ran_deployment", 
                "sdn_deployment": "sdn_topology"
            }
            
            template_name = example_mapping.get(example_name, example_name)
            
            if self.main_window.file_manager.loadExampleTemplate(template_name):
                self.main_window.status_manager.showCanvasStatus(f"Loaded example: {example_name}")
            else:
                warning_print(f"Failed to load example: {example_name}")
                
        except Exception as e:
            error_print(f"Failed to load example topology: {e}")
            self.main_window.status_manager.showCanvasStatus(f"Error loading example: {str(e)}")

class WelcomeScreen(QMainWindow):
    """Welcome screen window that loads the UI file and handles interactions."""
    
    action_selected = pyqtSignal(str, str)  # action, data
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        
        # Load the welcome screen UI
        ui_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "gui", "ui", "Welcome_Screen.ui"
        )
        
        try:
            uic.loadUi(ui_file, self)
            self.setupWelcomeScreen()
        except Exception as e:
            error_print(f"Failed to load welcome screen UI: {e}")
            self.setupFallbackWelcomeScreen()
    
    def setupWelcomeScreen(self):
        """Setup the welcome screen with proper styling and connections."""
        # Set window properties
        self.setWindowTitle("NetFlux 5G Editor - Welcome")
        self.setFixedSize(870, 460)
        
        # Set application icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "gui", "Icon", "logoSquare.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Setup click handlers for UI elements
        self.setupClickHandlers()
        
        # Apply modern styling
        self.applyModernStyling()
        
        # Center the window
        self.centerWindow()
        
    def setupClickHandlers(self):
        """Setup click handlers for interactive elements."""
        # Make labels clickable by installing event filters
        clickable_labels = {
            'NewTopo': ('new_topology', None),
            'OpenTopo': ('open_topology', None),
            'Examples_1': ('load_example', 'basic_gnb_core'),
            'Examples_2': ('load_example', 'multi_ran'),
            'Examples_3': ('load_example', 'sdn_deployment'),
            'linkRepo': ('open_link', 'https://github.com/adaptivenetworklab/Riset_23-24_SDN/tree/netflux5g'),
        }
        
        for label_name, (action, data) in clickable_labels.items():
            if hasattr(self, label_name):
                label = getattr(self, label_name)
                label.setCursor(QCursor(Qt.PointingHandCursor))
                label.mousePressEvent = lambda event, a=action, d=data: self.handleLabelClick(a, d)
                
                # Add hover effect
                label.enterEvent = lambda event, l=label: self.addHoverEffect(l, True)
                label.leaveEvent = lambda event, l=label: self.addHoverEffect(l, False)
    
    def handleLabelClick(self, action, data):
        """Handle label clicks."""
        debug_print(f"Label clicked: {action}, {data}")
        self.action_selected.emit(action, data)
    
    def addHoverEffect(self, label, hover):
        """Add hover effect to labels."""
        if hover:
            label.setStyleSheet("QLabel { color: #0078d4; }")
        else:
            label.setStyleSheet("QLabel { color: black; }")
    
    def applyModernStyling(self):
        """Apply modern styling to the welcome screen."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #333333;
            }
            QLabel[text="Get Started"] {
                color: #0078d4;
                font-weight: bold;
            }
        """)
    
    def centerWindow(self):
        """Center the window on the screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def setupFallbackWelcomeScreen(self):
        """Setup a fallback welcome screen if UI file loading fails."""
        self.setWindowTitle("NetFlux 5G Editor - Welcome")
        self.setFixedSize(600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("NetFlux 5G Editor")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Visual simulation and planning tool for 5G network topologies")
        desc.setFont(QFont("Arial", 12))
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("New Topology")
        new_btn.clicked.connect(lambda: self.action_selected.emit("new_topology", None))
        button_layout.addWidget(new_btn)
        
        open_btn = QPushButton("Open Topology")
        open_btn.clicked.connect(lambda: self.action_selected.emit("open_topology", None))
        button_layout.addWidget(open_btn)
        
        layout.addLayout(button_layout)
        
        self.centerWindow()
    
    def closeEvent(self, event):
        """Handle close event."""
        self.action_selected.emit("close", None)
        event.accept()