"""
Image conversion module for HEIC, DNG, JPG, PNG and WebP to JPEG/WebP.

Every conversion runs through one pipeline:

    load (format-specific) -> apply EXIF orientation -> resize -> clean metadata -> encode

Metadata handling:
    - EXIF orientation is applied to the pixels and the tag is reset to 1, so
      viewers never rotate the image a second time.
    - GPS data is removed by default (``strip_gps=True``). XMP is dropped as
      well in that mode because it can carry its own copy of the location.
    - ICC color profiles are preserved.
"""

import io
from pathlib import Path
from typing import Literal, Optional

import pillow_heif
import rawpy
from PIL import Image

# Register HEIF opener globally (call once at module level)
pillow_heif.register_heif_opener()

EXIF_ORIENTATION = 0x0112
EXIF_GPS_IFD = 0x8825

# EXIF orientation value -> transpose operations that undo it
_ORIENTATION_TRANSPOSE = {
    2: [Image.Transpose.FLIP_LEFT_RIGHT],
    3: [Image.Transpose.ROTATE_180],
    4: [Image.Transpose.FLIP_TOP_BOTTOM],
    5: [Image.Transpose.TRANSPOSE],
    6: [Image.Transpose.ROTATE_270],
    7: [Image.Transpose.TRANSVERSE],
    8: [Image.Transpose.ROTATE_90],
}

RAW_EXTENSIONS = {'.dng'}
PILLOW_EXTENSIONS = {'.heic', '.heif', '.jpg', '.jpeg', '.png', '.webp'}
SUPPORTED_EXTENSIONS = RAW_EXTENSIONS | PILLOW_EXTENSIONS


class ConversionError(Exception):
    """Raised when image conversion fails (usually because the input is invalid)."""
    pass


def convert_image(
    input_bytes: bytes,
    filename: str,
    output_format: Literal["jpeg", "webp"] = "jpeg",
    lossless: bool = False,
    quality: int = 85,
    max_dimension: Optional[int] = None,
    strip_gps: bool = True,
) -> bytes:
    """
    Convert an image to JPEG or WebP.

    Args:
        input_bytes: Raw file bytes
        filename: Original filename (only the extension is used)
        output_format: 'jpeg' or 'webp'
        lossless: WebP only - use lossless compression
        quality: 0-100. JPEG is capped at 95. For lossless WebP this is the
                 compression effort (0=fastest, 100=smallest).
        max_dimension: If set, downscale so the longest edge is at most this
                       many pixels. Images are never upscaled.
        strip_gps: Remove GPS location data (and XMP) from the output.

    Returns:
        Encoded image bytes

    Raises:
        ConversionError: If the input can't be decoded or encoding fails
    """
    file_ext = Path(filename).suffix.lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise ConversionError(f"Unsupported file type: {file_ext}")
    if output_format not in ("jpeg", "webp"):
        raise ConversionError(f"Unsupported output format: {output_format}")

    try:
        if file_ext in RAW_EXTENSIONS:
            image, metadata = _load_dng(input_bytes)
        else:
            image, metadata = _load_with_pillow(input_bytes)

        image, exif = _apply_orientation(image, metadata.get('exif'))
        image = _resize(image, max_dimension)
        exif_bytes = _clean_exif(exif, strip_gps)

        out_metadata = {
            'exif': exif_bytes,
            'icc_profile': metadata.get('icc_profile'),
            'xmp': None if strip_gps else metadata.get('xmp'),
        }

        if output_format == "jpeg":
            return _encode_jpeg(image, out_metadata, quality)
        return _encode_webp(image, out_metadata, lossless, quality)

    except ConversionError:
        raise
    except Exception as e:
        raise ConversionError(f"Conversion failed: {e}")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _load_with_pillow(input_bytes: bytes) -> tuple[Image.Image, dict]:
    """Load HEIC/JPEG/PNG/WebP. Only the first frame of animated images is used."""
    try:
        with Image.open(io.BytesIO(input_bytes)) as image:
            image.load()
            metadata = {
                'exif': image.info.get('exif'),
                'icc_profile': image.info.get('icc_profile'),
                'xmp': image.info.get('xmp'),
            }
            original_mode = image.mode
            loaded = image.copy()
    except Exception as e:
        raise ConversionError(f"Could not read image: {e}")

    # A CMYK profile no longer matches once the pixels are converted to RGB
    if original_mode == 'CMYK':
        metadata['icc_profile'] = None

    return loaded, metadata


def _load_dng(input_bytes: bytes) -> tuple[Image.Image, dict]:
    """
    Develop a DNG with rawpy and read its EXIF with Pillow.

    rawpy already applies the sensor orientation (``flip``) during
    postprocess, so the returned EXIF has Orientation reset to 1 to stop the
    pipeline from rotating the image a second time.
    """
    try:
        with rawpy.imread(io.BytesIO(input_bytes)) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,                  # Camera white balance
                output_color=rawpy.ColorSpace.sRGB,  # Web-compatible color space
                no_auto_bright=False,                # Auto-brightness on
                auto_bright_thr=0.01,                # 1% clipping threshold
                exp_shift=2.0,                       # Linear exposure multiplier (+1 stop)
                exp_preserve_highlights=0.5,         # Protect highlights when brightening
                gamma=(2.222, 4.5),                  # BT.709 gamma
                output_bps=8,
            )
    except Exception as e:
        raise ConversionError(f"Could not develop DNG: {e}")

    metadata = {
        'exif': _dng_exif(input_bytes),
        'icc_profile': None,  # Output is plain sRGB from rawpy
        'xmp': None,
    }
    return Image.fromarray(rgb), metadata


