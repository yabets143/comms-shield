from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import shutil
from pathlib import Path
import threading
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import cgi
import sys
import io
from contextlib import redirect_stdout

from universal_scrubber import detect_and_scrub
from metadata_analyzer import show_comprehensive_metadata

# Add the current directory to path to ensure imports work
sys.path.append('.')

# Global logs storage
logs = []

def add_log(message, level="INFO"):
    """Add log entry with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    logs.append(log_entry)
    print(log_entry)

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

class MetadataScrubberHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/logs':
            self.send_logs()
        elif parsed_path.path == '/downloads':
            self.send_downloads_list()
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

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            add_log(f"Upload handling error: {str(e)}", "ERROR")
            self.send_error(500, f"Server error: {str(e)}")

    def send_logs(self):
        """Send the logs as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(logs).encode())

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

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(downloads).encode())

    def send_download_file(self, path):
        """Serve a file for download"""
        filename = path.split('/')[-1]
        file_path = Path("downloads") / filename
        
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
        file_path = Path("downloads") / filename
        
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        try:
            metadata = get_file_metadata(file_path)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"metadata": metadata}).encode())
            
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
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MetadataScrubberHandler)
    
    add_log(f"Starting metadata scrubber server on port {port}")
    add_log("Access the application at: http://localhost:8000")
    add_log("Uploads directory: ./uploads")
    add_log("Downloads directory: ./downloads")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        add_log("Server stopped by user")
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run_server()