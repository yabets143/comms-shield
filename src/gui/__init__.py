"""
GUI components for Comms Shield
Cross-platform graphical interface
"""

from .simple_window import SimpleMainWindow

# Create aliases for compatibility
MainWindow = SimpleMainWindow
Dashboard = SimpleMainWindow  # Alias for compatibility
SystemTray = SimpleMainWindow  # Alias for compatibility

__all__ = ['MainWindow', 'Dashboard', 'SystemTray', 'SimpleMainWindow']