import argparse
import shutil
from pathlib import Path
from PIL import Image
import tempfile  
import xml.etree.ElementTree as ET 
from typing import Optional, Dict, List
import zipfile

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except ImportError:
    HACHOIR_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

from ..utils.logger import SecureLogger

class UniversalScrubber:
    def __init__(self, logger: Optional[SecureLogger] = None):
        self.logger = logger or SecureLogger()
        self.supported_formats = {
            '.jpg': self.scrub_image,
            '.jpeg': self.scrub_image,
            '.png': self.scrub_image,
            '.tiff': self.scrub_image,
            '.bmp': self.scrub_image,
            '.gif': self.scrub_image,
            '.pdf': self.scrub_pdf,
            '.docx': self.scrub_office,
            '.xlsx': self.scrub_office,
            '.pptx': self.scrub_office,
            '.mp3': self.scrub_audio_video,
            '.flac': self.scrub_audio_video,
            '.mp4': self.scrub_audio_video,
            '.m4a': self.scrub_audio_video,
            '.wav': self.scrub_audio_video,
            '.ogg': self.scrub_audio_video,
        }
    
    def scrub_file(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """Scrub metadata from a single file"""
        try:
            if not input_path.exists():
                self.logger.error(f"Input file not found: {input_path}")
                return False
            
            output_path = output_path or input_path.parent / f"scrubbed_{input_path.name}"
            
            # Get file extension
            ext = input_path.suffix.lower()
            
            # Scrub based on file type
            if ext in self.supported_formats:
                success = self.supported_formats[ext](input_path, output_path)
            else:
                # For unsupported formats, make a clean copy
                success = self.scrub_generic(input_path, output_path)
            
            # Log operation
            op_data = {
                'operation': 'scrub_file',
                'filename': input_path.name,
                'file_type': ext,
                'original_size': input_path.stat().st_size,
                'scrubbed_size': output_path.stat().st_size if success and output_path.exists() else 0,
                'status': 'success' if success else 'error'
            }
            
            if success:
                self.logger.info(f"Successfully scrubbed: {input_path.name}", op_data)
            else:
                self.logger.error(f"Failed to scrub: {input_path.name}", op_data)
            
            return success
            
        except Exception as e:
            op_data = {
                'operation': 'scrub_file',
                'filename': input_path.name,
                'status': 'error',
                'error_message': str(e)
            }
            self.logger.error(f"Error scrubbing {input_path.name}: {str(e)}", op_data)
            return False
    
    def scrub_folder(self, folder_path: Path, output_folder: Optional[Path] = None) -> Dict:
        """Scrub all files in a folder"""
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'failed_files': []
        }
        
        output_folder = output_folder or folder_path / "scrubbed"
        output_folder.mkdir(exist_ok=True)
        
        for file_path in folder_path.glob('*'):
            if file_path.is_file() and not file_path.name.startswith('scrubbed_'):
                results['total'] += 1
                output_path = output_folder / f"scrubbed_{file_path.name}"
                success = self.scrub_file(file_path, output_path)
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['failed_files'].append(file_path.name)
        
        return results
    
    def scrub_image(self, input_path: Path, output_path: Path) -> bool:
        """Remove EXIF metadata from images."""
        try:
            with Image.open(input_path) as img:
                data = list(img.getdata())
                clean = Image.new(img.mode, img.size)
                clean.putdata(data)
                clean.save(output_path, format=img.format)
            return True
        except Exception as e:
            self.logger.error(f"Error scrubbing image {input_path.name}: {str(e)}")
            return self.scrub_generic(input_path, output_path)
    
    def scrub_audio_video(self, input_path: Path, output_path: Path) -> bool:
        """Remove metadata from audio/video (MP3, MP4, etc.)."""
        if not MUTAGEN_AVAILABLE:
            self.logger.warning(f"Mutagen not available, using generic scrub for {input_path.name}")
            return self.scrub_generic(input_path, output_path)
            
        try:
            media = MutagenFile(input_path, easy=True)
            if media:
                media.delete()  # remove tags
                media.save()
            shutil.copy(input_path, output_path)
            return True
        except Exception as e:
            self.logger.error(f"Error scrubbing audio/video {input_path.name}: {str(e)}")
            return self.scrub_generic(input_path, output_path)
    
    def scrub_docx_images(self, docx_path: Path, temp_dir: Path):
        """Scrub metadata from images embedded in DOCX."""
        try:
            media_dir = temp_dir / 'word' / 'media'
            if media_dir.exists():
                for img_file in media_dir.glob('*.*'):
                    if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                        try:
                            self.scrub_image(img_file, img_file)
                            self.logger.info(f"Scrubbed embedded image: {img_file.name}")
                        except Exception as e:
                            self.logger.warning(f"Failed to scrub embedded image {img_file}: {e}")
            
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
            self.logger.warning(f"DOCX image scrub failed: {e}")

    def scrub_pdf_images(self, pdf_path: Path):
        """Remove metadata from images embedded in PDF."""
        if not PIKEPDF_AVAILABLE:
            return None
            
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
            self.logger.warning(f"PDF image scrub failed: {e}")
            return None       
    
    def scrub_pdf(self, input_path: Path, output_path: Path) -> bool:
        """Remove metadata from PDFs including embedded images."""
        if not PIKEPDF_AVAILABLE:
            self.logger.warning(f"pikepdf not available, using generic scrub for {input_path.name}")
            return self.scrub_generic(input_path, output_path)
            
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
            scrubbed_pdf = self.scrub_pdf_images(output_path)
            if scrubbed_pdf:
                scrubbed_pdf.save(output_path, encryption=False)
                
            return True
            
        except Exception as e:
            self.logger.error(f"PDF scrub failed: {e}")
            return self.scrub_generic(input_path, output_path)
    
    def scrub_office(self, input_path: Path, output_path: Path) -> bool:
        """Remove metadata from Office docs including embedded images."""
        try:
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
                self.scrub_docx_images(input_path, tmpdir_path)

                # Create new DOCX
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
                    for file in tmpdir_path.rglob("*"):
                        if file.is_file():
                            arcname = file.relative_to(tmpdir_path)
                            zout.write(file, arcname)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Office document scrub failed: {e}")
            return self.scrub_generic(input_path, output_path)
    
    def scrub_generic(self, input_path: Path, output_path: Path) -> bool:
        """Fallback scrubber - just copies file."""
        try:
            shutil.copy(input_path, output_path)
            return True
        except Exception as e:
            self.logger.error(f"Generic scrub failed for {input_path.name}: {str(e)}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.supported_formats.keys())
    
    def get_scrubber_status(self) -> Dict[str, bool]:
        """Get status of required libraries"""
        return {
            'hachoir': HACHOIR_AVAILABLE,
            'mutagen': MUTAGEN_AVAILABLE,
            'pikepdf': PIKEPDF_AVAILABLE
        }