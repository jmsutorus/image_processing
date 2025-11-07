# Image Processing Service - Task Checklist

**Last Updated: 2025-11-06**

---

## Quick Reference

**Project:** Image Processing Service (HEIC/DNG → JPEG)
**Phase:** Phase 1 - Simple Synchronous MVP
**Status:** In Progress - Section 1 Complete (Docker Infrastructure)
**Estimated Time:** 1-2 weeks (40-80 hours)

---

## Task Progress Overview

### Phase 1: Simple Synchronous Service
- [x] Section 1: Project Structure & Docker Infrastructure (4 tasks) ✅ COMPLETE
- [ ] Section 2: Core Conversion Logic (2 tasks)
- [ ] Section 3: API Implementation (1 task)
- [ ] Section 4: Testing & Validation (4 tasks)
- [ ] Section 5: Documentation (3 tasks)

**Total Tasks:** 14 tasks across 5 sections
**Completed:** 4 tasks (29%)

---

## SECTION 1: Project Structure & Docker Infrastructure

### ✅ Task 1.1: Create Backend Directory Structure
**Priority:** P0 (Blocker) | **Effort:** S (Small) | **Est. Time:** 15 mins
**Status:** COMPLETE (2025-11-06)

**Checklist:**
- [x] Create `backend/` directory in project root
- [x] Create `backend/test_images/` subdirectory
- [x] Verify structure with `tree backend/` or `ls -R backend/`

**Commands:**
```bash
mkdir -p backend/test_images
```

**Completion Criteria:** Directories exist and are empty
**Notes:** Backend directory structure already existed in repository

---

### ✅ Task 1.2: Create Dockerfile with System Dependencies
**Priority:** P0 (Blocker) | **Effort:** M (Medium) | **Est. Time:** 2-3 hours
**Status:** COMPLETE (2025-11-06)

**Checklist:**
- [x] Create `backend/Dockerfile`
- [x] Base image: `python:3.11-slim-bookworm`
- [x] Install libheif-dev, libraw-dev, libjpeg-turbo-progs, libmagic1
- [x] Install exiftool (unpinned version - 12.76+dfsg-1 not available in Bookworm)
- [x] Create non-root user `appuser` (UID 1000)
- [x] Create /tmp directories with correct permissions
- [x] Add WORKDIR /app
- [x] Add health check: `python -c "import rawpy; import pillow_heif; from PIL import Image"`
- [x] Set USER appuser
- [x] EXPOSE 8000
- [x] CMD with uvicorn

**Validation:**
- [x] `docker build -t image-processor:phase1 ./backend` succeeds
- [x] Image size < 1GB
- [x] `docker run --rm image-processor:phase1 python -c "import rawpy; print('OK')"` succeeds

**Completion Criteria:** Docker image builds successfully and health check passes

**Issues Resolved:**
- Removed specific exiftool version pin (12.76+dfsg-1) as it was not available in Debian Bookworm repos
- Used latest available exiftool version from repos instead
- Build succeeded without the version pin

---

### ✅ Task 1.3: Create requirements.txt
**Priority:** P0 (Blocker) | **Effort:** S (Small) | **Est. Time:** 15 mins
**Status:** COMPLETE (2025-11-06)

**Checklist:**
- [x] Create `backend/requirements.txt`
- [x] Add fastapi==0.109.0
- [x] Add uvicorn[standard]==0.27.0
- [x] Add pillow==10.2.0
- [x] Add pillow-heif==0.15.0
- [x] Add rawpy==0.19.0
- [x] Add numpy<2.0 (for rawpy compatibility)
- [x] Add python-multipart==0.0.6
- [x] Add python-magic==0.4.27
- [x] NO celery, redis, or boto3 (Phase 2+)

**Validation:**
- [x] `pip install -r requirements.txt` succeeds (in Docker or venv)
- [x] `python -c "import fastapi, pillow_heif, rawpy"` succeeds

**Completion Criteria:** All packages install without errors

**Issues Resolved:**
- Added numpy<2.0 constraint to requirements.txt
- rawpy 0.19.0 requires numpy 1.x for binary compatibility
- Initial build failed with "numpy.dtype size changed" error when using numpy 2.3.4
- Fix: Added explicit constraint to install numpy 1.26.4 instead

---

### ✅ Task 1.4: Create docker-compose.yml
**Priority:** P0 (Blocker) | **Effort:** S (Small) | **Est. Time:** 30 mins
**Status:** COMPLETE (2025-11-06)

