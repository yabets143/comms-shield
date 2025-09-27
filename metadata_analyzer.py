#!/usr/bin/env python3
# metadata_analyzer.py - Comprehensive metadata analysis like exiftool

import argparse
from pathlib import Path
from PIL import Image, ExifTags
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from mutagen import File as MutagenFile
import pikepdf
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

def show_file_signature(file_path: Path):
    """Show file signature/headers."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            print("\n--- File Signature (Hex) ---")
            hex_str = ' '.join(f'{byte:02x}' for byte in header)
            print(f"Hex: {hex_str}")
            ascii_str = ''.join(chr(byte) if 32 <= byte <= 126 else '.' for byte in header)
            print(f"ASCII: {ascii_str}")
    except Exception as e:
        print(f"[WARN] File signature reading failed: {e}")

def show_image_metadata(file_path: Path):
    """Show detailed image metadata."""
    try:
        with Image.open(file_path) as img:
            print("\n--- PIL Image Metadata ---")
            print(f"Format: {img.format}")
            print(f"Size: {img.size}")
            print(f"Mode: {img.mode}")
            
            # EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                print("\n--- EXIF Data ---")
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    if tag_name == 'MakerNote' and isinstance(value, bytes):
                        continue
                   
                    print(f"{tag_name}: {value}")
            else:
                print("No EXIF data found")
             
    except Exception as e:
        print(f"[WARN] Image metadata extraction failed: {e}")

def show_pdf_metadata(file_path: Path):
    """Show detailed PDF metadata."""
    try:
        with pikepdf.open(file_path) as pdf:
            print("\n--- PDF Metadata ---")
            
            # Document info
            if hasattr(pdf, 'docinfo') and pdf.docinfo:
                print("\n--- PDF Document Info ---")
                for key, value in pdf.docinfo.items():
                    print(f"{key}: {value}")
            
            # XMP metadata
            if '/Metadata' in pdf.Root:
                print("\n--- XMP Metadata ---")
                print("XMP metadata stream present")
            
            # PDF structure info
            print(f"\n--- PDF Structure ---")
            print(f"PDF version: {pdf.pdf_version}")
            print(f"Number of pages: {len(pdf.pages)}")
            print(f"Encrypted: {pdf.is_encrypted}")
            
            # Check for embedded files
            if '/Names' in pdf.Root and '/EmbeddedFiles' in pdf.Root.Names:
                print("Embedded files present")
                
    except Exception as e:
        print(f"[WARN] PDF metadata extraction failed: {e}")

def show_office_metadata(file_path: Path):
    """Show Office document metadata."""
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # Core metadata
            if 'docProps/core.xml' in zf.namelist():
                with zf.open('docProps/core.xml') as core_file:
                    tree = ET.parse(core_file)
                    root = tree.getroot()
                    print("\n--- Office Core Metadata ---")
                    ns = {'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'}
                    for elem_name in ['creator', 'lastModifiedBy', 'created', 'modified', 'title', 'subject']:
                        elem = root.find(f'cp:{elem_name}', ns)
                        if elem is not None and elem.text:
                            print(f"{elem_name}: {elem.text}")
            
            # App metadata
            if 'docProps/app.xml' in zf.namelist():
                with zf.open('docProps/app.xml') as app_file:
                    tree = ET.parse(app_file)
                    root = tree.getroot()
                    print("\n--- Office Application Metadata ---")
                    for elem in root.iter():
                        if elem.text and elem.text.strip() and not elem.tag.endswith('}Pages'):
                            tag = elem.tag.split('}')[-1]
                            print(f"{tag}: {elem.text}")
            
            # Document structure
            print(f"\n--- Office Document Structure ---")
            files = [name for name in zf.namelist() if not name.endswith('/')]
            print(f"Total files in package: {len(files)}")
            for component in ['word/', 'xl/', 'ppt/', 'docProps/']:
                comp_files = [name for name in files if name.startswith(component)]
                if comp_files:
                    print(f"  {component}: {len(comp_files)} files")
                        
    except Exception as e:
        print(f"[WARN] Office metadata extraction failed: {e}")

def show_media_metadata(file_path: Path):
    """Show audio/video metadata."""
    try:
        media = MutagenFile(file_path)
        if media is not None:
            print("\n--- Media Metadata ---")
            for key, value in media.items():
                # Limit long values for readability
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"{key}: {value_str}")
            
            # Media info
            if hasattr(media, 'info'):
                print(f"\n--- Media Info ---")
                info = media.info
                if hasattr(info, 'length'):
                    print(f"Length: {info.length:.2f} seconds")
                if hasattr(info, 'bitrate'):
                    print(f"Bitrate: {info.bitrate} kbps")
                if hasattr(info, 'sample_rate'):
                    print(f"Sample rate: {info.sample_rate} Hz")
                    
    except Exception as e:
        print(f"[WARN] Media metadata extraction failed: {e}")

def show_comprehensive_metadata(file_path: Path):
    """Main function to show comprehensive metadata analysis."""
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE METADATA ANALYSIS: {file_path.name}")
    print(f"{'='*60}")
    
    # File basics
    show_file_signature(file_path)
    
    # File system metadata
    try:
        stat = file_path.stat()
        print("\n--- File System Metadata ---")
        print(f"Size: {stat.st_size:,} bytes")
        print(f"Created: {datetime.fromtimestamp(stat.st_ctime)}")
        print(f"Modified: {datetime.fromtimestamp(stat.st_mtime)}")
        print(f"Accessed: {datetime.fromtimestamp(stat.st_atime)}")
    except Exception as e:
        print(f"[WARN] File system metadata failed: {e}")

    # Type-specific detailed metadata
    suffix = file_path.suffix.lower()
    
    if suffix in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.webp']:
        show_image_metadata(file_path)
    elif suffix == '.pdf':
        show_pdf_metadata(file_path)
    elif suffix in ['.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp']:
        show_office_metadata(file_path)
    elif suffix in ['.mp3', '.flac', '.mp4', '.m4a', '.wav', '.ogg', '.avi', '.mkv']:
        show_media_metadata(file_path)
    else:
        print("\n--- Generic File Analysis ---")
        print(f"File type: {suffix or 'Unknown'}")
    
    # Hachoir as universal fallback
    try:
        parser = createParser(str(file_path))
        if parser:
            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    print("\n--- Hachoir Universal Metadata ---")
                    for line in metadata.exportPlaintext():
                        print(line)
    except Exception as e:
        print(f"[WARN] Hachoir parsing failed: {e}")
    
    print(f"\n{'='*60}")
    print(f"END OF METADATA ANALYSIS")
    print(f"{'='*60}")

def main():
    """Standalone CLI for metadata analysis."""
    parser = argparse.ArgumentParser(description="Comprehensive metadata analyzer")
    parser.add_argument("files", nargs="+", help="Path(s) to file(s)")
    
    args = parser.parse_args()
    
    for file in args.files:
        path = Path(file)
        if not path.exists():
            print(f"[ERROR] File not found: {file}")
            continue
        
        show_comprehensive_metadata(path)

if __name__ == "__main__":
    main()