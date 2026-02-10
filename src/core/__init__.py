"""
Core functionality for Comms Shield
Metadata scrubbing, analysis, and folder monitoring
"""

from .scrubber import UniversalScrubber

# Import metadata functions instead of class
from .metadata_analyzer import show_comprehensive_metadata

# Conditional imports for folder watcher
try:
    from .folder_watcher import FolderWatcher, AutoScrubFolderHandler
    FOLDER_WATCHER_AVAILABLE = True
except ImportError as e:
    print(f"Folder watcher not available: {e}")
    FOLDER_WATCHER_AVAILABLE = False
    # Create dummy classes if watchdog is not available
    class FolderWatcher:
        def __init__(self, *args, **kwargs):
            raise ImportError("watchdog not installed. Run: pip install watchdog")
    
    class AutoScrubFolderHandler:
        def __init__(self, *args, **kwargs):
            raise ImportError("watchdog not installed. Run: pip install watchdog")

__all__ = [
    'UniversalScrubber', 
    'show_comprehensive_metadata',
    'FolderWatcher', 
    'AutoScrubFolderHandler',
    'FOLDER_WATCHER_AVAILABLE'
]