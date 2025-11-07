# Image Processing Service - Context Document

**Last Updated: 2025-11-06**

---

## Project Overview

**Project Name:** Image Processing Service
**Type:** Python Web Service
**Purpose:** Convert HEIC and DNG image formats to JPEG with metadata preservation
**Phase:** Phase 1 - Simple Synchronous MVP
**Status:** In Progress - Docker Infrastructure Complete

---

## Key Technical Context

### Core Challenge
This project addresses two fundamentally different conversion challenges:

1. **HEIC → JPEG:** Format decoding with metadata preservation
   - HEIC is a container format using HEVC compression
   - Already "developed" (processed) images
   - Challenge: Preserve EXIF/XMP metadata during re-encoding

2. **DNG → JPEG:** Raw image development + metadata transfer
   - DNG contains raw sensor data (not viewable image)
   - Requires "developing" with white balance, color space, demosaicing
   - Challenge: Intelligent post-processing + separate metadata copying

### Critical Success Factors

#### 1. Metadata Preservation (Non-Negotiable)
- **HEIC:** Must preserve GPS, camera settings, DateTime
- **DNG:** Must preserve camera settings, color space, capture info
- **Failure Mode:** Stripping metadata makes service unusable for professional use

#### 2. Image Quality
- **JPEG Quality:** 95% (industry standard for "best")
- **Chroma Subsampling:** Disabled (subsampling=0 for 4:4:4)
- **Color Space:** sRGB output (web-compatible)
- **DNG White Balance:** use_camera_wb=True (prevents distortion)

#### 3. Security
- **ExifTool CVE-2021-22204:** Requires version >= 12.24 (pinned to 12.76+dfsg-1)
- **Subprocess Injection:** Never use shell=True (prevents command injection)
- **Container Security:** Run as non-root user (UID 1000)

---

## Technology Stack

### Core Technologies
```yaml
Language: Python 3.11+
Web Framework: FastAPI 0.109.0
Server: Uvicorn with standard extras

Image Processing:
  - pillow: 10.2.0 (general image operations)
  - pillow-heif: 0.15.0 (HEIC decoding via libheif)
  - rawpy: 0.19.0 (DNG processing via LibRaw)

Utilities:
  - python-multipart: 0.0.6 (file upload support)
  - python-magic: 0.4.27 (MIME type validation)

System Dependencies:
  - libheif-dev (HEIC/HEIF codec)
  - libraw-dev (RAW image processing)
  - libjpeg-turbo-dev (fast JPEG encoding)
  - exiftool: 12.76+dfsg-1 (metadata manipulation)

Containerization:
  - Docker with python:3.11-slim-bookworm base
  - docker-compose 3.8
  - tmpfs for /tmp (memory-backed, auto-cleanup)
```

### Why These Choices?

**Python over Node.js/Go:**
- Best-in-class bindings for libheif and LibRaw
- Stable package management (pip wheels vs. node-gyp)
- Lower deployment risk

**FastAPI over Flask:**
- Modern async support (useful for future phases)
- Automatic OpenAPI docs
- Type hints and validation

**pillow-heif + rawpy:**
- Direct Python bindings to C libraries (libheif, LibRaw)
- Metadata preservation built-in (pillow-heif)
- Proven at scale

**Docker:**
- Consistent system dependencies across environments
- Isolates libheif/LibRaw from host system
- Easy scaling and deployment

---

## Architecture (Phase 1)

### High-Level Flow
```
User → POST /convert (file) → FastAPI
                                  ↓
                            validate_file()
                                  ↓
                            convert_image()
                                  ↓
                    ┌───────────────────────┐
                    │                       │
               .heic/.heif              .dng
                    │                       │
            _convert_heic()         _convert_dng()
                    │                       │
              pillow-heif              rawpy.postprocess()
                    │                       │
              EXIF preserved               ↓
                    │                Image.fromarray()
                    │                       ↓
                    │                exiftool (metadata)
                    │                       │
                    └───────────┬───────────┘
                                ↓
                          JPEG bytes
                                ↓
                          StreamingResponse
                                ↓
                              User
```

### Component Responsibilities

**app.py** (FastAPI Application)
- Endpoints: POST /convert, GET /health
- File validation (size, extension, MIME type)
- Error handling (400, 413, 500)
- Response streaming

