import argparse
import shutil
from pathlib import Path
from PIL import Image
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from mutagen import File as MutagenFile
import pikepdf
import tempfile  
import xml.etree.ElementTree as ET 


try:
    from metadata_analyzer import show_comprehensive_metadata
    METADATA_ANALYZER_AVAILABLE = True
except ImportError:
    METADATA_ANALYZER_AVAILABLE = False
    print("[INFO] Advanced metadata analyzer not available")


def scrub_image(input_path: Path, output_path: Path):
    """Remove EXIF metadata from images."""
    with Image.open(input_path) as img:
        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)
        clean.save(output_path, format=img.format)


def scrub_audio_video(input_path: Path, output_path: Path):
    """Remove metadata from audio/video (MP3, MP4, etc.)."""
    media = MutagenFile(input_path, easy=True)
    if media:
        media.delete()  # remove tags
        media.save()
    shutil.copy(input_path, output_path)


def scrub_docx_images(docx_path: Path, temp_dir: Path):
    """Scrub metadata from images embedded in DOCX."""
    try:
        media_dir = temp_dir / 'word' / 'media'
        if media_dir.exists():
            for img_file in media_dir.glob('*.*'):
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                    try:
                        scrub_image(img_file, img_file)
                        print(f"[INFO] Scrubbed embedded image: {img_file.name}")
                    except Exception as e:
                        print(f"[WARN] Failed to scrub embedded image {img_file}: {e}")
        
        # Also check for images in headers/footers
        for rels_dir in temp_dir.glob('**/rels'):
            for rels_file in rels_dir.glob('*.rels'):
                try:
                    tree = ET.parse(rels_file)
                    root = tree.getroot()
                    # You could parse relationships to find embedded images here
                    # This is a simplified version
                except:
                    pass
                    
    except Exception as e:
        print(f"[WARN] DOCX image scrub failed: {e}")

def scrub_pdf_images(pdf_path: Path):
    """Remove metadata from images embedded in PDF. Returns path to scrubbed file."""
    try:
        with pikepdf.open(pdf_path) as pdf:
            modified = False
            for page in pdf.pages:
                if '/Resources' in page and '/XObject' in page.Resources:
                    xobjects = page.Resources.XObject
                    for obj_name in list(xobjects.keys()):  # Use list to avoid modification during iteration
                        xobj = xobjects[obj_name]
                        if xobj.Subtype == '/Image':
                            # Remove image metadata by recompressing
                            if '/Metadata' in xobj:
                                del xobj.Metadata
                                modified = True
            if modified:
                # Save to temporary file
                temp_path = pdf_path.parent / f"temp_{pdf_path.name}"
                pdf.save(temp_path, encryption=False, object_stream_mode=pikepdf.ObjectStreamMode.disable)
                return temp_path
            return None
    except Exception as e:
        print(f"[WARN] PDF image scrub failed: {e}")
        return None
def scrub_pdf(input_path: Path, output_path: Path):
    """Remove metadata from PDFs including embedded images."""
    try:
        # First pass: remove PDF metadata
        with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
            # Remove all metadata
            if '/Metadata' in pdf.Root:
                del pdf.Root.Metadata
            
            # Remove all docinfo entries systematically
            for key in list(pdf.docinfo.keys()):
                del pdf.docinfo[key]
            
            # Remove embedded files
            if '/Names' in pdf.Root and '/EmbeddedFiles' in pdf.Root.Names:
                del pdf.Root.Names.EmbeddedFiles
            
            # Save first pass
            temp_path = output_path.parent / f"temp_first_{output_path.name}"
            pdf.save(temp_path, encryption=False, object_stream_mode=pikepdf.ObjectStreamMode.disable)
        
        # Second pass: scrub embedded images
        final_pdf = scrub_pdf_images(temp_path)
        if final_pdf:
            # If image scrubbing created a new file, use it
            shutil.move(final_pdf, output_path)
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
        else:
            # No image scrubbing needed, just move the temp file
            shutil.move(temp_path, output_path)
            
    except Exception as e:
        print(f"[ERROR] PDF scrub failed: {e}")
        # Clean up any temp files
        temp_path = output_path.parent / f"temp_first_{output_path.name}"
        if temp_path.exists():
            temp_path.unlink()
        shutil.copy(input_path, output_path)
def scrub_office(input_path: Path, output_path: Path):
    """Remove metadata from Office docs including embedded images."""
    import zipfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Extract DOCX
        with zipfile.ZipFile(input_path, "r") as zin:
            zin.extractall(tmpdir)

        # Remove core metadata files
        for meta_file in ["docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"]:
            target = tmpdir_path / meta_file
            if target.exists():
                target.unlink()

        # Scrub embedded images
        scrub_docx_images(input_path, tmpdir_path)

        # Create new DOCX
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for file in tmpdir_path.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(tmpdir_path)
                    zout.write(file, arcname)
def scrub_generic(input_path: Path, output_path: Path):
    """Fallback scrubber - just copies file."""
    shutil.copy(input_path, output_path)


def detect_and_scrub(file_path: Path, output_path: Path = None):
    """Detect file type and scrub accordingly."""
    suffix = file_path.suffix.lower()

    if output_path is None:
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        output_path = downloads_dir / f"scrubbed_{file_path.name}"

    output_path.parent.mkdir(exist_ok=True)

    try:
        if suffix in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"]:
            scrub_image(file_path, output_path)
        elif suffix == ".pdf":
            scrub_pdf(file_path, output_path)
        elif suffix in [".mp3", ".flac", ".mp4", ".m4a", ".wav", ".ogg"]:
            scrub_audio_video(file_path, output_path)
        elif suffix in [".docx", ".xlsx", ".pptx"]:
            scrub_office(file_path, output_path)
        else:
            scrub_generic(file_path, output_path)

        print(f"[INFO] Scrubbed file saved → {output_path}")

        # Always show metadata AFTER scrubbing
        show_metadata(output_path)

    except Exception as e:
        print(f"[ERROR] Failed to scrub {file_path}: {e}")
        scrub_generic(file_path, output_path)


def show_metadata(file_path: Path):
    """Show metadata using the comprehensive analyzer."""
    if METADATA_ANALYZER_AVAILABLE:
        show_comprehensive_metadata(file_path)
    else:
        # Fallback to basic metadata display
        show_basic_metadata(file_path)


def main():
    parser = argparse.ArgumentParser(description="Universal metadata scrubber")
    parser.add_argument("files", nargs="+", help="Path(s) to file(s)")
    parser.add_argument("--show", action="store_true", help="Show metadata before scrubbing")

    args = parser.parse_args()

    for file in args.files:
        path = Path(file)
        if not path.exists():
            print(f"[WARN] File not found: {file}")
            continue

        if args.show:
            show_metadata(path)
        show_metadata(path)
        detect_and_scrub(path)


if __name__ == "__main__":
    main()
