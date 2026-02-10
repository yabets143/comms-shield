"""
Comms Shield - Defensive Communication Security Toolkit
Defending Against Metadata Leaks & Covert Channels
"""

__version__ = "1.0.0"
__author__ = "Comms Shield Team"
__description__ = "Metadata Leak Prevention System for secure communications"

from .core.scrubber import UniversalScrubber
from .core.folder_watcher import FolderWatcher
from .utils.logger import SecureLogger

__all__ = ['UniversalScrubber', 'FolderWatcher', 'SecureLogger']