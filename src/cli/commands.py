import argparse
from pathlib import Path
import sys
from typing import List

from ..core.scrubber import UniversalScrubber
from ..core.folder_watcher import FolderWatcher
from ..utils.logger import SecureLogger

class CLI:
    def __init__(self):
        self.scrubber = UniversalScrubber()
        self.parser = self.setup_parser()
    
    def setup_parser(self):
        parser = argparse.ArgumentParser(
            description="Comms Shield - Universal Metadata Scrubber",
            epilog="Example: comms-shield scrub document.pdf"
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Scrub command
        scrub_parser = subparsers.add_parser('scrub', help='Scrub files or folders')
        scrub_parser.add_argument('path', help='File or folder path to scrub')
        scrub_parser.add_argument('-o', '--output', help='Output path')
        scrub_parser.add_argument('--show-status', action='store_true', 
                                help='Show scrubber library status')
        
        # Watch command
        watch_parser = subparsers.add_parser('watch', help='Monitor folder for auto-scrubbing')
        watch_parser.add_argument('folder', help='Folder to watch')
        watch_parser.add_argument('-o', '--output', help='Output folder for scrubbed files')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show scrubber status')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Generate security report')
        report_parser.add_argument('-d', '--days', type=int, default=7, 
                                 help='Report period in days')
        
        return parser
    
    def handle_scrub(self, args):
        """Handle scrub command"""
        path = Path(args.path)
        
        if args.show_status:
            status = self.scrubber.get_scrubber_status()
            print("Scrubber Library Status:")
            for lib, available in status.items():
                status_str = "✓ Available" if available else "✗ Not Available"
                print(f"  {lib}: {status_str}")
            print()
        
        if not path.exists():
            print(f"Error: Path not found: {path}")
            return
        
        if path.is_file():
            print(f"Scrubbing file: {path.name}")
            success = self.scrubber.scrub_file(path, Path(args.output) if args.output else None)
            if success:
                print(f"✓ Successfully scrubbed: {path.name}")
            else:
                print(f"✗ Failed to scrub: {path.name}")
        
        elif path.is_dir():
            print(f"Scrubbing folder: {path}")
            results = self.scrubber.scrub_folder(path, Path(args.output) if args.output else None)
            self.print_folder_results(results)
    
    def handle_watch(self, args):
        """Handle watch command"""
        folder = Path(args.folder)
        output_folder = Path(args.output) if args.output else None
        
        if not folder.exists():
            print(f"Error: Folder not found: {folder}")
            return
        
        print(f"Starting folder watcher: {folder}")
        print("Press Ctrl+C to stop...")
        
        watcher = FolderWatcher(folder, output_folder)
        
        try:
            watcher.start()
            while True:
                # Keep the main thread alive
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping folder watcher...")
            watcher.stop()
    
    def handle_status(self, args):
        """Handle status command"""
        status = self.scrubber.get_scrubber_status()
        print("Comms Shield - Scrubber Status")
        print("=" * 40)
        
        print("\nLibrary Dependencies:")
        for lib, available in status.items():
            status_str = "✓ Available" if available else "✗ Not Available"
            print(f"  {lib:15} {status_str}")
        
        print(f"\nSupported Formats: {', '.join(self.scrubber.get_supported_formats())}")
        
        # Show recent activity
        logger = SecureLogger()
        recent_logs = logger.get_recent_logs(5)
        
        if recent_logs:
            print("\nRecent Activity:")
            for log in recent_logs:
                print(f"  {log[1]} - {log[3]} - {log[8]}")
    
    def handle_report(self, args):
        """Handle report command"""
        logger = SecureLogger()
        report = logger.generate_report(args.days)
        
        print(f"Comms Shield - Security Report (Last {args.days} days)")
        print("=" * 50)
        print(f"Total Operations: {report['total_operations']}")
        print(f"Successful: {report['successful']}")
        print(f"Failed: {report['failed']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        
        if report['failed'] > 0:
            print(f"\n⚠  {report['failed']} operations failed. Check logs for details.")
    
    def print_folder_results(self, results):
        """Print folder scrubbing results"""
        print(f"\nScrubbing Results:")
        print(f"  Total files: {results['total']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Failed: {results['failed']}")
        
        if results['failed_files']:
            print(f"\nFailed files:")
            for file in results['failed_files']:
                print(f"  - {file}")
    
    def run(self, args=None):
        """Run the CLI"""
        if args is None:
            args = sys.argv[1:]
        
        if not args:
            self.parser.print_help()
            return
        
        parsed_args = self.parser.parse_args(args)
        
        if parsed_args.command == 'scrub':
            self.handle_scrub(parsed_args)
        elif parsed_args.command == 'watch':
            self.handle_watch(parsed_args)
        elif parsed_args.command == 'status':
            self.handle_status(parsed_args)
        elif parsed_args.command == 'report':
            self.handle_report(parsed_args)
        else:
            self.parser.print_help()