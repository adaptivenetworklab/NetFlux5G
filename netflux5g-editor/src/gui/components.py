import os
from .links import NetworkLink
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPen
from .widgets.Dialog import *


class NetworkComponent(QGraphicsPixmapItem):
    """Network component (node) that can be placed on the canvas"""

    # Map component types to their respective dialog classes
    DIALOG_MAP = {
        "Host": HostPropertiesDialog,
        "STA": STAPropertiesDialog,
        "UE": UEPropertiesDialog,
        "GNB": GNBPropertiesDialog,
        "DockerHost": DockerHostPropertiesDialog,
        "AP": APPropertiesDialog,
        "VGcore": Core5GPropertiesDialog,
        "Controller": ControllerPropertiesDialog,
    }
    
    def __init__(self, component_type, icon_path, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.icon_path = icon_path

        # Set the pixmap for the item
        pixmap = QPixmap(self.icon_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)

        # Make the item draggable and selectable
        self.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        self.setFlag(QGraphicsPixmapItem.ItemIsSelectable)

        
    def boundingRect(self):
        return QRectF(0, 0, 50, 50)
        
    def paint(self, painter, option, widget):
        """Draw the component."""
        # Draw the component icon
        if not self.pixmap().isNull():
            painter.drawPixmap(0, 0, 50, 50, self.pixmap())

        # If selected, draw a selection rectangle
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())

        # # Draw component name below the icon
        # painter.setPen(Qt.black)
        # painter.drawText(QRectF(-50, 25, 100, 20), Qt.AlignHCenter, self.component_type)


    def contextMenuEvent(self, event):
        """Handle right-click context menu events."""
        dialog_class = self.DIALOG_MAP.get(self.component_type)
        if dialog_class:
            # Close the existing dialog if it is already open
            canvas = self.scene().views()[0]
            if canvas.current_dialog:
                canvas.current_dialog.close()

            # Create a new dialog
            dialog = dialog_class(label_text=self.component_type, parent=canvas)

            # Get the item's position in the scene and map it to the global position
            item_scene_pos = self.scenePos()
            item_global_pos = canvas.viewport().mapToGlobal(canvas.mapFromScene(item_scene_pos))
            print(f"DEBUG: Item scene position: {item_scene_pos}")
            print(f"DEBUG: Item global position: {item_global_pos}")

            # Move the dialog to the item's position
            dialog.move(item_global_pos)

            # Show the dialog
            dialog.show()

            # Notify the canvas about the currently open dialog
            canvas.setCurrentDialog(dialog)
        else:
            print(f"DEBUG: No dialog found for component type: {self.component_type}")
    # def contextMenuEvent(self, event):
    #     """Handle right-click context menu events."""
    #     dialog_class = self.DIALOG_MAP.get(self.component_type)
    #     if dialog_class:
    #         # Close the currently open dialog if it exists
    #         canvas = self.scene().views()[0]
    #         if canvas.current_dialog:
    #             canvas.current_dialog.close()

    #         # Create and show the dialog
    #         dialog = dialog_class(label_text=self.component_type, parent=canvas)
    #         dialog.move(event.screenPos().toPoint())  # Position the dialog at the cursor
    #         dialog.show()

    #         # Track the currently open dialog in the canvas
    #         canvas.setCurrentDialog(dialog)
    #     else:
    #         print(f"DEBUG: No dialog found for component type: {self.component_type}")