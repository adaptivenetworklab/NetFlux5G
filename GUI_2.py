#!/usr/bin/env python3

import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                            QGraphicsItem, QGraphicsPixmapItem, QGraphicsTextItem,
                            QGraphicsLineItem, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                            QMenu, QAction, QFileDialog, QMessageBox, QPushButton)
from PyQt5.QtGui import QIcon, QPixmap, QPen, QFont, QCursor, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, QSize, pyqtSignal
from PyQt5 import uic

class NodeType:
    HOST = "Host"
    STA = "STA"
    GNB = "GNB"
    DOCKER_HOST = "DockerHost"
    AP = "AP"
    VGCORE = "VGcore"
    ROUTER = "Router"
    SWITCH = "Switch"
    CONTROLLER = "Controller"
    LINK = "LinkCable"

class ToolType:
    PICK = "Pick"
    HAND = "Hand"
    DELETE = "Delete"
    TEXT = "Text"
    SQUARE = "Square"

class Node(QGraphicsPixmapItem):
    def __init__(self, node_type, x, y, scene, parent=None):
        super().__init__(parent)
        self.node_type = node_type
        self.scene = scene
        self.links = []
        self.label = QGraphicsTextItem(self)
        self.label.setFont(QFont("Arial", 10))
        
        # Set the appropriate icon based on node type
        icon_path = f"../Icon/{self._get_icon_name()}.png"
        if os.path.exists(icon_path):
            self.setPixmap(QPixmap(icon_path).scaled(50, 50, Qt.KeepAspectRatio))
        else:
            # Fallback icon if file not found
            self.setPixmap(QPixmap(50, 50))
        
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Set default node name based on type
        self.name = f"{node_type}{scene.get_node_count(node_type)}"
        self.label.setPlainText(self.name)
        self._adjust_label_position()
    
    def _get_icon_name(self):
        icon_map = {
            NodeType.HOST: "host",
            NodeType.STA: "sta",
            NodeType.GNB: "gNB",
            NodeType.DOCKER_HOST: "docker",
            NodeType.AP: "AP",
            NodeType.VGCORE: "5G core",
            NodeType.ROUTER: "Router",
            NodeType.SWITCH: "switch",
            NodeType.CONTROLLER: "controller"
        }
        return icon_map.get(self.node_type, "host")
    
    def _adjust_label_position(self):
        rect = self.boundingRect()
        label_width = self.label.boundingRect().width()
        self.label.setPos((rect.width() - label_width) / 2, rect.height() + 5)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene:
            # Update connected links when the node is moved
            for link in self.links:
                link.update_position()
        return super().itemChange(change, value)

class Link(QGraphicsLineItem):
    def __init__(self, source_node, dest_node, scene, parent=None):
        super().__init__(parent)
        self.source = source_node
        self.dest = dest_node
        self.scene = scene
        
        # Add this link to both nodes' links list
        self.source.links.append(self)
        self.dest.links.append(self)
        
        # Set line style
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.setPen(pen)
        
        # Initial position update
        self.update_position()
        
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    
    def update_position(self):
        # Calculate the center points of source and destination nodes
        source_center = self.source.pos() + QPointF(self.source.boundingRect().width()/2, 
                                                 self.source.boundingRect().height()/2)
        dest_center = self.dest.pos() + QPointF(self.dest.boundingRect().width()/2, 
                                             self.dest.boundingRect().height()/2)
        
        # Update the line position
        self.setLine(source_center.x(), source_center.y(), dest_center.x(), dest_center.y())

class NetworkCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Set scene properties
        self.scene.setSceneRect(0, 0, 4000, 3000)  # Large canvas
        
        # Init variables
        self.current_tool = ToolType.PICK
        self.current_node_type = None
        self.temp_line = None
        self.source_node = None
        self.show_grid = False
        self.scale_factor = 1.0
        
        # Node counters for generating unique names
        self.node_counts = {
            NodeType.HOST: 0,
            NodeType.STA: 0,
            NodeType.GNB: 0,
            NodeType.DOCKER_HOST: 0,
            NodeType.AP: 0,
            NodeType.VGCORE: 0,
            NodeType.ROUTER: 0,
            NodeType.SWITCH: 0,
            NodeType.CONTROLLER: 0
        }
    
    def get_node_count(self, node_type):
        self.node_counts[node_type] += 1
        return self.node_counts[node_type]
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            if self.current_node_type:
                # Create a new node
                if self.current_node_type != NodeType.LINK:
                    node = Node(self.current_node_type, scene_pos.x(), scene_pos.y(), self)
                    self.scene.addItem(node)
                else:
                    # Start creating a link
                    item = self.scene.itemAt(scene_pos, self.transform())
                    if isinstance(item, Node):
                        self.source_node = item
                        # Create temporary line for visual feedback
                        self.temp_line = QGraphicsLineItem(
                            item.pos().x() + item.boundingRect().width()/2,
                            item.pos().y() + item.boundingRect().height()/2,
                            scene_pos.x(), scene_pos.y()
                        )
                        self.scene.addItem(self.temp_line)
            
            elif self.current_tool == ToolType.DELETE:
                # Delete selected item
                item = self.scene.itemAt(scene_pos, self.transform())
                if item:
                    if isinstance(item, Link):
                        # Remove link from nodes' link lists
                        if item.source:
                            item.source.links.remove(item)
                        if item.dest:
                            item.dest.links.remove(item)
                    self.scene.removeItem(item)
            
            elif self.current_tool == ToolType.TEXT:
                # Create a text box (simplified - would normally open a dialog)
                text_item = QGraphicsTextItem("Text")
                text_item.setPos(scene_pos)
                text_item.setFlag(QGraphicsItem.ItemIsMovable)
                text_item.setFlag(QGraphicsItem.ItemIsSelectable)
                self.scene.addItem(text_item)
            
            elif self.current_tool == ToolType.SQUARE:
                # Create a rectangle
                rect_item = self.scene.addRect(QRectF(scene_pos, QSizeF(100, 100)), 
                                              QPen(Qt.black), QBrush(Qt.transparent))
                rect_item.setFlag(QGraphicsItem.ItemIsMovable)
                rect_item.setFlag(QGraphicsItem.ItemIsSelectable)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.temp_line and self.source_node:
            # Update temporary line when creating a link
            scene_pos = self.mapToScene(event.pos())
            self.temp_line.setLine(
                self.source_node.pos().x() + self.source_node.boundingRect().width()/2,
                self.source_node.pos().y() + self.source_node.boundingRect().height()/2,
                scene_pos.x(), scene_pos.y()
            )
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.temp_line and self.source_node:
            # Finish creating a link
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            
            # Remove temporary line
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
            
            # Create permanent link if destination is a node and not the same as source
            if isinstance(item, Node) and item != self.source_node:
                link = Link(self.source_node, item, self)
                self.scene.addItem(link)
            
            self.source_node = None
        
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        # Zoom in/out with mouse wheel
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
            self.scale_factor *= zoom_factor
        else:
            # Zoom out
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
            self.scale_factor /= zoom_factor

class DraggableButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node_type = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Create a drag object
            from PyQt5.QtGui import QDrag
            from PyQt5.QtCore import QMimeData
            
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.node_type)
            drag.setMimeData(mime_data)
            
            # Start the drag operation
            drag.exec_(Qt.CopyAction)
        else:
            super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load UI from file
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI", "MainWindow.ui"), self)
        
        # Initialize canvas widget
        self.canvas = NetworkCanvas()
        self.horizontalLayout.replaceWidget(self.Canvas, self.canvas)
        
        # Set up draggable buttons for node creation
        self.setup_draggable_buttons()
        
        # Enable drag and drop for canvas
        self.canvas.setAcceptDrops(True)
        
        # Connect toolbar actions
        self.actionPickTool.triggered.connect(lambda: self.set_current_tool(ToolType.PICK))
        self.actionHandTool.triggered.connect(lambda: self.set_current_tool(ToolType.HAND))
        self.actionDelete.triggered.connect(lambda: self.set_current_tool(ToolType.DELETE))
        self.actionTextBox.triggered.connect(lambda: self.set_current_tool(ToolType.TEXT))
        self.actionDrawSquare.triggered.connect(lambda: self.set_current_tool(ToolType.SQUARE))
        
        # Connect zoom actions
        self.actionZoomIn.triggered.connect(self.zoom_in)
        self.actionZoomOut.triggered.connect(self.zoom_out)
        self.actionResetZoom.triggered.connect(self.reset_zoom)
        self.actionShowGrid.triggered.connect(self.toggle_grid)
        
        # Connect menu actions
        self.actionNew.triggered.connect(self.new_topology)
        self.actionOpen.triggered.connect(self.open_topology)
        self.actionSave.triggered.connect(self.save_topology)
        self.actionSave_As.triggered.connect(self.save_topology_as)
        self.actionExport_to_Level_2_Script.triggered.connect(self.export_to_script)
        self.actionQuit.triggered.connect(self.close)
        
        self.actionRun.triggered.connect(self.run_topology)
        self.actionStop.triggered.connect(self.stop_topology)
        
        # Set window title
        self.setWindowTitle("NetFlux5G - Network Topology Editor")
        
        # Current topology file
        self.current_file = None
        
        # Initially select pick tool
        self.actionPickTool.trigger()
    
    def setup_draggable_buttons(self):
        # Replace standard QPushButtons with DraggableButtons for node types
        # and add click event connections as well
        
        # First, map original buttons to node types
        button_node_map = {
            self.Host: NodeType.HOST,
            self.STA: NodeType.STA,
            self.GNB: NodeType.GNB,
            self.DockerHost: NodeType.DOCKER_HOST,
            self.AP: NodeType.AP,
            self.VGcore: NodeType.VGCORE,
            self.Router: NodeType.ROUTER,
            self.Switch: NodeType.SWITCH,
            self.Controller: NodeType.CONTROLLER,
            self.LinkCable: NodeType.LINK
        }
        
        # For each button in the layout, replace with a draggable version
        for original_button, node_type in button_node_map.items():
            # Get position and parent of original button
            parent = original_button.parent()
            layout = parent.layout()
            index = layout.indexOf(original_button)
            
            # Create new draggable button with same properties
            new_button = DraggableButton(parent)
            new_button.node_type = node_type
            new_button.setIcon(original_button.icon())
            new_button.setIconSize(original_button.iconSize())
            new_button.setToolTip(node_type)
            
            # Remove original and add new at same position
            layout.removeWidget(original_button)
            original_button.deleteLater()
            layout.insertWidget(index, new_button)
            
            # Connect the click event to set current node type
            new_button.clicked.connect(lambda checked=False, nt=node_type: self.set_current_node(nt))
            
            # Store reference with same name as original
            setattr(self, original_button.objectName(), new_button)
    
    def setup_canvas_drag_drop(self):
        # Override the canvas drag and drop events
        original_canvas = self.canvas
        
        class DragDropCanvas(NetworkCanvas):
            def __init__(self, original):
                super().__init__(original.parent())
                self.scene = original.scene
                self.setScene(self.scene)
                self.current_tool = original.current_tool
                self.current_node_type = original.current_node_type
                self.temp_line = original.temp_line
                self.source_node = original.source_node
                self.show_grid = original.show_grid
                self.scale_factor = original.scale_factor
                self.node_counts = original.node_counts
            
            def dragEnterEvent(self, event):
                if event.mimeData().hasText():
                    event.acceptProposedAction()
            
            def dropEvent(self, event):
                if event.mimeData().hasText():
                    node_type = event.mimeData().text()
                    position = self.mapToScene(event.pos())
                    if node_type != NodeType.LINK:  # Can't drop a link directly
                        node = Node(node_type, position.x(), position.y(), self)
                        self.scene.addItem(node)
                    event.acceptProposedAction()
        
        # Replace canvas with drag-drop enabled version
        new_canvas = DragDropCanvas(original_canvas)
        self.horizontalLayout.replaceWidget(original_canvas, new_canvas)
        original_canvas.deleteLater()
        self.canvas = new_canvas
    
    def set_current_node(self, node_type):
        # Reset tool to pick when a node type is selected
        self.canvas.current_node_type = node_type
        self.canvas.current_tool = ToolType.PICK
        self.actionPickTool.setChecked(True)
        
        # Update cursor
        self.canvas.setCursor(Qt.ArrowCursor)
        
        # Update status bar
        self.statusbar.showMessage(f"Creating {node_type}")
    
    def set_current_tool(self, tool_type):
        self.canvas.current_node_type = None
        self.canvas.current_tool = tool_type
        
        # Update cursor based on tool
        if tool_type == ToolType.HAND:
            self.canvas.setCursor(Qt.OpenHandCursor)
            self.canvas.setDragMode(QGraphicsView.ScrollHandDrag)
        elif tool_type == ToolType.DELETE:
            self.canvas.setCursor(Qt.CrossCursor)
            self.canvas.setDragMode(QGraphicsView.NoDrag)
        else:
            self.canvas.setCursor(Qt.ArrowCursor)
            self.canvas.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Update status bar
        self.statusbar.showMessage(f"Selected {tool_type} tool")
    
    def zoom_in(self):
        self.canvas.scale(1.15, 1.15)
        self.canvas.scale_factor *= 1.15
    
    def zoom_out(self):
        self.canvas.scale(1.0 / 1.15, 1.0 / 1.15)
        self.canvas.scale_factor /= 1.15
    
    def reset_zoom(self):
        self.canvas.resetTransform()
        self.canvas.scale_factor = 1.0
    
    def toggle_grid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        # Implementation of grid drawing would be needed here
        self.canvas.viewport().update()
    
    def new_topology(self):
        # Clear the scene
        reply = QMessageBox.question(self, 'New Topology', 
                                      'Are you sure you want to create a new topology? Unsaved changes will be lost.',
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.canvas.scene.clear()
            self.canvas.node_counts = {node_type: 0 for node_type in self.canvas.node_counts}
            self.current_file = None
            self.setWindowTitle("NetFlux5G - Network Topology Editor")
    
    def open_topology(self):
        # Would implement file loading here
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Topology", "", 
                                                  "Topology Files (*.nft);;All Files (*)")
        if file_path:
            # Implementation of topology loading would go here
            self.current_file = file_path
            self.setWindowTitle(f"NetFlux5G - {os.path.basename(file_path)}")
            QMessageBox.information(self, "Open Topology", "Loading topology file is not implemented in this example.")
    
    def save_topology(self):
        if self.current_file:
            # Implementation of topology saving would go here
            QMessageBox.information(self, "Save Topology", "Saving topology is not implemented in this example.")
        else:
            self.save_topology_as()
    
    def save_topology_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Topology As", "", 
                                                  "Topology Files (*.nft);;All Files (*)")
        if file_path:
            # Implementation of topology saving would go here
            self.current_file = file_path
            self.setWindowTitle(f"NetFlux5G - {os.path.basename(file_path)}")
            QMessageBox.information(self, "Save Topology", "Saving topology is not implemented in this example.")
    
    def export_to_script(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to Script", "", 
                                                  "Python Files (*.py);;All Files (*)")
        if file_path:
            # Implementation of script export would go here
            QMessageBox.information(self, "Export Script", "Exporting to script is not implemented in this example.")
    
    def run_topology(self):
        # Implementation of running the topology in Mininet with 5G extensions would go here
        QMessageBox.information(self, "Run Topology", "Running topology is not implemented in this example.")
    
    def stop_topology(self):
        # Implementation of stopping the topology would go here
        QMessageBox.information(self, "Stop Topology", "Stopping topology is not implemented in this example.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # Setup the drag and drop functionality after MainWindow is initialized
    window.setup_canvas_drag_drop()
    window.show()
    sys.exit(app.exec_())