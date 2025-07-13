import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent
from PyQt5.QtCore import Qt, QRectF, QPoint, QPointF
from PyQt5.QtGui import QPixmap, QPen, QColor
from .widgets.Dialog import *
from manager.debug import debug_print, error_print, warning_print


class NetworkComponent(QGraphicsPixmapItem):
    """Network component (node) that can be placed on the canvas"""

    # Map component types to their respective dialog classes
    PROPERTIES_MAP = {
        "Host": HostPropertiesWindow,
        "STA": STAPropertiesWindow,
        "UE": UEPropertiesWindow,
        "GNB": GNBPropertiesWindow,
        "DockerHost": DockerHostPropertiesWindow,
        "AP": APPropertiesWindow,
        "VGcore": Component5GPropertiesWindow,
        "Controller": ControllerPropertiesWindow,
    }

    # Track the count of each component type
    component_counts = {
        "Host": 0, "STA": 0, "UE": 0, "GNB": 0, "DockerHost": 0,
        "AP": 0, "VGcore": 0, "Controller": 0, "Router": 0, "Switch": 0,
    }
    # Track available (unused) numbers for each component type
    available_numbers = {
        "Host": set(), "STA": set(), "UE": set(), "GNB": set(), "DockerHost": set(),
        "AP": set(), "VGcore": set(), "Controller": set(), "Router": set(), "Switch": set(),
    }
    copied_properties = None  # Class-level clipboard for properties
    
    def __init__(self, component_type, icon_path, parent=None, main_window=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path
        self.main_window = main_window  # Store reference to main window for change notifications

        # Assign the lowest available number or increment
        if NetworkComponent.available_numbers[component_type]:
            self.component_number = min(NetworkComponent.available_numbers[component_type])
            NetworkComponent.available_numbers[component_type].remove(self.component_number)
        else:
            NetworkComponent.component_counts[component_type] = NetworkComponent.component_counts.get(component_type, 0) + 1
            self.component_number = NetworkComponent.component_counts[component_type]
        
        # Set the display name (e.g., "Host #1")
        self.display_name = f"{component_type} #{self.component_number}"
    
        # Initialize properties dictionary to store configuration
        self.properties = {
            "name": self.display_name,
            "type": self.component_type,
            "x": 0,  # Initial x position
            "y": 0,  # Initial y position
        }
        
        # Set default range for wireless components (matching mininet-wifi defaults)
        if self.component_type == "AP":
            self.properties["AP_SignalRange"] = "100"  # Default AP range in meters (as string for dialog compatibility)
            self.properties["range"] = 100.0  # Also set as float for calculations
        elif self.component_type == "GNB":
            self.properties["GNB_Range"] = 300  # Default gNB range in meters (as int for SpinBox compatibility)
            self.properties["range"] = 300.0  # Also set as float for calculations
    
        # Set the pixmap for the item (increase icon size to 80x80)
        pixmap = QPixmap(self.icon_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
    
        # Make the item draggable and selectable
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        self.setFlag(QGraphicsPixmapItem.ItemSendsGeometryChanges)
        
        # Enable handling context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        # Coverage radius for wireless components - based on range property (meters)
        self.coverage_radius = self.calculateCoverageRadius()
        
        # Set appropriate Z-value
        if self.component_type in ["AP", "GNB"]:
            self.setZValue(5)  # Components with coverage circles slightly higher
        else:
            self.setZValue(10)  # Regular components on top

    def setPosition(self, x, y):
        """Set the component's position and update properties."""
        self.setPos(x, y)
        self.updatePositionProperties()

    def updatePositionProperties(self):
        """Update the position properties based on current position."""
        current_pos = self.pos()
        self.properties["x"] = current_pos.x()
        self.properties["y"] = current_pos.y()

    def setProperties(self, properties_dict):
        """Update the component's properties dictionary"""
        self.properties.update(properties_dict)
        
        # Update the component's name if it exists in properties
        if "name" in properties_dict:
            self.display_name = properties_dict["name"]
        
        # Update position if provided in properties
        if "x" in properties_dict and "y" in properties_dict:
            self.setPos(properties_dict["x"], properties_dict["y"])
        
        # Update coverage radius if range-related properties changed
        range_fields = ["AP_SignalRange", "GNB_Range", "range", "lineEdit_range"]
        if any(field in properties_dict for field in range_fields):
            self.updateCoverageRadius()

    def getProperties(self):
        """Get the current properties including updated position."""
        self.updatePositionProperties()  # Ensure position is current
        return self.properties.copy()

    def boundingRect(self):
        """Define the bounding rectangle for the component including text."""
        if self.component_type in ["AP", "GNB"]:
            radius = self.coverage_radius
            # Icon is now 80x80, text below, add extra padding
            return QRectF(-radius, -radius, radius * 2 + 80, radius * 2 + 80 + 30)
        else:
            # For all other components (including DockerHost and Controller)
            # Use consistent dimensions: icon + text + extra padding
            return QRectF(-10, -10, 100, 120)  # Icon 80x80 + text + margins
    
    def paint(self, painter, option, widget):
        """Draw the component."""
        painter.save()
        # Draw coverage circle for wireless components first (so it's behind the icon)
        if self.component_type in ["AP", "GNB"]:
            # Get current range to determine color intensity
            range_meters = self.getCurrentRange()
            
            # Color-code based on range (coverage area)
            # Larger range = more intense/warmer color
            if range_meters <= 50:
                # Short range: Blue-green
                color = QColor(0, 150, 100, 40)
                border_color = QColor(0, 100, 70, 120)
            elif range_meters <= 100:
                # Medium range: Blue
                color = QColor(0, 128, 255, 50)
                border_color = QColor(0, 100, 200, 140)
            elif range_meters <= 200:
                # Long range: Orange
                color = QColor(255, 150, 0, 60)
                border_color = QColor(200, 120, 0, 160)
            else:
                # Very long range: Red
                color = QColor(255, 50, 50, 70)
                border_color = QColor(200, 30, 30, 180)
            
            # Set up the fill and border for the coverage area
            painter.setBrush(color)
            painter.setPen(QPen(border_color, 2, Qt.DashLine))
            
            # Draw the coverage circle using QRectF to handle float values
            circle_rect = QRectF(
                40 - self.coverage_radius,  # x (centered for 80x80 icon)
                40 - self.coverage_radius,  # y
                self.coverage_radius * 2,
                self.coverage_radius * 2
            )
            painter.drawEllipse(circle_rect)
        painter.restore()
        painter.save()
        # Draw the component icon (now 80x80)
        if not self.pixmap().isNull():
            painter.drawPixmap(0, 0, 80, 80, self.pixmap())
    
        # Draw the component name below the icon with larger font
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSize(12)  # Larger font size
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text metrics
        text_width = painter.fontMetrics().width(self.display_name)
        text_height = painter.fontMetrics().height()
        
        # Clear the text area with white background to prevent traces
        text_rect = QRectF(
            (80 - text_width) / 2 - 4,  # x position with padding
            85,  # y position (below icon)
            text_width + 8,  # width with padding
            text_height + 8  # height with padding
        )
        
        # Fill text background with white to clear any traces
        painter.fillRect(text_rect, Qt.white)
        
        # Draw the text
        painter.drawText(
            int((80 - text_width) / 2),  # Center horizontally (ensure integer)
            85 + text_height,  # Position below the icon
            self.display_name
        )
    
        # Restore painter state
        painter.restore()
        painter.save()
        
        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(QRectF(-2, -2, 84, 110))  # Selection rectangle around icon and text
            
        # If highlighted, draw a red border
        if hasattr(self, 'highlighted') and self.highlighted:
            painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            painter.drawRect(QRectF(-2, -2, 84, 110))
            
        # Restore painter state
        painter.restore()

    def shape(self):
        """Return the shape of the item for collision detection and repainting.
        Only the icon+text area is selectable, not the coverage circle."""
        from PyQt5.QtGui import QPainterPath
        
        path = QPainterPath()
        # Only the icon and text area (icon: 80x80, text below)
        path.addRect(0, 0, 80, 110)  # 80x80 icon + text area
        
        return path

    def itemChange(self, change, value):
        """Handle position changes and update connected links."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Update position properties when position changes
            if hasattr(value, 'x') and hasattr(value, 'y'):
                self.properties["x"] = value.x()
                self.properties["y"] = value.y()
            
            # If we have connected links, update them
            if hasattr(self, 'connected_links'):
                for link in self.connected_links:
                    link.updatePosition()
        
        # For position changes, update the coverage area for AP/GNB components
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # Final position update after the move is complete
            self.updatePositionProperties()
            
            # Mark topology as modified when component is moved
            if self.main_window and hasattr(self.main_window, 'onTopologyChanged'):
                self.main_window.onTopologyChanged()
            
            # Force a comprehensive scene update to clear any traces
            if self.scene():
                # Update a larger area around the component to ensure text traces are cleared
                expanded_rect = self.sceneBoundingRect().adjusted(-20, -20, 20, 20)
                self.scene().update(expanded_rect)
            
            # Force a complete repaint for this item
            self.update()
            
            if self.component_type in ["AP", "GNB"]:
                # Additional update for coverage circles
                self.scene().update()
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = value
            debug_print(f"Component '{self.display_name}' moved to position: x={pos.x()}, y={pos.y()}")
        return super().itemChange(change, value)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """Handle right-click context menu events."""
        # Always reset dragging state and offset on context menu
        self.dragging = False
        self._drag_start_pos = None
        
        parent_widget = None
        scene = self.scene()
        if scene and scene.views():
            parent_widget = scene.views()[0]
        menu = QMenu(parent_widget)
        menu.setStyleSheet("""
            QMenu {
            background-color: #f0f0f0;
            border: 1px solid #000000;
            }
            QMenu::item:selected {
            background-color: #cccccc;
            }
        """)
        if self.component_type in ["Switch", "Router"]:
            menu.addAction("Delete", lambda: self._delete_and_cleanup())
        else:
            menu.addAction("Properties", self.openPropertiesDialog)
            menu.addSeparator()
            # Add component operations
            cut_action = menu.addAction("Cut")
            copy_action = menu.addAction("Copy")
            paste_action = menu.addAction("Paste")
            
            # Enable paste only if there's something in the clipboard
            clipboard_info = None
            if (hasattr(self, 'scene') and self.scene() and 
                hasattr(self.scene(), 'views') and self.scene().views() and
                hasattr(self.scene().views()[0], 'app_instance') and
                hasattr(self.scene().views()[0].app_instance, 'component_operations_manager')):
                clipboard_info = self.scene().views()[0].app_instance.component_operations_manager.getClipboardInfo()
            
            paste_action.setEnabled(clipboard_info is not None)
            
            # Connect actions
            cut_action.triggered.connect(self._cutComponent)
            copy_action.triggered.connect(self._copyComponent)
            paste_action.triggered.connect(self._pasteComponent)
            
            menu.addSeparator()
            menu.addAction("Delete", lambda: self._delete_and_cleanup())
            
            menu.addSeparator()
            # Add copy/paste properties actions
            copy_props_action = menu.addAction("Copy Properties")
            paste_props_action = menu.addAction("Paste Properties")
            paste_props_action.setEnabled(NetworkComponent.copied_properties is not None and (NetworkComponent.copied_properties.get('type') == self.component_type))
            copy_props_action.triggered.connect(self.copy_properties)
            paste_props_action.triggered.connect(self.paste_properties)
        menu.exec_(event.screenPos())
        event.accept()  # Prevent further propagation and duplicate menu
        # After menu closes, ensure dragging state and offset are reset
        self.dragging = False
        self._drag_start_pos = None
        # Explicitly release mouse and focus after context menu
        try:
            self.ungrabMouse()
        except Exception:
            pass
        try:
            self.clearFocus()
        except Exception:
            pass
        # Do NOT call super().contextMenuEvent(event) here to avoid duplicate menu

    def copy_properties(self):
        # Copy all properties except position and name/number
        props = self.getProperties().copy()
        for k in ["x", "y", "name"]:
            if k in props:
                del props[k]
        props['type'] = self.component_type  # Ensure type is present
        NetworkComponent.copied_properties = props
        # Show status and debug
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance'):
                view.app_instance.showCanvasStatus(f"Copied properties from {self.display_name}")
        debug_print(f"Copied properties from {self.display_name}: {props}")

    def paste_properties(self):
        # Only paste if types match
        props = NetworkComponent.copied_properties
        if props and props.get('type') == self.component_type:
            # Don't overwrite name/number/position
            for k, v in props.items():
                if k not in ["x", "y", "name", "type"]:
                    self.properties[k] = v
            # Optionally, update dialog if open
            if hasattr(self, 'dialog') and self.dialog is not None:
                self.dialog.loadProperties()
            # Optionally, visually indicate update
            self.update()
            # Show status and debug
            scene = self.scene()
            if scene and scene.views():
                view = scene.views()[0]
                if hasattr(view, 'app_instance'):
                    view.app_instance.showCanvasStatus(f"Pasted properties to {self.display_name}")
            debug_print(f"Pasted properties to {self.display_name}: {props}")
        else:
            debug_print(f"Paste failed: clipboard type {props.get('type') if props else None} does not match {self.component_type}")

    def _cutComponent(self):
        """Cut this component via the operations manager."""
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and hasattr(view.app_instance, 'component_operations_manager'):
                # Select this component first
                scene.clearSelection()
                self.setSelected(True)
                # Call cut operation
                view.app_instance.component_operations_manager.cutComponent()

    def _copyComponent(self):
        """Copy this component via the operations manager."""
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and hasattr(view.app_instance, 'component_operations_manager'):
                # Select this component first
                scene.clearSelection()
                self.setSelected(True)
                # Call copy operation
                view.app_instance.component_operations_manager.copyComponent()

    def _pasteComponent(self):
        """Paste component at this component's position via the operations manager."""
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and hasattr(view.app_instance, 'component_operations_manager'):
                # Paste at a slight offset from this component
                paste_pos = self.pos() + QPointF(60, 60)
                view.app_instance.component_operations_manager.pasteComponent(paste_pos)

    def _delete_and_cleanup(self):
        # Remove any connected links first (same as before)
        scene = self.scene()
        if hasattr(self, 'connected_links') and self.connected_links:
            links_to_remove = self.connected_links.copy()
            for link in links_to_remove:
                if hasattr(link, 'source_node') and hasattr(link.source_node, 'connected_links'):
                    if link in link.source_node.connected_links:
                        link.source_node.connected_links.remove(link)
                if hasattr(link, 'dest_node') and hasattr(link.dest_node, 'connected_links'):
                    if link in link.dest_node.connected_links:
                        link.dest_node.connected_links.remove(link)
                if link.scene():
                    scene.removeItem(link)
        # Free up the number for reuse
        self.deleteComponent()
        # Remove this component
        if scene:
            scene.removeItem(self)
        # Show status message if possible
        if scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance'):
                num_links = len(self.connected_links) if hasattr(self, 'connected_links') and self.connected_links else 0
                view.app_instance.showCanvasStatus(f"Deleted component and {num_links} connected link(s)")
                
        # Mark topology as modified using stored reference first, fallback to scene traversal
        if self.main_window and hasattr(self.main_window, 'onTopologyChanged'):
            self.main_window.onTopologyChanged()
        elif scene and scene.views():
            view = scene.views()[0]
            if hasattr(view, 'app_instance') and hasattr(view.app_instance, 'onTopologyChanged'):
                view.app_instance.onTopologyChanged()

    def deleteComponent(self):
        """Call this when the component is deleted to free up its number."""
        ctype = self.component_type
        cnum = self.component_number
        # Add this number back to available numbers for reuse
        NetworkComponent.available_numbers[ctype].add(cnum)
        # Optionally, decrement count if you want strictly sequential numbers
        # NetworkComponent.component_counts[ctype] = max(NetworkComponent.component_counts[ctype] - 1, 0)

    def openPropertiesDialog(self):
        """Open the properties dialog for the component."""
        dialog_class = self.PROPERTIES_MAP.get(self.component_type)
        if dialog_class:
            # Pass the component reference to the dialog
            dialog = dialog_class(label_text=self.display_name, parent=self.scene().views()[0], component=self)
            dialog.show()
            # After dialog closes, always reset dragging state and offset
            self.dragging = False
            self._drag_start_pos = None

    def setHighlighted(self, highlight=True):
        """Set the highlight state of this component"""
        self.highlighted = highlight
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            # Always calculate offset fresh on left press
            self._drag_start_pos = event.pos()
        else:
            self.dragging = False
            self._drag_start_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and (event.buttons() & Qt.LeftButton):
            # Calculate new position based on drag start
            if hasattr(self, '_drag_start_pos') and self._drag_start_pos is not None:
                new_pos = self.mapToParent(event.pos() - self._drag_start_pos)
                self.setPos(new_pos)
                if hasattr(self, 'updatePositionProperties'):
                    self.updatePositionProperties()
        else:
            self.dragging = False
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # Call the same cleanup as context menu delete
            self._delete_and_cleanup()
            return
        elif event.key() == Qt.Key_Escape:
            self.clearFocus()
        super().keyPressEvent(event)

    def calculateCoverageRadius(self):
        """Calculate coverage radius based on component range settings (in meters).
        
        This method aligns with mininet-wifi's plotGraph behavior, where coverage
        circles are drawn based on the 'range' property of wireless interfaces.
        """
        if self.component_type not in ["AP", "GNB"]:
            return 0
        
        # Get range from properties (in meters)
        range_meters = None
        range_fields = []
        
        if self.component_type == "AP":
            range_fields = ["AP_SignalRange", "range", "lineEdit_range"]
        elif self.component_type == "GNB":
            range_fields = ["GNB_Range", "range", "lineEdit_range"]
        
        # Try to get range value from properties
        for field in range_fields:
            if self.properties.get(field):
                try:
                    range_meters = float(str(self.properties[field]).strip())
                    if range_meters > 0:
                        break
                except (ValueError, TypeError):
                    continue
        
        # Use mininet-wifi defaults if not specified
        if range_meters is None or range_meters <= 0:
            if self.component_type == "AP":
                # Default AP range based on 802.11g mode (from mininet-wifi devices.py)
                range_meters = 100.0
            elif self.component_type == "GNB":
                # Default gNB range (5G base station typically has longer range)
                range_meters = 300.0
        
        # Convert meters to pixels for GUI display
        # Use a configurable scale: 1 meter = 2 pixels (reasonable for typical canvas sizes)
        # This ensures that the GUI scale is consistent with mininet-wifi's meter-based plots
        # You can adjust this scale factor to match your canvas size preferences
        meters_to_pixels = 2.0
        radius_pixels = range_meters * meters_to_pixels
        
        # Clamp radius to reasonable visual limits (but allow larger ranges than before)
        min_radius = 20.0   # Minimum visual radius (10m range)
        max_radius = 800.0  # Maximum visual radius (400m range)
        
        return max(min_radius, min(radius_pixels, max_radius))

    def updateCoverageRadius(self):
        """Update the coverage radius and trigger a repaint."""
        if self.component_type in ["AP", "GNB"]:
            old_radius = self.coverage_radius
            self.coverage_radius = self.calculateCoverageRadius()
            
            # Only update scene if radius changed significantly
            if abs(old_radius - self.coverage_radius) > 5.0:
                self.prepareGeometryChange()
                self.update()

    def getCurrentRange(self):
        """Get the current range setting for this component (in meters)."""
        if self.component_type not in ["AP", "GNB"]:
            return 0
        
        # Get range from properties
        range_fields = []
        if self.component_type == "AP":
            range_fields = ["AP_SignalRange", "range", "lineEdit_range"]
        elif self.component_type == "GNB":
            range_fields = ["GNB_Range", "range", "lineEdit_range"]
        
        # Try to get range value from properties
        for field in range_fields:
            if self.properties.get(field):
                try:
                    range_meters = float(str(self.properties[field]).strip())
                    if range_meters > 0:
                        return range_meters
                except (ValueError, TypeError):
                    continue
        
        # Return default range if not specified
        return 100.0 if self.component_type == "AP" else 300.0

    @staticmethod
    def scanAndInitializeNumbering(main_window=None):
        """
        Scan all existing components and properly initialize the numbering system.
        This ensures that component_counts and available_numbers are accurate.
        """
        # Reset the tracking systems
        NetworkComponent.component_counts = {
            "Host": 0, "STA": 0, "UE": 0, "GNB": 0, "DockerHost": 0,
            "AP": 0, "VGcore": 0, "Controller": 0, "Router": 0, "Switch": 0,
        }
        NetworkComponent.available_numbers = {
            "Host": set(), "STA": set(), "UE": set(), "GNB": set(), "DockerHost": set(),
            "AP": set(), "VGcore": set(), "Controller": set(), "Router": set(), "Switch": set(),
        }
        
        # Find the scene to scan components
        scene = None
        
        # Try to get scene from provided main_window
        if main_window and hasattr(main_window, 'canvas_view') and hasattr(main_window.canvas_view, 'scene'):
            scene = main_window.canvas_view.scene
        else:
            # Fallback: find a canvas widget with scene
            import PyQt5.QtWidgets as widgets
            app = widgets.QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    widget_scene = None
                    
                    # Handle different ways widgets can have a scene
                    if hasattr(widget, 'scene'):
                        if callable(widget.scene):
                            try:
                                widget_scene = widget.scene()
                            except:
                                continue
                        else:
                            widget_scene = widget.scene
                    
                    # Check if this is a canvas widget with an app_instance
                    if widget_scene and hasattr(widget, 'app_instance'):
                        scene = widget_scene
                        break
        
        if not scene:
            debug_print("No scene found for component scanning")
            return
            
        # Scan all components in the scene
        components_by_type = {}
        for item in scene.items():
            if isinstance(item, NetworkComponent):
                comp_type = item.component_type
                comp_number = getattr(item, 'component_number', 0)
                if comp_number > 0:
                    if comp_type not in components_by_type:
                        components_by_type[comp_type] = []
                    components_by_type[comp_type].append(comp_number)
        
        # Update counts and find available numbers
        for comp_type in NetworkComponent.component_counts:
            if comp_type in components_by_type:
                numbers = components_by_type[comp_type]
                max_number = max(numbers) if numbers else 0
                NetworkComponent.component_counts[comp_type] = max_number
                
                # Find gaps in the sequence (available numbers)
                used_numbers = set(numbers)
                for i in range(1, max_number + 1):
                    if i not in used_numbers:
                        NetworkComponent.available_numbers[comp_type].add(i)
            else:
                NetworkComponent.component_counts[comp_type] = 0
        
        debug_print(f"Scanned and initialized numbering:")
        debug_print(f"  Component counts: {NetworkComponent.component_counts}")
        debug_print(f"  Available numbers: {NetworkComponent.available_numbers}")