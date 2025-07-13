import os
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QGraphicsSceneContextMenuEvent, QMenu, QGraphicsItem
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRectF, QTimer
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen, QCursor
from .widgets.Dialog import *
from .components import NetworkComponent
from manager.debug import debug_print, error_print, warning_print

class MovableLabel(QLabel):
    PROPERTIES_MAP = {
        "Host": HostPropertiesWindow,
        "STA": STAPropertiesWindow,
        "UE": UEPropertiesWindow,
        "GNB": GNBPropertiesWindow,
        "DockerHost": DockerHostPropertiesWindow,
        "AP": APPropertiesWindow,
        "VGcore": Component5GPropertiesWindow,
        "Controller": ControllerPropertiesWindow
    }

    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.ClickFocus)

        if icon and not icon.isNull():
            pixmap = icon.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
        else:
            self.setText(text)

        self.dragging = False
        self.offset = QPoint()
        self.dialog = None
        self.object_type = text

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent().app_instance.current_tool == "delete":
                self.close()
                return
            
            self.dragging = True
            self.offset = event.pos()
            self.setFocus()

    def mouseReleaseEvent(self, event):
        self.dragging = False


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # Find the parent canvas to handle deletion properly
            parent_widget = self.parent()
            while parent_widget and not isinstance(parent_widget, Canvas):
                parent_widget = parent_widget.parent()
            
            if parent_widget:
                # Let the canvas handle the deletion to ensure proper link cleanup
                parent_widget.keyPressEvent(event)
            else:
                # Fallback: just delete this label
                self.deleteLater()
                
        elif event.key() == Qt.Key_Escape:
            self.clearFocus()
        
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
        # Always reset dragging state and offset on context menu
        self.dragging = False
        self.offset = QPoint()
        menu = QMenu(self)
        if self.object_type in ["Switch", "Router"]:
            menu.addAction("Delete", self.close)
        else:
            menu.addAction("Properties", self.openPropertiesDialog)
            menu.addSeparator()
            menu.addAction("Delete", self.close)
        menu.exec_(event.globalPos())

    def openPropertiesDialog(self):
        dialog_class = self.PROPERTIES_MAP.get(self.object_type)
        if dialog_class:
            dialog = dialog_class(label_text=self.object_type, parent=self.parent(), component=self)
            dialog.show()
            
            # After dialog closes, always reset dragging state and offset
            self.dragging = False
            self.offset = QPoint()

    def setHighlighted(self, highlight=True):
        self.highlighted = highlight
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if hasattr(self, 'highlighted') and self.highlighted:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 3))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

