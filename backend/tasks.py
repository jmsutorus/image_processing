"""
Celery tasks for asynchronous image processing.

This module defines background tasks for converting images
using Celery for distributed task processing.
"""

from celery import Task
from celery_app import celery_app
from converter import convert_image, ConversionError
import base64
from typing import Dict, Any


class ImageConversionTask(Task):
    """Base task class with error handling and retries"""

    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True  # Exponential backoff


@celery_app.task(
    bind=True,
    base=ImageConversionTask,
    name="tasks.convert_image_task"
)
def convert_image_task(
    self,
    image_data_base64: str,
    filename: str,
    output_format: str = "jpeg",
    lossless: bool = False,
    quality: int = 85
) -> Dict[str, Any]:
    """
    Convert image asynchronously.

    Args:
        self: Celery task instance (auto-injected)
        image_data_base64: Base64-encoded image bytes
        filename: Original filename
        output_format: Output format ('jpeg' or 'webp')
        lossless: Use lossless compression (WebP only)
        quality: Quality setting (0-100)

    Returns:
        Dict with:
            - status: 'success' or 'error'
            - result_base64: Base64-encoded converted image (if success)
            - error: Error message (if error)
            - output_format: Output format used
            - filename: Suggested output filename

    Raises:
        ConversionError: If conversion fails after retries
    """
    try:
        # Update task state to PROCESSING
        self.update_state(
            state="PROCESSING",
            meta={"current": "Converting image", "total": 100, "percent": 50}
        )

        # Decode input image
        image_bytes = base64.b64decode(image_data_base64)

        # Perform conversion
        result_bytes = convert_image(
            image_bytes,
            filename,
            output_format=output_format,
            lossless=lossless,
            quality=quality
        )

        # Encode result
        result_base64 = base64.b64encode(result_bytes).decode("utf-8")

        # Generate output filename
        from pathlib import Path
        stem = Path(filename).stem
        ext = "jpg" if output_format == "jpeg" else "webp"
        output_filename = f"{stem}_converted.{ext}"

        return {
            "status": "success",
            "result_base64": result_base64,
            "output_format": output_format,
            "filename": output_filename,
            "size_bytes": len(result_bytes),
        }

    except ConversionError as e:
        # Conversion-specific error
        return {
            "status": "error",
            "error": str(e),
            "error_type": "ConversionError"
        }

    except Exception as e:
        # Unexpected error
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        }


@celery_app.task(
    bind=True,
    base=ImageConversionTask,
    name="tasks.batch_convert_images_task"
)
def batch_convert_images_task(
    self,
    files_data: list,
    output_format: str = "webp",
    lossless: bool = False,
    quality: int = 85
) -> Dict[str, Any]:
    """
    Convert multiple images in batch by dispatching individual tasks.

    This task dispatches individual conversion tasks and stores their IDs.
    The client polls the batch status endpoint to check progress.

    Args:
        self: Celery task instance
        files_data: List of dicts with 'image_data_base64' and 'filename'
        output_format: Output format for all images
        lossless: Use lossless compression (WebP only)
        quality: Quality setting for all images

    Returns:
        Dict with:
            - batch_id: This task's ID
            - status: 'dispatched'
            - total_files: Number of files in batch
            - task_ids: List of individual task IDs
            - filenames: List of filenames (same order as task_ids)
    """
    total = len(files_data)
    batch_id = self.request.id

    try:
        # Dispatch individual tasks and collect their IDs
        task_ids = []
        filenames = []

        for file_data in files_data:
            # Submit individual task
            task = convert_image_task.apply_async(
                args=[
                    file_data["image_data_base64"],
                    file_data["filename"],
                    output_format,
                    lossless,
                    quality
                ]
            )
            task_ids.append(task.id)
            filenames.append(file_data["filename"])

        # Return immediately with task tracking info
        return {
            "batch_id": batch_id,
            "status": "dispatched",
            "total_files": total,
            "task_ids": task_ids,
            "filenames": filenames
        }

    except Exception as e:
        return {
            "batch_id": batch_id,
            "status": "error",
            "error": f"Batch dispatch failed: {str(e)}",
            "total_files": total
        }
