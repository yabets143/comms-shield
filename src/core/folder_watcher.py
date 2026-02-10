import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .scrubber import UniversalScrubber
from ..utils.logger import SecureLogger

class AutoScrubFolderHandler(FileSystemEventHandler):
    def __init__(self, watch_folder, output_folder=None, logger=None):
        self.watch_folder = Path(watch_folder)
        self.output_folder = output_folder or self.watch_folder / "scrubbed"
        self.output_folder.mkdir(exist_ok=True)
        self.logger = logger or SecureLogger()
        self.scrubber = UniversalScrubber()
        
        # Process existing files
        self.process_existing_files()
    
    def process_existing_files(self):
        """Process files already in the folder when watcher starts"""
        for file_path in self.watch_folder.glob('*'):
            if file_path.is_file() and not file_path.name.startswith('scrubbed_'):
                self.process_file(file_path)
    
    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.5)  # Wait for file to be fully written
            self.process_file(Path(event.src_path))
    
    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(Path(event.src_path))
    
    def process_file(self, file_path):
        """Process a single file"""
        try:
            if file_path.name.startswith('scrubbed_'):
                return
                
            self.logger.info(f"Processing new file: {file_path.name}")
            
            # Scrub the file
            output_path = self.output_folder / f"scrubbed_{file_path.name}"
            success = self.scrubber.scrub_file(file_path, output_path)
            
            if success:
                self.logger.info(f"Successfully scrubbed: {file_path.name}")
                # Optional: Remove original file for security
                # file_path.unlink()
            else:
                self.logger.error(f"Failed to scrub: {file_path.name}")
                
        except Exception as e:
            self.logger.error(f"Error processing {file_path.name}: {str(e)}")

class FolderWatcher:
    def __init__(self, watch_folder, output_folder=None):
        self.watch_folder = Path(watch_folder)
        self.output_folder = output_folder
        self.observer = Observer()
        self.event_handler = None
        self.is_watching = False
        
    def start(self):
        """Start watching the folder"""
        self.event_handler = AutoScrubFolderHandler(
            self.watch_folder, 
            self.output_folder
        )
        
        self.observer.schedule(
            self.event_handler, 
            str(self.watch_folder), 
            recursive=False
        )
        self.observer.start()
        self.is_watching = True
        
    def stop(self):
        """Stop watching the folder"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.is_watching = False
    
    def get_status(self):
        """Get watcher status"""
        return {
            "watching": self.is_watching,
            "folder": str(self.watch_folder),
            "output_folder": str(self.event_handler.output_folder if self.event_handler else "")
        }