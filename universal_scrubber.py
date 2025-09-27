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
    """Remove metadata from images embedded in PDF."""
    try:
        with pikepdf.open(pdf_path) as pdf:
            for page in pdf.pages:
                if '/Resources' in page and '/XObject' in page.Resources:
                    xobjects = page.Resources.XObject
                    for obj_name in xobjects:
                        xobj = xobjects[obj_name]
                        if xobj.Subtype == '/Image':
                            # Remove image metadata by recompressing
                            if '/Metadata' in xobj:
                                del xobj.Metadata
                            # You can add more specific image metadata removal here
            return pdf
    except Exception as e:
        print(f"[WARN] PDF image scrub failed: {e}")
        return None       
def scrub_pdf(input_path: Path, output_path: Path):
    """Remove metadata from PDFs including embedded images."""
    try:
        # First pass: remove PDF metadata
        with pikepdf.open(input_path) as pdf:
            # Remove all metadata
            if '/Metadata' in pdf.Root:
                del pdf.Root.Metadata
            
            # Remove producer and creator info
            if '/Producer' in pdf.docinfo:
                del pdf.docinfo.Producer
            if '/Creator' in pdf.docinfo:
                del pdf.docinfo.Creator
            if '/CreationDate' in pdf.docinfo:
                del pdf.docinfo.CreationDate
            if '/ModDate' in pdf.docinfo:
                del pdf.docinfo.ModDate
            
            # Remove embedded files
            if '/Names' in pdf.Root and '/EmbeddedFiles' in pdf.Root.Names:
                del pdf.Root.Names.EmbeddedFiles
            
            # Use this instead of minimize=True for older pikepdf versions
            pdf.save(output_path, encryption=False, object_stream_mode=pikepdf.ObjectStreamMode.disable)
        
        # Second pass: scrub embedded images
        scrubbed_pdf = scrub_pdf_images(output_path)
        if scrubbed_pdf:
            scrubbed_pdf.save(output_path, encryption=False)
            
    except Exception as e:
        print(f"[ERROR] PDF scrub failed: {e}")
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


def detect_and_scrub(file_path: Path):
    """Detect file type and scrub accordingly."""
    suffix = file_path.suffix.lower()
    scrubbed_path = file_path.with_name(f"scrubbed_{file_path.name}")

    try:
        if suffix in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"]:
            scrub_image(file_path, scrubbed_path)
        elif suffix == ".pdf":
            scrub_pdf(file_path, scrubbed_path)
        elif suffix in [".mp3", ".flac", ".mp4", ".m4a", ".wav", ".ogg"]:
            scrub_audio_video(file_path, scrubbed_path)
        elif suffix in [".docx", ".xlsx", ".pptx"]:
            scrub_office(file_path, scrubbed_path)
        else:
            scrub_generic(file_path, scrubbed_path)

        print(f"[INFO] Scrubbed file saved → {scrubbed_path}")

        # Always show metadata AFTER scrubbing
        show_metadata(scrubbed_path)

    except Exception as e:
        print(f"[ERROR] Failed to scrub {file_path}: {e}")
        scrub_generic(file_path, scrubbed_path)


def show_metadata(file_path: Path):
    """Extract and print metadata with hachoir (if any)."""
    parser = createParser(str(file_path))
    if not parser:
        print(f"[WARN] Cannot parse metadata for {file_path}")
        return

    metadata = extractMetadata(parser)
    if metadata:
        print(f"\n--- Metadata for {file_path} ---")
        for item in metadata.exportPlaintext():
            print(item)
    else:
        print(f"\n--- No metadata found in {file_path} ---")


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
