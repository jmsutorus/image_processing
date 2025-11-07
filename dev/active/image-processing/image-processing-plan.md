# Image Processing Service - Implementation Plan

**Last Updated: 2025-11-06**
**Status:** In Progress - Section 1 Complete (Docker Infrastructure)

---

## Executive Summary

This project implements a scalable web service for converting HEIC (High-Efficiency Image Container) and DNG (Digital Negative) image formats to JPEG with complete metadata preservation. The implementation follows a phased approach, starting with a simple synchronous Python application and evolving into a production-ready microservices architecture.

**Core Value Proposition:**
- Professional-grade image conversion with EXIF/XMP/IPTC metadata preservation
- Support for both consumer (HEIC from iPhones) and professional (DNG from cameras) formats
- High-quality output (95% JPEG quality, no chroma subsampling)

**Technology Stack:**
- **Backend:** Python 3.11+ with FastAPI
- **Core Libraries:** pillow-heif (HEIC), rawpy (DNG), Pillow (image processing)
- **Containerization:** Docker with system dependencies (libheif, LibRaw, exiftool)
- **Future Scaling:** Celery + Redis (async), AWS S3 (storage), React (frontend)

---

## Current State Analysis

### Existing Assets
- ✅ Comprehensive PRD research document (`context/prd_research.md`)
- ✅ Technology evaluation and architecture blueprint completed
- ✅ Git repository initialized
- ✅ Python-specific .gitignore configured

### Current Gaps
- ❌ No backend code implementation
- ❌ No Docker infrastructure
- ❌ No test images or validation suite
- ❌ No API endpoints
- ❌ No documentation beyond PRD

### Technical Challenges Identified
1. **Metadata Preservation:** HEIC metadata must be copied via Pillow's EXIF support; DNG requires exiftool subprocess
2. **DNG Processing:** Requires specific rawpy parameters (use_camera_wb=True, sRGB color space) to avoid distorted output
3. **Security:** ExifTool CVE-2021-22204 requires version pinning; subprocess injection prevention needed
4. **Resource Management:** Large files (20-100MB DNG) require tmpfs storage and proper cleanup

---

## Proposed Future State

### Phase 1: Simple Synchronous Service (MVP)
**Timeline:** 1-2 weeks
**Goal:** Prove conversion pipeline with metadata preservation

**Architecture:**
```
┌─────────────────────────────────────┐
│   Docker Container                  │
│  ┌─────────────────────────────┐   │
│  │  FastAPI App                │   │
│  │  - POST /convert            │   │
│  │  - GET /health              │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│  ┌──────────▼──────────────────┐   │
│  │  converter.py               │   │
│  │  - HEIC → JPEG (pillow-heif)│   │
│  │  - DNG → JPEG (rawpy+exiftool)│ │
│  └─────────────────────────────┘   │
│                                     │
│  System Dependencies:               │
│  - libheif-dev                      │
│  - libraw-dev                       │
│  - libjpeg-turbo-dev                │
│  - exiftool (v12.76+)               │
└─────────────────────────────────────┘
```

**Deliverables:**
- Single Docker container with all dependencies
- Synchronous image conversion (blocking)
- Local tmpfs storage (memory-backed /tmp)
- Manual testing with sample images
- README with usage instructions

### Phase 2: Asynchronous Processing (Future)
**Goal:** Handle concurrent users and long-running conversions

**Additions:**
- Celery distributed task queue
- Redis message broker
- Job status polling API
- Multiple worker containers

### Phase 3: Cloud Storage Integration (Future)
**Goal:** Scalable storage and client-side uploads

**Additions:**
- AWS S3 bucket configuration
- Presigned URL generation
- Direct client-to-S3 uploads
- Result persistence (1 hour TTL)

### Phase 4: Production Deployment (Future)
**Goal:** Production-ready with monitoring and frontend

**Additions:**
- React frontend with drag-and-drop
- Client-side HEIC preview (WASM)
- CI/CD pipeline (GitHub Actions)
- Authentication (API keys)
- Monitoring and logging

---

## Implementation Phases

## PHASE 1: Simple Synchronous Service (MVP)

### Section 1: Project Structure & Docker Infrastructure

#### Task 1.1: Create Backend Directory Structure
**Priority:** P0 (Blocker)
**Effort:** S (Small)
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Create `backend/` directory in project root
- [ ] Create subdirectories: `backend/test_images/`
- [ ] Verify structure matches plan

**Implementation Notes:**
```bash
mkdir -p backend/test_images
```

---

#### Task 1.2: Create Dockerfile with System Dependencies
**Priority:** P0 (Blocker)
**Effort:** M (Medium)
**Dependencies:** Task 1.1

