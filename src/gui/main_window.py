import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

from ..core.scrubber import UniversalScrubber
from ..core.folder_watcher import FolderWatcher
from ..utils.logger import SecureLogger

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.scrubber = UniversalScrubber()
        self.watcher = None
        self.setup_ui()
    
    def setup_window(self):
        self.root.title("Comms Shield - Metadata Protection Toolkit")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
    
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        
        # Dashboard tab
        dashboard_frame = ttk.Frame(notebook)
        self.setup_dashboard_tab(dashboard_frame)
        
        # File Scrubber tab
        scrubber_frame = ttk.Frame(notebook)
        self.setup_scrubber_tab(scrubber_frame)
        
        # Folder Watcher tab
        watcher_frame = ttk.Frame(notebook)
        self.setup_watcher_tab(watcher_frame)
        
        # Logs tab
        logs_frame = ttk.Frame(notebook)
        self.setup_logs_tab(logs_frame)
        
        notebook.add(dashboard_frame, text="Dashboard")
        notebook.add(scrubber_frame, text="File Scrubber")
        notebook.add(watcher_frame, text="Folder Watcher")
        notebook.add(logs_frame, text="Logs")
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
    
    def setup_dashboard_tab(self, parent):
        # Dashboard content
        label = ttk.Label(parent, text="Comms Shield Dashboard", font=('Arial', 16))
        label.pack(pady=20)
        
        # Add dashboard widgets
        # (Implementation details for dashboard)
    
    def setup_scrubber_tab(self, parent):
        # File scrubber interface
        ttk.Label(parent, text="Select files to scrub:").pack(pady=5)
        
        ttk.Button(parent, text="Browse Files", 
                  command=self.browse_files).pack(pady=5)
        
        ttk.Button(parent, text="Browse Folder", 
                  command=self.browse_folder).pack(pady=5)
        
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=10)
    
    def setup_watcher_tab(self, parent):
        # Folder watcher interface
        ttk.Label(parent, text="Monitor folder for auto-scrubbing:").pack(pady=5)
        
        ttk.Button(parent, text="Select Watch Folder", 
                  command=self.select_watch_folder).pack(pady=5)
        
        self.watch_status = ttk.Label(parent, text="Not watching")
        self.watch_status.pack(pady=5)
        
        ttk.Button(parent, text="Start Watching", 
                  command=self.start_watching).pack(pady=5)
        
        ttk.Button(parent, text="Stop Watching", 
                  command=self.stop_watching).pack(pady=5)
    
    def setup_logs_tab(self, parent):
        # Logs display
        self.logs_text = tk.Text(parent, height=20, width=80)
        scrollbar = ttk.Scrollbar(parent, command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=scrollbar.set)
        
        self.logs_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select files to scrub",
            filetypes=[("All files", "*.*")]
        )
        if files:
            self.scrub_files(files)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select folder to scrub")
        if folder:
            self.scrub_folder(Path(folder))
    
    def scrub_files(self, file_paths):
        def scrub_thread():
            self.progress.start()
            for file_path in file_paths:
                success = self.scrubber.scrub_file(Path(file_path))
                if success:
                    self.log(f"Scrubbed: {Path(file_path).name}")
                else:
                    self.log(f"Failed: {Path(file_path).name}")
            self.progress.stop()
            messagebox.showinfo("Complete", "File scrubbing completed!")
        
        threading.Thread(target=scrub_thread, daemon=True).start()
    
    def scrub_folder(self, folder_path):
        def scrub_thread():
            self.progress.start()
            results = self.scrubber.scrub_folder(folder_path)
            self.progress.stop()
            messagebox.showinfo("Complete", 
                              f"Scrubbed {results['successful']}/{results['total']} files")
        
        threading.Thread(target=scrub_thread, daemon=True).start()
    
    def select_watch_folder(self):
        folder = filedialog.askdirectory(title="Select folder to watch")
        if folder:
            self.watch_folder = Path(folder)
            self.watch_status.config(text=f"Watching: {folder}")
    
    def start_watching(self):
        if hasattr(self, 'watch_folder'):
            self.watcher = FolderWatcher(self.watch_folder)
            self.watcher.start()
            self.watch_status.config(text=f"Watching: {self.watch_folder} - ACTIVE")
            self.log(f"Started watching folder: {self.watch_folder}")
    
    def stop_watching(self):
        if self.watcher:
            self.watcher.stop()
            self.watch_status.config(text=f"Watching: {self.watch_folder} - INACTIVE")
            self.log(f"Stopped watching folder: {self.watch_folder}")
    
    def log(self, message):
        self.logs_text.insert('end', f"{message}\n")
        self.logs_text.see('end')
    
    def run(self):
        self.root.mainloop()