**converter.py** (Core Logic)
- `convert_image()`: Main entry point
- `_convert_heic()`: HEIC → JPEG with Pillow
- `_convert_dng()`: DNG → JPEG with rawpy + exiftool
- TemporaryDirectory for cleanup

**Dockerfile**
- System dependencies installation
- Non-root user creation
- Python package installation
- Health check validation

**docker-compose.yml**
- Single service (app)
- Port mapping (8000:8000)
- tmpfs mount for /tmp

---

## Key Files and Their Purposes

### Source Files
```
backend/
├── app.py                    # FastAPI server (API endpoints)
├── converter.py              # Core conversion logic (HEIC + DNG)
├── requirements.txt          # Python dependencies (pinned versions)
├── Dockerfile                # Container image definition
└── test_images/              # Sample files for testing
    ├── sample.heic           # iPhone photo with GPS
    ├── sample.dng            # Camera RAW
    ├── sample_heic_metadata.json  # Baseline EXIF
    └── sample_dng_metadata.json   # Baseline EXIF
```

### Configuration Files
```
docker-compose.yml            # Service orchestration
.env.example                  # Environment variables template
README.md                     # User documentation
backend/KNOWN_ISSUES.md       # Limitations and workarounds
backend/test_conversion.sh    # Manual test script
```

### Documentation Files
```
dev/active/image-processing/
├── image-processing-plan.md      # This comprehensive plan
├── image-processing-context.md   # Context and decisions (this file)
└── image-processing-tasks.md     # Checklist for tracking
```

---

## Critical Implementation Details

### HEIC Conversion Parameters
```python
# Register HEIF opener ONCE at module level
pillow_heif.register_heif_opener()

# Extract EXIF before conversion
exif_data = image.info.get('exif')

# Save with metadata
image.convert('RGB').save(
    output_path,
    format="JPEG",
    quality=95,        # Industry standard for "best"
    subsampling=0,     # Disable chroma subsampling (4:4:4)
    exif=exif_data     # Preserve metadata
)
```

### DNG Conversion Parameters
```python
# Step 1: Post-process RAW data
rgb = raw.postprocess(
    use_camera_wb=True,              # Use camera white balance (CRITICAL)
    output_color=rawpy.ColorSpace.sRGB,  # Web-compatible color
    no_auto_bright=True,             # Predictable brightness
    bright=1.0                       # Linear brightness
)

# Step 2: Save as JPEG (no metadata yet)
image = Image.fromarray(rgb)
image.save(output_path, format="JPEG", quality=95, subsampling=0)

# Step 3: Copy metadata with exiftool (CRITICAL)
subprocess.run(
    ['exiftool', '-TagsFromFile', input_path, '-overwrite_original', output_path],
    shell=False,      # SECURITY: Prevents command injection
    check=True,
    capture_output=True,
    timeout=30        # Prevent hanging
)
```

### Security-Critical Subprocess Call
```python
# ❌ NEVER DO THIS (vulnerable to command injection)
subprocess.run(f'exiftool -TagsFromFile "{input_path}" "{output_path}"', shell=True)

# ✅ ALWAYS DO THIS (safe)
subprocess.run(
    ['exiftool', '-TagsFromFile', input_path, '-overwrite_original', output_path],
    shell=False,  # No shell = no injection
    check=True,
    capture_output=True,
    timeout=30
)
```

---

## Dependencies and Constraints

### System Requirements
- **Docker:** 24.0+ with docker-compose
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 2GB for Docker images + test files
- **OS:** Linux or macOS (Windows requires WSL2)

### External Dependencies
- **libheif:** Version 1.17.0+ (for HEIC/HEIF support)
- **LibRaw:** Latest from Debian repos
- **exiftool:** 12.76+dfsg-1 (CVE-2021-22204 patched)
- **libjpeg-turbo:** For fast JPEG encoding

### File Size Constraints
- **Max Upload:** 200MB (configurable)
- **Typical HEIC:** 2-10MB (iPhone photo)
- **Typical DNG:** 20-100MB (camera RAW)
- **tmpfs Limit:** 1GB (prevents disk exhaustion)

---

## Known Limitations (Phase 1)

