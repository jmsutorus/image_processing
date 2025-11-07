# Image Processing Service - Project Knowledge

**Last Updated: 2025-01-05**

---

## Project Overview

**Name:** Image Processing Service
**Purpose:** Convert HEIC and DNG image formats to JPEG with full metadata preservation
**Current Phase:** Phase 1 - Simple Synchronous MVP (Planning Complete, Implementation Pending)

---

## Quick Start

### For Developers Starting Fresh

1. **Read the PRD Research**
   - Location: `context/prd_research.md`
   - This is the comprehensive architectural blueprint based on research
   - Contains all technology decisions and rationale

2. **Review the Implementation Plan**
   - Location: `dev/active/image-processing/image-processing-plan.md`
   - Comprehensive implementation guide with all phases
   - Includes security considerations, testing strategy, and migration paths

3. **Check the Context Document**
   - Location: `dev/active/image-processing/image-processing-context.md`
   - Key technical decisions and their rationale
   - Technology stack details
   - Critical implementation snippets

4. **Start with the Task Checklist**
   - Location: `dev/active/image-processing/image-processing-tasks.md`
   - 14 tasks organized in 5 sections
   - Clear acceptance criteria for each task
   - Progress tracking checkboxes

---

## Project Architecture (Phase 1)

### High-Level Overview
```
User → FastAPI (POST /convert) → Validate → Convert → Return JPEG
                                              ↓
                                      ┌───────┴────────┐
                                   HEIC              DNG
                                      ↓                ↓
                              pillow-heif        rawpy + exiftool
                                      ↓                ↓
                                      └────────┬───────┘
                                               ↓
                                          JPEG (metadata preserved)
```

### Technology Stack

**Core:**
- Python 3.11+
- FastAPI 0.109.0
- Docker with docker-compose

**Image Processing:**
- pillow-heif (HEIC decoding)
- rawpy (DNG processing)
- Pillow (image operations)
- exiftool (metadata copying for DNG)

**System Dependencies:**
- libheif-dev (HEIC/HEIF codec)
- libraw-dev (RAW processing)
- libjpeg-turbo-dev (fast JPEG)
- exiftool 12.76+ (CVE patched)

---

## Key Technical Challenges & Solutions

### Challenge 1: HEIC vs DNG Are Fundamentally Different
**Problem:** Cannot use single "converter" - HEIC is compressed image, DNG is raw sensor data

**Solution:**
- Separate pipelines: `_convert_heic()` and `_convert_dng()`
- HEIC: Simple decode + re-encode with pillow-heif
- DNG: Complex "development" with rawpy (white balance, color space, demosaicing)

---

### Challenge 2: Metadata Preservation Is Critical
**Problem:** Client-side solutions strip all metadata (deal-breaker for professional use)

**Solution:**
- HEIC: Pillow's `exif` parameter preserves EXIF directly
- DNG: exiftool subprocess copies metadata after conversion
- Server-side processing mandatory for both formats

---

### Challenge 3: DNG Images Come Out Too Dark/Distorted
**Problem:** Default rawpy settings produce poor results

**Solution:**
```python
rgb = raw.postprocess(
    use_camera_wb=True,       # CRITICAL: Use camera white balance
    output_color=rawpy.ColorSpace.sRGB,  # Web-compatible
    no_auto_bright=True,      # Predictable brightness
    bright=1.0                # Linear
)
```

---

### Challenge 4: Security Vulnerabilities
**Problem 1:** ExifTool CVE-2021-22204 (RCE via malicious DNG)
**Solution:** Pin exiftool to version 12.76+dfsg-1 in Dockerfile

**Problem 2:** Subprocess command injection
**Solution:** Always use `shell=False` and list format:
```python
# ✅ SAFE
subprocess.run(['exiftool', '-TagsFromFile', input_path, output_path], shell=False)

# ❌ VULNERABLE
subprocess.run(f'exiftool -TagsFromFile "{input_path}" "{output_path}"', shell=True)
```

---

## Critical Code Snippets

