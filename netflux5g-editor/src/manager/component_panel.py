from PyQt5.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QPushButton, 
                           QLabel, QSizePolicy, QSplitter, QToolButton, QFrame,
                           QHBoxLayout, QScrollArea, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QPainter, QLinearGradient
from manager.debug import debug_print, error_print
import os

class ModernComponentWidget(QFrame):
    """A modern, stylish component widget with hover effects and animations."""
    
    clicked = pyqtSignal(str, str)  # Signal now emits component_type and icon_path
    
    def __init__(self, component_type, icon_path, display_text, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path
        self.display_text = display_text
        self.is_hovered = False
        
        self.setupUI()
        self.setupAnimations()
        self.setupShadowEffect()
        
    def setupUI(self):
        """Setup the UI components with modern styling."""
        self.setFixedSize(80, 95)
        self.setFrameStyle(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon container
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(48, 48)
        self.icon_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 24px;
            }
        """)
        
        # Icon label
        self.icon_label = QLabel(self.icon_container)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setGeometry(4, 4, 40, 40)
        
        # Set icon
        if self.icon_path and os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        
        # Text label
        self.text_label = QLabel(self.display_text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("border: none;")
        # Manually adjust the position by adding a top margin
        self.text_label.setContentsMargins(0, 8, 0, 0)
        
        # Set font
        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Medium)
        self.text_label.setFont(font)
        
        # Add to layout
        layout.addWidget(self.icon_container, 0, Qt.AlignCenter)
        layout.addWidget(self.text_label, 0, Qt.AlignCenter)
        
        # Setup shadow effect before initial styling
        self.setupShadowEffect()
        # Initial styling
        self.updateStyling(False)
        
    def setupAnimations(self):
        """Setup hover animations."""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def setupShadowEffect(self):
        """Add subtle shadow effect."""
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setXOffset(0)
        self.shadow_effect.setYOffset(2)
        self.shadow_effect.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self.shadow_effect)
        
    def updateStyling(self, hovered):
        """Update styling based on hover state."""
        if hovered:
            self.setStyleSheet("""
                ModernComponentWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 #f8f9ff, stop:1 #e6f2ff);
                    border: 2px solid #4a90e2;
                    border-radius: 12px;
                }
            """)
            self.icon_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 2px solid #4a90e2;
                    border-radius: 24px;
                }
            """)
            self.text_label.setStyleSheet("color: #2c5282; font-weight: 600;")
            
            # Update shadow for hover
            self.shadow_effect.setBlurRadius(12)
            self.shadow_effect.setYOffset(4)
            self.shadow_effect.setColor(QColor(74, 144, 226, 40))
            
        else:
            self.setStyleSheet("""
                ModernComponentWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 #ffffff, stop:1 #f8f9fa);
                    border: 1px solid #e9ecef;
                    border-radius: 12px;
                }
            """)
            self.icon_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 24px;
                }
            """)
            self.text_label.setStyleSheet("color: #495057;")
            
            # Reset shadow
            self.shadow_effect.setBlurRadius(8)
            self.shadow_effect.setYOffset(2)
            self.shadow_effect.setColor(QColor(0, 0, 0, 30))
    
    def enterEvent(self, event):
        """Handle mouse enter event."""
        self.is_hovered = True
        self.updateStyling(True)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.is_hovered = False
        self.updateStyling(False)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            # Emit clicked signal with component type and icon path (for click-to-place)
            self.clicked.emit(self.component_type, self.icon_path)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if self.is_hovered:
            self.updateStyling(True)
        else:
            self.updateStyling(False)
        super().mouseReleaseEvent(event)

class ComponentPanelManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.component_widgets = []
        self.component_data = [
            ('Host', 'host.png', 'Host', 'Basic network host'),
            ('STA', 'sta.png', 'Station', 'WiFi station device'),
            ('UE', 'ue.png', 'User Equipment', '5G user device'), 
            ('GNB', 'gNB.png', 'gNodeB', '5G base station'),
            ('DockerHost', 'docker.png', 'Docker', 'Containerized host'),
            ('AP', 'AP.png', 'Access Point', 'WiFi access point'),
            ('VGcore', '5G core.png', '5G Core', '5G core network'),
            ('Router', 'Router.png', 'Router', 'Network router'),
            ('Switch', 'switch.png', 'Switch', 'Network switch'),
            ('Controller', 'controller.png', 'Controller', 'SDN controller')
        ]
        
    def setupComponentPanel(self):
        """Setup the component panel with modern, beautiful styling."""
        if not hasattr(self.main_window, 'ObjectFrame'):
            error_print("ERROR: ObjectFrame not found in UI")
            return
        
        self.createModernComponentLayout()
        self.arrangeComponentsInGrid()

    def createModernComponentLayout(self):
        """Create a modern, beautiful layout for components."""
        # Clear existing layout
        if hasattr(self.main_window, 'ObjectFrame'):
            for child in self.main_window.ObjectFrame.findChildren(QWidget):
                child.deleteLater()
        
        # Create main scroll area for better organization
        self.scroll_area = QScrollArea(self.main_window.ObjectFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        
        # Style the scroll area
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f8f9fa;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 4px;
                border-radius: 2px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c757d;
            }
        """)
        
        # Create main container widget
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
        
        # Create main vertical layout
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)
        
        # Create header section
        self.createHeaderSection()
        
        # Create component sections
        self.createComponentSections()
        
        # Add stretch at the end
        self.main_layout.addStretch()
        
        # Set up the scroll area
        self.scroll_area.setWidget(self.container_widget)
        
        # Position scroll area to fill ObjectFrame
        self.updateScrollAreaGeometry()
        
    def createHeaderSection(self):
        """Create a beautiful header section with readable font sizes."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #4a90e2, stop:1 #357abd);
                border-radius: 8px;
                /* Remove padding here, let layout handle it */
            }
        """)
        # Increase height to fit font and margins
        header_frame.setMinimumHeight(50)
        header_frame.setMaximumHeight(100)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 12, 8, 12)  # More vertical space
        header_layout.setSpacing(4)
        
        # Title
        title_label = QLabel("Components")
        title_font = QFont("Segoe UI", 0, QFont.Bold)
        title_font.setPointSize(20)  # Larger for visibility
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Subtitle
        subtitle_label = QLabel("Click and Drop to Canvas")
        subtitle_font = QFont("Segoe UI", 0)
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: white; border: none;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch(1)  # Push content to top if extra space
        
        self.main_layout.addWidget(header_frame)

    def createComponentSections(self):
        """Create organized sections for different component types."""
        # Group components by category
        categories = {
            "Network Devices": [
                ('Host', 'host.png', 'Host'),
                ('Router', 'Router.png', 'Router'),
                ('Switch', 'switch.png', 'Switch'),
                ('Controller', 'controller.png', 'Controller')
            ],
            "Wireless & 5G": [
                ('STA', 'sta.png', 'Station'),
                ('AP', 'AP.png', 'Access Point'),
                ('UE', 'ue.png', 'User Equipment'),
                ('GNB', 'gNB.png', 'gNodeB'),
                ('VGcore', '5G core.png', '5G Core')
            ],
            "Containers": [
                ('DockerHost', 'docker.png', 'Docker')
            ]
        }
        
        self.component_widgets = []
        
        for category_name, components in categories.items():
            if components:  # Only create section if it has components
                self.createCategorySection(category_name, components)

    def createCategorySection(self, category_name, components):
        """Create a category section with components."""
        # Category header
        category_frame = QFrame()
        category_frame.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border-radius: 6px;
                margin: 0px 2px;
                /* Remove border if present */
            }
        """)
        category_frame.setFixedHeight(42)  # Increased height for better font fit
        
        category_layout = QHBoxLayout(category_frame)
        category_layout.setContentsMargins(12, 6, 12, 6)  # More vertical space
        category_layout.setAlignment(Qt.AlignCenter)
        
        category_label = QLabel(category_name)
        category_font = QFont("Segoe UI", 13, QFont.DemiBold)
        category_label.setFont(category_font)
        category_label.setStyleSheet("color: #495057;")
        
        category_layout.addWidget(category_label)
        category_layout.addStretch()
        
        self.main_layout.addWidget(category_frame)
        
        # Components grid for this category
        components_frame = QFrame()
        components_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        components_layout = QGridLayout(components_frame)
        components_layout.setContentsMargins(4, 4, 4, 8)
        components_layout.setSpacing(4)
        
        # Add components to grid
        for i, (comp_type, icon_file, display_text) in enumerate(components):
            row = i // 2
            col = i % 2
            
            # Get full icon path
            icon_path = self.main_window.component_icon_map.get(comp_type)
            
            # Create modern component widget
            component_widget = ModernComponentWidget(comp_type, icon_path, display_text)
            self.component_widgets.append(component_widget)
            
            # Connect click to placement mode (now expects two arguments)
            component_widget.clicked.connect(self.main_window.enterPlacementMode)
            
            components_layout.addWidget(component_widget, row, col, Qt.AlignCenter)
        
        self.main_layout.addWidget(components_frame)

    def arrangeComponentsInGrid(self):
        """Components are now arranged within their category sections."""
        # This method is kept for compatibility but logic moved to createCategorySection
        self.updateScrollAreaGeometry()

    def updateScrollAreaGeometry(self):
        """Update the geometry of the scroll area to fill ObjectFrame."""
        if hasattr(self, 'scroll_area') and hasattr(self.main_window, 'ObjectFrame'):
            frame_rect = self.main_window.ObjectFrame.geometry()
            self.scroll_area.setGeometry(0, 0, frame_rect.width(), frame_rect.height())

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
        self.updateScrollAreaGeometry()

    def toggleComponentPanel(self):
        """Toggle the visibility of the component panel with smooth animation."""
        if not hasattr(self.main_window, 'main_splitter') or not hasattr(self.main_window, 'ObjectFrame'):
            return
        
        if self.main_window.ObjectFrame.isVisible():
            # Hide panel
            self.main_window.ObjectFrame.hide()
            if hasattr(self.main_window, 'panel_toggle_button'):
                self.main_window.panel_toggle_button.setText("▶")
                self.main_window.panel_toggle_button.setToolTip("Show Component Panel")
            self.main_window.status_manager.showCanvasStatus("Component panel hidden")
        else:
            # Show panel
            self.main_window.ObjectFrame.show()
            if hasattr(self.main_window, 'panel_toggle_button'):
                self.main_window.panel_toggle_button.setText("◀")
                self.main_window.panel_toggle_button.setToolTip("Hide Component Panel")
            QTimer.singleShot(100, self.updateComponentButtonSizes)
            self.main_window.status_manager.showCanvasStatus("Component panel shown")

    def setupComponentPanelToggle(self):
        """Add a modern toggle button to show/hide the component panel."""
        self.main_window.panel_toggle_button = QToolButton()
        self.main_window.panel_toggle_button.setText("◀")
        self.main_window.panel_toggle_button.setToolTip("Hide Component Panel")
        self.main_window.panel_toggle_button.setFixedSize(24, 32)
        
        # Style the toggle button
        self.main_window.panel_toggle_button.setStyleSheet("""
            QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-weight: bold;
                color: #495057;
            }
            QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e9ecef, stop:1 #dee2e6);
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #dee2e6, stop:1 #ced4da);
            }
        """)
        
        self.main_window.panel_toggle_button.clicked.connect(self.toggleComponentPanel)
        
        if hasattr(self.main_window, 'toolBar'):
            self.main_window.toolBar.addWidget(self.main_window.panel_toggle_button)
        
        # Connect ModernComponentWidget clicks to placement mode
        for widget in self.component_widgets:
            widget.clicked.connect(self.main_window.enterPlacementMode)
