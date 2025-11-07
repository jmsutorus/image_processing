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
from tasks import convert_image_task, batch_convert_images_task
from celery.result import AsyncResult
import base64
import zipfile
import tempfile
from typing import List

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


@app.post("/jobs/convert")
async def create_conversion_job(
    file: UploadFile = File(...),
    output_format: str = "webp",
    lossless: bool = False,
    quality: int = 85
):
    """
    Submit an async conversion job (Phase 2).

    Non-blocking: Returns job_id immediately. Use GET /jobs/{job_id}
    to check status and GET /jobs/{job_id}/result to download.

    Args:
        file: Uploaded image file (HEIC, DNG, or JPG)
        output_format: Output format ('jpeg' or 'webp')
        lossless: Use lossless compression (WebP only)
        quality: Quality setting (0-100)

    Returns:
        JSON with job_id for status tracking

    Example Response:
        {
            "job_id": "abc123-def456-...",
            "status": "pending",
            "message": "Job submitted successfully"
        }
    """
    # Read file
    contents = await file.read()

    # Validate
    validate_file(contents, file.filename)

    # Validate output format
    if output_format not in ["jpeg", "webp"]:
        raise HTTPException(
            status_code=400,
            detail="output_format must be 'jpeg' or 'webp'"
        )

    # Validate quality
    if not 0 <= quality <= 100:
        raise HTTPException(
            status_code=400,
            detail="Quality must be between 0 and 100"
        )

    # Encode image data to base64 for Celery
    image_data_base64 = base64.b64encode(contents).decode("utf-8")

    # Submit task to Celery
    task = convert_image_task.delay(
        image_data_base64=image_data_base64,
        filename=file.filename,
        output_format=output_format,
        lossless=lossless,
        quality=quality
    )

    return {
        "job_id": task.id,
        "status": "pending",
        "message": "Job submitted successfully. Use GET /jobs/{job_id} to check status."
    }


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of an async conversion job.

    Args:
        job_id: Job ID returned from POST /jobs/convert

    Returns:
        JSON with current job status

    Status Values:
        - PENDING: Job is queued
        - PROCESSING: Job is being processed
        - SUCCESS: Job completed successfully
        - FAILURE: Job failed with error

    Example Success Response:
        {
            "job_id": "abc123...",
            "status": "SUCCESS",
            "result": {
                "output_format": "webp",
                "filename": "photo_converted.webp",
                "size_bytes": 256789
            }
        }

    Example Error Response:
        {
            "job_id": "abc123...",
            "status": "FAILURE",
            "error": "Conversion failed: Invalid file format"
        }
    """
    task_result = AsyncResult(job_id)

    if task_result.state == "PENDING":
        return {
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job is queued and waiting to be processed"
        }

    elif task_result.state == "PROCESSING":
        # Get progress metadata if available
        meta = task_result.info or {}
        return {
            "job_id": job_id,
            "status": "PROCESSING",
            "progress": meta.get("percent", 0),
            "current": meta.get("current", "Processing...")
        }

    elif task_result.state == "SUCCESS":
        result = task_result.result
        if result.get("status") == "error":
            # Task completed but conversion failed
            return {
                "job_id": job_id,
                "status": "FAILURE",
                "error": result.get("error", "Unknown error"),
                "error_type": result.get("error_type", "Unknown")
            }

        return {
            "job_id": job_id,
            "status": "SUCCESS",
            "result": {
                "output_format": result["output_format"],
                "filename": result["filename"],
                "size_bytes": result["size_bytes"]
            },
            "message": "Job completed. Use GET /jobs/{job_id}/result to download."
        }

    elif task_result.state == "FAILURE":
        return {
            "job_id": job_id,
            "status": "FAILURE",
            "error": str(task_result.info) if task_result.info else "Task failed"
        }

    else:
        # RETRY, REVOKED, etc.
        return {
            "job_id": job_id,
            "status": task_result.state,
            "message": f"Job is in {task_result.state} state"
        }


@app.get("/jobs/{job_id}/result", response_class=StreamingResponse)
async def get_job_result(job_id: str):
    """
    Download the converted image from a completed job.

    Args:
        job_id: Job ID returned from POST /jobs/convert

    Returns:
        StreamingResponse with converted image bytes

    Raises:
        HTTPException 404: Job not found or not completed
        HTTPException 500: Job failed
    """
    task_result = AsyncResult(job_id)

    if task_result.state == "PENDING":
        raise HTTPException(
            status_code=404,
            detail="Job is still queued. Check status with GET /jobs/{job_id}"
        )

    elif task_result.state == "PROCESSING":
        raise HTTPException(
            status_code=404,
            detail="Job is still processing. Check status with GET /jobs/{job_id}"
        )

    elif task_result.state == "SUCCESS":
        result = task_result.result

        # Check if conversion actually succeeded
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Conversion failed: {result.get('error', 'Unknown error')}"
            )

        # Decode result
        result_base64 = result.get("result_base64")
        if not result_base64:
            raise HTTPException(
                status_code=500,
                detail="Result data not found in task result"
            )

        result_bytes = base64.b64decode(result_base64)
        filename = result.get("filename", "converted.webp")
        output_format = result.get("output_format", "webp")
        media_type = "image/jpeg" if output_format == "jpeg" else "image/webp"

        return StreamingResponse(
            io.BytesIO(result_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    elif task_result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {str(task_result.info) if task_result.info else 'Unknown error'}"
        )

    else:
        raise HTTPException(
            status_code=404,
            detail=f"Job is in unexpected state: {task_result.state}"
        )


@app.post("/jobs/batch-convert")
async def create_batch_conversion_job(
    files: List[UploadFile] = File(...),
    output_format: str = "webp",
    lossless: bool = False,
    quality: int = 85
):
    """
    Submit a batch conversion job for multiple files (Phase 2 - Batch).

    Non-blocking: Returns batch_job_id immediately. All files are processed
    in parallel. Use GET /jobs/batch/{batch_id} to check progress.

    Args:
        files: List of uploaded image files (HEIC, DNG, or JPG)
        output_format: Output format ('jpeg' or 'webp')
        lossless: Use lossless compression (WebP only)
        quality: Quality setting (0-100)

    Returns:
        JSON with batch_id for status tracking

    Example Response:
        {
            "batch_id": "batch_abc123",
            "status": "pending",
            "total_files": 5,
            "message": "Batch job submitted successfully"
        }
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided. Please upload at least one file."
        )

    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 files per batch. Please split into smaller batches."
        )

    # Validate output format
    if output_format not in ["jpeg", "webp"]:
        raise HTTPException(
            status_code=400,
            detail="output_format must be 'jpeg' or 'webp'"
        )

    # Validate quality
    if not 0 <= quality <= 100:
        raise HTTPException(
            status_code=400,
            detail="Quality must be between 0 and 100"
        )

    # Read and validate all files
    files_data = []
    for file in files:
        contents = await file.read()

        # Validate each file
        try:
            validate_file(contents, file.filename)
        except HTTPException as e:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' validation failed: {e.detail}"
            )

        # Encode for Celery
        image_data_base64 = base64.b64encode(contents).decode("utf-8")
        files_data.append({
            "image_data_base64": image_data_base64,
            "filename": file.filename
        })

    # Submit batch task to Celery
    task = batch_convert_images_task.delay(
        files_data=files_data,
        output_format=output_format,
        lossless=lossless,
        quality=quality
    )

    return {
        "batch_id": task.id,
        "status": "pending",
        "total_files": len(files),
        "message": f"Batch job submitted successfully. Processing {len(files)} files. Use GET /jobs/batch/{{batch_id}} to check status."
    }


