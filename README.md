# Image Processing Service

Converts HEIC, DNG, JPG, PNG and WebP images to web-ready WebP or JPEG. `homepage` sends every photo upload through it (`homepage/lib/services/image-processor.ts`) to resize it to 2048px and strip GPS location before storage.

Deployed on GCP Cloud Run as `image-processing-backend`, invoked with an OIDC token.

## What it does

- **Decodes** HEIC/HEIF (pillow-heif), DNG raw files (rawpy/LibRaw), JPEG, PNG and WebP
- **Rotates** pixels to match EXIF orientation and resets the tag, so images display upright everywhere
- **Resizes** to a max longest edge (`max_dimension`), never upscaling
- **Strips GPS** location by default (`strip_gps`)
- **Keeps** other EXIF (camera, dates, exposure) and ICC color profiles, plus PNG/WebP transparency in WebP output
- **Encodes** WebP (lossy or lossless) or JPEG

See [ENDPOINTS.md](ENDPOINTS.md) for the API reference.

## Stack

- **Backend:** Python 3.11, FastAPI, Pillow, pillow-heif, rawpy, python-magic
- **Frontend:** React 19 + Vite, TanStack Query, React Hook Form + Zod, Tailwind + shadcn/ui. A small single-file converter UI for manual use.

## Running locally

```bash
# Backend (Docker), http://localhost:8000
docker-compose up -d --build
docker-compose down

# Frontend, http://localhost:5173 (expects the backend on :8000)
cd frontend && npm install && npm run dev
```

Without Docker:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # or: source .venv/bin/activate
pip install -r requirements-dev.txt               # on Windows also: pip install python-magic-bin
uvicorn app:app --reload
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The suite covers orientation (including the DNG double-rotation case), GPS stripping, resizing, transparency, the real HEIC/DNG samples in `test_images/`, and the API's validation and error codes.

## Project structure

```
image_processing/
├── backend/
│   ├── app.py              # FastAPI endpoints + upload validation
│   ├── converter.py        # Conversion pipeline: load -> orient -> resize -> clean metadata -> encode
│   ├── tests/              # pytest suite
│   ├── test_images/        # sample.heic, sample.DNG (test fixtures)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/               # React converter UI
├── docker-compose.yml
├── ENDPOINTS.md            # API reference
└── PROJECT_KNOWLEDGE.md    # Original design notes (historical)
```

## Security

- Non-root container user
- Uploads validated by extension, magic-number MIME type and size before decoding
- Oversized requests rejected from `Content-Length` before parsing
- No temp files or subprocesses; the uploaded filename is never used in a path
- Conversion runs in FastAPI's thread pool, so one large file doesn't block other requests
