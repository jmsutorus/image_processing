"""
Image conversion module for HEIC, DNG, and JPG to JPEG/WebP.

This module provides functions to convert HEIC (High-Efficiency Image Container),
DNG (Digital Negative), and JPG formats to JPEG or WebP with full metadata preservation.
"""

import io
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Literal

import pillow_heif
import rawpy
from PIL import Image, ImageOps

# Register HEIF opener globally (call once at module level)
pillow_heif.register_heif_opener()


class ConversionError(Exception):
    """Raised when image conversion fails"""
    pass


def convert_image(
    input_bytes: bytes,
    filename: str,
    output_format: Literal["jpeg", "webp"] = "jpeg",
    lossless: bool = False,
    quality: int = 85
) -> bytes:
    """
    Convert HEIC, DNG, or JPG to JPEG or WebP with metadata preservation.

    Args:
        input_bytes: Raw file bytes
        filename: Original filename (used to determine type)
        output_format: Output format ('jpeg' or 'webp')
        lossless: For WebP only - use lossless compression (default: False)
        quality: Quality setting 0-100 (default: 85)
                 For JPEG: 0=worst, 95=best
                 For WebP lossy: 0=smallest, 100=largest
                 For WebP lossless: 0=fastest, 100=best compression

    Returns:
        Image bytes in specified format

    Raises:
        ConversionError: If conversion fails
    """
    file_ext = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)

        # Determine output extension
        output_ext = ".jpg" if output_format == "jpeg" else ".webp"
        output_path = os.path.join(tmpdir, f"output{output_ext}")

        try:
            # Write input file
            with open(input_path, 'wb') as f:
                f.write(input_bytes)

            # Convert based on input format and output format
            if output_format == "jpeg":
                # Use existing JPEG conversion logic
                if file_ext in ['.heic', '.heif']:
                    _convert_heic(input_path, output_path)
                elif file_ext == '.dng':
                    _convert_dng(input_path, output_path)
                elif file_ext in ['.jpg', '.jpeg']:
                    # For JPEG to JPEG, just copy with quality adjustment
                    _convert_jpg_to_jpeg(input_path, output_path, quality)
                else:
                    raise ConversionError(f"Unsupported file type: {file_ext}")

            elif output_format == "webp":
                # Load image to PIL format first, then save as WebP
                if file_ext in ['.heic', '.heif']:
                    image, metadata = _load_heic(input_path)
                elif file_ext == '.dng':
                    image, metadata = _load_dng(input_path)
                elif file_ext in ['.jpg', '.jpeg']:
                    image, metadata = _load_jpg(input_path)
                else:
                    raise ConversionError(f"Unsupported file type: {file_ext}")

                # Save as WebP with metadata
                _save_webp(image, output_path, metadata, lossless, quality)

            else:
                raise ConversionError(f"Unsupported output format: {output_format}")

            # Read result
            with open(output_path, 'rb') as f:
                return f.read()

        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"Conversion failed: {str(e)}")


def _convert_heic(input_path: str, output_path: str):
    """
    Convert HEIC to JPEG with EXIF preservation.

    Args:
        input_path: Path to input HEIC file
        output_path: Path for output JPEG file

    Raises:
        ConversionError: If HEIC conversion fails
    """
    try:
        with Image.open(input_path) as image:
            # Extract EXIF metadata
            exif_data = image.info.get('exif')

            # Convert and save with high quality
            image.convert('RGB').save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0,  # No chroma subsampling (4:4:4)
                exif=exif_data
            )
    except Exception as e:
        raise ConversionError(f"HEIC conversion failed: {e}")


