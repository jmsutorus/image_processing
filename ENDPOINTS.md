# API Endpoints

Complete API reference for the Image Processing Service.

## API Documentation

Once running, visit:
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Synchronous Endpoints

### Convert to JPEG

```bash
# Convert HEIC to JPEG
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.heic" \
  --output converted.jpg

# Convert DNG to JPEG
curl -X POST "http://localhost:8000/convert" \
  -F "file=@raw.dng" \
  --output converted.jpg

# Convert JPG to JPEG (with quality adjustment)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.jpg" \
  --output converted.jpg
```

### Convert to WebP

```bash
# Convert HEIC to WebP (lossy, quality 85)
curl -X POST "http://localhost:8000/convert-to-webp?quality=85&lossless=false" \
  -F "file=@photo.heic" \
  --output converted.webp

# Convert DNG to WebP (high quality)
curl -X POST "http://localhost:8000/convert-to-webp?quality=90&lossless=false" \
  -F "file=@raw.dng" \
  --output converted.webp

# Convert JPG to WebP (lossless)
curl -X POST "http://localhost:8000/convert-to-webp?lossless=true&quality=100" \
  -F "file=@photo.jpg" \
  --output converted.webp

# Convert JPG to WebP (maximum compression for web)
curl -X POST "http://localhost:8000/convert-to-webp?quality=80&lossless=false" \
  -F "file=@photo.jpg" \
  --output converted.webp
```

### WebP Parameters

- **quality** (0-100): Quality/compression level
  - For lossy: 0=smallest file, 100=largest/best quality (default: 85)
  - For lossless: 0=fastest compression, 100=slowest/smallest (default: 85)
- **lossless** (true/false): Enable lossless compression (default: false)

### Compression Results

Real-world test results from our sample images:

| Input Format | Input Size | Output Format | Output Size | Reduction | Quality |
|--------------|-----------|---------------|-------------|-----------|---------|
| HEIC | 3.7 MB | WebP | 2.9 MB | 22% | quality=85 |
| JPG | 1.5 MB | WebP | 258 KB | **83%** | quality=85 |
| DNG | 28 MB | WebP | 448 KB | **98.4%** | quality=90 |
| JPG | 1.5 MB | WebP (lossless) | 3.2 MB | -113% | lossless=true |

**Key Takeaways:**
- WebP provides 25-80% file size reduction for typical web use cases
- DNG → WebP is ideal for publishing RAW photos to websites
- Lossless WebP is larger than lossy but maintains perfect quality
- Recommended: quality=85 for web images, quality=90 for hero images

## Asynchronous Endpoints

For large files or when you need non-blocking responses.

### Submit Async Job

```bash
# Submit job (returns immediately with job_id)
JOB_RESPONSE=$(curl -X POST "http://localhost:8000/jobs/convert?output_format=webp&quality=85" \
  -F "file=@large_dng_file.DNG")
JOB_ID=$(echo $JOB_RESPONSE | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
echo "Job submitted: $JOB_ID"
```

### Check Job Status

```bash
curl "http://localhost:8000/jobs/$JOB_ID"
# Response: {"job_id":"abc...","status":"SUCCESS","result":{...}}
```

### Download Result

```bash
curl "http://localhost:8000/jobs/$JOB_ID/result" --output converted.webp
```

### Job Status Values

- `PENDING` - Job is queued
- `PROCESSING` - Job is being processed
- `SUCCESS` - Job completed, ready to download
- `FAILURE` - Job failed, check error message

### Async Benefits

- Non-blocking: Get immediate response even for large files
- Concurrent: Multiple jobs processed in parallel (2 workers by default)
- Resilient: Jobs survive worker restarts
- TTL: Results stored for 1 hour

## Batch Processing Endpoints

For converting multiple files in a single operation.

### Submit Batch Job

```bash
# Submit batch job with multiple files (returns immediately with batch_id)
BATCH_RESPONSE=$(curl -X POST "http://localhost:8000/jobs/batch-convert?output_format=webp&quality=85" \
  -F "files=@photo1.heic" \
  -F "files=@photo2.jpg" \
  -F "files=@photo3.DNG")
BATCH_ID=$(echo $BATCH_RESPONSE | grep -o '"batch_id":"[^"]*' | cut -d'"' -f4)
echo "Batch submitted: $BATCH_ID"
```

### Check Batch Status

```bash
curl "http://localhost:8000/jobs/batch/$BATCH_ID"
# Response: {
#   "batch_id": "abc...",
#   "status": "SUCCESS",
#   "total_files": 3,
#   "completed": 3,
#   "failed": 0,
#   "percent": 100,
#   "files": [
#     {"filename": "photo1.heic", "job_id": "xyz1", "status": "SUCCESS", "size_bytes": 2981616},
#     {"filename": "photo2.jpg", "job_id": "xyz2", "status": "SUCCESS", "size_bytes": 263564},
#     {"filename": "photo3.DNG", "job_id": "xyz3", "status": "SUCCESS", "size_bytes": 327688}
#   ]
# }
```

### Download Batch Results

```bash
# Download all converted files as a ZIP
curl "http://localhost:8000/jobs/batch/$BATCH_ID/results" --output results.zip
unzip results.zip
```

### Batch Status Values

- `PENDING` - Batch is queued
- `PROCESSING` - Files are being processed (some may be complete)
- `SUCCESS` - All files completed successfully
- `PARTIAL` - Some files succeeded, some failed
- `FAILURE` - All files failed or batch error

### Batch Limits

- Maximum 50 files per batch
- Each file subject to standard validation (200MB max, HEIC/DNG/JPG only)
- Individual file conversions run in parallel for faster processing

### Batch Benefits

- Single upload: Submit multiple files at once
- Parallel processing: All files converted simultaneously
- Partial success: Get successful conversions even if some files fail
- Easy download: All results packaged in a single ZIP file

## Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

## Expected Performance

| File Type | Size | Processing Time |
|-----------|------|----------------|
| HEIC | 10MB | ~2-3 seconds |
| HEIC | 50MB | ~5-8 seconds |
| DNG | 20MB | ~8-10 seconds |
| DNG | 100MB | ~15-20 seconds |

## Security Considerations

- Maximum file size: 200MB
- Supported formats: .heic, .heif, .dng, .jpg, .jpeg only
- All uploads validated before processing
- No shell interpretation in subprocess calls
