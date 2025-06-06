from PyQt5.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QPushButton, 
                           QLabel, QSizePolicy, QSplitter, QToolButton, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QFont
from manager.debug import debug_print, error_print
import os

class ComponentPanelManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.component_widgets = []
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
        
    def setupComponentPanel(self):
        """Setup the component panel with clean, organized layout."""
        if not hasattr(self.main_window, 'ObjectFrame'):
            error_print("ERROR: ObjectFrame not found in UI")
            return
        
        # Clear the ObjectFrame and create a clean layout
        self.createCleanComponentLayout()
        
        # Initial layout arrangement
        self.arrangeComponentsInGrid()

    def createCleanComponentLayout(self):
        """Create a clean, organized layout for components."""
        # Clear existing layout
        if hasattr(self.main_window, 'ObjectFrame'):
            # Remove any existing widgets
            for child in self.main_window.ObjectFrame.findChildren(QWidget):
                child.deleteLater()
        
        # Create main container widget that fills the ObjectFrame
        self.responsive_widget = QWidget(self.main_window.ObjectFrame)
        
        # Create main vertical layout with proper margins
        self.main_vertical_layout = QVBoxLayout(self.responsive_widget)
        self.main_vertical_layout.setContentsMargins(5, 5, 5, 5)
        self.main_vertical_layout.setSpacing(3)
        
        # Create a titled frame for components
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel)
        title_frame.setLineWidth(1)
        
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(3, 3, 3, 3)
        title_layout.setSpacing(2)
        
        # Add title label
        title_label = QLabel("Network Components")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333; padding: 2px;")
        title_layout.addWidget(title_label)
        
        # Create grid layout for components
        self.component_grid_layout = QGridLayout()
        self.component_grid_layout.setContentsMargins(2, 2, 2, 2)
        self.component_grid_layout.setSpacing(3)
        self.component_grid_layout.setAlignment(Qt.AlignTop)
        
        # Add grid layout to title frame
        title_layout.addLayout(self.component_grid_layout)
        
        # Add title frame to main layout
        self.main_vertical_layout.addWidget(title_frame)
        self.main_vertical_layout.addStretch()
        
        # Create component widgets
        self.component_widgets = []
        for i, (button_name, label_name, display_text) in enumerate(self.component_data):
            widget_container = self.createCleanComponentWidget(button_name, label_name, display_text)
            self.component_widgets.append(widget_container)
        
        # Set size policy for responsive behavior
        self.responsive_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Position the responsive widget to fill the ObjectFrame
        self.updateResponsiveWidgetGeometry()

    def createCleanComponentWidget(self, button_name, label_name, display_text):
        """Create a clean, well-organized component widget."""
        # Create container frame with border
        container = QFrame()
        container.setFrameStyle(QFrame.Box)
        container.setLineWidth(1)
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border: 2px solid #0078d4;
                background-color: #fff;
            }
        """)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create vertical layout for button and label
        layout = QVBoxLayout(container)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        
        # Create button with consistent size
        button = QPushButton()
        button.setObjectName(button_name)
        button.setFixedSize(48, 48)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setStyleSheet("""
            QPushButton {
                border: 1px solid #999;
                border-radius: 4px;
                background-color: white;
                padding: 2px;
            }
            QPushButton:hover {
                border: 2px solid #0078d4;
                background-color: #e6f3ff;
            }
            QPushButton:pressed {
                background-color: #cce6ff;
            }
        """)
        
        # Set button icon with proper scaling
        icon_path = self.main_window.component_icon_map.get(button_name)
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to fit button with padding
            scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            button.setIcon(QIcon(scaled_pixmap))
            button.setIconSize(scaled_pixmap.size())
        
        # Connect button to drag function
        button.mousePressEvent = lambda event, comp_type=button_name: self.main_window.onComponentButtonPress(event, comp_type)
        
        # Create label with proper text wrapping
        label = QLabel(display_text)
        label.setObjectName(label_name)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setMinimumHeight(15)
        label.setMaximumHeight(25)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Set label font
        font = QFont()
        font.setPointSize(7)
        font.setBold(False)
        label.setFont(font)
        label.setStyleSheet("color: #333; background: transparent; border: none;")
        
        # Add widgets to layout
        layout.addWidget(button, 0, Qt.AlignCenter)
        layout.addWidget(label, 0, Qt.AlignCenter)
        
        # Store references
        container.button = button
        container.label = label
        container.button_name = button_name
        container.label_name = label_name
        container.display_text = display_text
        
        return container

    def arrangeComponentsInGrid(self):
        """Arrange components in a clean grid layout."""
        if not self.component_widgets or not hasattr(self, 'component_grid_layout'):
            return
        
        # Clear existing layout items
        while self.component_grid_layout.count():
            item = self.component_grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        
        # Calculate optimal grid layout
        panel_width = self.main_window.ObjectFrame.width()
        debug_print(f"DEBUG: Arranging components for panel width: {panel_width}")
        
        # Determine number of columns based on available width
        if panel_width >= 180:
            num_columns = 2
            widget_width = 85
        else:
            num_columns = 1
            widget_width = min(panel_width - 15, 120)
        
        # Set consistent widget heights
        widget_height = 80
        
        # Arrange widgets in grid
        for i, widget in enumerate(self.component_widgets):
            row = i // num_columns
            col = i % num_columns
            
            # Set consistent size for all widgets
            widget.setFixedSize(widget_width, widget_height)
            
            # Add to grid with proper alignment
            self.component_grid_layout.addWidget(widget, row, col, Qt.AlignCenter)
        
        # Update text based on available space
        self.updateComponentTextForLayout(panel_width)

    def updateComponentTextForLayout(self, panel_width):
        """Update component text based on available space."""
        if not self.component_widgets:
            return
        
        # Determine text style based on panel width
        if panel_width < 80:
            text_mode = 'minimal'
            font_size = 6
        elif panel_width < 140:
            text_mode = 'abbreviated'
            font_size = 7
        else:
            text_mode = 'full'
            font_size = 8
        
        # Text mappings for different modes
        text_mappings = {
            'full': {
                'Host': 'Host', 'STA': 'Station', 'UE': 'User Equipment', 'GNB': 'gNodeB',
                'DockerHost': 'Docker', 'AP': 'Access Point', 'VGcore': '5G Cores',
                'Router': 'Router', 'Switch': 'Switch', 'Controller': 'Controller'
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
        
        # Update each component's text
        for widget in self.component_widgets:
            text = text_mappings[text_mode].get(widget.button_name, widget.display_text)
            widget.label.setText(text)
            
            # Update font size
            font = widget.label.font()
            font.setPointSize(font_size)
            widget.label.setFont(font)

    def updateResponsiveWidgetGeometry(self):
        """Update the geometry of the responsive widget to fill ObjectFrame."""
        if hasattr(self, 'responsive_widget') and hasattr(self.main_window, 'ObjectFrame'):
            frame_rect = self.main_window.ObjectFrame.geometry()
            self.responsive_widget.setGeometry(0, 0, frame_rect.width(), frame_rect.height())

    def updateComponentButtonSizes(self):
        """Update component layout with debouncing."""
        if hasattr(self, '_update_timer'):
            self._update_timer.stop()
        else:
            self._update_timer = QTimer()
            self._update_timer.setSingleShot(True)
            self._update_timer.timeout.connect(self._performComponentUpdate)
    
        self._update_timer.start(100)

    def _performComponentUpdate(self):
        """Perform the actual component update."""
        self.updateResponsiveWidgetGeometry()
        self.arrangeComponentsInGrid()

    def toggleComponentPanel(self):
        """Toggle the visibility of the component panel."""
        if not hasattr(self.main_window, 'main_splitter') or not hasattr(self.main_window, 'ObjectFrame'):
            return
        
        if self.main_window.ObjectFrame.isVisible():
            self.main_window.ObjectFrame.hide()
            if hasattr(self.main_window, 'panel_toggle_button'):
                self.main_window.panel_toggle_button.setText("▶")
            self.main_window.status_manager.showCanvasStatus("Component panel hidden")
        else:
            self.main_window.ObjectFrame.show()
            if hasattr(self.main_window, 'panel_toggle_button'):
                self.main_window.panel_toggle_button.setText("◀")
            QTimer.singleShot(100, self.updateComponentButtonSizes)
            self.main_window.status_manager.showCanvasStatus("Component panel shown")

    def setupComponentPanelToggle(self):
        """Add a toggle button to show/hide the component panel."""
        self.main_window.panel_toggle_button = QToolButton()
        self.main_window.panel_toggle_button.setText("◀")
        self.main_window.panel_toggle_button.setToolTip("Toggle Component Panel")
        self.main_window.panel_toggle_button.setFixedSize(20, 30)
        self.main_window.panel_toggle_button.clicked.connect(self.toggleComponentPanel)
        
        if hasattr(self.main_window, 'toolBar'):
            self.main_window.toolBar.addWidget(self.main_window.panel_toggle_button)