**Acceptance Criteria:**
- [ ] Base image: `python:3.11-slim-bookworm`
- [ ] System packages installed: libheif-dev, libraw-dev, libjpeg-turbo-dev
- [ ] ExifTool pinned to version 12.76+dfsg-1 (prevents CVE-2021-22204)
- [ ] Non-root user `appuser` created (UID 1000)
- [ ] `/tmp/uploads` and `/tmp/converted` directories created with correct permissions
- [ ] Health check validates Python libraries load: `python -c "import rawpy; import pillow_heif; from PIL import Image"`
- [ ] Docker image builds successfully without errors
- [ ] Image size < 1GB (ideally ~500-700MB)

**Security Requirements:**
- Non-root execution (USER appuser)
- No shell=True in any subprocess calls
- Pinned exiftool version to prevent RCE vulnerability

**Implementation Template:**
```dockerfile
FROM python:3.11-slim-bookworm

# Install system dependencies with pinned versions
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libraw-dev \
    libjpeg-turbo-dev \
    exiftool=12.76+dfsg-1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /tmp/uploads /tmp/converted && \
    chown -R appuser:appuser /tmp/uploads /tmp/converted

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify libraries load correctly (fail fast if deps broken)
RUN python -c "import rawpy; import pillow_heif; from PIL import Image"

COPY . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Validation Commands:**
```bash
cd backend
docker build -t image-processor:phase1 .
docker images | grep image-processor  # Check size
docker run --rm image-processor:phase1 python -c "import rawpy; print('Libraries OK')"
```

---

#### Task 1.3: Create requirements.txt
**Priority:** P0 (Blocker)
**Effort:** S (Small)
**Dependencies:** Task 1.2

**Acceptance Criteria:**
- [ ] All required Python packages listed with pinned versions
- [ ] NO async libraries (celery, redis, boto3) included in Phase 1
- [ ] Includes: fastapi, uvicorn, pillow, pillow-heif, rawpy, python-multipart, python-magic
- [ ] `pip install -r requirements.txt` succeeds without errors
- [ ] Total install size documented

**Implementation:**
```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# Image Processing
pillow==10.2.0
pillow-heif==0.15.0
rawpy==0.19.0

# Utilities
python-multipart==0.0.6  # File upload support
python-magic==0.4.27     # MIME type validation
```

**Validation:**
```bash
pip install -r requirements.txt
python -c "import fastapi, pillow_heif, rawpy; print('All imports successful')"
```

---

#### Task 1.4: Create docker-compose.yml
**Priority:** P0 (Blocker)
**Effort:** S (Small)
**Dependencies:** Task 1.2, Task 1.3

**Acceptance Criteria:**
- [ ] Single service definition (app only)
- [ ] Port 8000 exposed and mapped
- [ ] tmpfs mount configured for /tmp (1GB limit)
- [ ] Environment variables configured (PYTHONUNBUFFERED=1)
- [ ] `docker-compose up` starts service successfully
- [ ] Service responds to health check at http://localhost:8000/health

**Implementation:**
```yaml
version: '3.8'

services:
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      # Mount tmpfs for /tmp (memory-backed, auto-cleanup)
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 1G  # Limit to 1GB RAM
    restart: unless-stopped
```

**Validation:**
```bash
docker-compose up -d
curl http://localhost:8000/health  # Should return {"status": "healthy"}
docker-compose logs -f app
docker-compose down
```

---

### Section 2: Core Conversion Logic

#### Task 2.1: Implement converter.py - HEIC Conversion
**Priority:** P0 (Blocker)
**Effort:** M (Medium)
**Dependencies:** Task 1.3

**Acceptance Criteria:**
- [ ] `convert_image()` function accepts bytes and filename, returns JPEG bytes
- [ ] `_convert_heic()` function handles HEIC → JPEG conversion
- [ ] EXIF metadata preserved using Pillow's `exif` parameter
- [ ] JPEG quality set to 95 with subsampling=0 (4:4:4)
- [ ] Uses TemporaryDirectory for automatic file cleanup
- [ ] pillow_heif.register_heif_opener() called once at module level
- [ ] ConversionError custom exception defined
- [ ] Error handling catches corrupt files gracefully

**Implementation Template:**
```python
import io
import os
import tempfile
from pathlib import Path
from typing import Literal

import pillow_heif
from PIL import Image

# Register HEIF opener globally (call once)
pillow_heif.register_heif_opener()

class ConversionError(Exception):
    """Raised when conversion fails"""
    pass

def convert_image(
    input_bytes: bytes,
    filename: str,
    output_format: Literal["jpeg"] = "jpeg"
) -> bytes:
    """
    Convert HEIC or DNG to JPEG with metadata preservation.

    Args:
        input_bytes: Raw file bytes
        filename: Original filename (used to determine type)
        output_format: Output format (only 'jpeg' supported)

    Returns:
        JPEG bytes

    Raises:
        ConversionError: If conversion fails
    """
    file_ext = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)
        output_path = os.path.join(tmpdir, "output.jpg")

        try:
            # Write input file
            with open(input_path, 'wb') as f:
                f.write(input_bytes)

            if file_ext in ['.heic', '.heif']:
                _convert_heic(input_path, output_path)
            elif file_ext == '.dng':
                _convert_dng(input_path, output_path)
            else:
                raise ConversionError(f"Unsupported file type: {file_ext}")

            # Read result
            with open(output_path, 'rb') as f:
                return f.read()

        except Exception as e:
            raise ConversionError(f"Conversion failed: {str(e)}")

