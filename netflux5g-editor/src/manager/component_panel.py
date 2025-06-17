from PyQt5.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QPushButton, 
                           QLabel, QSizePolicy, QSplitter, QToolButton, QFrame,
                           QHBoxLayout, QScrollArea, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QPainter, QLinearGradient
from manager.debug import debug_print, error_print
import os

class ModernComponentWidget(QFrame):
    """A modern, stylish component widget with hover effects and animations."""
    
    clicked = pyqtSignal(str)  # Signal emitted when clicked
    
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
        self.setFixedSize(75, 75)  # Ultra compact size
        self.setFrameStyle(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)  # Ultra minimal margins
        layout.setSpacing(1)  # Ultra minimal spacing
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon container
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(48, 48)  # Larger icon container
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
        self.icon_label.setGeometry(4, 4, 40, 40)  # Larger icon area
        
        # Set icon
        if self.icon_path and os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            scaled_pixmap = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Larger icon
            self.icon_label.setPixmap(scaled_pixmap)
        
        # Text label
        self.text_label = QLabel(self.display_text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(16)  # Ultra compact text area
        self.text_label.setMaximumHeight(20)  # Ultra compact text area
        
        # Set font - very small for ultra compact layout
        font = QFont("Segoe UI", 5)  # Very small font
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
                    border-radius: 10px;
                }
            """)
            self.icon_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 2px solid #4a90e2;
                    border-radius: 25px;
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
                    border-radius: 10px;
                }
            """)
            self.icon_container.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 2px solid #e0e0e0;
                    border-radius: 25px;
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
            # Add click animation
            self.setStyleSheet("""
                ModernComponentWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 #e6f2ff, stop:1 #cce7ff);
                    border: 2px solid #2c5282;
                    border-radius: 10px;
                }
            """)
            
            # Emit signal and delegate to parent
            self.clicked.emit(self.component_type)
            
            # Find main window and call drag handler
            parent = self.parent()
            while parent and not hasattr(parent, 'onComponentButtonPress'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'onComponentButtonPress'):
                parent.onComponentButtonPress(event, self.component_type)
                
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
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                border-radius: 4px;
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
        self.main_layout.setContentsMargins(1, 1, 1, 1)  # Ultra minimal margins
        self.main_layout.setSpacing(2)  # Ultra compact spacing
        
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
                border-radius: 6px;
            }
        """)
        header_frame.setMinimumHeight(35)  # Ultra compact header
        header_frame.setMaximumHeight(35)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(4, 2, 4, 2)  # Ultra minimal margins
        header_layout.setSpacing(0)  # No spacing
        
        # Title - ENLARGED as requested
        title_label = QLabel("Components")
        title_font = QFont("Segoe UI", 12, QFont.Bold)  # LARGER font for title
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel("Drag to canvas")
        subtitle_font = QFont("Segoe UI", 7)  # Readable font for subtitle
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 180);")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

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
        # Add ultra minimal spacing before each category (except first one)
        if hasattr(self, '_category_count'):
            self._category_count += 1
        else:
            self._category_count = 1
            
        if self._category_count > 1:
            # Add ultra minimal spacing between categories
            spacer_frame = QFrame()
            spacer_frame.setFixedHeight(1)  # Ultra minimal spacing
            spacer_frame.setStyleSheet("background-color: transparent;")
            self.main_layout.addWidget(spacer_frame)
        
        # Category header - ENLARGED as requested
        category_frame = QFrame()
        category_frame.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border-radius: 4px;
                margin: 1px 0px;
            }
        """)
        category_frame.setFixedHeight(24)  # Slightly taller for larger text
        
        category_layout = QHBoxLayout(category_frame)
        category_layout.setContentsMargins(6, 2, 6, 2)  # Minimal margins
        category_layout.setAlignment(Qt.AlignCenter)
        
        category_label = QLabel(category_name)
        category_font = QFont("Segoe UI", 9, QFont.Bold)  # LARGER and BOLD font for categories
        category_label.setFont(category_font)
        category_label.setStyleSheet("color: #495057;")
        
        category_layout.addWidget(category_label)
        
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
        components_layout.setContentsMargins(1, 1, 1, 2)  # Ultra minimal margins
        components_layout.setSpacing(2)  # Ultra minimal spacing between components
        
        # Use 2 column layout as requested
        for i, (comp_type, icon_file, display_text) in enumerate(components):
            row = i // 2
            col = i % 2
            
            # Get full icon path
            icon_path = self.main_window.component_icon_map.get(comp_type)
            
            # Create modern component widget
            component_widget = ModernComponentWidget(comp_type, icon_path, display_text)
            self.component_widgets.append(component_widget)
            
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
            # Optimized width for ultra compact layout
            min_width = max(170, frame_rect.width())  # Narrower panel for compact design
            self.scroll_area.setGeometry(0, 0, min_width, frame_rect.height())

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
            self.main_window.toolBar.addWidget(self.main_window.panel_toggle_button)