class Canvas(QGraphicsView):
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_dialog = None

        self.updateSceneSize()
        self.setDragMode(QGraphicsView.NoDrag)
        self.setStyleSheet("background-color: white;")
        self.setAcceptDrops(True)

        self.show_grid = False
        self.zoom_level = 1.0
        self.link_mode = False
        
        self.is_panning = False
        self.pan_start_point = QPoint()
        self.last_pan_point = QPoint()
        
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def updateSceneSize(self):
        """Update scene size based on canvas size with better proportions."""
        try:
            canvas_width = self.viewport().width()
            canvas_height = self.viewport().height()
            
            debug_print(f"Updating scene size - canvas viewport: {canvas_width}x{canvas_height}")
            
            if canvas_width > 0 and canvas_height > 0:
                # Make scene larger than the visible area to allow panning
                scene_width = max(canvas_width * 2, 5000)  # At least 5000px wide
                scene_height = max(canvas_height * 2, 5000)  # At least 5000px high

                # Center the scene
                scene_rect = QRectF(-scene_width//2, -scene_height//2, scene_width, scene_height)
                self.scene.setSceneRect(scene_rect)
                
                debug_print(f"Scene size updated - {scene_width}x{scene_height}")
                debug_print(f"Scene rect: {scene_rect}")
                
            else:
                warning_print("Canvas viewport has zero or negative dimensions")
                
        except Exception as e:
            error_print(f"Failed to update scene size: {e}")

    def resizeEvent(self, event):
        """Handle canvas resize events."""
        super().resizeEvent(event)
        
        debug_print(f"Canvas resize event - new size: {event.size()}")
        
        # Update scene size when canvas is resized
        QTimer.singleShot(100, self.updateSceneSize)  # Small delay to ensure geometry is settled
        
        # Force a viewport update to ensure proper rendering
        self.viewport().update()

    def zoomIn(self, zoom_factor=0.5):
        self.zoom_level *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def zoomOut(self, zoom_factor=0.5):
        self.zoom_level /= zoom_factor
        self.scale(1 / zoom_factor, 1 / zoom_factor)

    def resetZoom(self):
        self.resetTransform()
        self.zoom_level = 1.0

    def setShowGrid(self, show):
        self.show_grid = show
        self.viewport().update()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self.show_grid:
            pen = QPen(Qt.lightGray)
            pen.setWidth(0)
            painter.setPen(pen)

            grid_size = 35
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            right = int(rect.right())
            bottom = int(rect.bottom())

            for x in range(left, right, grid_size):
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            for y in range(top, bottom, grid_size):
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        
        if modifiers & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoomIn(1.15)
                self.app_instance.showCanvasStatus(f"Zoomed in (Level: {self.zoom_level:.1f}x)")
            else:
                self.zoomOut(1.15)
                self.app_instance.showCanvasStatus(f"Zoomed out (Level: {self.zoom_level:.1f}x)")
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        # If in placement mode, place the component at the clicked position
        if hasattr(self.app_instance, 'placement_mode') and self.app_instance.placement_mode:
            component_type = self.app_instance.placement_component_type
            if component_type:
                pos = self.mapToScene(event.pos())
                self.placeComponent(component_type, pos)
                self.app_instance.exitPlacementMode()
                return  # Do not propagate event further

        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.pan_start_point = event.pos()
            self.last_pan_point = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            self.app_instance.showCanvasStatus("Panning mode - drag to navigate")
            event.accept()
            return

        if self.app_instance.current_tool == "delete":
            item = self.itemAt(event.pos())
            if item:
                self.scene.removeItem(item)
                self.app_instance.showCanvasStatus("Item deleted")
                self.cleanupBrokenLinks()

        if self.link_mode and event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            
            if item is not None and (isinstance(item, NetworkComponent) or hasattr(item, 'object_type')):
                if self.app_instance.current_link_source is None:
                    self.app_instance.current_link_source = item
                    
                    if hasattr(item, 'setHighlighted'):
                        item.setHighlighted(True)
                    
                    self.app_instance.showCanvasStatus(
                        f"Source selected: {item.object_type if hasattr(item, 'object_type') else 'component'} (highlighted in red) - now select destination"
                    )
                    
                    if hasattr(item, 'setFlag'):
                        item.setFlag(QGraphicsItem.ItemIsMovable, False)
                        
                    if hasattr(item, 'update'):
                        item.update()
                
                else:
                    source = self.app_instance.current_link_source
                    destination = item
                    
                    if source != destination:
                        if hasattr(source, 'setHighlighted'):
                            source.setHighlighted(False)
                        
                        self.app_instance.createLink(source, destination)
                
                    if hasattr(source, 'setFlag'):
                        source.setFlag(QGraphicsItem.ItemIsMovable, True)
                    
                    self.app_instance.current_link_source = None
                    self.app_instance.showCanvasStatus("Link created. Select next source or change tool.")
                    return
                    
        if self.current_dialog:
            self.current_dialog.close()
            self.current_dialog = None

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning and event.buttons() & Qt.MiddleButton:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            
            event.accept()
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.is_panning:
            self.is_panning = False
            
            # Restore appropriate cursor based on current tool
            if self.link_mode:
                self.setCursor(QCursor(Qt.CrossCursor))
            elif self.app_instance.current_tool == "delete":
                self.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
            
            total_delta = event.pos() - self.pan_start_point
            distance = (total_delta.x() ** 2 + total_delta.y() ** 2) ** 0.5
            self.app_instance.showCanvasStatus(f"Panning completed (moved {distance:.0f} pixels)")
            
            event.accept()
            return
            
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.scene.update()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            component_type = event.mimeData().text()

            if not hasattr(self.app_instance, 'component_icon_map'):
                event.ignore()
                return

            icon_path = self.app_instance.component_icon_map.get(component_type)
            
            if icon_path and os.path.exists(icon_path):
                from .components import NetworkComponent
                
                # Scan and initialize numbering before creating component
                NetworkComponent.scanAndInitializeNumbering(self.app_instance)
                
                position = self.mapToScene(event.pos())
                component = NetworkComponent(component_type, icon_path, main_window=self.app_instance)
                component.setPosition(position.x(), position.y())
                
                self.scene.addItem(component)
                self.scene.update()
                self.viewport().update()
                
                self.app_instance.showCanvasStatus(f"{component_type} added to canvas")
            else:
                self.app_instance.showCanvasStatus(f"ERROR: Icon not found for {component_type}")
                
            event.acceptProposedAction()
        else:
            event.ignore()

    def setCurrentDialog(self, dialog):
        if self.current_dialog and self.current_dialog.isVisible():
            self.current_dialog.close()
        self.current_dialog = dialog

    def setLinkMode(self, enabled):
        """Set link mode state for the canvas."""
        self.link_mode = enabled
        debug_print(f"DEBUG: Canvas link mode set to: {enabled}")
        
        if enabled:
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        
        # Update the canvas status if app instance is available
        if hasattr(self, 'app_instance') and self.app_instance:
            if enabled:
                self.app_instance.showCanvasStatus("Link mode enabled - Click source, then destination")
            else:
                self.app_instance.showCanvasStatus("Link mode disabled")

    def cleanupBrokenLinks(self):
        """Remove any links that reference deleted components."""
        try:
            from .links import NetworkLink
            
            items_to_remove = []
            
            for item in self.scene.items():
                if isinstance(item, NetworkLink):
                    # Check if either the source or destination node still exists in the scene
                    if (not item.source_node or item.source_node not in self.scene.items() or
                        not item.dest_node or item.dest_node not in self.scene.items()):
                        items_to_remove.append(item)
                        debug_print(f"DEBUG: Found broken link to remove: {item}")
            
            # Remove broken links
            for link in items_to_remove:
                self.scene.removeItem(link)
                debug_print(f"DEBUG: Removed broken link")
            
            if items_to_remove:
                debug_print(f"DEBUG: Cleaned up {len(items_to_remove)} broken links")
                self.scene.update()
                
        except Exception as e:
            error_print(f"ERROR: Failed to cleanup broken links: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    # Remove any connected links first if this is a NetworkComponent
                    if hasattr(item, 'connected_links') and item.connected_links:
                        links_to_remove = item.connected_links.copy()
                        for link in links_to_remove:
                            if hasattr(link, 'source_node') and hasattr(link.source_node, 'connected_links'):
                                if link in link.source_node.connected_links:
                                    link.source_node.connected_links.remove(link)
                            if hasattr(link, 'dest_node') and hasattr(link.dest_node, 'connected_links'):
                                if link in link.dest_node.connected_links:
                                    link.dest_node.connected_links.remove(link)
                            if link.scene():
                                self.scene.removeItem(link)
                    # If it's a NetworkComponent, use its cleanup method
                    from .components import NetworkComponent
                    if isinstance(item, NetworkComponent):
                        item._delete_and_cleanup()
                    else:
                        self.scene.removeItem(item)
                self.cleanupBrokenLinks()
                if hasattr(self, 'app_instance') and self.app_instance:
                    num_items = len(selected_items)
                    self.app_instance.showCanvasStatus(f"Deleted {num_items} selected item(s)")
        elif event.key() == Qt.Key_Escape:
            if hasattr(self, 'app_instance') and self.app_instance:
                if self.app_instance.current_tool in ["delete", "link", "placement", "text", "square"]:
                    self.app_instance.tool_manager.enablePickTool()
        super().keyPressEvent(event)

    def placeComponent(self, component_type, pos):
        """Create and place a component at the given scene position."""
        # Use the icon map from main window
        icon_path = self.app_instance.component_icon_map.get(component_type)
        from .components import NetworkComponent
        
        # Scan and initialize numbering before creating component
        NetworkComponent.scanAndInitializeNumbering(self.app_instance)
        
        component = NetworkComponent(component_type, icon_path, main_window=self.app_instance)
        component.setPos(pos)
        self.scene.addItem(component)
        debug_print(f"Placed component '{component_type}' at position: x={pos.x()}, y={pos.y()}")
        
        # Mark topology as modified
        if hasattr(self.app_instance, 'onTopologyChanged'):
            self.app_instance.onTopologyChanged()

    def contextMenuEvent(self, event):
        """Handle right-click context menu on canvas."""
        # Check if we clicked on an empty area (no items under the cursor)
        item_at_pos = self.itemAt(event.pos())
        
        if item_at_pos is None:
            # Empty area - show canvas context menu with paste option
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #f0f0f0;
                    border: 1px solid #000000;
                }
                QMenu::item:selected {
                    background-color: #cccccc;
                }
            """)
            
            # Check if there's something to paste
            has_clipboard_content = False
            if (hasattr(self, 'app_instance') and 
                hasattr(self.app_instance, 'component_operations_manager')):
                has_clipboard_content = self.app_instance.component_operations_manager.hasClipboardContent()
            
            paste_action = menu.addAction("Paste")
            paste_action.setEnabled(has_clipboard_content)
            
            if has_clipboard_content:
                clipboard_info = self.app_instance.component_operations_manager.getClipboardInfo()
                if clipboard_info:
                    paste_action.setText(f"Paste {clipboard_info['type']}")
            
            # Connect the paste action
            paste_action.triggered.connect(lambda: self._pasteAtPosition(event.pos()))
            
            # Show the menu
            menu.exec_(event.globalPos())
        else:
            # Item was clicked - let the item handle its own context menu
            super().contextMenuEvent(event)

    def _pasteAtPosition(self, view_pos):
        """Paste component at the specified view position."""
        if (hasattr(self, 'app_instance') and 
            hasattr(self.app_instance, 'component_operations_manager')):
            # Convert view position to scene position
            scene_pos = self.mapToScene(view_pos)
            self.app_instance.component_operations_manager.pasteComponent(scene_pos)