def _convert_heic(input_path: str, output_path: str):
    """Convert HEIC to JPEG with EXIF preservation"""
    try:
        with Image.open(input_path) as image:
            # Extract EXIF metadata
            exif_data = image.info.get('exif')

            # Convert and save with high quality
            image.convert('RGB').save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0,
                exif=exif_data
            )
    except Exception as e:
        raise ConversionError(f"HEIC conversion failed: {e}")
```

**Test Requirements:**
- Unit test with sample HEIC file
- Verify output is valid JPEG
- Verify EXIF data preserved (compare with exiftool)
- Test with corrupt HEIC (should raise ConversionError)

---

#### Task 2.2: Implement converter.py - DNG Conversion
**Priority:** P0 (Blocker)
**Effort:** L (Large)
**Dependencies:** Task 2.1

**Acceptance Criteria:**
- [ ] `_convert_dng()` function handles DNG → JPEG conversion
- [ ] Uses rawpy with correct parameters:
  - `use_camera_wb=True` (camera white balance)
  - `output_color=rawpy.ColorSpace.sRGB` (web-compatible color)
  - `no_auto_bright=True` (predictable brightness)
  - `bright=1.0` (linear brightness)
- [ ] Converts numpy array to PIL Image correctly
- [ ] JPEG saved with quality=95, subsampling=0
- [ ] Metadata copied using exiftool subprocess
- [ ] Subprocess uses `shell=False` (security requirement)
- [ ] Subprocess has 30-second timeout
- [ ] Temporary DNG file cleaned up after exiftool
- [ ] Error handling for rawpy and subprocess failures

**Critical Security Note:**
NEVER use `shell=True` with subprocess. This prevents command injection attacks.

**Implementation Template:**
```python
import subprocess
import rawpy

def _convert_dng(input_path: str, output_path: str):
    """Convert DNG to JPEG with metadata copying via exiftool"""
    try:
        # Step 1: Develop RAW with rawpy
        with rawpy.imread(input_path) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,       # Use camera white balance
                output_color=rawpy.ColorSpace.sRGB,
                no_auto_bright=True,      # Don't auto-adjust brightness
                bright=1.0                # Linear brightness
            )

        # Step 2: Save RGB array as JPEG (no metadata yet)
        with Image.fromarray(rgb) as image:
            image.save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0
            )

        # Step 3: Copy metadata using exiftool (CRITICAL STEP)
        subprocess.run(
            [
                'exiftool',
                '-TagsFromFile', input_path,
                '-overwrite_original',
                output_path
            ],
            shell=False,      # SECURITY: Never use shell=True
            check=True,
            capture_output=True,
            timeout=30
        )

    except subprocess.CalledProcessError as e:
        raise ConversionError(f"exiftool failed: {e.stderr.decode()}")
    except Exception as e:
        raise ConversionError(f"DNG conversion failed: {e}")
```

**Test Requirements:**
- Unit test with sample DNG file
- Verify output is valid JPEG
- Verify metadata preserved (use exiftool to compare)
- Test rawpy parameters produce correct white balance
- Test subprocess timeout (mock slow exiftool)
- Verify no shell injection vulnerability

---

### Section 3: API Implementation

#### Task 3.1: Implement FastAPI Application (app.py)
**Priority:** P0 (Blocker)
**Effort:** M (Medium)
**Dependencies:** Task 2.2

**Acceptance Criteria:**
- [ ] FastAPI app initialized with title "Image Conversion Service"
- [ ] POST /convert endpoint accepts file uploads
- [ ] GET /health endpoint returns {"status": "healthy"}
- [ ] File size validation (max 200MB)
- [ ] File extension validation (.heic, .heif, .dng)
- [ ] MIME type validation using python-magic
- [ ] Returns JPEG as StreamingResponse with correct headers
- [ ] Error responses use appropriate HTTP status codes:
  - 400: Invalid file type
  - 413: File too large
  - 500: Conversion error
- [ ] All file validation happens before processing

**Implementation Template:**
```python
import io
import magic
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from converter import convert_image, ConversionError

app = FastAPI(title="Image Conversion Service")

MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'.heic', '.heif', '.dng'}