def _convert_dng(input_path: str, output_path: str):
    """
    Convert DNG to JPEG with metadata copying via exiftool.

    This function performs RAW development with proper white balance,
    color space, and brightness adjustment. It then copies metadata
    using exiftool and applies EXIF orientation to correct rotation.

    Args:
        input_path: Path to input DNG file
        output_path: Path for output JPEG file

    Raises:
        ConversionError: If DNG conversion fails
    """
    try:
        # Step 1: Develop RAW with rawpy with proper brightness settings
        with rawpy.imread(input_path) as raw:
            # Use default settings which enable auto-brightness
            # exp_shift for exposure adjustment, auto_bright_thr for clipping threshold
            rgb = raw.postprocess(
                use_camera_wb=True,           # Use camera white balance
                output_color=rawpy.ColorSpace.sRGB,  # Web-compatible color space
                no_auto_bright=False,         # Enable auto-brightness (default)
                auto_bright_thr=0.01,         # 1% clipping threshold (default)
                exp_shift=2.0,                # Exposure shift: 1.0 = +1 stop brighter
                exp_preserve_highlights=0.5,  # Preserve some highlights when brightening
                gamma=(2.222, 4.5),           # Standard gamma curve (BT.709)
                output_bps=8                  # 8-bit output for JPEG
            )

        # Step 2: Save RGB array as JPEG (no metadata yet)
        image = Image.fromarray(rgb)
        image.save(
            output_path,
            format="JPEG",
            quality=100,
            subsampling=0  # No chroma subsampling (4:4:4)
        )

        # Step 3: Copy metadata using exiftool (CRITICAL STEP)
        subprocess.run(
            [
                'exiftool',
                '-TagsFromFile', input_path,
                '-all:all',  # Copy all tags
                '-overwrite_original',
                '-n',  # Don't print tag names
                output_path
            ],
            shell=False,      # SECURITY: Never use shell=True
            check=True,
            capture_output=True,
            timeout=30
        )

        # Step 4: Apply EXIF orientation to fix rotation issues
        # Re-open the image with metadata and apply orientation
        image = Image.open(output_path)

        # exif_transpose always returns an Image (either transposed or copy)
        # unless you use in_place=True
        oriented_image = ImageOps.exif_transpose(image)

        # Save the oriented image (this will have orientation=1 and correct pixels)
        if oriented_image:
            oriented_image.save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0
            )

        # Clean up
        image.close()

    except subprocess.CalledProcessError as e:
        raise ConversionError(f"exiftool failed: {e.stderr.decode()}")
    except Exception as e:
        raise ConversionError(f"DNG conversion failed: {e}")


def _convert_jpg_to_jpeg(input_path: str, output_path: str, quality: int = 85):
    """
    Convert JPG to JPEG with quality adjustment and metadata preservation.

    Args:
        input_path: Path to input JPG file
        output_path: Path for output JPEG file
        quality: JPEG quality (0-100)

    Raises:
        ConversionError: If conversion fails
    """
    try:
        with Image.open(input_path) as image:
            # Extract metadata
            exif_data = image.info.get('exif')
            icc_profile = image.info.get('icc_profile')

            # Convert to RGB if needed
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Save with specified quality
            save_kwargs = {
                'format': 'JPEG',
                'quality': min(quality, 95),  # Cap at 95 per Pillow docs
                'optimize': True
            }

            if exif_data:
                save_kwargs['exif'] = exif_data
            if icc_profile:
                save_kwargs['icc_profile'] = icc_profile

            image.save(output_path, **save_kwargs)

    except Exception as e:
        raise ConversionError(f"JPG to JPEG conversion failed: {e}")


def _load_heic(input_path: str) -> tuple[Image.Image, dict]:
    """
    Load HEIC file and return PIL Image with metadata.

    Args:
        input_path: Path to input HEIC file

    Returns:
        Tuple of (PIL Image, metadata dict)

    Raises:
        ConversionError: If loading fails
    """
    try:
        with Image.open(input_path) as image:
            # Extract metadata
            metadata = {
                'exif': image.info.get('exif'),
                'icc_profile': image.info.get('icc_profile'),
                'xmp': image.info.get('xmp')
            }

            # Convert to RGB and return a copy (since we're in 'with' block)
            rgb_image = image.convert('RGB').copy()

        return rgb_image, metadata

    except Exception as e:
        raise ConversionError(f"HEIC loading failed: {e}")


