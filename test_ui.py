#!/usr/bin/env python3
"""
Quick test script for Comms Shield GUI
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from gui.simple_window import SimpleMainWindow
    print("✓ GUI modules imported successfully")
    
    # Test basic functionality
    from core.scrubber import UniversalScrubber
    from utils.logger import SecureLogger
    
    scrubber = UniversalScrubber()
    logger = SecureLogger()
    
    print("✓ Core modules imported successfully")
    print("✓ Scrubber status:", scrubber.get_scrubber_status())
    
    print("\n🎉 All tests passed! Starting GUI...")
    
    # Start the GUI
    app = SimpleMainWindow()
    app.run()
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nTry installing missing dependencies:")
    print("pip install pillow watchdog mutagen pikepdf hachoir python-docx")
except Exception as e:
    print(f"✗ Error: {e}")