### HEIC Conversion (Minimal Example)
```python
import pillow_heif
from PIL import Image

pillow_heif.register_heif_opener()

with Image.open('input.heic') as image:
    exif_data = image.info.get('exif')
    image.convert('RGB').save(
        'output.jpg',
        format="JPEG",
        quality=95,
        subsampling=0,
        exif=exif_data
    )
```

### DNG Conversion (Minimal Example)
```python
import rawpy
from PIL import Image
import subprocess

with rawpy.imread('input.dng') as raw:
    rgb = raw.postprocess(
        use_camera_wb=True,
        output_color=rawpy.ColorSpace.sRGB,
        no_auto_bright=True,
        bright=1.0
    )

image = Image.fromarray(rgb)
image.save('output.jpg', format="JPEG", quality=95, subsampling=0)

# Copy metadata (CRITICAL - rawpy doesn't transfer it)
subprocess.run(
    ['exiftool', '-TagsFromFile', 'input.dng', '-overwrite_original', 'output.jpg'],
    shell=False,
    check=True,
    timeout=30
)
```

---

## Phase 1 Scope (MVP)

### What's Included
- ✅ Single Docker container with all dependencies
- ✅ Synchronous POST /convert endpoint
- ✅ HEIC → JPEG with EXIF preservation
- ✅ DNG → JPEG with rawpy + exiftool
- ✅ High-quality output (95% quality, no chroma subsampling)
- ✅ Local tmpfs storage (memory-backed /tmp)
- ✅ Basic validation (file size, extension, MIME type)
- ✅ Manual testing suite

### What's NOT Included (Future Phases)
- ❌ Async processing (Celery + Redis)
- ❌ Cloud storage (AWS S3)
- ❌ Result persistence (one-time download only)
- ❌ Authentication
- ❌ React frontend
- ❌ Automated tests (unit, integration)
- ❌ CI/CD pipeline

---

## Known Limitations (Phase 1)

1. **Synchronous Processing**
   - Large files may timeout (>60s)
   - Blocks other requests during conversion
   - Mitigation: Limit file size to 200MB, run multiple workers

2. **No Result Persistence**
   - Must download immediately or lose file
   - No download history or replay
   - Fix in Phase 3 with S3 storage

3. **No Authentication**
   - Anyone with network access can use service
   - Mitigation: Restrict to internal network
   - Fix in Phase 4 with API keys/JWT

4. **Performance**
   - Single worker per container
   - HEIC: ~2-5 seconds
   - DNG: ~8-20 seconds (depends on file size)

---

## Decision Log

### Why Python?
- Best bindings for libheif (pillow-heif) and LibRaw (rawpy)
- Stable package management (pip wheels vs node-gyp)
- Metadata preservation proven in ecosystem

### Why Synchronous First?
- Simpler to implement and debug
- Proves conversion quality before adding complexity
- Easy migration to Celery later (core logic unchanged)

### Why FastAPI?
- Modern async support (useful for Phase 2+)
- Automatic OpenAPI docs
- Better type hints than Flask

### Why Docker?
- Consistent system dependencies (libheif, LibRaw)
- Isolated from host system
- Easy scaling with docker-compose

### Why ExifTool for DNG?
- rawpy only returns pixel data, not metadata
- exiftool is industry standard for EXIF manipulation
- subprocess approach is proven

---

## Testing Strategy

### Phase 1 (Manual Testing)
1. Acquire sample HEIC (iPhone photo with GPS)
2. Acquire sample DNG (camera RAW)
3. Extract baseline metadata with exiftool
4. Run conversions via curl
5. Compare output metadata to baseline
6. Visual inspection of image quality
7. Document findings in KNOWN_ISSUES.md

### Phase 3+ (Automated Testing)
- Unit tests for converter functions
- Integration tests for API endpoints
- Visual regression tests (pixel comparison)
- Metadata validation (JSON comparison)
- Performance benchmarks

---

## Migration Path to Future Phases

### Phase 1 → Phase 2: Add Async Processing
- Add Celery + Redis
- Move converter.py functions to Celery tasks
- Change /convert to return task_id
- Add /status/<task_id> polling
- **Core logic unchanged** (100% reusable)

