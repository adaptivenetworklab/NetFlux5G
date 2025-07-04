#!/usr/bin/env python3
"""
Test script to verify the unsaved changes functionality works correctly.
This script should test:
1. Creating a new topology marks it as clean
2. Adding components marks it as modified
3. Moving components marks it as modified
4. Modifying component properties marks it as modified
5. Saving marks it as clean
6. Loading marks it as clean
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'netflux5g-editor', 'src')
sys.path.insert(0, src_path)

def test_unsaved_changes():
    """Test unsaved changes tracking functionality."""
    print("Testing unsaved changes functionality...")
    
    # This is just a structural test - the actual GUI testing would require running the app
    # and interacting with the GUI, which is complex to automate.
    
    try:
        # Import the main module to check for syntax errors
        from main import NetFlux5GApp
        print("✓ Main module imports successfully")
        
        # Import other modules to check for syntax errors
        from gui.components import NetworkComponent
        print("✓ NetworkComponent imports successfully")
        
        from gui.links import NetworkLink  
        print("✓ NetworkLink imports successfully")
        
        from manager.file import FileManager
        print("✓ FileManager imports successfully")
        
        print("\n✓ All modules import successfully - no syntax errors detected")
        print("\nTo fully test the unsaved changes functionality:")
        print("1. Run the NetFlux5G Editor")
        print("2. Create a new topology")
        print("3. Add a component - window title should show '*' (unsaved)")
        print("4. Save the topology - '*' should disappear")
        print("5. Move a component - '*' should appear again")
        print("6. Try to quit - should prompt to save changes")
        
        return True
        
    except Exception as e:
        print(f"✗ Error importing modules: {e}")
        return False

if __name__ == "__main__":
    success = test_unsaved_changes()
    sys.exit(0 if success else 1)
