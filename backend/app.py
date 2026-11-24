"""
FastAPI application for image conversion service.

Converts HEIC, DNG, JPG, PNG and WebP images to JPEG or WebP, with optional
downscaling and GPS stripping.

The conversion endpoints are plain ``def`` functions on purpose: conversion
is CPU-bound, and FastAPI runs sync endpoints in a thread pool so one slow
DNG doesn't block the event loop for every other request.
"""

import re
from pathlib import Path
from typing import Optional

import magic
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from converter import convert_image, ConversionError, SUPPORTED_EXTENSIONS

app = FastAPI(
    title="Image Conversion Service",
    description="Convert HEIC, DNG, JPG, PNG and WebP images to JPEG or WebP",
    version="1.1.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Configuration constants
MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB
MULTIPART_OVERHEAD = 1024 * 1024     # Allowance for multipart boundaries/headers

# Accepted MIME types per extension (magic-number detection)
ALLOWED_MIME_TYPES = {
    '.heic': {'image/heic', 'image/heif', 'image/heic-sequence', 'image/heif-sequence'},
    '.heif': {'image/heic', 'image/heif', 'image/heic-sequence', 'image/heif-sequence'},
    # DNG is TIFF-based and libmagic reports it inconsistently
    '.dng': {'image/x-adobe-dng', 'image/tiff', 'image/x-canon-cr2', 'application/octet-stream'},
    '.jpg': {'image/jpeg'},
    '.jpeg': {'image/jpeg'},
    '.png': {'image/png'},
    '.webp': {'image/webp'},
}


@app.middleware("http")
async def reject_oversized_uploads(request: Request, call_next):
    """Reject oversized bodies before the multipart parser spools them to disk."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > MAX_UPLOAD_SIZE + MULTIPART_OVERHEAD:
            return JSONResponse(
                status_code=413,
                content={"detail": f"File too large (max {MAX_UPLOAD_SIZE // (1024 * 1024)}MB)"},
            )
    return await call_next(request)


def read_and_validate(file: UploadFile) -> bytes:
    """
    Read the upload (bounded by MAX_UPLOAD_SIZE) and validate extension and MIME type.

    Raises:
        HTTPException: 413 if too large, 400 if the type is unsupported or doesn't match
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext or '(none)'}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    contents = file.file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_UPLOAD_SIZE // (1024 * 1024)}MB)"
        )
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    mime = magic.from_buffer(contents, mime=True)
    if mime not in ALLOWED_MIME_TYPES[ext]:
        raise HTTPException(
            status_code=400,
            detail=f"File content doesn't match {ext} (detected MIME type: {mime})"
        )

    return contents


def output_filename(original: Optional[str], ext: str) -> str:
    """Build a safe ASCII download name from the original filename."""
    stem = Path(original or "image").stem
    stem = re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('._') or "image"
    return f"{stem}.{ext}"


def run_conversion(file: UploadFile, **options) -> bytes:
    contents = read_and_validate(file)
    try:
        return convert_image(contents, file.filename, **options)
    except ConversionError as e:
        # The file passed validation but couldn't be decoded/encoded: bad input
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/convert")
def convert_endpoint(
    file: UploadFile = File(...),
    quality: int = Query(95, ge=0, le=100, description="JPEG quality (capped at 95)"),
    max_dimension: Optional[int] = Query(None, ge=16, le=16384, description="Max length of the longest edge in pixels; never upscales"),
    strip_gps: bool = Query(True, description="Remove GPS location data from the output"),
):
    """Convert an image to JPEG."""
    result = run_conversion(
        file,
        output_format="jpeg",
        quality=quality,
        max_dimension=max_dimension,
        strip_gps=strip_gps,
    )
    return Response(
        content=result,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{output_filename(file.filename, "jpg")}"'},
    )


@app.post("/convert-to-webp")
def convert_to_webp_endpoint(
    file: UploadFile = File(...),
    lossless: bool = Query(False, description="Use lossless WebP compression"),
    quality: int = Query(85, ge=0, le=100, description="Lossy: quality. Lossless: compression effort"),
    max_dimension: Optional[int] = Query(None, ge=16, le=16384, description="Max length of the longest edge in pixels; never upscales"),
    strip_gps: bool = Query(True, description="Remove GPS location data from the output"),
):
    """Convert an image to WebP. Transparency from PNG/WebP input is preserved."""
    result = run_conversion(
        file,
        output_format="webp",
        lossless=lossless,
        quality=quality,
        max_dimension=max_dimension,
        strip_gps=strip_gps,
    )
    return Response(
        content=result,
        media_type="image/webp",
        headers={"Content-Disposition": f'attachment; filename="{output_filename(file.filename, "webp")}"'},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Service information and available endpoints."""
    return {
        "service": "Image Conversion Service",
        "version": app.version,
        "endpoints": {
            "Synchronous": {
                "POST /convert": "Convert to JPEG",
                "POST /convert-to-webp": "Convert to WebP"
            },
            "System": {
                "GET /health": "Health check",
                "GET /docs": "API documentation"
            }
        },
        "supported_input_formats": sorted(SUPPORTED_EXTENSIONS),
        "output_formats": ["jpeg", "webp"],
        "options": {
            "quality": "0-100",
            "lossless": "WebP only",
            "max_dimension": "16-16384, downscale only",
            "strip_gps": "default true",
        },
        "max_file_size_mb": MAX_UPLOAD_SIZE // (1024 * 1024),
    }