# IFD0 tags worth carrying over from a DNG. The rest of IFD0 describes the raw
# sensor data (strip offsets, color matrices, DNG version...) and is meaningless
# on a developed image.
_DNG_IFD0_KEEP = {
    0x010E,  # ImageDescription
    0x010F,  # Make
    0x0110,  # Model
    0x0131,  # Software
    0x0132,  # DateTime
    0x013B,  # Artist
    0x8298,  # Copyright
}
EXIF_SUB_IFD = 0x8769
EXIF_MAKER_NOTE = 0x927C


def _dng_exif(input_bytes: bytes) -> Optional[bytes]:
    """Build a clean EXIF block (camera, capture settings, GPS) from a DNG's TIFF headers."""
    try:
        with Image.open(io.BytesIO(input_bytes)) as tiff:
            source = tiff.getexif()
            exif = Image.Exif()
            for tag in _DNG_IFD0_KEEP:
                if tag in source:
                    exif[tag] = source[tag]
            exif[EXIF_ORIENTATION] = 1

            sub_ifd = dict(source.get_ifd(EXIF_SUB_IFD))
            sub_ifd.pop(EXIF_MAKER_NOTE, None)  # Large, camera-private, offsets break on rewrite
            if sub_ifd:
                exif[EXIF_SUB_IFD] = sub_ifd

            gps_ifd = dict(source.get_ifd(EXIF_GPS_IFD))
            if gps_ifd:
                exif[EXIF_GPS_IFD] = gps_ifd

            return exif.tobytes()
    except Exception:
        # Metadata is a nice-to-have; never fail the conversion over it
        return None


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def _parse_exif(exif_bytes: Optional[bytes]) -> Optional[Image.Exif]:
    if not exif_bytes:
        return None
    try:
        exif = Image.Exif()
        exif.load(exif_bytes)
        return exif
    except Exception:
        return None


def _apply_orientation(image: Image.Image, exif_bytes: Optional[bytes]) -> tuple[Image.Image, Optional[Image.Exif]]:
    """Rotate/flip the pixels to match the EXIF orientation, then reset the tag to 1."""
    exif = _parse_exif(exif_bytes)
    if exif is None:
        return image, None

    orientation = exif.get(EXIF_ORIENTATION, 1)
    for op in _ORIENTATION_TRANSPOSE.get(orientation, []):
        image = image.transpose(op)

    if EXIF_ORIENTATION in exif:
        exif[EXIF_ORIENTATION] = 1

    return image, exif


def _resize(image: Image.Image, max_dimension: Optional[int]) -> Image.Image:
    """Downscale so the longest edge is <= max_dimension. Never upscales."""
    if not max_dimension or max(image.size) <= max_dimension:
        return image
    resized = image.copy()
    resized.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return resized


def _clean_exif(exif: Optional[Image.Exif], strip_gps: bool) -> Optional[bytes]:
    """Serialize EXIF, removing GPS data if requested.

    If the EXIF can't be rewritten safely while stripping GPS, it is dropped
    entirely rather than risking a location leak.
    """
    if exif is None:
        return None
    try:
        if strip_gps and EXIF_GPS_IFD in exif:
            del exif[EXIF_GPS_IFD]
        return exif.tobytes()
    except Exception:
        return None


def _normalize_mode(image: Image.Image, keep_alpha: bool) -> Image.Image:
    """Convert to RGB/RGBA/L. Transparent images become RGBA, or are flattened onto white."""
    has_alpha = image.mode in ('RGBA', 'LA', 'PA') or (
        image.mode == 'P' and 'transparency' in image.info
    )
    if has_alpha:
        rgba = image.convert('RGBA')
        if keep_alpha:
            return rgba
        background = Image.new('RGB', rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel('A'))
        return background
    if image.mode in ('RGB', 'L'):
        return image
    return image.convert('RGB')


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def _encode_jpeg(image: Image.Image, metadata: dict, quality: int) -> bytes:
    image = _normalize_mode(image, keep_alpha=False)
    quality = min(quality, 95)  # Pillow: values above 95 only bloat the file
    save_kwargs = {
        'format': 'JPEG',
        'quality': quality,
        'optimize': True,
        # Full chroma resolution for high-quality output, 4:2:0 otherwise
        'subsampling': 0 if quality >= 90 else 2,
    }
    if metadata.get('exif'):
        save_kwargs['exif'] = metadata['exif']
    if metadata.get('icc_profile'):
        save_kwargs['icc_profile'] = metadata['icc_profile']

    buffer = io.BytesIO()
    try:
        image.save(buffer, **save_kwargs)
    except Exception as e:
        raise ConversionError(f"JPEG encoding failed: {e}")
    return buffer.getvalue()


def _encode_webp(image: Image.Image, metadata: dict, lossless: bool, quality: int) -> bytes:
    image = _normalize_mode(image, keep_alpha=True)
    save_kwargs = {
        'format': 'WebP',
        'lossless': lossless,
        'quality': quality,
        'method': 4,  # Balance of speed and compression
    }
    if metadata.get('exif'):
        save_kwargs['exif'] = metadata['exif']
    if metadata.get('icc_profile'):
        save_kwargs['icc_profile'] = metadata['icc_profile']
    if metadata.get('xmp'):
        save_kwargs['xmp'] = metadata['xmp']

    buffer = io.BytesIO()
    try:
        image.save(buffer, **save_kwargs)
    except Exception as e:
        raise ConversionError(f"WebP encoding failed: {e}")
    return buffer.getvalue()