**Checklist:**
- [x] Create `docker-compose.yml` in project root
- [x] Version: 3.8
- [x] Single service: `app`
- [x] Build context: `./backend`
- [x] Port mapping: `8000:8000`
- [x] Environment: PYTHONUNBUFFERED=1
- [x] tmpfs mount for /tmp (size: 1G)
- [x] Restart policy: unless-stopped

**Validation:**
- [x] `docker-compose up -d` starts successfully
- [x] Service is running on port 8000
- [x] `docker-compose logs -f app` shows uvicorn starting
- [x] `docker-compose down` stops cleanly

**Completion Criteria:** Container starts and is accessible on port 8000

**Verification:**
- Container status: Up and running
- Uvicorn started successfully
- Server listening on http://0.0.0.0:8000
- All dependencies loaded successfully

---

## SECTION 2: Core Conversion Logic

### ☐ Task 2.1: Implement converter.py - HEIC Conversion
**Priority:** P0 (Blocker) | **Effort:** M (Medium) | **Est. Time:** 4-6 hours

**Checklist:**
- [ ] Create `backend/converter.py`
- [ ] Import: pillow_heif, Pillow, tempfile, pathlib
- [ ] Call `pillow_heif.register_heif_opener()` at module level
- [ ] Define `ConversionError` exception class
- [ ] Implement `convert_image(bytes, filename) -> bytes` function
- [ ] Implement `_convert_heic(input_path, output_path)` function
- [ ] Use TemporaryDirectory for file management
- [ ] Extract EXIF: `exif_data = image.info.get('exif')`
- [ ] Save with: quality=95, subsampling=0, exif=exif_data
- [ ] Add try/except with ConversionError
- [ ] Add docstrings to all functions

**Validation:**
- [ ] Syntax check: `python -m py_compile backend/converter.py`
- [ ] Import test: `python -c "from converter import convert_image"`
- [ ] Unit test with sample HEIC (manual)

**Completion Criteria:** HEIC conversion works with metadata preserved

---

### ☐ Task 2.2: Implement converter.py - DNG Conversion
**Priority:** P0 (Blocker) | **Effort:** L (Large) | **Est. Time:** 6-8 hours

**Checklist:**
- [ ] Import: rawpy, subprocess
- [ ] Implement `_convert_dng(input_path, output_path)` function
- [ ] Use rawpy.imread() with context manager
- [ ] Post-process with:
  - [ ] use_camera_wb=True
  - [ ] output_color=rawpy.ColorSpace.sRGB
  - [ ] no_auto_bright=True
  - [ ] bright=1.0
- [ ] Convert numpy array to PIL Image with Image.fromarray()
- [ ] Save as JPEG (quality=95, subsampling=0)
- [ ] Call exiftool subprocess with:
  - [ ] List format (not string): `['exiftool', ...]`
  - [ ] shell=False (CRITICAL)
  - [ ] check=True
  - [ ] capture_output=True
  - [ ] timeout=30
- [ ] Handle subprocess.CalledProcessError
- [ ] Add comprehensive error handling
- [ ] Clean up temporary DNG file

**Security Validation:**
- [ ] Verify shell=False in all subprocess.run() calls
- [ ] Verify no string formatting in subprocess commands
- [ ] Test with filename containing special characters

**Completion Criteria:** DNG conversion works with correct brightness and metadata

---

## SECTION 3: API Implementation

### ☐ Task 3.1: Implement FastAPI Application (app.py)
**Priority:** P0 (Blocker) | **Effort:** M (Medium) | **Est. Time:** 4-6 hours

**Checklist:**
- [ ] Create `backend/app.py`
- [ ] Import: FastAPI, UploadFile, File, HTTPException, StreamingResponse, magic
- [ ] Import: convert_image, ConversionError from converter
- [ ] Initialize app: `app = FastAPI(title="Image Conversion Service")`
- [ ] Define constants:
  - [ ] MAX_UPLOAD_SIZE = 200 * 1024 * 1024
  - [ ] ALLOWED_EXTENSIONS = {'.heic', '.heif', '.dng'}
- [ ] Implement `validate_file(contents, filename)` function:
  - [ ] Check file size
  - [ ] Check extension
  - [ ] Check MIME type with python-magic
  - [ ] Raise HTTPException for failures
- [ ] Implement `@app.post("/convert")` endpoint:
  - [ ] Accept UploadFile parameter
  - [ ] Read file contents
  - [ ] Validate file
  - [ ] Call convert_image()
  - [ ] Return StreamingResponse with:
    - [ ] media_type="image/jpeg"
    - [ ] Content-Disposition header
- [ ] Implement `@app.get("/health")` endpoint
- [ ] Add error handling for all exception types