def validate_file(contents: bytes, filename: str) -> None:
    """Validate file size and type"""
    # Check size
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(413, "File too large (max 200MB)")

    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Check MIME type (magic number)
    mime = magic.from_buffer(contents, mime=True)

    if ext in ['.heic', '.heif']:
        if not mime.startswith('image/heic') and mime != 'image/heif':
            raise HTTPException(400, "File is not a valid HEIC")
    elif ext == '.dng':
        if mime not in ['image/x-adobe-dng', 'image/tiff']:
            raise HTTPException(400, "File is not a valid DNG")

@app.post("/convert")
async def convert_endpoint(file: UploadFile = File(...)):
    """
    Convert HEIC or DNG to JPEG.

    Synchronous processing: returns JPEG when complete.
    """
    # Read file
    contents = await file.read()

    # Validate
    validate_file(contents, file.filename)

    # Convert (blocking operation)
    try:
        result_bytes = convert_image(contents, file.filename)
    except ConversionError as e:
        raise HTTPException(500, str(e))

    # Return JPEG
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f"attachment; filename=converted.jpg"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

**Test Requirements:**
- Integration test: upload valid HEIC, verify JPEG response
- Integration test: upload valid DNG, verify JPEG response
- Error test: upload 300MB file, verify 413 status
- Error test: upload .txt file with .heic extension, verify 400 status
- Error test: upload corrupt HEIC, verify 500 status

---

### Section 4: Testing & Validation

#### Task 4.1: Acquire Test Images
**Priority:** P0 (Blocker)
**Effort:** S (Small)
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Obtain sample.heic (iPhone photo with GPS EXIF)
- [ ] Obtain sample.dng (camera RAW with full metadata)
- [ ] Both files stored in `backend/test_images/`
- [ ] File sizes documented
- [ ] Baseline metadata extracted: `exiftool -json sample.heic > sample_heic_metadata.json`
- [ ] Baseline metadata extracted: `exiftool -json sample.dng > sample_dng_metadata.json`

**Sources:**
- HEIC: Take photo with iPhone or use sample from https://github.com/nokiatech/heif/tree/gh-pages/content
- DNG: Use camera or download from https://www.adobe.com/support/downloads/dng/dng_sdk.html

**Documentation Required:**
Create `backend/test_images/README.md` with:
- Source of each file
- File sizes
- Expected metadata fields
- Known issues (if any)

---

#### Task 4.2: Create Manual Test Script
**Priority:** P1 (High)
**Effort:** S (Small)
**Dependencies:** Task 3.1, Task 4.1

**Acceptance Criteria:**
- [ ] Bash script `backend/test_conversion.sh` created
- [ ] Script tests HEIC conversion via curl
- [ ] Script tests DNG conversion via curl
- [ ] Script extracts and compares metadata using exiftool
- [ ] Script includes visual inspection instructions
- [ ] Script exits with non-zero on failure

**Implementation:**
```bash
#!/bin/bash
set -e

echo "=== Image Conversion Manual Test Suite ==="

# Ensure docker-compose is running
docker-compose up -d
sleep 3

# Test HEIC conversion
echo "[1/4] Testing HEIC conversion..."
curl -X POST "http://localhost:8000/convert" \
  -F "file=@test_images/sample.heic" \
  --output result_heic.jpg \
  --fail

echo "[2/4] Verifying HEIC metadata..."
exiftool -json test_images/sample.heic > heic_original.json
exiftool -json result_heic.jpg > heic_result.json
# Manual comparison required - automate in Phase 3

# Test DNG conversion
echo "[3/4] Testing DNG conversion..."
curl -X POST "http://localhost:8000/convert" \
  -F "file=@test_images/sample.dng" \
  --output result_dng.jpg \
  --fail

echo "[4/4] Verifying DNG metadata..."
exiftool -json test_images/sample.dng > dng_original.json
exiftool -json result_dng.jpg > dng_result.json

echo "✅ All conversions completed successfully"
echo ""
echo "Manual Verification Steps:"
echo "1. Open result_heic.jpg and result_dng.jpg"
echo "2. Verify image quality is high (no artifacts)"
echo "3. Compare *_original.json vs *_result.json"
echo "4. Verify critical fields preserved: Make, Model, DateTimeOriginal, GPSLatitude"
```

**Usage:**
```bash
cd backend
chmod +x test_conversion.sh
./test_conversion.sh
```

---

#### Task 4.3: Validate Metadata Preservation
**Priority:** P0 (Blocker)
**Effort:** M (Medium)
**Dependencies:** Task 4.2

**Acceptance Criteria:**
- [ ] HEIC test: GPS coordinates preserved
- [ ] HEIC test: Camera make/model preserved
- [ ] HEIC test: DateTime preserved
- [ ] DNG test: Camera settings preserved (ISO, aperture, shutter speed)
- [ ] DNG test: ColorSpace preserved
- [ ] DNG test: No metadata corruption
- [ ] Document any known metadata losses

