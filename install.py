#!/usr/bin/env python3
import sys
import subprocess
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    requirements_file = Path("requirements.txt")
    
    if requirements_file.exists():
        print("Installing requirements...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
    else:
        print("requirements.txt not found")

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "uploads", "downloads", "config"]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"Created directory: {dir_name}")

def main():
    print("Comms Shield Installation")
    print("=" * 30)
    
    try:
        install_requirements()
        create_directories()
        
        print("\nInstallation completed successfully!")
        print("\nUsage:")
        print("  python main.py gui      # Start graphical interface")
        print("  python main.py scrub    # Scrub files from command line")
        print("  python main.py watch    # Monitor folder for auto-scrubbing")
        
    except Exception as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()