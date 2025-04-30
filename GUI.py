import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                             QGraphicsItem, QGraphicsPixmapItem, QLabel, QVBoxLayout, QWidget,
                             QGraphicsTextItem, QMenu, QAction, QDialog, QFormLayout, QLineEdit, 
                             QDialogButtonBox, QGraphicsRectItem)
from PyQt5.QtCore import Qt, QPoint, QMimeData, QRect, QRectF, QPointF
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen, QBrush, QColor, QCursor
from PyQt5 import uic

class DraggableButton:
    """Helper class to make QPushButtons draggable"""
    def __init__(self, button, device_type, icon_path):
        self.button = button
        self.device_type = device_type
        self.icon_path = icon_path
        self.button.mousePressEvent = self.mousePressEvent
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startDrag(event)
            
    def startDrag(self, event):
        # Create mime data with device type information
        mime_data = QMimeData()
        mime_data.setText(self.device_type)
        
        # Create drag object with the button's icon
        drag = QDrag(self.button)
        drag.setMimeData(mime_data)
        
        # Set the pixmap for drag visual feedback
        pixmap = QPixmap(self.icon_path)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        
        # Execute the drag
        drag.exec_(Qt.CopyAction)

class NetworkDevice(QGraphicsPixmapItem):
    """Class for network device items that can be placed on the canvas"""
    def __init__(self, device_type, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.device_type = device_type
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Default properties
        self.properties = {
            "name": f"{device_type}_{id(self)}",
            "ip": "",
            "mac": "",
            "description": ""
        }
        
        # Store connected links
        self.links = []
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu()
        
        configure_action = menu.addAction("Configure")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(event.screenPos())
        
        if action == configure_action:
            self.configure()
        elif action == delete_action:
            # Remove links connected to this device
            for link in self.links[:]:  # Create a copy of the list to iterate
                self.scene().removeItem(link)
                # Remove link from connected devices
                for device in link.devices:
                    if device != self and device in link.devices:
                        device.links.remove(link)
            self.links.clear()
            self.scene().removeItem(self)
    
    def configure(self):
        """Open configuration dialog"""
        dialog = QDialog()
        dialog.setWindowTitle(f"Configure {self.device_type}")
        
        layout = QFormLayout()
        
        name_edit = QLineEdit(self.properties["name"])
        ip_edit = QLineEdit(self.properties["ip"])
        mac_edit = QLineEdit(self.properties["mac"])
        desc_edit = QLineEdit(self.properties["description"])
        
        layout.addRow("Name:", name_edit)
        layout.addRow("IP Address:", ip_edit)
        layout.addRow("MAC Address:", mac_edit)
        layout.addRow("Description:", desc_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.properties["name"] = name_edit.text()
            self.properties["ip"] = ip_edit.text()
            self.properties["mac"] = mac_edit.text()
            self.properties["description"] = desc_edit.text()
            
            # Update label if exists
            for child in self.childItems():
                if isinstance(child, QGraphicsTextItem):
                    child.setPlainText(self.properties["name"])
                    break
            
            # If no label exists, create one
            if not any(isinstance(child, QGraphicsTextItem) for child in self.childItems()):
                label = QGraphicsTextItem(self.properties["name"], self)
                label.setPos(0, self.pixmap().height())
                label.setTextWidth(self.pixmap().width())
                label.setDefaultTextColor(Qt.black)

class LinkItem(QGraphicsRectItem):
    """Class for network links between devices"""
    def __init__(self, source_device, parent=None):
        super().__init__(parent)
        self.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        self.source_device = source_device
        self.target_device = None
        self.devices = []  # Will store both devices when link is complete
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Initialize line with source position
        source_pos = self.source_device.scenePos() + QPointF(self.source_device.pixmap().width()/2, 
                                                           self.source_device.pixmap().height()/2)
        self.setRect(QRectF(source_pos, QPointF(source_pos.x() + 1, source_pos.y() + 1)))
        
    def updatePosition(self, target_pos=None):
        """Update the line's position based on connected devices"""
        if not target_pos and not self.target_device:
            return
            
        start_pos = self.source_device.scenePos() + QPointF(self.source_device.pixmap().width()/2, 
                                                          self.source_device.pixmap().height()/2)
        
        end_pos = target_pos if target_pos else (self.target_device.scenePos() + 
                                                QPointF(self.target_device.pixmap().width()/2, 
                                                       self.target_device.pixmap().height()/2))
        
        # Update the line
        self.setRect(QRectF(start_pos, end_pos))
    
    def paint(self, painter, option, widget):
        """Custom paint to draw a line instead of a rectangle"""
        painter.setPen(self.pen())
        line_start = self.rect().topLeft()
        line_end = self.rect().bottomRight()
        painter.drawLine(line_start, line_end)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec_(event.screenPos())
        
        if action == delete_action:
            # Remove link from connected devices
            for device in self.devices:
                if self in device.links:
                    device.links.remove(self)
            
            # Remove from scene
            self.scene().removeItem(self)

class NetworkCanvas(QGraphicsView):
    """Custom graphics view for the network canvas"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Create scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Drawing state variables
        self.drawing_link = False
        self.current_link = None
        self.grid_visible = False
        self.grid_size = 20
        
    def dragEnterEvent(self, event):
        """Handle drag enter events from component panel"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle drop events to create network devices"""
        if event.mimeData().hasText():
            device_type = event.mimeData().text()
            
            # Get drop position
            pos = self.mapToScene(event.pos())
            
            # Create device based on type
            icon_path = self.getIconPath(device_type)
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                device = NetworkDevice(device_type, pixmap)
                
                # Place device on canvas
                self.scene.addItem(device)
                device.setPos(pos - QPointF(pixmap.width()/2, pixmap.height()/2))
                
                # Add a label with the device type
                label = QGraphicsTextItem(device_type, device)
                label.setPos(0, pixmap.height())
                label.setTextWidth(pixmap.width())
                label.setDefaultTextColor(Qt.black)
                
                event.acceptProposedAction()
                
    def getIconPath(self, device_type):
        """Get the icon path for a specific device type"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "Icon", f"{device_type.lower()}.png")
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            # Check if LinkCable mode is active
            if hasattr(self.parent(), 'link_mode') and self.parent().link_mode:
                # Find if we clicked on a device
                item = self.itemAt(event.pos())
                if isinstance(item, NetworkDevice):
                    # Start drawing a link from this device
                    self.drawing_link = True
                    self.current_link = LinkItem(item)
                    self.scene.addItem(self.current_link)
                    item.links.append(self.current_link)
                    self.current_link.devices.append(item)
                
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing_link and self.current_link:
            # Update the end point of the link to follow the cursor
            pos = self.mapToScene(event.pos())
            self.current_link.updatePosition(pos)
            
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if self.drawing_link and self.current_link and event.button() == Qt.LeftButton:
            # Find if we released on a device
            item = self.itemAt(event.pos())
            
            if isinstance(item, NetworkDevice) and item != self.current_link.source_device:
                # Complete the link between the two devices
                self.current_link.target_device = item
                self.current_link.updatePosition()
                self.current_link.devices.append(item)
                item.links.append(self.current_link)
            else:
                # No valid target device, remove the link
                self.current_link.source_device.links.remove(self.current_link)
                self.scene.removeItem(self.current_link)
            
            self.drawing_link = False
            self.current_link = None
            
            # Disable link mode after creating a link
            if hasattr(self.parent(), 'link_mode'):
                self.parent().link_mode = False
            
        super().mouseReleaseEvent(event)
        
    def drawBackground(self, painter, rect):
        """Draw background with optional grid"""
        super().drawBackground(painter, rect)
        
        if self.grid_visible:
            # Draw the grid
            left = int(rect.left()) - (int(rect.left()) % self.grid_size)
            top = int(rect.top()) - (int(rect.top()) % self.grid_size)
            
            # Create light gray lines for grid
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            
            # Draw horizontal grid lines
            for y in range(top, int(rect.bottom()), self.grid_size):
                painter.drawLine(rect.left(), y, rect.right(), y)
                
            # Draw vertical grid lines
            for x in range(left, int(rect.right()), self.grid_size):
                painter.drawLine(x, rect.top(), x, rect.bottom())

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        
        # Load UI from file
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "MainWindow.ui"), self)
        
        # Set window title
        self.setWindowTitle("NetFlux5G - Network Designer")
        
        # Replace QWidget Canvas with NetworkCanvas
        self.canvas_layout = QVBoxLayout(self.Canvas)
        self.canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        self.network_canvas = NetworkCanvas(self)
        self.canvas_layout.addWidget(self.network_canvas)
        
        # Set up object buttons for drag and drop
        self.setupDraggableComponents()
        
        # Connect toolbar and menu actions
        self.setupActions()
        
        # State variables
        self.link_mode = False
        
        # Show the window
        self.show()
    
    def setupDraggableComponents(self):
        """Setup draggable buttons for network components"""
        # Dictionary mapping button names to component types and icons
        components = {
            "Host": ("Host", "../Icon/host.png"),
            "STA": ("STA", "../Icon/sta.png"),
            "GNB": ("GNB", "../Icon/gNB.png"),
            "DockerHost": ("DockerHost", "../Icon/docker.png"),
            "AP": ("AP", "../Icon/AP.png"),
            "VGcore": ("VGcore", "../Icon/5G core.png"),
            "Router": ("Router", "../Icon/Router.png"),
            "Switch": ("Switch", "../Icon/switch.png"),
            "LinkCable": ("LinkCable", "../Icon/link cable.png"),
            "Controller": ("Controller", "../Icon/controller.png")
        }
        
        # Make each button draggable
        for btn_name, (device_type, icon_path) in components.items():
            if hasattr(self, btn_name):
                button = getattr(self, btn_name)
                DraggableButton(button, device_type, icon_path)
    
    def setupActions(self):
        """Connect actions to their functions"""
        # File menu actions
        self.actionNew.triggered.connect(self.newProject)
        self.actionOpen.triggered.connect(self.openProject)
        self.actionSave.triggered.connect(self.saveProject)
        self.actionSave_As.triggered.connect(self.saveProjectAs)
        self.actionExport_to_Level_2_Script.triggered.connect(self.exportScript)
        self.actionQuit.triggered.connect(self.close)
        
        # Edit menu actions
        
        # Run menu actions
        self.actionRun.triggered.connect(self.runSimulation)
        self.actionStop.triggered.connect(self.stopSimulation)
        
        # Help menu actions
        self.actionAbout_NetFlux5G.triggered.connect(self.showAbout)
        
        # Toolbar actions
        self.actionPickTool.triggered.connect(lambda: self.setTool("pick"))
        self.actionHandTool.triggered.connect(lambda: self.setTool("hand"))
        self.actionDelete.triggered.connect(lambda: self.setTool("delete"))
        self.actionTextBox.triggered.connect(lambda: self.setTool("text"))
        self.actionDrawSquare.triggered.connect(lambda: self.setTool("square"))
        
        self.actionShowGrid.triggered.connect(self.toggleGrid)
        self.actionZoomIn.triggered.connect(self.zoomIn)
        self.actionZoomOut.triggered.connect(self.zoomOut)
        self.actionResetZoom.triggered.connect(self.resetZoom)
        
        # Link cable button special functionality
        self.LinkCable.clicked.connect(self.enableLinkMode)
    
    def newProject(self):
        """Create a new empty project"""
        self.network_canvas.scene.clear()
    
    def openProject(self):
        """Open an existing project"""
        # TODO: Implement file loading
        pass
    
    def saveProject(self):
        """Save the current project"""
        # TODO: Implement file saving
        pass
    
    def saveProjectAs(self):
        """Save the current project with a new name"""
        # TODO: Implement file saving with name
        pass
    
    def exportScript(self):
        """Export the network design to a level 2 script"""
        # TODO: Implement script export
        pass
    
    def runSimulation(self):
        """Run the network simulation"""
        # TODO: Implement simulation functionality
        pass
    
    def stopSimulation(self):
        """Stop the network simulation"""
        # TODO: Implement simulation stop
        pass
    
    def showAbout(self):
        """Show information about the application"""
        # TODO: Implement about dialog
        pass
    
    def setTool(self, tool_type):
        """Set the current tool"""
        self.link_mode = False
        
        if tool_type == "pick":
            self.network_canvas.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.ArrowCursor)
        elif tool_type == "hand":
            self.network_canvas.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif tool_type == "delete":
            self.network_canvas.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(QCursor(QPixmap("../Icon/delete.png")))
        elif tool_type == "text":
            # TODO: Implement text box tool
            pass
        elif tool_type == "square":
            # TODO: Implement square drawing tool
            pass
    
    def toggleGrid(self):
        """Toggle grid visibility"""
        self.network_canvas.grid_visible = not self.network_canvas.grid_visible
        self.network_canvas.viewport().update()
    
    def zoomIn(self):
        """Zoom in the view"""
        self.network_canvas.scale(1.2, 1.2)
    
    def zoomOut(self):
        """Zoom out the view"""
        self.network_canvas.scale(1/1.2, 1/1.2)
    
    def resetZoom(self):
        """Reset zoom to original level"""
        self.network_canvas.resetTransform()
    
    def enableLinkMode(self):
        """Enable link cable mode"""
        self.link_mode = True
        self.network_canvas.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(QCursor(QPixmap("../Icon/link cable.png")))

# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())