**Validation Process:**
1. Run test script from Task 4.2
2. Compare JSON outputs manually
3. Focus on critical fields:
   - Make, Model (camera info)
   - DateTimeOriginal (capture time)
   - GPSLatitude, GPSLongitude (location)
   - ISO, FNumber, ExposureTime (camera settings)
   - ColorSpace (sRGB for output)

**Success Criteria:**
- All critical fields match between original and converted
- No corruption (garbled text, wrong dates)
- Output is sRGB color space

---

#### Task 4.4: Validate Image Quality
**Priority:** P0 (Blocker)
**Effort:** S (Small)
**Dependencies:** Task 4.2

**Acceptance Criteria:**
- [ ] Visual inspection: No visible compression artifacts
- [ ] Visual inspection: Colors appear accurate
- [ ] Visual inspection: DNG brightness looks correct (not too dark/light)
- [ ] JPEG file size is reasonable (not 10x larger than expected)
- [ ] No black images or corrupt output
- [ ] Document quality observations

**Validation Process:**
1. Open result_heic.jpg and result_dng.jpg in image viewer
2. Zoom to 100% and inspect edges/text for artifacts
3. Compare colors to original (if viewable)
4. Check file sizes: should be 2-5MB for typical images

**Known Issues to Watch For:**
- DNG too dark: Check rawpy parameters (use_camera_wb=True)
- Color shift: Verify output_color=sRGB
- Artifacts on edges: Check subsampling=0 is set
- Huge files: Verify quality=95 (not 100)

---

### Section 5: Documentation

#### Task 5.1: Create Project README.md
**Priority:** P1 (High)
**Effort:** M (Medium)
**Dependencies:** All Phase 1 tasks

**Acceptance Criteria:**
- [ ] Project overview and features listed
- [ ] Technology stack documented
- [ ] Quick start guide with docker-compose
- [ ] API usage examples with curl
- [ ] Phase 1 limitations clearly stated
- [ ] Future roadmap outlined
- [ ] Contributing guidelines (if applicable)
- [ ] License specified

**Required Sections:**
1. Project Description
2. Features
3. Technology Stack
4. Getting Started
   - Prerequisites
   - Installation
   - Running with Docker
5. API Documentation
   - POST /convert
   - GET /health
6. Testing
7. Known Limitations (Phase 1)
8. Future Roadmap (Phases 2-4)
9. License

---

#### Task 5.2: Create .env.example
**Priority:** P2 (Medium)
**Effort:** S (Small)
**Dependencies:** Task 3.1

**Acceptance Criteria:**
- [ ] Example environment variables documented
- [ ] Comments explain each variable
- [ ] No sensitive values included
- [ ] Instructions for Phase 2+ variables (commented out)

**Implementation:**
```bash
# Phase 1 Configuration
PYTHONUNBUFFERED=1
MAX_UPLOAD_SIZE_MB=200

# Phase 2 (Future - Not Used Yet)
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Phase 3 (Future - Not Used Yet)
# AWS_REGION=us-east-1
# AWS_S3_BUCKET=my-image-converter
# AWS_ACCESS_KEY_ID=your-key-here
# AWS_SECRET_ACCESS_KEY=your-secret-here
```

---

#### Task 5.3: Document Known Issues & Workarounds
**Priority:** P2 (Medium)
**Effort:** S (Small)
**Dependencies:** Task 4.3, Task 4.4

**Acceptance Criteria:**
- [ ] Create `backend/KNOWN_ISSUES.md`
- [ ] List any metadata losses observed
- [ ] Document timeout issues (if any)
- [ ] Note file size limits
- [ ] Provide workarounds where possible

**Template:**
```markdown
# Known Issues - Phase 1

## Limitations
1. **Synchronous Processing**: Large files may timeout (>60s processing time)
   - Workaround: Limit file size to 200MB
   - Fix in Phase 2: Async processing with Celery

2. **No Result Persistence**: Download must happen immediately
   - Workaround: None in Phase 1
   - Fix in Phase 3: S3 storage with 1-hour TTL

3. **Single Worker**: Only one conversion at a time per container
   - Workaround: Run multiple containers (docker-compose scale)
   - Fix in Phase 2: Multiple Celery workers

## Metadata Known Losses
- [Document any fields that don't transfer correctly]

## Performance
- Average HEIC conversion: ~2-3 seconds (50MB file)
- Average DNG conversion: ~8-15 seconds (100MB file)
```

---

## PHASE 2: Asynchronous Processing (Future)

### Overview
Add Celery + Redis for background job processing. This enables:
- Non-blocking API responses
- Job status polling
- Multiple concurrent conversions
- Worker pool scaling

### Key Changes
- Add Redis service to docker-compose
- Convert `converter.py` functions to Celery tasks
- Replace `/convert` with `/upload` → task_id → `/status/<task_id>`
- No changes to core conversion logic

### Timeline
2-3 weeks after Phase 1 validation

---

## PHASE 3: Cloud Storage (Future)