**Validation:**
- [ ] Syntax check: `python -m py_compile backend/app.py`
- [ ] Import test: `python -c "from app import app"`
- [ ] Docker rebuild and start
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8000/docs` shows OpenAPI docs

**Completion Criteria:** All endpoints respond correctly

---

## SECTION 4: Testing & Validation

### ☐ Task 4.1: Acquire Test Images
**Priority:** P0 (Blocker) | **Effort:** S (Small) | **Est. Time:** 1-2 hours

**Checklist:**
- [x] Obtain sample.heic (iPhone photo with GPS EXIF)
- [x] Obtain sample.dng (camera RAW with full metadata)
- [x] Save both to `backend/test_images/`
- [ ] Extract baseline metadata:
  - [ ] `exiftool -json sample.heic > sample_heic_metadata.json`
  - [ ] `exiftool -json sample.dng > sample_dng_metadata.json`
- [ ] Document file sizes and sources
- [ ] Create `backend/test_images/README.md` with:
  - [ ] Source of each file
  - [ ] File sizes
  - [ ] Expected metadata fields

**Sources:**
- HEIC: iPhone photo or https://github.com/nokiatech/heif
- DNG: Camera or https://www.adobe.com/support/downloads/dng/dng_sdk.html

**Completion Criteria:** Both sample files available with documented metadata

---

### ☐ Task 4.2: Create Manual Test Script
**Priority:** P1 (High) | **Effort:** S (Small) | **Est. Time:** 1-2 hours

**Checklist:**
- [ ] Create `backend/test_conversion.sh`
- [ ] Add shebang: `#!/bin/bash`
- [ ] Add `set -e` for fail-fast
- [ ] Start docker-compose if not running
- [ ] Test HEIC conversion with curl
- [ ] Save output to result_heic.jpg
- [ ] Extract metadata from result
- [ ] Test DNG conversion with curl
- [ ] Save output to result_dng.jpg
- [ ] Extract metadata from result
- [ ] Print success message with manual verification steps
- [ ] Make executable: `chmod +x test_conversion.sh`

**Validation:**
- [ ] Script runs without errors
- [ ] Both JPEG outputs created
- [ ] Metadata JSON files created

**Completion Criteria:** Script successfully converts both test images

---

### ☐ Task 4.3: Validate Metadata Preservation
**Priority:** P0 (Blocker) | **Effort:** M (Medium) | **Est. Time:** 2-3 hours

**Checklist:**
- [ ] Run test script from Task 4.2
- [ ] Compare HEIC metadata:
  - [ ] GPS coordinates preserved
  - [ ] Make/Model preserved
  - [ ] DateTimeOriginal preserved
- [ ] Compare DNG metadata:
  - [ ] Camera settings preserved (ISO, FNumber, ExposureTime)
  - [ ] ColorSpace is sRGB in output
  - [ ] No corruption (garbled text, wrong dates)
- [ ] Document any metadata losses in KNOWN_ISSUES.md
- [ ] Take screenshots of key metadata fields

**Critical Fields to Verify:**
- Make, Model
- DateTimeOriginal
- GPSLatitude, GPSLongitude (HEIC)
- ISO, FNumber, ExposureTime (DNG)
- ColorSpace (should be sRGB)

**Completion Criteria:** All critical metadata fields preserved correctly

---

### ☐ Task 4.4: Validate Image Quality
**Priority:** P0 (Blocker) | **Effort:** S (Small) | **Est. Time:** 1-2 hours

**Checklist:**
- [ ] Open result_heic.jpg in image viewer
- [ ] Open result_dng.jpg in image viewer
- [ ] Visual inspection at 100% zoom:
  - [ ] No visible compression artifacts
  - [ ] Colors appear accurate
  - [ ] DNG brightness looks correct (not too dark/light)
  - [ ] No black images or corrupt output
- [ ] Check file sizes (should be 2-5MB typically)
- [ ] Document observations in KNOWN_ISSUES.md
- [ ] Take screenshots if issues found

**Known Issues to Watch:**
- DNG too dark → Check use_camera_wb=True
- Color shift → Verify output_color=sRGB
- Artifacts → Check subsampling=0
- Huge files → Check quality=95 (not 100)

**Completion Criteria:** Image quality meets professional standards

---

## SECTION 5: Documentation

### ☐ Task 5.1: Create Project README.md
**Priority:** P1 (High) | **Effort:** M (Medium) | **Est. Time:** 2-3 hours

