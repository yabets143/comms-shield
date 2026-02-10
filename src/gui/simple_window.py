import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import sys
import os
import io
from contextlib import redirect_stdout

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.scrubber import UniversalScrubber
from utils.logger import SecureLogger
from core.metadata_analyzer import show_comprehensive_metadata

class SimpleMainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.scrubber = UniversalScrubber()
        self.logger = SecureLogger()
        self.selected_files = []
        self.setup_ui()
    
    def setup_window(self):
        self.root.title("Comms Shield - Metadata Protection Toolkit")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🛡️ Comms Shield", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(main_frame, text="Defensive Communication Security Toolkit",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        
        # File Scrubber tab
        scrubber_frame = ttk.Frame(notebook, padding="10")
        self.setup_scrubber_tab(scrubber_frame)
        
        # Folder Scrubber tab
        folder_frame = ttk.Frame(notebook, padding="10")
        self.setup_folder_tab(folder_frame)
        
        # Logs tab
        logs_frame = ttk.Frame(notebook, padding="10")
        self.setup_logs_tab(logs_frame)
        
        # Status tab
        status_frame = ttk.Frame(notebook, padding="10")
        self.setup_status_tab(status_frame)
        
        notebook.add(scrubber_frame, text="File Scrubber")
        notebook.add(folder_frame, text="Folder Scrubber") 
        notebook.add(logs_frame, text="Operation Logs")
        notebook.add(status_frame, text="System Status")
        notebook.pack(expand=True, fill=tk.BOTH)
    
    def setup_scrubber_tab(self, parent):
        """Setup file scrubbing interface"""
        # File selection
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Select File(s) to Scrub", 
                  command=self.browse_files).pack(pady=5)
        
        self.selected_files_label = ttk.Label(file_frame, text="No files selected")
        self.selected_files_label.pack(pady=5)
        
        # Scrub button
        ttk.Button(parent, text="Start Scrubbing", 
                  command=self.start_scrubbing,
                  style='Accent.TButton').pack(pady=10)
        
        # Progress
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Output area
        output_frame = ttk.LabelFrame(parent, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_folder_tab(self, parent):
        """Setup folder scrubbing interface"""
        # Folder selection
        folder_frame = ttk.LabelFrame(parent, text="Folder Selection", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(folder_frame, text="Select Folder to Scrub", 
                  command=self.browse_folder).pack(pady=5)
        
        self.selected_folder_label = ttk.Label(folder_frame, text="No folder selected")
        self.selected_folder_label.pack(pady=5)
        
        # Output folder
        ttk.Button(folder_frame, text="Select Output Folder (Optional)", 
                  command=self.browse_output_folder).pack(pady=5)
        
        self.output_folder_label = ttk.Label(folder_folder, text="Same as input folder")
        self.output_folder_label.pack(pady=5)
        
        # Scrub button
        ttk.Button(parent, text="Start Folder Scrubbing", 
                  command=self.start_folder_scrubbing,
                  style='Accent.TButton').pack(pady=10)
        
        # Progress
        self.folder_progress = ttk.Progressbar(parent, mode='indeterminate')
        self.folder_progress.pack(fill=tk.X, pady=5)
        
        # Results
        self.folder_results = scrolledtext.ScrolledText(parent, height=10, width=80)
        self.folder_results.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def setup_logs_tab(self, parent):
        """Setup logs display"""
        # Refresh button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Export Logs", 
                  command=self.export_logs).pack(side=tk.LEFT)
        
        # Logs display
        logs_frame = ttk.LabelFrame(parent, text="Operation Logs", padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20, width=80)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Load initial logs
        self.refresh_logs()
    
    def setup_status_tab(self, parent):
        """Setup system status display"""
        # Scrubber status
        status_frame = ttk.LabelFrame(parent, text="Scrubber Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(parent, text="Refresh Status", 
                  command=self.refresh_status).pack(pady=5)
        
        # Load initial status
        self.refresh_status()
    
    def browse_files(self):
        """Browse for files to scrub"""
        files = filedialog.askopenfilenames(
            title="Select files to scrub",
            filetypes=[
                ("All files", "*.*"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
                ("PDFs", "*.pdf"),
                ("Office documents", "*.docx *.xlsx *.pptx"),
                ("Audio/Video", "*.mp3 *.mp4 *.wav *.flac *.m4a")
            ]
        )
        if files:
            self.selected_files = [Path(f) for f in files]
            file_names = ", ".join([f.name for f in self.selected_files[:3]])
            if len(self.selected_files) > 3:
                file_names += f" ... and {len(self.selected_files) - 3} more"
            self.selected_files_label.config(text=file_names)
    
    def browse_folder(self):
        """Browse for folder to scrub"""
        folder = filedialog.askdirectory(title="Select folder to scrub")
        if folder:
            self.selected_folder = Path(folder)
            self.selected_folder_label.config(text=str(self.selected_folder))
    
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = Path(folder)
            self.output_folder_label.config(text=str(self.output_folder))
    
    def start_scrubbing(self):
        """Start scrubbing selected files"""
        if not self.selected_files:
            messagebox.showwarning("No files", "Please select files to scrub first")
            return
        
        def scrub_thread():
            self.progress.start()
            self.output_text.delete(1.0, tk.END)
            
            for i, file_path in enumerate(self.selected_files, 1):
                self.output_text.insert(tk.END, f"Scrubbing: {file_path.name}\n")
                self.output_text.see(tk.END)
                self.root.update()
                
                success = self.scrubber.scrub_file(file_path)
                
                if success:
                    self.output_text.insert(tk.END, f"✓ Success: scrubbed_{file_path.name}\n")
                else:
                    self.output_text.insert(tk.END, f"✗ Failed: {file_path.name}\n")
                
                self.output_text.see(tk.END)
                self.root.update()
            
            self.progress.stop()
            messagebox.showinfo("Complete", f"Scrubbed {len(self.selected_files)} files")
            self.refresh_logs()
        
        threading.Thread(target=scrub_thread, daemon=True).start()
    
    def start_folder_scrubbing(self):
        """Start scrubbing selected folder"""
        if not hasattr(self, 'selected_folder'):
            messagebox.showwarning("No folder", "Please select a folder to scrub first")
            return
        
        output_folder = getattr(self, 'output_folder', None)
        
        def scrub_thread():
            self.folder_progress.start()
            self.folder_results.delete(1.0, tk.END)
            
            self.folder_results.insert(tk.END, f"Scrubbing folder: {self.selected_folder}\n")
            if output_folder:
                self.folder_results.insert(tk.END, f"Output folder: {output_folder}\n")
            self.folder_results.insert(tk.END, "Working...\n")
            self.root.update()
            
            results = self.scrubber.scrub_folder(self.selected_folder, output_folder)
            
            self.folder_results.delete(1.0, tk.END)
            self.folder_results.insert(tk.END, f"Folder Scrubbing Results:\n")
            self.folder_results.insert(tk.END, f"Total files: {results['total']}\n")
            self.folder_results.insert(tk.END, f"Successful: {results['successful']}\n")
            self.folder_results.insert(tk.END, f"Failed: {results['failed']}\n")
            
            if results['failed_files']:
                self.folder_results.insert(tk.END, f"\nFailed files:\n")
                for file in results['failed_files']:
                    self.folder_results.insert(tk.END, f"  - {file}\n")
            
            self.folder_progress.stop()
            self.refresh_logs()
        
        threading.Thread(target=scrub_thread, daemon=True).start()
    
    def refresh_logs(self):
        """Refresh logs display"""
        try:
            logs = self.logger.get_recent_logs(50)
            self.logs_text.delete(1.0, tk.END)
            
            if not logs:
                self.logs_text.insert(tk.END, "No logs found")
                return
            
            for log in reversed(logs):  # Show newest first
                log_id, timestamp, level, operation, filename, orig_size, scrub_size, metadata, status, error = log
                log_entry = f"[{timestamp}] {level} - {operation}"
                if filename:
                    log_entry += f" - {filename}"
                log_entry += f" - {status}"
                if error:
                    log_entry += f" - {error}"
                log_entry += "\n"
                
                self.logs_text.insert(tk.END, log_entry)
        except Exception as e:
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"Error loading logs: {e}")
    
    def clear_logs(self):
        """Clear logs (interface only)"""
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.insert(tk.END, "Logs cleared from display\n")
    
    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Export logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.logs_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Logs exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export logs: {e}")
    
    def refresh_status(self):
        """Refresh system status"""
        status = self.scrubber.get_scrubber_status()
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "Library Dependencies:\n")
        self.status_text.insert(tk.END, "=" * 40 + "\n")
        
        for lib, available in status.items():
            status_str = "✓ Available" if available else "✗ Not Available"
            self.status_text.insert(tk.END, f"{lib:20} {status_str}\n")
        
        self.status_text.insert(tk.END, "\nSupported File Formats:\n")
        self.status_text.insert(tk.END, "=" * 40 + "\n")
        formats = self.scrubber.get_supported_formats()
        self.status_text.insert(tk.END, ", ".join(formats) + "\n")
        
        # Show recent activity count
        try:
            logs = self.logger.get_recent_logs(100)
            success_count = sum(1 for log in logs if log[8] == 'success')  # status field
            fail_count = sum(1 for log in logs if log[8] == 'error')
            
            self.status_text.insert(tk.END, f"\nRecent Activity (last 100 operations):\n")
            self.status_text.insert(tk.END, "=" * 40 + "\n")
            self.status_text.insert(tk.END, f"Successful: {success_count}\n")
            self.status_text.insert(tk.END, f"Failed: {fail_count}\n")
        except:
            self.status_text.insert(tk.END, "\nCould not load activity stats\n")
    
    def run(self):
        """Start the GUI"""
        # Configure styles
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='white', background='#007acc')
        
        self.root.mainloop()