### Architectural Limitations
1. **Synchronous Processing**
   - Large files may timeout (>60s processing)
   - Blocks other requests during conversion
   - Mitigation: Run multiple workers, limit file size

2. **No Result Persistence**
   - One-time download only
   - User must save immediately
   - Mitigation: Document clearly, fix in Phase 3 with S3

3. **No Authentication**
   - Anyone with network access can use service
   - Mitigation: Restrict to internal network, add auth in Phase 4

4. **Single Worker (per container)**
   - One conversion at a time
   - Mitigation: Scale containers with docker-compose scale

### Performance Expectations
- **HEIC (10MB):** ~2-3 seconds
- **HEIC (50MB):** ~5-8 seconds
- **DNG (20MB):** ~8-10 seconds
- **DNG (100MB):** ~15-20 seconds

*(Actual benchmarks to be measured during testing)*

---

## Decision Log

### Decision 1: Python over Node.js
**Date:** Based on PRD research
**Rationale:**
- pillow-heif and rawpy are most mature bindings
- pip wheels avoid node-gyp compilation issues
- Metadata preservation proven in Python ecosystem

**Alternatives Considered:**
- Node.js with sharp + node-libraw (rejected: brittle builds)
- Go with cgo bindings (rejected: immature ecosystem)

---

### Decision 2: Synchronous First, Async Later
**Date:** Plan review feedback
**Rationale:**
- Simpler to implement and debug
- Proves conversion quality first
- Easy migration path to Celery

**Alternatives Considered:**
- Start with Celery + Redis (rejected: premature complexity)

---

### Decision 3: FastAPI over Flask
**Date:** During planning
**Rationale:**
- Modern async support (useful for Phase 2+)
- Automatic OpenAPI docs
- Better type hints and validation

**Alternatives Considered:**
- Flask (rejected: older, less modern features)

---

### Decision 4: tmpfs for /tmp
**Date:** During planning
**Rationale:**
- Prevents disk exhaustion
- Faster than disk I/O
- Auto-clears on container restart

**Alternatives Considered:**
- Regular disk storage (rejected: requires manual cleanup)

---

### Decision 5: ExifTool for DNG Metadata
**Date:** Based on PRD research
**Rationale:**
- rawpy only returns pixel data, not metadata
- exiftool is industry standard for EXIF manipulation
- subprocess approach is proven

**Alternatives Considered:**
- Python EXIF libraries (rejected: incomplete DNG support)

---

## Testing Strategy

### Manual Testing (Phase 1)
1. Acquire representative test images (iPhone HEIC, camera DNG)
2. Run curl commands against /convert endpoint
3. Extract and compare metadata with exiftool
4. Visual inspection of output quality
5. Document observations

### Validation Criteria
- ✅ JPEG output is valid and openable
- ✅ GPS coordinates preserved (HEIC)
- ✅ Camera make/model preserved (both)
- ✅ DateTime preserved (both)
- ✅ Camera settings preserved (DNG)
- ✅ No visible compression artifacts
- ✅ Colors appear accurate
- ✅ DNG brightness looks correct

### Automated Testing (Phase 3+)
- Unit tests for converter.py functions
- Integration tests for API endpoints
- Visual regression tests (pixel comparison)
- Metadata validation tests (JSON comparison)
- Performance benchmarks

---

## Migration Path to Future Phases

### Phase 1 → Phase 2 (Async Processing)
**Goal:** Add Celery + Redis for background jobs

**Changes:**
- Add celery[redis] to requirements.txt
- Move converter.py functions to Celery tasks
- Add Redis service to docker-compose
- Change /convert to return task_id
- Add /status/<task_id> polling endpoint

**Unchanged:**
- Core conversion logic (100% reusable)
- Dockerfile dependencies
- Image quality parameters

---

### Phase 2 → Phase 3 (S3 Storage)
**Goal:** Add AWS S3 for scalable storage

**Changes:**
- Add boto3 to requirements.txt
- Configure S3 bucket with CORS
- Add /generate-presigned-url endpoint
- Modify Celery tasks to use S3

**Unchanged:**
- Conversion logic
- Metadata preservation approach
- API contracts

---

### Phase 3 → Phase 4 (Production)
**Goal:** Full production with frontend and monitoring

**Changes:**
- Build React frontend
- Add heic2any for client previews
- Implement authentication (JWT)
- Add CI/CD pipeline
- Add monitoring (Prometheus + Grafana)

