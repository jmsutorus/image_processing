FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libheif-dev \
    libraw-dev \
    libjpeg-turbo-progs \
    libwebp-dev \
    libmagic1 \
    exiftool \
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
RUN python -c "import rawpy; import pillow_heif; from PIL import Image, features; print('All dependencies loaded successfully'); print('WebP support:', features.check('webp'))"

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