### Phase 2 → Phase 3: Add S3 Storage
- Add boto3 and AWS credentials
- Configure S3 bucket with CORS
- Add /generate-presigned-url endpoint
- Modify Celery tasks to use S3
- **Conversion logic unchanged**

### Phase 3 → Phase 4: Production Ready
- Build React frontend
- Add heic2any for client previews
- Implement authentication (JWT)
- Add CI/CD pipeline
- Add monitoring (Prometheus + Grafana)
- Visual regression tests

---

## File Organization

```
image_processing/
├── context/
│   └── prd_research.md           # Comprehensive PRD (58KB)
├── dev/
│   └── active/
│       └── image-processing/
│           ├── image-processing-plan.md     # Implementation plan
│           ├── image-processing-context.md  # Technical context
│           └── image-processing-tasks.md    # Task checklist (14 tasks)
├── backend/                       # (To be created in Task 1.1)
│   ├── app.py                    # FastAPI server
│   ├── converter.py              # Core conversion logic
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Container definition
│   └── test_images/              # Sample HEIC/DNG files
├── docker-compose.yml            # Service orchestration
├── README.md                     # User documentation
├── PROJECT_KNOWLEDGE.md          # This file
└── .gitignore                    # Python + Docker ignores
```

---

## Quick Commands

### Start Development
```bash
# 1. Create backend structure
mkdir -p backend/test_images

# 2. Create Dockerfile and requirements.txt (see plan)

# 3. Build and run
docker-compose up -d

# 4. View logs
docker-compose logs -f app

# 5. Test health check
curl http://localhost:8000/health
```

### Test Conversion
```bash
# Convert HEIC
curl -X POST "http://localhost:8000/convert" \
  -F "file=@backend/test_images/sample.heic" \
  --output result.jpg

# Check metadata
exiftool result.jpg
```

### Debug
```bash
# Shell into container
docker-compose exec app bash

# Test Python imports
docker-compose exec app python -c "import rawpy, pillow_heif"

# Check exiftool version
docker-compose exec app exiftool -ver
```

---

## Resources

### Internal Documentation
- **PRD Research:** `context/prd_research.md`
- **Implementation Plan:** `dev/active/image-processing/image-processing-plan.md`
- **Technical Context:** `dev/active/image-processing/image-processing-context.md`
- **Task Checklist:** `dev/active/image-processing/image-processing-tasks.md`

### External References
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pillow-HEIF Docs](https://pillow-heif.readthedocs.io/)
- [rawpy Docs](https://letmaik.github.io/rawpy/)
- [ExifTool Docs](https://exiftool.org/)
- [LibRaw API](https://www.libraw.org/docs/API-overview.html)

### Key PRD Sections
- **Section IV:** Metadata preservation (critical requirement)
- **Section IX:** Conversion code examples
- **Section X:** Security considerations
- **Section XII:** Testing strategy

---

## Troubleshooting Quick Reference

### Docker Build Fails
**Symptom:** libheif-dev not found
**Solution:** Add backports or compile from source (see plan Appendix D)

### HEIC Metadata Lost
**Symptom:** GPS/EXIF missing in output
**Check:** pillow-heif.register_heif_opener() called? exif_data passed to save()?

### DNG Too Dark
**Symptom:** Output is too dark or distorted
**Check:** use_camera_wb=True set? no_auto_bright=True?

### Subprocess Timeout
**Symptom:** exiftool hangs on DNG
**Check:** File is valid? Timeout >= 30s? exiftool version correct?

### Security Alert
**Symptom:** Command injection vulnerability
**Check:** shell=False in all subprocess.run()? No string formatting?

---

## Current Status

**Phase:** Phase 1 (Planning Complete)
**Next Step:** Begin implementation with Task 1.1 (Create Backend Directory Structure)
**Estimated Time to MVP:** 1-2 weeks (40-80 hours)
**Blockers:** None

---

## Contact & Support

For questions about:
- **Architecture decisions:** See `context/prd_research.md`
- **Implementation details:** See `dev/active/image-processing/image-processing-plan.md`
- **Current task:** See `dev/active/image-processing/image-processing-tasks.md`
- **Technical context:** See `dev/active/image-processing/image-processing-context.md`

---

**Last Updated: 2025-01-05**