### Overview
Add AWS S3 for scalable storage and direct client uploads.

### Key Changes
- S3 bucket configuration with CORS
- Presigned URL generation endpoint
- React frontend uploads directly to S3
- Celery workers read from/write to S3

### Timeline
3-4 weeks after Phase 2

---

## PHASE 4: Production Deployment (Future)

### Overview
Full production stack with frontend, monitoring, and CI/CD.

### Key Changes
- React frontend with heic2any previews
- GitHub Actions CI/CD pipeline
- API authentication (JWT tokens)
- Prometheus + Grafana monitoring
- Automated visual regression tests

### Timeline
4-6 weeks after Phase 3

---

## Risk Assessment and Mitigation

### High-Risk Items

#### Risk 1: Docker Build Failures (System Dependencies)
**Likelihood:** Medium
**Impact:** High (blocks development)

**Scenario:** libheif or LibRaw not available in apt repositories for Debian Bookworm

**Mitigation:**
- Use multi-stage build to compile from source if needed
- Test Docker build early (Task 1.2)
- Alternative: Use alpine base with apk packages
- Fallback: Manual compilation with Dockerfile RUN commands

**Contingency:**
```dockerfile
# If apt-get fails, compile from source
RUN wget https://github.com/strukturag/libheif/releases/download/v1.17.0/libheif-1.17.0.tar.gz && \
    tar xzf libheif-1.17.0.tar.gz && \
    cd libheif-1.17.0 && \
    ./configure && make && make install
```

---

#### Risk 2: Metadata Loss (Critical Business Requirement)
**Likelihood:** Medium
**Impact:** Critical (project failure)

**Scenario:** HEIC or DNG metadata not preserved correctly, making service unusable

**Mitigation:**
- Early testing with real-world files (Task 4.1)
- Automated metadata comparison (Task 4.3)
- Baseline validation before proceeding
- Consult PRD research if issues arise

**Contingency:**
- If HEIC metadata fails: Investigate Pillow version compatibility
- If DNG metadata fails: Verify exiftool command flags
- Last resort: Use ImageMagick with `convert -auto-orient`

---

#### Risk 3: Performance (Timeout Issues)
**Likelihood:** Medium
**Impact:** Medium (degrades UX)

**Scenario:** 100MB DNG takes >60 seconds to process, causing timeouts

**Mitigation:**
- Increase Uvicorn timeout: `--timeout-keep-alive 120`
- Use tmpfs for faster I/O
- Document file size limits clearly
- Plan Phase 2 async upgrade

**Contingency:**
- Reduce max file size to 100MB
- Add progress indicators (Phase 2+)
- Upgrade to larger Docker host

---

### Medium-Risk Items

#### Risk 4: ExifTool Subprocess Hanging
**Likelihood:** Low
**Impact:** Medium (conversion fails)

**Scenario:** exiftool process hangs indefinitely on corrupt file

**Mitigation:**
- 30-second timeout on subprocess.run()
- Capture stderr for debugging
- Test with intentionally corrupt files

---

#### Risk 5: Disk Space Exhaustion
**Likelihood:** Low (with tmpfs)
**Impact:** Medium

**Scenario:** /tmp fills up if tmpfs limit reached or TemporaryDirectory cleanup fails

**Mitigation:**
- Use tmpfs (auto-clears on restart)
- TemporaryDirectory context manager (auto-cleanup)
- Monitor Docker disk usage

---

## Success Metrics

### Phase 1 Completion Criteria
- [ ] Docker container builds successfully
- [ ] Health check endpoint responds
- [ ] HEIC conversion works with metadata preserved
- [ ] DNG conversion works with metadata preserved
- [ ] Manual test script passes
- [ ] Image quality meets standards (quality=95, subsampling=0)
- [ ] Security requirements met (non-root user, no shell=True)
- [ ] Documentation complete (README, KNOWN_ISSUES)

### Quality Metrics
- **Metadata Preservation Rate:** 100% for critical fields (Make, Model, DateTime, GPS)
- **Image Quality:** No visible artifacts at 100% zoom
- **Conversion Speed:** <5s for HEIC, <20s for DNG (100MB file)
- **Error Rate:** <1% for valid files
- **Security:** No CVEs, no shell injection vulnerabilities

### Performance Benchmarks (Baseline)
Document actual performance during testing:
- HEIC (10MB): __ seconds
- HEIC (50MB): __ seconds
- DNG (20MB): __ seconds
- DNG (100MB): __ seconds

---

## Required Resources and Dependencies

### Development Environment
- **OS:** Linux or macOS (Windows requires WSL2)
- **Docker:** Version 24.0+ with docker-compose
- **Python:** 3.11+ (for local development)
- **Disk Space:** 2GB for Docker images
- **RAM:** 4GB minimum (8GB recommended)

