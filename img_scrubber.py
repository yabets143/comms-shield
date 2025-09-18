import argparse
from pathlib import Path
from PIL import Image, ExifTags
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


def extract_exif(file_path: str) -> None:
    """Extract and print EXIF metadata from an image."""
    try:
        with Image.open(file_path) as img:
            exifdata = img.getexif()

            if not exifdata:
                print(f"\n[INFO] No EXIF metadata found in {file_path}")
                return

            print(f"\n--- EXIF Metadata for {file_path} ---")
            for tagid, value in exifdata.items():
                tagname = ExifTags.TAGS.get(tagid, tagid)
                print(f"{tagname:25}: {value}")

    except Exception as e:
        print(f"[ERROR] Failed to extract EXIF from {file_path}: {e}")


def extract_deep_metadata(file_path: str) -> None:
    """Extract and print deep metadata (IPTC/XMP/etc.) using hachoir."""
    parser = createParser(file_path)
    if not parser:
        print(f"[WARN] Unable to parse {file_path}")
        return

    metadata = extractMetadata(parser)
    if metadata:
        print(f"\n--- Deep Metadata for {file_path} ---")
        for item in metadata.exportPlaintext():
            print(item)


def scrub_exif(input_path: str, output_path: str) -> None:
    """Remove EXIF metadata and save a clean image."""
    try:
        with Image.open(input_path) as img:
            data = list(img.getdata())
            clean = Image.new(img.mode, img.size)
            clean.putdata(data)
            clean.save(output_path, format=img.format)

        print(f"[INFO] Saved scrubbed image → {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to scrub {input_path}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Image metadata extractor & scrubber")
    parser.add_argument("files", nargs="+", help="Path(s) to image file(s)")

    args = parser.parse_args()

    for file_path in args.files:
        file = Path(file_path)

        if not file.exists():
            print(f"[WARN] File not found: {file}")
            continue

        # 1. Extract original metadata
        extract_exif(str(file))
        extract_deep_metadata(str(file))

        # 2. Scrub and save
        scrubbed_file = file.with_name(f"scrubbed_{file.name}")
        scrub_exif(str(file), str(scrubbed_file))

        # 3. Verify scrubbed image
        extract_exif(str(scrubbed_file))


if __name__ == "__main__":
    main()
