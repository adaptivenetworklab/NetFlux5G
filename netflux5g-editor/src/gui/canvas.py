import os
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QGraphicsSceneContextMenuEvent, QMenu, QGraphicsItem
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRect 
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen, QCursor
from .widgets.Dialog import *
from .components import NetworkComponent

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
        if event.key() == Qt.Key_Escape:
            if hasattr(self, 'current_tool') and self.current_tool in ["delete", "link", "placement", "text", "square"]:
                self.enablePickTool()
        super().keyPressEvent(event)
    
    def contextMenuEvent(self, event):
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
        if self.size().width() > 0 and self.size().height() > 0:
            width = max(self.size().width() * 4, 4000)
            height = max(self.size().height() * 4, 4000)
            self.scene.setSceneRect(-width//2, -height//2, width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateSceneSize()

    def zoomIn(self, zoom_factor=1.2):
        self.zoom_level *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def zoomOut(self, zoom_factor=1.2):
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
                    
                    return
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
                
                position = self.mapToScene(event.pos())
                component = NetworkComponent(component_type, icon_path)
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    self.scene.removeItem(item)
        elif event.key() == Qt.Key_Escape:
            if hasattr(self, 'app_instance') and self.app_instance:
                if self.app_instance.current_tool in ["delete", "link", "placement", "text", "square"]:
                    self.app_instance.enablePickTool()
                    return
        
        super().keyPressEvent(event)

    def setLinkMode(self, enabled):
        self.link_mode = enabled

    def cleanupBrokenLinks(self):
        from .links import NetworkLink
        
        links_to_remove = []
        for item in self.scene.items():
            if isinstance(item, NetworkLink):
                if not item.source_item or not item.destination_item:
                    links_to_remove.append(item)
                elif item.source_item not in self.scene.items() or item.destination_item not in self.scene.items():
                    links_to_remove.append(item)
                    
        for link in links_to_remove:
            self.scene.removeItem(link)