# proxy.py - Main HTTP server (minimal changes)
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import cgi
import sys
import io
from contextlib import redirect_stdout

# Import watcher functionality
from watcher import (
    start_file_watcher, stop_file_watcher, set_watch_folder,
    process_existing_files, get_clean_files, get_watcher_status,
    get_watcher_logs, watch_folder, clean_folder
)

from universal_scrubber import detect_and_scrub
from metadata_analyzer import show_comprehensive_metadata

# Add the current directory to path to ensure imports work
sys.path.append('.')

# Global logs storage (for non-watcher logs)
logs = []

def add_log(message, level="INFO"):
    """Add log entry with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    logs.append(log_entry)
    print(f"PROXY: {log_entry}")

def get_file_metadata(file_path: Path):
    """Extract metadata from file and return as formatted string"""
    try:
        # Capture the metadata output
        f = io.StringIO()
        with redirect_stdout(f):
            show_comprehensive_metadata(file_path)
        metadata_output = f.getvalue()
        return metadata_output
    except Exception as e:
        return f"Error extracting metadata: {str(e)}"

def get_all_logs():
    """Combine proxy logs and watcher logs"""
    all_logs = logs + get_watcher_logs()
    all_logs.sort(key=lambda x: x[1:20])  # Sort by timestamp
    return all_logs

class MetadataScrubberHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/logs':
            self.send_logs()
        elif parsed_path.path == '/downloads':
            self.send_downloads_list()
        elif parsed_path.path == '/clean_files':
            self.send_clean_files()
        elif parsed_path.path == '/watcher_status':
            self.send_watcher_status()
        elif parsed_path.path.startswith('/download/'):
            self.send_download_file(parsed_path.path)
        elif parsed_path.path.startswith('/metadata/'):
            self.send_file_metadata(parsed_path.path)
        else:
            # Serve static files (HTML, CSS, JS)
            super().do_GET()

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/upload':
            self.handle_upload()
        elif parsed_path.path == '/start_watcher':
            self.handle_start_watcher()
        elif parsed_path.path == '/stop_watcher':
            self.handle_stop_watcher()
        elif parsed_path.path == '/set_watch_folder':
            self.handle_set_watch_folder()
        elif parsed_path.path == '/process_existing':
            self.handle_process_existing()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_upload(self):
        """Handle file upload and scrubbing"""
        try:
            content_type = self.headers.get('content-type')
            if not content_type or not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Only multipart/form-data supported")
                return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            if 'file' not in form:
                self.send_error(400, "No file uploaded")
                return

            file_item = form['file']
            if not file_item.filename:
                self.send_error(400, "No file selected")
                return

            # Ensure uploads directory exists
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)
            downloads_dir = Path("downloads")
            downloads_dir.mkdir(exist_ok=True)

            # Save uploaded file
            upload_path = uploads_dir / file_item.filename
            with open(upload_path, 'wb') as f:
                f.write(file_item.file.read())

            add_log(f"File uploaded: {file_item.filename}")

            # Get original metadata
            original_metadata = get_file_metadata(upload_path)
            add_log(f"Original metadata extracted for: {file_item.filename}")

            # Scrub the file
            try:
                detect_and_scrub(upload_path)
                add_log(f"File scrubbed successfully: {file_item.filename}")
                
                # Check if scrubbed file was created
                scrubbed_filename = f"scrubbed_{file_item.filename}"
                scrubbed_path = downloads_dir / scrubbed_filename
                
                if scrubbed_path.exists():
                    # Get scrubbed metadata
                    scrubbed_metadata = get_file_metadata(scrubbed_path)
                    add_log(f"Scrubbed metadata extracted for: {scrubbed_filename}")
                    
                    response = {
                        "status": "success",
                        "message": "File scrubbed successfully",
                        "original_file": file_item.filename,
                        "scrubbed_file": scrubbed_filename,
                        "original_metadata": original_metadata,
                        "scrubbed_metadata": scrubbed_metadata
                    }
                else:
                    response = {
                        "status": "error",
                        "message": "Scrubbing completed but output file not found"
                    }
                    add_log(f"Output file not found: {scrubbed_path}", "ERROR")
                    
            except Exception as e:
                add_log(f"Scrubbing failed: {str(e)}", "ERROR")
                response = {
                    "status": "error",
                    "message": f"Scrubbing failed: {str(e)}"
                }

            self.send_json_response(response)

        except Exception as e:
            add_log(f"Upload handling error: {str(e)}", "ERROR")
            self.send_error(500, f"Server error: {str(e)}")

    def handle_start_watcher(self):
        """Handle starting the file watcher"""
        response = start_file_watcher()
        self.send_json_response(response)

    def handle_stop_watcher(self):
        """Handle stopping the file watcher"""
        response = stop_file_watcher()
        self.send_json_response(response)

    def handle_set_watch_folder(self):
        """Handle setting a new watch folder"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, "No data provided")
            return
            
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
            folder_path = data.get('folder_path', '')
            
            if not folder_path:
                self.send_error(400, "No folder path provided")
                return
                
            response = set_watch_folder(folder_path)
            self.send_json_response(response)
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON data")

    def handle_process_existing(self):
        """Handle processing existing files in watch folder"""
        response = process_existing_files()
        self.send_json_response(response)

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_logs(self):
        """Send the logs as JSON"""
        all_logs = get_all_logs()
        self.send_json_response(all_logs)

    def send_downloads_list(self):
        """Send list of available downloads"""
        downloads_dir = Path("downloads")
        downloads = []
        
        if downloads_dir.exists():
            for file_path in downloads_dir.glob('*'):
                if file_path.is_file():
                    downloads.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })

        self.send_json_response(downloads)

    def send_clean_files(self):
        """Send list of cleaned files"""
        clean_files = get_clean_files()
        self.send_json_response(clean_files)

    def send_watcher_status(self):
        """Send current watcher status"""
        status = get_watcher_status()
        self.send_json_response(status)

    def send_download_file(self, path):
        """Serve a file for download"""
        filename = path.split('/')[-1]
        
        # Check both downloads and clean folders
        file_path = Path("downloads") / filename
        if not file_path.exists():
            file_path = clean_folder / filename
        
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
                
        except Exception as e:
            add_log(f"Download error: {str(e)}", "ERROR")
            self.send_error(500, "Download failed")

    def send_file_metadata(self, path):
        """Send metadata for a specific file"""
        filename = path.split('/')[-1]
        
        # Check both downloads and clean folders
        file_path = Path("downloads") / filename
        if not file_path.exists():
            file_path = clean_folder / filename
        
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        try:
            metadata = get_file_metadata(file_path)
            self.send_json_response({"metadata": metadata})
            
        except Exception as e:
            add_log(f"Metadata extraction error: {str(e)}", "ERROR")
            self.send_error(500, "Metadata extraction failed")

    def log_message(self, format, *args):
        """Override to use our logging system"""
        add_log(format % args, "ACCESS")

def run_server(port=8000):
    """Start the proxy server"""
    # Create necessary directories
    Path("uploads").mkdir(exist_ok=True)
    Path("downloads").mkdir(exist_ok=True)
    watch_folder.mkdir(exist_ok=True)
    clean_folder.mkdir(exist_ok=True)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetadataScrubberHandler)
    
    add_log(f"Starting metadata scrubber server on port {port}")
    add_log("Access the application at: http://localhost:8000")
    add_log("Single file upload: http://localhost:8000/index.html")
    add_log("Folder watcher: http://localhost:8000/watcher.html")
    add_log("Uploads directory: ./uploads")
    add_log("Downloads directory: ./downloads")
    add_log("Watch folder: ./watch_folder")
    add_log("Clean folder: ./clean")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        add_log("Server stopped by user")
        stop_file_watcher()
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run_server()