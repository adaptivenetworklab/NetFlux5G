"""
Debug manager for NetFlux5G Editor
Provides centralized debug logging control
"""

class DebugManager:
    """Singleton class to manage debug state across the application"""
    
    _instance = None
    _debug_enabled = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def is_debug_enabled(cls):
        """Check if debug mode is enabled"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance._debug_enabled
    
    @classmethod
    def set_debug_enabled(cls, enabled):
        """Enable or disable debug mode"""
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._debug_enabled = enabled
        # Use print directly to avoid recursion
        print(f"DEBUG: Debug mode {'enabled' if enabled else 'disabled'}")
    
    @classmethod
    def debug_print(cls, message, force=False):
        """Print debug message if debug mode is enabled or forced"""
        if force or cls.is_debug_enabled():
            print(f"DEBUG: {message}")
    
    @classmethod
    def error_print(cls, message):
        """Always print error messages"""
        print(f"ERROR: {message}")
    
    @classmethod
    def warning_print(cls, message):
        """Always print warning messages"""
        print(f"WARNING: {message}")

# Convenience functions for easy use throughout the application
def debug_print(message, force=False):
    """Print debug message if debug mode is enabled"""
    DebugManager.debug_print(message, force)

def error_print(message):
    """Print error message"""
    DebugManager.error_print(message)

def warning_print(message):
    """Print warning message"""
    DebugManager.warning_print(message)

def is_debug_enabled():
    """Check if debug mode is enabled"""
    return DebugManager.is_debug_enabled()

def set_debug_enabled(enabled):
    """Enable or disable debug mode"""
    DebugManager.set_debug_enabled(enabled)