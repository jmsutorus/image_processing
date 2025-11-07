# Image Processing Service

A professional-grade web service for converting HEIC, DNG, and JPG image formats to JPEG or WebP with complete metadata preservation.

## Current Status

✅ **Production Ready** - Async processing with Celery + Redis
✅ **Batch Processing** - Multiple file upload with ZIP download
✅ **WebP Support** - Lossy and lossless compression

## Overview

This service handles multiple image conversion formats optimized for web use:

- **HEIC → JPEG/WebP:** Decode High-Efficiency Image Container files (from iPhones)
- **DNG → JPEG/WebP:** Develop Digital Negative RAW files (from cameras) with proper white balance and color space
- **JPG → WebP:** Convert existing JPEG images to modern WebP format for web optimization

### Key Features

- Multiple output formats (JPEG and WebP)
- Metadata preservation (EXIF, XMP, ICC profiles, GPS data)
- High quality configurable settings
- Professional RAW processing with correct white balance
- Web optimization (WebP reduces file sizes by 25-80%)
- Security hardened (CVE-patched ExifTool, no shell injection)
- Docker containerized

## Technology Stack

**Backend:**
- Python 3.11+ with FastAPI
- Celery 5.3.4 (distributed task queue)
- Redis 7 (message broker + result backend)
- Docker + docker-compose

**Image Processing:**
- Pillow 10.2.0 (image operations, WebP encoding)
- pillow-heif (HEIC decoding via libheif)
- rawpy (DNG processing via LibRaw)
- exiftool (metadata copying)

**Supported Formats:**
- **Input:** HEIC, HEIF, DNG, JPG, JPEG
- **Output:** JPEG, WebP (lossy and lossless)

**Architecture:**
```
┌──────────┐      ┌──────────┐      ┌───────────────┐
│  Client  │ ───> │ FastAPI  │ ───> │ Redis Broker  │
└──────────┘      │  (8000)  │      │    (6379)     │
                  └──────────┘      └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Celery Worker │
                                    │ (2 concurrent)│
                                    └───────────────┘
```

## Quick Start

### Prerequisites
- Docker 24.0+
- docker-compose
- 4GB RAM (8GB recommended)
- 2GB disk space

### Running the Service

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f app

# Check health
curl http://localhost:8000/health

# Stop the service
docker-compose down
```

### API Usage

See [ENDPOINTS.md](ENDPOINTS.md) for complete API reference including:
- Synchronous conversion endpoints
- Async job processing
- Batch processing
- WebP parameters and compression results

**Quick Example:**

```bash
# Convert HEIC to WebP
curl -X POST "http://localhost:8000/convert-to-webp?quality=85" \
  -F "file=@photo.heic" \
  --output converted.webp

# Submit async batch job
curl -X POST "http://localhost:8000/jobs/batch-convert?output_format=webp&quality=85" \
  -F "files=@photo1.heic" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.DNG"
```

**Interactive API Docs:** http://localhost:8000/docs

## Project Structure

```
image_processing/
├── backend/
│   ├── app.py                       # FastAPI server
│   ├── converter.py                 # Core conversion logic
│   ├── tasks.py                     # Celery tasks
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Container definition
│   └── test_images/                 # Sample files
├── docker-compose.yml               # Service orchestration
├── ENDPOINTS.md                     # API reference
├── PROJECT_KNOWLEDGE.md             # Project knowledge base
└── README.md                        # This file
```

## Documentation

### Quick Links

| Document | Purpose |
|----------|---------|
| [ENDPOINTS.md](ENDPOINTS.md) | Complete API reference with examples |
| [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) | Decisions, troubleshooting, detailed notes |
| [context/prd_research.md](context/prd_research.md) | Comprehensive technology analysis |
| [Interactive Docs](http://localhost:8000/docs) | Live API documentation (when running) |

### For New Developers

1. Start with this README for overview and quick start
2. Review [ENDPOINTS.md](ENDPOINTS.md) for API usage
3. Check [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) for detailed context
4. Use [context/prd_research.md](context/prd_research.md) for deep technical understanding

## Testing

### Manual Testing

```bash
# Run test script
cd backend
./test_conversion.sh

# Verify metadata preservation
exiftool result.jpg
```

### Test Coverage

- HEIC, DNG, and JPG conversion
- WebP lossy and lossless modes
- Metadata preservation
- Async job processing
- Batch processing with ZIP download

## Security

### Security Measures

- ✅ ExifTool CVE-2021-22204 patched (version 12.76+)
- ✅ No subprocess shell injection (`shell=False`)
- ✅ Non-root container user (UID 1000)
- ✅ Input validation (file size, extension, MIME type)

### Security Limits

- Maximum file size: 200MB
- Allowed extensions: .heic, .heif, .dng, .jpg, .jpeg
- No shell interpretation in subprocess calls
- All uploads validated before processing

## Troubleshooting

For common issues, see [PROJECT_KNOWLEDGE.md - Troubleshooting Section](PROJECT_KNOWLEDGE.md#troubleshooting-quick-reference):

- Docker build failures
- Metadata not preserved
- Image quality issues
- Performance optimization

## Contributing

### Code Quality Standards

- Follow PEP 8 style guide
- Add docstrings to all functions
- Never use `shell=True` in subprocess calls
- Pin all dependency versions
- Include type hints where possible

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pillow-HEIF Documentation](https://pillow-heif.readthedocs.io/)
- [rawpy Documentation](https://letmaik.github.io/rawpy/)
- [ExifTool Documentation](https://exiftool.org/)

---

**Last Updated:** 2025-01-05