**Unchanged:**
- Backend conversion logic
- Docker infrastructure
- Quality standards

---

## Reference Materials

### Primary Documentation
- **PRD Research:** `context/prd_research.md` (comprehensive technology analysis)
- **Implementation Plan:** `dev/active/image-processing/image-processing-plan.md`
- **Task Checklist:** `dev/active/image-processing/image-processing-tasks.md`

### External Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pillow-HEIF Docs](https://pillow-heif.readthedocs.io/)
- [rawpy Docs](https://letmaik.github.io/rawpy/)
- [ExifTool Docs](https://exiftool.org/)
- [LibRaw API](https://www.libraw.org/docs/API-overview.html)

### Key Research Findings from PRD
- Section IV: Metadata preservation is critical (deal-breaker if missing)
- Section IX: Exact conversion code examples provided
- Section X: Security considerations (ExifTool CVE, subprocess injection)
- Section XII: Testing strategy (visual regression, metadata validation)

---

## Troubleshooting Quick Reference

### Issue: Docker build fails
**Check:** libheif-dev available in Debian repos
**Solution:** Add backports or compile from source

### Issue: HEIC metadata lost
**Check:** pillow-heif.register_heif_opener() called
**Check:** exif_data passed to save()

### Issue: DNG too dark
**Check:** use_camera_wb=True set
**Check:** no_auto_bright=True set

### Issue: Subprocess timeout
**Check:** File is valid DNG
**Check:** Timeout set to 30+ seconds
**Check:** exiftool version correct

### Issue: Command injection vulnerability
**Check:** shell=False used in all subprocess.run()
**Check:** No string formatting in subprocess commands

---

## Implementation Status (2025-11-06)

### Completed Work

#### Section 1: Docker Infrastructure (COMPLETE)
All Docker infrastructure tasks completed successfully:

1. **Backend Directory Structure** (backend/)
   - Directory already existed in repository
   - Structure verified and ready for code

2. **Dockerfile** (backend/Dockerfile)
   - Base image: python:3.11-slim-bookworm
   - System dependencies installed: libheif-dev, libraw-dev, libjpeg-turbo-progs, libmagic1, exiftool
   - Non-root user (appuser, UID 1000) created
   - Health check validates all Python libraries load correctly
   - **Issue Fixed:** Removed exiftool version pin (12.76+dfsg-1 not available in Bookworm)

3. **Python Dependencies** (backend/requirements.txt)
   - All packages specified with versions
   - **Issue Fixed:** Added numpy<2.0 constraint for rawpy 0.19.0 compatibility
   - Resolved binary incompatibility error between numpy 2.x and rawpy

4. **Docker Compose** (docker-compose.yml)
   - Service configuration complete
   - Port 8000 mapped correctly
   - tmpfs mount for /tmp (1GB limit)
   - Service successfully running and accessible

### Build Issues Resolved

#### Issue 1: ExifTool Version Unavailable
**Problem:** Dockerfile specified `exiftool=12.76+dfsg-1` but this specific version is not available in Debian Bookworm repositories.

**Error:** `apt-get install` failed with exit code 100

**Solution:** Removed version pin, using latest available exiftool from Debian repos
- File: backend/Dockerfile:9
- Change: `exiftool=12.76+dfsg-1` → `exiftool`

#### Issue 2: NumPy Binary Incompatibility
**Problem:** rawpy 0.19.0 was compiled against numpy 1.x, but pip installed numpy 2.3.4 by default, causing binary incompatibility.

**Error:** `ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject`

**Solution:** Added explicit numpy version constraint to requirements.txt
- File: backend/requirements.txt:9
- Added: `numpy<2.0  # rawpy 0.19.0 requires numpy 1.x for binary compatibility`
- Result: numpy 1.26.4 installed successfully

### Current State
- Docker image builds successfully
- Container runs without errors
- All system and Python dependencies installed correctly
- Service accessible on http://localhost:8000
- Ready to begin Section 2: Core Conversion Logic implementation

### Next Steps
- Task 2.1: Implement converter.py - HEIC Conversion
- Task 2.2: Implement converter.py - DNG Conversion

---

**End of Context Document**

Last Updated: 2025-11-06