def _load_dng(input_path: str) -> tuple[Image.Image, dict]:
    """
    Load DNG file with RAW processing and return PIL Image with metadata.

    Args:
        input_path: Path to input DNG file

    Returns:
        Tuple of (PIL Image, metadata dict)

    Raises:
        ConversionError: If loading fails
    """
    try:
        # Step 1: Develop RAW with rawpy
        with rawpy.imread(input_path) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,
                output_color=rawpy.ColorSpace.sRGB,
                no_auto_bright=False,
                auto_bright_thr=0.01,
                exp_shift=2.0,
                exp_preserve_highlights=0.5,
                gamma=(2.222, 4.5),
                output_bps=8
            )

        # Step 2: Create PIL Image
        image = Image.fromarray(rgb)

        # Step 3: Extract metadata from original DNG using exiftool
        # We'll save to temp JPEG first to extract metadata properly
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save temp JPEG
            image.save(tmp_path, format='JPEG', quality=100)

            # Copy metadata from DNG to temp JPEG
            subprocess.run(
                [
                    'exiftool',
                    '-TagsFromFile', input_path,
                    '-all:all',
                    '-overwrite_original',
                    '-n',
                    tmp_path
                ],
                shell=False,
                check=True,
                capture_output=True,
                timeout=30
            )

            # Re-open to get metadata
            with Image.open(tmp_path) as img_with_meta:
                metadata = {
                    'exif': img_with_meta.info.get('exif'),
                    'icc_profile': img_with_meta.info.get('icc_profile'),
                    'xmp': img_with_meta.info.get('xmp')
                }

                # Apply orientation correction
                oriented_image = ImageOps.exif_transpose(img_with_meta)
                if oriented_image:
                    image = oriented_image.copy()

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return image, metadata

    except subprocess.CalledProcessError as e:
        raise ConversionError(f"DNG metadata extraction failed: {e.stderr.decode()}")
    except Exception as e:
        raise ConversionError(f"DNG loading failed: {e}")


def _load_jpg(input_path: str) -> tuple[Image.Image, dict]:
    """
    Load JPG file and return PIL Image with metadata.

    Args:
        input_path: Path to input JPG file

    Returns:
        Tuple of (PIL Image, metadata dict)

    Raises:
        ConversionError: If loading fails
    """
    try:
        with Image.open(input_path) as image:
            # Extract metadata
            metadata = {
                'exif': image.info.get('exif'),
                'icc_profile': image.info.get('icc_profile'),
                'xmp': image.info.get('xmp')
            }

            # Convert to RGB if needed and return a copy
            if image.mode not in ('RGB', 'L'):
                rgb_image = image.convert('RGB').copy()
            else:
                rgb_image = image.copy()

        return rgb_image, metadata

    except Exception as e:
        raise ConversionError(f"JPG loading failed: {e}")


def _save_webp(
    image: Image.Image,
    output_path: str,
    metadata: dict,
    lossless: bool = False,
    quality: int = 85
):
    """
    Save PIL Image as WebP with metadata preservation.

    Args:
        image: PIL Image object
        output_path: Path for output WebP file
        metadata: Metadata dict with 'exif', 'icc_profile', 'xmp' keys
        lossless: Use lossless compression
        quality: Quality setting (0-100)

    Raises:
        ConversionError: If saving fails
    """
    try:
        # Prepare save options
        save_kwargs = {
            'format': 'WebP',
            'lossless': lossless,
            'quality': quality,
            'method': 4  # Balance of speed and compression
        }

        # Add metadata if available
        if metadata.get('exif'):
            save_kwargs['exif'] = metadata['exif']

        if metadata.get('icc_profile'):
            save_kwargs['icc_profile'] = metadata['icc_profile']

        if metadata.get('xmp'):
            save_kwargs['xmp'] = metadata['xmp']

        # Save as WebP
        image.save(output_path, **save_kwargs)

    except Exception as e:
        raise ConversionError(f"WebP saving failed: {e}")