**Checklist:**
- [ ] Create/update `README.md` in project root
- [ ] Add sections:
  - [ ] Project Description
  - [ ] Features (HEIC/DNG support, metadata preservation)
  - [ ] Technology Stack
  - [ ] Getting Started
    - [ ] Prerequisites
    - [ ] Installation steps
    - [ ] Running with docker-compose
  - [ ] API Documentation
    - [ ] POST /convert (with curl examples)
    - [ ] GET /health
  - [ ] Testing instructions
  - [ ] Known Limitations (Phase 1)
  - [ ] Future Roadmap (Phases 2-4)
  - [ ] License
- [ ] Add code examples for API usage
- [ ] Add screenshots (optional)

**Completion Criteria:** README provides complete usage instructions

---

### ☐ Task 5.2: Create .env.example
**Priority:** P2 (Medium) | **Effort:** S (Small) | **Est. Time:** 15 mins

**Checklist:**
- [ ] Create `.env.example` in project root
- [ ] Document Phase 1 variables:
  - [ ] PYTHONUNBUFFERED=1
  - [ ] MAX_UPLOAD_SIZE_MB=200
- [ ] Add commented Phase 2+ variables:
  - [ ] CELERY_BROKER_URL (commented)
  - [ ] CELERY_RESULT_BACKEND (commented)
- [ ] Add commented Phase 3+ variables:
  - [ ] AWS_REGION (commented)
  - [ ] AWS_S3_BUCKET (commented)
  - [ ] AWS credentials (commented)
- [ ] Add comments explaining each variable

**Completion Criteria:** Environment variables documented for all phases

---

### ☐ Task 5.3: Document Known Issues & Workarounds
**Priority:** P2 (Medium) | **Effort:** S (Small) | **Est. Time:** 1-2 hours

**Checklist:**
- [ ] Create `backend/KNOWN_ISSUES.md`
- [ ] Document Phase 1 Limitations:
  - [ ] Synchronous processing (may timeout)
  - [ ] No result persistence
  - [ ] No authentication
  - [ ] Single-threaded per container
- [ ] Document known metadata losses (if any from testing)
- [ ] Document performance benchmarks:
  - [ ] HEIC (10MB): __ seconds
  - [ ] HEIC (50MB): __ seconds
  - [ ] DNG (20MB): __ seconds
  - [ ] DNG (100MB): __ seconds
- [ ] Provide workarounds where possible
- [ ] Reference future fixes (Phases 2-4)

**Completion Criteria:** All limitations and workarounds documented

---

## Phase 1 Completion Checklist

### Pre-Deployment Verification
- [ ] All 14 tasks completed
- [ ] Docker image builds successfully
- [ ] docker-compose starts cleanly
- [ ] Health check endpoint responds
- [ ] HEIC conversion works with metadata
- [ ] DNG conversion works with metadata
- [ ] Image quality meets standards
- [ ] Security requirements met (non-root user, no shell=True)
- [ ] Documentation complete (README, KNOWN_ISSUES)
- [ ] Test script runs successfully

### Quality Gates
- [ ] Metadata preservation rate: 100% for critical fields
- [ ] Image quality: No visible artifacts at 100% zoom
- [ ] Conversion speed: <5s for HEIC, <20s for DNG (100MB)
- [ ] Security: No CVEs, no shell injection vulnerabilities
- [ ] Docker image size: < 1GB

### Final Sign-Off
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Known issues documented
- [ ] Performance benchmarks recorded
- [ ] Ready for Phase 2 planning

---

## Quick Commands Reference

### Build and Run
```bash
# Build Docker image
cd backend && docker build -t image-processor:phase1 .

# Start service
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop service
docker-compose down
```

### Testing
```bash
# Run manual tests
cd backend && ./test_conversion.sh

# Convert HEIC
curl -X POST "http://localhost:8000/convert" \
  -F "file=@test_images/sample.heic" \
  --output result.jpg

# Check metadata
exiftool result.jpg
```

### Debugging
```bash
# Shell into container
docker-compose exec app bash

# Check Python imports
docker-compose exec app python -c "import rawpy, pillow_heif"

# Check exiftool version
docker-compose exec app exiftool -ver
```

---

## Progress Tracking

**Started:** 2025-11-06
**Last Updated:** 2025-11-06
**Completed:** [In Progress]

**Current Status:** In Progress - Section 1 Complete (29% of Phase 1)
**Blocked By:** None
**Next Task:** Task 2.1 - Implement converter.py (HEIC Conversion)

**Completed Tasks:**
- ✅ Task 1.1 - Backend directory structure
- ✅ Task 1.2 - Dockerfile with system dependencies
- ✅ Task 1.3 - requirements.txt with Python dependencies
- ✅ Task 1.4 - docker-compose.yml service definition

---

**End of Task Checklist**

Last Updated: 2025-11-06
