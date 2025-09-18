import argparse
import shutil
from pathlib import Path
from PIL import Image
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from mutagen import File as MutagenFile
import pikepdf


def scrub_image(input_path: Path, output_path: Path):
    """Remove EXIF metadata from images."""
    with Image.open(input_path) as img:
        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)
        clean.save(output_path, format=img.format)


def scrub_pdf(input_path: Path, output_path: Path):
    """Remove metadata from PDFs."""
    with pikepdf.open(input_path) as pdf:
        pdf.save(output_path, minimize=True, encryption=False)


def scrub_audio_video(input_path: Path, output_path: Path):
    """Remove metadata from audio/video (MP3, MP4, etc.)."""
    media = MutagenFile(input_path, easy=True)
    if media:
        media.delete()  # remove tags
        media.save()
    shutil.copy(input_path, output_path)


def scrub_office(input_path: Path, output_path: Path):
    """Remove metadata from Office docs (DOCX, XLSX, PPTX)."""
    import zipfile
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(input_path, "r") as zin:
            zin.extractall(tmpdir)

        # Remove metadata files
        for meta_file in ["docProps/core.xml", "docProps/app.xml"]:
            target = Path(tmpdir) / meta_file
            if target.exists():
                target.unlink()

        with zipfile.ZipFile(output_path, "w") as zout:
            for file in Path(tmpdir).rglob("*"):
                zout.write(file, file.relative_to(tmpdir))


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

        detect_and_scrub(path)


if __name__ == "__main__":
    main()
