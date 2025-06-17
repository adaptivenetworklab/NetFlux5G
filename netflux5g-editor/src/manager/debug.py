"""
Debug management module for NetFlux5G Editor
Provides centralized debug, error, and warning printing functionality.
"""

import sys
import os
from datetime import datetime

# Global debug state
_debug_enabled = False

def set_debug_enabled(enabled):
    """Enable or disable debug mode."""
    global _debug_enabled
    _debug_enabled = enabled

def is_debug_enabled():
    """Check if debug mode is enabled."""
    return _debug_enabled

def debug_print(message, force=False):
    """Print debug message if debug mode is enabled or force is True."""
    if _debug_enabled or force:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}", file=sys.stderr)

def error_print(message):
    """Print error message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)

def warning_print(message):
    """Print warning message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] WARNING: {message}", file=sys.stderr)

class DebugManager:
    """Debug manager class for additional functionality."""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def toggle_debug(self):
        """Toggle debug mode."""
        current = is_debug_enabled()
        set_debug_enabled(not current)
        return not current
    
    def get_debug_info(self):
        """Get current debug information."""
        return {
            'debug_enabled': is_debug_enabled(),
            'timestamp': datetime.now().isoformat()
        }