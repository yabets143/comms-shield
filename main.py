import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    parser = argparse.ArgumentParser(description='Comms Shield - Metadata Protection Toolkit')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help='Start graphical interface')
    
    # CLI commands (delegated to CLI class)
    scrub_parser = subparsers.add_parser('scrub', help='Scrub a file or folder')
    scrub_parser.add_argument('path', help='File or folder path to scrub')
    scrub_parser.add_argument('-o', '--output', help='Output path')
    scrub_parser.add_argument('--show-status', action='store_true', 
                            help='Show scrubber library status')
    
    watch_parser = subparsers.add_parser('watch', help='Monitor a folder for auto-scrubbing')
    watch_parser.add_argument('folder', help='Folder to watch')
    watch_parser.add_argument('-o', '--output', help='Output folder for scrubbed files')
    
    status_parser = subparsers.add_parser('status', help='Show scrubber status')
    
    report_parser = subparsers.add_parser('report', help='Generate security report')
    report_parser.add_argument('-d', '--days', type=int, default=7, help='Report period in days')
    
    args = parser.parse_args()
    
    if args.command == 'gui':
        from src.gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    
    elif args.command in ['scrub', 'watch', 'status', 'report']:
        from src.cli.commands import CLI
        cli = CLI()
        
        # Reconstruct args for CLI
        cli_args = [args.command]
        if hasattr(args, 'path'):
            cli_args.append(args.path)
        if hasattr(args, 'output') and args.output:
            cli_args.extend(['-o', args.output])
        if hasattr(args, 'show_status') and args.show_status:
            cli_args.append('--show-status')
        if hasattr(args, 'days'):
            cli_args.extend(['--days', str(args.days)])
        
        cli.run(cli_args)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()