### External Dependencies
- **System Packages:** libheif-dev, libraw-dev, libjpeg-turbo-dev, exiftool
- **Python Packages:** See requirements.txt
- **Test Assets:** HEIC and DNG sample files

### Skills Required
- Python development (intermediate)
- Docker and containerization (intermediate)
- FastAPI or similar web frameworks (beginner)
- Image processing concepts (basic understanding)
- Subprocess management (security awareness)

---

## Timeline Estimates

### Phase 1: Simple Synchronous Service
**Total Estimated Time:** 1-2 weeks (40-80 hours)

| Task Category | Estimated Time | Priority |
|--------------|----------------|----------|
| Docker Infrastructure (1.1-1.4) | 8-12 hours | P0 |
| Core Conversion Logic (2.1-2.2) | 16-24 hours | P0 |
| API Implementation (3.1) | 8-12 hours | P0 |
| Testing & Validation (4.1-4.4) | 8-16 hours | P0 |
| Documentation (5.1-5.3) | 4-8 hours | P1 |

**Breakdown by Day (Aggressive):**
- Day 1-2: Docker setup and dependencies
- Day 3-4: HEIC conversion implementation
- Day 5-6: DNG conversion implementation
- Day 7-8: API and integration testing
- Day 9-10: Documentation and final validation

**Breakdown by Day (Conservative):**
- Week 1: Infrastructure + HEIC conversion
- Week 2: DNG conversion + testing + docs

---

## Appendix A: Technology Decisions Rationale

### Why Python?
- Best-in-class bindings for libheif (pillow-heif) and LibRaw (rawpy)
- Mature ecosystem with Pillow for image processing
- Simpler deployment (pip wheels vs. node-gyp compilation)
- Proven at scale (Instagram, Dropbox use Python for image processing)

### Why FastAPI over Flask?
- Modern async support (useful for Phase 2+)
- Automatic OpenAPI documentation
- Type hints and validation with Pydantic
- Better performance than Flask for async workloads

### Why Docker?
- Ensures consistent system dependencies (libheif, LibRaw)
- Isolates environment from host system
- Easy to scale (docker-compose scale)
- Production-ready (can deploy to Kubernetes later)

### Why Synchronous First?
- Simpler to implement and debug
- Proves core conversion logic works
- Can validate quality before adding complexity
- Easy migration path to async (Celery)

---

## Appendix B: Migration Path to Phases 2-4

### Phase 1 → Phase 2 (Async)
**Changes Required:**
1. Add `celery[redis]` to requirements.txt
2. Create `backend/tasks.py` with @shared_task decorators
3. Move conversion logic to Celery tasks (no logic changes)
4. Add Redis service to docker-compose.yml
5. Change API: `/convert` → `/upload` (returns task_id)
6. Add `/status/<task_id>` endpoint

**What Stays the Same:**
- converter.py logic (100% reusable)
- Dockerfile dependencies
- Test images and validation

---

### Phase 2 → Phase 3 (S3)
**Changes Required:**
1. Add `boto3` to requirements.txt
2. Create S3 bucket with CORS configuration
3. Add `/generate-presigned-url` endpoint
4. Modify Celery tasks to download from S3
5. Modify Celery tasks to upload results to S3

**What Stays the Same:**
- Core conversion logic
- Metadata preservation approach
- Image quality parameters

---

### Phase 3 → Phase 4 (Production)
**Changes Required:**
1. Build React frontend with file upload
2. Implement heic2any for client-side previews
3. Add authentication (JWT tokens or API keys)
4. GitHub Actions CI/CD pipeline
5. Visual regression tests
6. Monitoring (Prometheus + Grafana)

**What Stays the Same:**
- Backend API contracts
- Conversion quality
- Infrastructure (Docker base)

---

## Appendix C: Security Considerations

### Subprocess Injection Prevention
**Vulnerability:** Command injection via filenames with shell metacharacters

**Example Attack:**
```python
# VULNERABLE CODE (DO NOT USE)
filename = "; rm -rf /"
subprocess.run(f'exiftool -TagsFromFile "{filename}" output.jpg', shell=True)
```

**Mitigation:**
```python
# SAFE CODE (ALWAYS USE THIS)
subprocess.run(
    ['exiftool', '-TagsFromFile', filename, output_path],
    shell=False,  # CRITICAL: Prevents shell interpretation
    check=True,
    capture_output=True,
    timeout=30
)
```

---

### ExifTool CVE-2021-22204
**Vulnerability:** Remote code execution via malicious DNG files (ExifTool < 12.24)

**Mitigation:**
- Pin exiftool version to 12.76+dfsg-1 in Dockerfile
- Verify version: `docker run --rm image-processor:phase1 exiftool -ver`

---

### Non-Root Container Execution
**Vulnerability:** Privilege escalation if container compromised

**Mitigation:**
- Run as non-root user (UID 1000)
- Drop capabilities if possible
- Use read-only filesystem where possible

