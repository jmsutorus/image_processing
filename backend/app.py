"""
FastAPI application for image conversion service.

This service converts HEIC, DNG, and JPG image formats to JPEG or WebP
with full metadata preservation.
"""

import io
import magic
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from converter import convert_image, ConversionError

app = FastAPI(
    title="Image Conversion Service",
    description="Convert HEIC, DNG, and JPG images to JPEG or WebP with metadata preservation",
    version="1.0.0"
)

# Configure CORS for frontend access
# Must be added immediately after FastAPI app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Configuration constants
MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'.heic', '.heif', '.dng', '.jpg', '.jpeg'}
ALLOWED_EXTENSIONS_WEBP = {'.heic', '.heif', '.dng', '.jpg', '.jpeg'}  # WebP supports all formats


def validate_file(contents: bytes, filename: str) -> None:
    """
    Validate file size, extension, and MIME type.

    Args:
        contents: File contents as bytes
        filename: Original filename

    Raises:
        HTTPException: If validation fails
    """
    # Check size
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_UPLOAD_SIZE // (1024 * 1024)}MB)"
        )

    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check MIME type (magic number validation)
    mime = magic.from_buffer(contents, mime=True)

    if ext in ['.heic', '.heif']:
        # HEIC files can have various MIME types
        if not (mime.startswith('image/heic') or mime == 'image/heif' or mime == 'image/heif-sequence'):
            raise HTTPException(
                status_code=400,
                detail=f"File is not a valid HEIC (detected MIME type: {mime})"
            )
    elif ext == '.dng':
        # DNG files are TIFF-based
        if mime not in ['image/x-adobe-dng', 'image/tiff', 'image/x-canon-cr2', 'application/octet-stream']:
            raise HTTPException(
                status_code=400,
                detail=f"File is not a valid DNG (detected MIME type: {mime})"
            )
    elif ext in ['.jpg', '.jpeg']:
        # JPEG files
        if mime != 'image/jpeg':
            raise HTTPException(
                status_code=400,
                detail=f"File is not a valid JPEG (detected MIME type: {mime})"
            )


@app.post("/convert", response_class=StreamingResponse)
async def convert_endpoint(file: UploadFile = File(...)):
    """
    Convert HEIC or DNG to JPEG.

    Synchronous processing: returns JPEG when complete.

    Args:
        file: Uploaded HEIC or DNG file

    Returns:
        StreamingResponse with JPEG image

    Raises:
        HTTPException: If validation or conversion fails
    """
    # Read file
    contents = await file.read()

    # Validate
    validate_file(contents, file.filename)

    # Convert (blocking operation)
    try:
        result_bytes = convert_image(contents, file.filename)
    except ConversionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return JPEG
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": "attachment; filename=converted.jpg"
        }
    )


@app.post("/convert-to-webp", response_class=StreamingResponse)
async def convert_to_webp_endpoint(
    file: UploadFile = File(...),
    lossless: bool = False,
    quality: int = 85
):
    """
    Convert HEIC, DNG, or JPG to WebP.

    Synchronous processing: returns WebP when complete.

    Args:
        file: Uploaded image file (HEIC, DNG, or JPG)
        lossless: Use lossless WebP compression (default: False)
        quality: Quality setting 0-100 (default: 85)
                 For lossy: 0=smallest, 100=largest
                 For lossless: 0=fastest, 100=best compression

    Returns:
        StreamingResponse with WebP image

    Raises:
        HTTPException: If validation or conversion fails
    """
    # Read file
    contents = await file.read()

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS_WEBP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(ALLOWED_EXTENSIONS_WEBP)}"
        )

    # Validate size and MIME type
    validate_file(contents, file.filename)

    # Validate quality parameter
    if not 0 <= quality <= 100:
        raise HTTPException(
            status_code=400,
            detail="Quality must be between 0 and 100"
        )

    # Convert to WebP (blocking operation)
    try:
        result_bytes = convert_image(
            contents,
            file.filename,
            output_format="webp",
            lossless=lossless,
            quality=quality
        )
    except ConversionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return WebP
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="image/webp",
        headers={
            "Content-Disposition": "attachment; filename=converted.webp"
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Status indicating service health
    """
    return {"status": "healthy"}


@app.get("/")
async def root():
    """
    Root endpoint with service information.

    Returns:
        dict: Service information and available endpoints
    """
    return {
        "service": "Image Conversion Service",
        "version": "1.0.0",
        "endpoints": {
            "Synchronous": {
                "POST /convert": "Convert HEIC/DNG/JPG to JPEG",
                "POST /convert-to-webp": "Convert HEIC/DNG/JPG to WebP"
            },
            "System": {
                "GET /health": "Health check",
                "GET /docs": "API documentation"
            }
        },
        "supported_input_formats": list(ALLOWED_EXTENSIONS),
        "output_formats": ["jpeg", "webp"],
        "max_file_size_mb": MAX_UPLOAD_SIZE // (1024 * 1024),
        "features": {
            "async_processing": False,
            "job_queuing": False
        }
    }