@app.get("/jobs/batch/{batch_id}")
async def get_batch_job_status(batch_id: str):
    """
    Get status of a batch conversion job.

    Args:
        batch_id: Batch ID returned from POST /jobs/batch-convert

    Returns:
        JSON with batch status and individual file results

    Example Response:
        {
            "batch_id": "batch_abc123",
            "status": "SUCCESS",
            "total_files": 3,
            "completed": 2,
            "failed": 1,
            "percent": 100,
            "files": [
                {
                    "filename": "photo1.jpg",
                    "job_id": "job_xyz1",
                    "status": "SUCCESS",
                    "size_bytes": 256000
                },
                {
                    "filename": "photo2.heic",
                    "job_id": "job_xyz2",
                    "status": "SUCCESS",
                    "size_bytes": 128000
                },
                {
                    "filename": "photo3.dng",
                    "job_id": "job_xyz3",
                    "status": "FAILURE",
                    "error": "Conversion failed"
                }
            ]
        }
    """
    task_result = AsyncResult(batch_id)

    if task_result.state == "PENDING":
        return {
            "batch_id": batch_id,
            "status": "PENDING",
            "message": "Batch job is queued and waiting to be processed"
        }

    elif task_result.state == "PROCESSING":
        # Get progress metadata
        meta = task_result.info or {}
        return {
            "batch_id": batch_id,
            "status": "PROCESSING",
            "total_files": meta.get("total", 0),
            "completed": meta.get("completed", 0),
            "failed": meta.get("failed", 0),
            "percent": meta.get("percent", 0),
            "current": meta.get("current", "Processing...")
        }

    elif task_result.state == "SUCCESS":
        result = task_result.result

        # Check if batch dispatch failed
        if result.get("status") == "error":
            return {
                "batch_id": batch_id,
                "status": "FAILURE",
                "error": result.get("error", "Batch dispatch failed"),
                "total_files": result.get("total_files", 0)
            }

        # Get individual task IDs and filenames
        task_ids = result.get("task_ids", [])
        filenames = result.get("filenames", [])
        total_files = result.get("total_files", 0)

        # Poll each individual task
        files = []
        completed = 0
        failed = 0
        pending = 0

        for task_id, filename in zip(task_ids, filenames):
            individual_task = AsyncResult(task_id)
            file_info = {
                "filename": filename,
                "job_id": task_id,
                "status": individual_task.state
            }

            if individual_task.state == "SUCCESS":
                task_data = individual_task.result
                if isinstance(task_data, dict) and task_data.get("status") == "success":
                    completed += 1
                    file_info["status"] = "SUCCESS"
                    file_info["output_format"] = task_data.get("output_format")
                    file_info["size_bytes"] = task_data.get("size_bytes")
                else:
                    failed += 1
                    file_info["status"] = "FAILURE"
                    file_info["error"] = task_data.get("error", "Conversion failed")
            elif individual_task.state == "FAILURE":
                failed += 1
                file_info["status"] = "FAILURE"
                file_info["error"] = str(individual_task.info) if individual_task.info else "Task failed"
            elif individual_task.state == "PENDING":
                pending += 1
                file_info["status"] = "PENDING"
            elif individual_task.state == "PROCESSING":
                pending += 1
                file_info["status"] = "PROCESSING"

            files.append(file_info)

        # Determine overall status
        if pending > 0:
            overall_status = "PROCESSING"
            percent = int((completed + failed) / total_files * 100)
            message = f"Processing {pending} files. {completed} completed, {failed} failed."
        else:
            percent = 100
            if failed == 0:
                overall_status = "SUCCESS"
                message = f"All {completed} files converted successfully."
            elif completed == 0:
                overall_status = "FAILURE"
                message = f"All {failed} files failed to convert."
            else:
                overall_status = "PARTIAL"
                message = f"Batch completed with {completed} successes and {failed} failures."

        return {
            "batch_id": batch_id,
            "status": overall_status,
            "total_files": total_files,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "percent": percent,
            "files": files,
            "message": message
        }

    elif task_result.state == "FAILURE":
        return {
            "batch_id": batch_id,
            "status": "FAILURE",
            "error": str(task_result.info) if task_result.info else "Batch task failed"
        }

    else:
        return {
            "batch_id": batch_id,
            "status": task_result.state,
            "message": f"Batch is in {task_result.state} state"
        }