---

## Appendix D: Troubleshooting Guide

### Issue: Docker build fails with "libheif-dev not found"
**Cause:** Package not available in Debian Bookworm repositories

**Solution:**
```dockerfile
# Add backports repository
RUN echo "deb http://deb.debian.org/debian bookworm-backports main" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y libheif-dev/bookworm-backports
```

---

### Issue: HEIC metadata not preserved
**Cause:** Pillow version incompatibility or EXIF data not passed to save()

**Diagnosis:**
```python
with Image.open('test.heic') as img:
    print(img.info.keys())  # Should include 'exif'
```

**Solution:**
- Ensure pillow-heif.register_heif_opener() called before Image.open()
- Verify exif_data is not None before save()
- Check Pillow version >= 10.0

---

### Issue: DNG conversion too dark
**Cause:** Incorrect rawpy post-processing parameters

**Solution:**
```python
# Ensure these parameters are set
rgb = raw.postprocess(
    use_camera_wb=True,  # CRITICAL for correct white balance
    no_auto_bright=True,  # Prevents over-darkening
    bright=1.0            # Linear brightness
)
```

---

### Issue: Subprocess timeout on exiftool
**Cause:** Corrupt DNG file or slow I/O

**Diagnosis:**
```bash
# Test exiftool directly
docker exec -it <container_id> exiftool -TagsFromFile test.dng output.jpg
```

**Solution:**
- Increase timeout to 60 seconds
- Validate DNG file before exiftool
- Add file size check (<200MB)

---

## Appendix E: References

### Documentation
- [PRD Research Document](../../../context/prd_research.md) - Comprehensive technology analysis
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pillow-HEIF Documentation](https://pillow-heif.readthedocs.io/)
- [rawpy Documentation](https://letmaik.github.io/rawpy/)
- [ExifTool Documentation](https://exiftool.org/)

### Key Research Findings
- HEIC metadata preservation requires Pillow's `exif` parameter (PRD Section IV)
- DNG requires `use_camera_wb=True` to avoid distorted output (PRD Section IV)
- Client-side conversion strips metadata (PRD Section IV)
- ExifTool CVE-2021-22204 requires version >= 12.24 (PRD Section X)

---

## Implementation Progress (2025-11-06)

### Phase 1 Status: 29% Complete (4 of 14 tasks)

#### ✅ Section 1: Project Structure & Docker Infrastructure (COMPLETE)
All infrastructure tasks successfully completed:

**Task 1.1: Backend Directory Structure** ✅
- Backend directory structure exists and verified
- Ready for implementation

**Task 1.2: Dockerfile with System Dependencies** ✅
- Docker image builds successfully
- All system dependencies installed correctly
- Health check passes
- **Issue Resolved:** Removed exiftool version pin (12.76+dfsg-1 unavailable in Bookworm repos)

**Task 1.3: Python Dependencies (requirements.txt)** ✅
- All packages installed successfully
- **Issue Resolved:** Added numpy<2.0 constraint for rawpy binary compatibility
- Fixed "numpy.dtype size changed" error

**Task 1.4: Docker Compose Configuration** ✅
- Service running successfully on port 8000
- tmpfs configured for /tmp
- Uvicorn started and listening

#### 🔄 Section 2: Core Conversion Logic (NOT STARTED)
- Task 2.1: Implement converter.py - HEIC Conversion
- Task 2.2: Implement converter.py - DNG Conversion

#### 🔄 Section 3: API Implementation (NOT STARTED)
- Task 3.1: Implement FastAPI Application

#### 🔄 Section 4: Testing & Validation (NOT STARTED)
- Task 4.1: Acquire Test Images
- Task 4.2: Create Manual Test Script
- Task 4.3: Validate Metadata Preservation
- Task 4.4: Validate Image Quality

#### 🔄 Section 5: Documentation (NOT STARTED)
- Task 5.1: Create Project README.md
- Task 5.2: Create .env.example
- Task 5.3: Document Known Issues

### Key Issues Resolved

**ExifTool Version Compatibility**
- Original plan specified exiftool=12.76+dfsg-1
- This version not available in Debian Bookworm repositories
- Solution: Use latest available exiftool from repos (12.57+dfsg-1)
- Security note: Still addresses CVE-2021-22204 (patched in 12.24+)

**NumPy Binary Compatibility**
- rawpy 0.19.0 compiled against numpy 1.x
- Default pip install pulled numpy 2.3.4
- Binary incompatibility caused import failures
- Solution: Added numpy<2.0 constraint to requirements.txt
- Result: numpy 1.26.4 installed successfully

### Next Steps
1. Begin Section 2: Core Conversion Logic
2. Start with Task 2.1: HEIC conversion implementation
3. Proceed to Task 2.2: DNG conversion implementation

---

**End of Phase 1 Plan**

Last Updated: 2025-11-06
