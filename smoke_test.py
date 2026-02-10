#!/usr/bin/env python3
"""Smoke test for core Comms Shield functionality.

Runs lightweight checks for:
- Universal scrubber on generic files and images
- Metadata analyzer execution
- Watcher processing of existing files

Exit code is non-zero on failure.
"""

import sys
import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

# Ensure src modules are importable
ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))

from core.scrubber import UniversalScrubber
from metadata_analyzer import show_comprehensive_metadata
from watcher import process_existing_files, watch_folder, clean_folder


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"[OK] {message}")


def scrubber_smoke_test(tmp_dir: Path) -> None:
    scrubber = UniversalScrubber()
    ok(f"Scrubber status: {scrubber.get_scrubber_status()}")

    text_file = tmp_dir / "smoke_sample.txt"
    text_file.write_text("smoke test content", encoding="utf-8")
    scrubbed_text = tmp_dir / "scrubbed_smoke_sample.txt"
    if not scrubber.scrub_file(text_file, scrubbed_text):
        fail("Generic file scrubbing failed")
    if not scrubbed_text.exists():
        fail("Scrubbed generic file not created")
    ok("Generic file scrubbed")

    try:
        from PIL import Image
    except Exception as exc:
        fail(f"Pillow not available for image scrub test: {exc}")

    image_file = tmp_dir / "smoke_image.png"
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(image_file)
    scrubbed_image = tmp_dir / "scrubbed_smoke_image.png"
    if not scrubber.scrub_file(image_file, scrubbed_image):
        fail("Image scrubbing failed")
    if not scrubbed_image.exists():
        fail("Scrubbed image file not created")
    ok("Image scrubbed")


def metadata_analyzer_smoke_test(tmp_dir: Path) -> None:
    test_file = tmp_dir / "metadata_sample.txt"
    test_file.write_text("metadata analyzer sample", encoding="utf-8")

    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            show_comprehensive_metadata(test_file)
    except Exception as exc:
        fail(f"Metadata analyzer threw an exception: {exc}")

    output = buffer.getvalue()
    if "COMPREHENSIVE METADATA ANALYSIS" not in output:
        fail("Metadata analyzer output missing expected header")
    ok("Metadata analyzer executed")


def watcher_smoke_test(tmp_dir: Path) -> None:
    watch_folder.mkdir(exist_ok=True)
    clean_folder.mkdir(exist_ok=True)

    watch_file = watch_folder / "watch_smoke.txt"
    watch_file.write_text("watcher smoke test", encoding="utf-8")

    result = process_existing_files()
    if result.get("status") != "success":
        fail(f"Watcher process_existing_files failed: {result}")

    cleaned_file = clean_folder / f"cleaned_{watch_file.name}"
    if not cleaned_file.exists():
        fail("Watcher did not create cleaned file")

    ok("Watcher processed existing files")

    # Cleanup watcher artifacts
    if watch_file.exists():
        watch_file.unlink()
    if cleaned_file.exists():
        cleaned_file.unlink()


def main() -> None:
    print("=== Comms Shield Smoke Test ===")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        scrubber_smoke_test(tmp_dir)
        metadata_analyzer_smoke_test(tmp_dir)
        watcher_smoke_test(tmp_dir)

    print("=== Smoke Test Complete ===")


if __name__ == "__main__":
    main()
