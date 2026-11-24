FROM python:3.11-slim-bookworm

# System dependencies
# - libmagic1: MIME detection for upload validation
# pillow, pillow-heif and rawpy ship wheels with libjpeg/libwebp/libheif/libraw bundled.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify libraries load correctly (fail fast if deps broken)
RUN python -c "import rawpy, pillow_heif, magic; from PIL import features; assert features.check('webp'), 'WebP support missing'; print('All dependencies loaded successfully')"

# Copy application code (tests and sample images excluded by .dockerignore)
COPY . .

# Switch to non-root user
USER appuser

EXPOSE 8000

# Cloud Run sets $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
