# watcher.py - Standalone file watcher functionality
import shutil
from pathlib import Path
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from universal_scrubber import detect_and_scrub

# Global state
watch_folder = Path("watch_folder")
clean_folder = watch_folder / "clean"
is_watcher_active = False
file_observer = None
watcher_logs = []

def add_watcher_log(message, level="INFO"):
    """Add log entry with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    watcher_logs.append(log_entry)
    print(f"WATCHER: {log_entry}")

class FileWatcher(FileSystemEventHandler):
    def on_created(self, event):
        """Called when a file is created in the watch folder"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            add_watcher_log(f"New file detected: {file_path.name}")
            self.process_file(file_path)
    
    def on_modified(self, event):
        """Called when a file is modified in the watch folder"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            # Add a small delay to ensure file is completely written
            threading.Timer(2.0, self.process_file, [file_path]).start()
    
    def process_file(self, file_path):
        """Process a file by scrubbing it and saving to clean folder"""
        if not file_path.exists():
            return
            
        try:
            add_watcher_log(f"Processing file: {file_path.name}")
            
            # Create clean folder if it doesn't exist
            clean_folder.mkdir(exist_ok=True)
            
            # Generate output filename
            output_filename = f"cleaned_{file_path.name}"
            output_path = clean_folder / output_filename
            
            # Skip if already processed
            if output_path.exists():
                add_watcher_log(f"File already processed: {file_path.name}")
                return
            
            # Use the existing scrub function - handle both function signatures
            try:
                # Try the new signature with output path
                detect_and_scrub(file_path, output_path)
            except TypeError as e:
                # Fall back to old signature
                add_watcher_log(f"Using fallback processing for {file_path.name}")
                detect_and_scrub(file_path)
                # Move the scrubbed file to clean folder
                downloads_dir = Path("downloads")
                scrubbed_file = downloads_dir / f"scrubbed_{file_path.name}"
                if scrubbed_file.exists():
                    shutil.move(scrubbed_file, output_path)
            
            if output_path.exists():
                add_watcher_log(f"Successfully cleaned: {file_path.name} -> {output_filename}")
            else:
                add_watcher_log(f"Warning: Output file not created for {file_path.name}", "WARNING")
                
        except Exception as e:
            add_watcher_log(f"Error processing {file_path.name}: {str(e)}", "ERROR")

def start_file_watcher():
    """Start watching the folder for new files"""
    global is_watcher_active, file_observer
    
    if is_watcher_active:
        return {"status": "error", "message": "Watcher is already running"}
    
    try:
        # Create watch folder if it doesn't exist
        watch_folder.mkdir(exist_ok=True)
        clean_folder.mkdir(exist_ok=True)
        
        # Set up file observer
        event_handler = FileWatcher()
        file_observer = Observer()
        file_observer.schedule(event_handler, str(watch_folder), recursive=False)
        file_observer.start()
        
        is_watcher_active = True
        add_watcher_log(f"File watcher started. Watching: {watch_folder.absolute()}")
        
        return {
            "status": "success", 
            "message": "File watcher started successfully",
            "watch_folder": str(watch_folder.absolute())
        }
        
    except Exception as e:
        add_watcher_log(f"Failed to start file watcher: {str(e)}", "ERROR")
        return {"status": "error", "message": f"Failed to start watcher: {str(e)}"}

def stop_file_watcher():
    """Stop the file watcher"""
    global is_watcher_active, file_observer
    
    if not is_watcher_active or not file_observer:
        return {"status": "error", "message": "Watcher is not running"}
    
    try:
        file_observer.stop()
        file_observer.join()
        is_watcher_active = False
        add_watcher_log("File watcher stopped")
        
        return {"status": "success", "message": "File watcher stopped successfully"}
        
    except Exception as e:
        add_watcher_log(f"Failed to stop file watcher: {str(e)}", "ERROR")
        return {"status": "error", "message": f"Failed to stop watcher: {str(e)}"}

def set_watch_folder(folder_path):
    """Set a new folder to watch"""
    global watch_folder, clean_folder
    
    try:
        new_folder = Path(folder_path)
        if not new_folder.exists():
            return {"status": "error", "message": "Folder does not exist"}
        
        watch_folder = new_folder
        clean_folder = watch_folder / "clean"
        clean_folder.mkdir(exist_ok=True)
        add_watcher_log(f"Watch folder set to: {watch_folder.absolute()}")
        
        # Restart watcher if it was running
        if is_watcher_active:
            stop_file_watcher()
            return start_file_watcher()
        
        return {
            "status": "success", 
            "message": "Watch folder updated successfully",
            "watch_folder": str(watch_folder.absolute())
        }
        
    except Exception as e:
        add_watcher_log(f"Failed to set watch folder: {str(e)}", "ERROR")
        return {"status": "error", "message": f"Failed to set watch folder: {str(e)}"}

def process_existing_files():
    """Process all existing files in the watch folder"""
    try:
        if not watch_folder.exists():
            return {"status": "error", "message": "Watch folder does not exist"}
        
        processed_count = 0
        clean_folder.mkdir(exist_ok=True)
        
        # Process all files in watch folder
        for file_path in watch_folder.glob('*'):
            if file_path.is_file():
                try:
                    output_filename = f"cleaned_{file_path.name}"
                    output_path = clean_folder / output_filename
                    
                    # Skip if already processed
                    if output_path.exists():
                        continue
                    
                    # Try new signature first, then fallback
                    try:
                        detect_and_scrub(file_path, output_path)
                    except TypeError:
                        detect_and_scrub(file_path)
                        downloads_dir = Path("downloads")
                        scrubbed_file = downloads_dir / f"scrubbed_{file_path.name}"
                        if scrubbed_file.exists():
                            shutil.move(scrubbed_file, output_path)
                    
                    processed_count += 1
                    add_watcher_log(f"Processed existing file: {file_path.name}")
                    
                except Exception as e:
                    add_watcher_log(f"Failed to process {file_path.name}: {str(e)}", "ERROR")
        
        add_watcher_log(f"Processed {processed_count} existing files")
        return {
            "status": "success", 
            "message": f"Processed {processed_count} existing files",
            "processed_count": processed_count
        }
        
    except Exception as e:
        add_watcher_log(f"Failed to process existing files: {str(e)}", "ERROR")
        return {"status": "error", "message": f"Failed to process existing files: {str(e)}"}

def get_clean_files():
    """Get list of cleaned files"""
    clean_files = []
    
    if clean_folder.exists():
        for file_path in clean_folder.glob('*'):
            if file_path.is_file():
                clean_files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    
    return clean_files

def get_watcher_status():
    """Get current watcher status"""
    return {
        "is_active": is_watcher_active,
        "watch_folder": str(watch_folder.absolute()),
        "clean_folder": str(clean_folder.absolute())
    }

def get_watcher_logs():
    """Get watcher-specific logs"""
    return watcher_logs

# Test function for debugging
def test_watcher():
    """Test the watcher functionality independently"""
    print("=== Testing Watcher Functionality ===")
    
    # Test folder setup
    watch_folder.mkdir(exist_ok=True)
    clean_folder.mkdir(exist_ok=True)
    print(f"Watch folder: {watch_folder.absolute()}")
    print(f"Clean folder: {clean_folder.absolute()}")
    
    # Test watcher start/stop
    result = start_file_watcher()
    print(f"Start watcher: {result}")
    
    if result["status"] == "success":
        result = stop_file_watcher()
        print(f"Stop watcher: {result}")
    
    print("=== Watcher Test Complete ===")

if __name__ == "__main__":
    test_watcher()