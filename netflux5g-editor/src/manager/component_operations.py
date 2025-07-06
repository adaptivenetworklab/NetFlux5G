"""
Component Operations Manager
Handles cut, copy, and paste operations for network components
"""
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QMessageBox
from gui.components import NetworkComponent
from manager.debug import debug_print, error_print, warning_print
import copy

class ComponentOperationsManager:
    """
    Manager for component cut, copy, and paste operations.
    
    IMPORTANT: For cut operations, this manager ensures that component numbers
    are properly reused by deleting the original component BEFORE creating the
    new one, so that the number becomes available in the available_numbers set.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.clipboard_component = None  # Stores the copied/cut component data
        self.cut_component = None  # Reference to the component that was cut
        
    def cutComponent(self):
        """Cut the selected component to clipboard."""
        selected_items = self.main_window.canvas_view.scene.selectedItems()
        
        if not selected_items:
            self.main_window.showCanvasStatus("No component selected for cut operation. Select a component first.", 3000)
            return
            
        # Find the first NetworkComponent in selection
        component = None
        for item in selected_items:
            if isinstance(item, NetworkComponent):
                component = item
                break
                
        if not component:
            self.main_window.showCanvasStatus("No valid component selected for cut", 2000)
            return
            
        # Store component data in clipboard
        self.clipboard_component = {
            'type': component.component_type,
            'properties': component.getProperties().copy(),
            'icon_path': component.icon_path,
            'operation': 'cut'
        }
        
        # Store reference to cut component for deletion on paste
        self.cut_component = component
        
        # Visual feedback - make component semi-transparent
        component.setOpacity(0.5)
        
        self.main_window.showCanvasStatus(f"Cut {component.display_name} - will be moved on paste", 2000)
        debug_print(f"Cut component: {component.display_name}")
        
    def copyComponent(self):
        """Copy the selected component to clipboard."""
        selected_items = self.main_window.canvas_view.scene.selectedItems()
        
        if not selected_items:
            self.main_window.showCanvasStatus("No component selected for copy operation. Select a component first.", 3000)
            return
            
        # Find the first NetworkComponent in selection
        component = None
        for item in selected_items:
            if isinstance(item, NetworkComponent):
                component = item
                break
                
        if not component:
            self.main_window.showCanvasStatus("No valid component selected for copy", 2000)
            return
            
        # Store component data in clipboard
        self.clipboard_component = {
            'type': component.component_type,
            'properties': component.getProperties().copy(),
            'icon_path': component.icon_path,
            'operation': 'copy'
        }
        
        # Reset cut component reference since this is a copy operation
        if self.cut_component:
            self.cut_component.setOpacity(1.0)  # Restore opacity of previously cut component
            self.cut_component = None
        
        self.main_window.showCanvasStatus(f"Copied {component.display_name}", 2000)
        debug_print(f"Copied component: {component.display_name}")
        
    def pasteComponent(self, position=None):
        """Paste the clipboard component at the specified position or smart position."""
        if not self.clipboard_component:
            self.main_window.showCanvasStatus("Nothing to paste. Copy or cut a component first.", 3000)
            return
            
        # Determine paste position with smart positioning
        if position is None or not hasattr(position, 'x') or not hasattr(position, 'y'):
            position = self._getSmartPastePosition()
        
        # Ensure position is valid and within scene bounds
        position = self._validatePastePosition(position)
        
        # Final type check
        if not hasattr(position, 'x') or not hasattr(position, 'y'):
            error_print(f"Invalid position type: {type(position)}. Falling back to QPointF(0,0)")
            from PyQt5.QtCore import QPointF
            position = QPointF(0, 0)
        
        # For cut operations, delete the original component FIRST to make its number available
        cut_component_number = None
        if self.clipboard_component['operation'] == 'cut' and self.cut_component:
            cut_component_number = getattr(self.cut_component, 'component_number', None)
            debug_print(f"About to delete cut component #{cut_component_number} to free up the number")
            self._deleteOriginalCutComponent()
            debug_print(f"Available numbers after deletion: {NetworkComponent.available_numbers[self.clipboard_component['type']]}")
            
        # Create new component (will reuse the number if it was just freed)
        new_component = self._createComponentFromClipboard(position, cut_component_number)
        
        if new_component:
            # Handle cut vs copy behavior
            if self.clipboard_component['operation'] == 'cut':
                self.cut_component = None
                # Clear clipboard after cut-paste
                self.clipboard_component = None
                self.main_window.showCanvasStatus(f"Moved {new_component.display_name}", 2000)
            else:
                # For copy operation, keep clipboard for multiple pastes
                self.main_window.showCanvasStatus(f"Pasted {new_component.display_name}", 2000)
            
            # Select the new component
            self.main_window.canvas_view.scene.clearSelection()
            new_component.setSelected(True)
            
            # Mark topology as modified
            if hasattr(self.main_window, 'onTopologyChanged'):
                self.main_window.onTopologyChanged()
                
    def _createComponentFromClipboard(self, position, cut_component_number=None):
        """Create a new component from clipboard data."""
        try:
            # Validate position before proceeding
            if not isinstance(position, QPointF):
                error_print(f"Invalid position type for component creation: {type(position)}")
                position = QPointF(100, 100)
            
            debug_print(f"Creating component from clipboard at position: {position}")
            
            # Scan and initialize numbering before creating component
            NetworkComponent.scanAndInitializeNumbering(self.main_window)
            
            # Create the component using the same method as normal placement
            component_type = self.clipboard_component['type']
            icon_path = self.clipboard_component['icon_path']
            
            # Create new component - this will automatically assign a new name/number
            new_component = NetworkComponent(component_type, icon_path, main_window=self.main_window)
            
            debug_print(f"Created component: {new_component.display_name} (#{new_component.component_number})")
            
            # Verify the numbering worked correctly for cut operations
            if cut_component_number is not None:
                if new_component.component_number == cut_component_number:
                    debug_print(f"SUCCESS: Component reused the cut component's number #{cut_component_number}")
                else:
                    debug_print(f"INFO: Component got new number #{new_component.component_number} instead of #{cut_component_number}")
                    debug_print(f"Available numbers were: {NetworkComponent.available_numbers[component_type]}")
            
            # Set position
            new_component.setPos(position)
            
            # Copy properties but DON'T override the automatically assigned name/number
            properties = copy.deepcopy(self.clipboard_component['properties'])
            
            # Preserve the new component's name and number that were automatically assigned
            auto_assigned_name = new_component.display_name
            
            # Copy all properties except name-related ones and position
            for key, value in properties.items():
                if key not in ['name', 'display_name', 'x', 'y']:
                    new_component.properties[key] = value
            
            # Keep the auto-assigned name
            new_component.properties['name'] = auto_assigned_name
            new_component.properties['display_name'] = auto_assigned_name
            
            # Update position properties
            new_component.updatePositionProperties()
            
            # Add to scene
            self.main_window.canvas_view.scene.addItem(new_component)
            
            debug_print(f"Successfully created and placed component {new_component.display_name} at position {position}")
            return new_component
            
        except Exception as e:
            error_print(f"Failed to create component from clipboard: {e}")
            import traceback
            error_print(f"Traceback: {traceback.format_exc()}")
            return None
            
    def _deleteOriginalCutComponent(self):
        """Delete the original component that was cut."""
        if self.cut_component and hasattr(self.cut_component, 'scene') and self.cut_component.scene():
            try:
                # Make the number available for reuse using the component's stored number
                component_type = self.cut_component.component_type
                if hasattr(self.cut_component, 'component_number'):
                    NetworkComponent.available_numbers[component_type].add(self.cut_component.component_number)
                    debug_print(f"Made component number {self.cut_component.component_number} available for reuse")
                
                # Clean up any connected links
                if hasattr(self.cut_component, 'connected_links'):
                    for link in list(self.cut_component.connected_links):
                        if link.scene():
                            link.scene().removeItem(link)
                
                # Remove from scene
                debug_print(f"Deleting cut component: {self.cut_component.display_name}")
                self.cut_component.scene().removeItem(self.cut_component)
                
            except Exception as e:
                error_print(f"Failed to delete cut component: {e}")
                
    def clearClipboard(self):
        """Clear the component clipboard."""
        if self.cut_component:
            self.cut_component.setOpacity(1.0)  # Restore opacity
            self.cut_component = None
        self.clipboard_component = None
        
    def hasClipboardContent(self):
        """Check if there's content in the clipboard."""
        return self.clipboard_component is not None
        
    def getClipboardInfo(self):
        """Get information about clipboard content."""
        if self.clipboard_component:
            return {
                'type': self.clipboard_component['type'],
                'operation': self.clipboard_component['operation']
            }
        return None

    def _getSmartPastePosition(self):
        """Get a smart position for pasting components."""
        from PyQt5.QtCore import QPointF
        try:
            # Try to get mouse position first
            if hasattr(self.main_window, 'canvas_view'):
                cursor_pos = self.main_window.canvas_view.mapFromGlobal(self.main_window.canvas_view.cursor().pos())
                if self.main_window.canvas_view.rect().contains(cursor_pos):
                    scene_pos = self.main_window.canvas_view.mapToScene(cursor_pos)
                    if hasattr(scene_pos, 'x') and hasattr(scene_pos, 'y'):
                        return scene_pos
            # Fallback to center of visible area
            if hasattr(self.main_window, 'canvas_view'):
                view_rect = self.main_window.canvas_view.rect()
                center_point = QPointF(view_rect.width() / 2, view_rect.height() / 2)
                return self.main_window.canvas_view.mapToScene(center_point.toPoint())
            return QPointF(0, 0)
        except Exception as e:
            error_print(f"Error getting smart paste position: {e}")
            return QPointF(0, 0)

    def _validatePastePosition(self, position):
        from PyQt5.QtCore import QPointF, QRectF
        try:
            if not hasattr(position, 'x') or not hasattr(position, 'y'):
                error_print(f"Invalid position type in _validatePastePosition: {type(position)}")
                return QPointF(0, 0)
            # Check if there's already a component at this position
            if hasattr(self.main_window, 'canvas_view') and hasattr(self.main_window.canvas_view, 'scene'):
                scene = self.main_window.canvas_view.scene
                
                # Check for overlapping components in a 60x60 area around the position
                overlap_rect = QRectF(position.x() - 30, position.y() - 30, 60, 60)
                items_at_position = scene.items(overlap_rect)
                
                # Filter to only NetworkComponent items
                from gui.components import NetworkComponent
                components_at_position = [item for item in items_at_position if isinstance(item, NetworkComponent)]
                
                if components_at_position:
                    # Find a nearby position that's free
                    for offset_x in range(0, 200, 60):
                        for offset_y in range(0, 200, 60):
                            if offset_x == 0 and offset_y == 0:
                                continue  # Skip the original position
                                
                            test_position = QPointF(position.x() + offset_x, position.y() + offset_y)
                            test_rect = QRectF(test_position.x() - 30, test_position.y() - 30, 60, 60)
                            test_items = scene.items(test_rect)
                            test_components = [item for item in test_items if isinstance(item, NetworkComponent)]
                            
                            if not test_components:
                                debug_print(f"Found free position at offset ({offset_x}, {offset_y})")
                                return test_position
                
                debug_print("No free position found nearby, using original position")
            
            return position
            
        except Exception as e:
            error_print(f"Error validating paste position: {e}")
            return QPointF(0, 0)