@app.get("/jobs/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    """
    Download all converted images from a batch job as a ZIP file.

    Args:
        batch_id: Batch ID returned from POST /jobs/batch-convert

    Returns:
        ZIP file containing all successfully converted images

    Raises:
        HTTPException 404: Batch not found or not completed
        HTTPException 500: Batch failed or no successful conversions
    """
    task_result = AsyncResult(batch_id)

    if task_result.state == "PENDING":
        raise HTTPException(
            status_code=404,
            detail="Batch is still queued. Check status with GET /jobs/batch/{batch_id}"
        )

    elif task_result.state == "PROCESSING":
        raise HTTPException(
            status_code=404,
            detail="Batch is still processing. Check status with GET /jobs/batch/{batch_id}"
        )

    elif task_result.state == "SUCCESS":
        result = task_result.result

        # Check if batch dispatch failed
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Batch dispatch failed: {result.get('error', 'Unknown error')}"
            )

        # Get individual task IDs and filenames
        task_ids = result.get("task_ids", [])
        filenames = result.get("filenames", [])

        # Collect successful conversions
        successful_files = []
        for task_id, filename in zip(task_ids, filenames):
            individual_task = AsyncResult(task_id)

            if individual_task.state == "SUCCESS":
                task_data = individual_task.result
                if isinstance(task_data, dict) and task_data.get("status") == "success":
                    result_base64 = task_data.get("result_base64")
                    output_filename = task_data.get("filename", filename)

                    if result_base64:
                        successful_files.append({
                            "filename": output_filename,
                            "data": base64.b64decode(result_base64)
                        })

        # Check if we have any successful results
        if len(successful_files) == 0:
            raise HTTPException(
                status_code=500,
                detail="All files in batch failed to convert or are still processing. Check batch status for details."
            )

        # Create ZIP file with all successful conversions
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            zip_path = tmp_zip.name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in successful_files:
                    zipf.writestr(file_info["filename"], file_info["data"])

            # Read ZIP file
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()

            # Clean up temp file
            import os
            os.unlink(zip_path)

            return StreamingResponse(
                io.BytesIO(zip_bytes),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=batch_{batch_id[:8]}_results.zip"
                }
            )

    elif task_result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail=f"Batch failed: {str(task_result.info) if task_result.info else 'Unknown error'}"
        )

    else:
        raise HTTPException(
            status_code=404,
            detail=f"Batch is in unexpected state: {task_result.state}"
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
        "version": "2.0.0",
        "endpoints": {
            "Synchronous (Phase 1)": {
                "POST /convert": "Convert HEIC/DNG/JPG to JPEG (blocking)",
                "POST /convert-to-webp": "Convert HEIC/DNG/JPG to WebP (blocking)"
            },
            "Asynchronous (Phase 2)": {
                "POST /jobs/convert": "Submit async conversion job (non-blocking)",
                "GET /jobs/{job_id}": "Check job status",
                "GET /jobs/{job_id}/result": "Download converted image"
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
            "async_processing": True,
            "job_queuing": True,
            "concurrent_workers": 2,
            "result_ttl_seconds": 3600
        }
    }
