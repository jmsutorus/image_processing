# API Endpoints

Complete API reference for the Image Processing Service. Both conversion endpoints are synchronous: the response body is the converted image.

Interactive docs once running: http://localhost:8000/docs (Swagger) or http://localhost:8000/redoc

## `POST /convert-to-webp`

| Query param | Default | Description |
|---|---|---|
| `quality` | 85 | 0-100. Lossy: output quality. Lossless: compression effort (0 fastest, 100 smallest). |
| `lossless` | false | Lossless WebP. |
| `max_dimension` | none | 16-16384. Downscale so the longest edge fits; never upscales. |
| `strip_gps` | true | Remove GPS location. XMP is also dropped, since it can carry a copy of the location. |

```bash
# Phone photo -> web-ready WebP, max 2048px, location removed (what homepage uses)
curl -X POST "http://localhost:8000/convert-to-webp?max_dimension=2048" \
  -F "file=@photo.heic" --output photo.webp

# Keep full size and location
curl -X POST "http://localhost:8000/convert-to-webp?strip_gps=false" \
  -F "file=@raw.dng" --output raw.webp

# Lossless (e.g. screenshots)
curl -X POST "http://localhost:8000/convert-to-webp?lossless=true" \
  -F "file=@screenshot.png" --output screenshot.webp
```

## `POST /convert`

Same as above but outputs JPEG. `quality` defaults to 95 and is capped at 95; `lossless` doesn't apply.

```bash
curl -X POST "http://localhost:8000/convert?max_dimension=2048" \
  -F "file=@photo.heic" --output photo.jpg
```

## Behavior

- **Inputs:** `.heic`, `.heif`, `.dng`, `.jpg`, `.jpeg`, `.png`, `.webp`. The extension must match the file's content.
- **Orientation:** EXIF orientation is applied to the pixels and the tag reset to 1, so the image displays upright everywhere.
- **Metadata:** EXIF (camera, capture settings, dates) and ICC profiles are kept. For DNG, only standard camera/capture tags are carried over (no raw-sensor tags or MakerNote).
- **Transparency:** kept in WebP output, flattened onto white for JPEG.
- **Animated images:** only the first frame is converted.

## Errors

| Status | Cause |
|---|---|
| 400 | Unsupported extension, empty file, or content doesn't match the extension |
| 413 | Larger than 200MB |
| 422 | Invalid parameter, or the file passed validation but couldn't be decoded |

Note: Cloud Run caps HTTP/1 request bodies at 32MB, so in production the practical limit is 32MB.

## Size Results

Sample images, WebP quality 85:

| Input | Input size | `max_dimension` | Output size |
|---|---|---|---|
| HEIC (iPhone, 3024×4032) | 3.8 MB | none | 2.98 MB |
| HEIC (iPhone, 3024×4032) | 3.8 MB | 2048 | 967 KB |
| DNG (iPhone 13 Pro) | 28 MB | 2048 | 146 KB |

## `GET /health`

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

`GET /` returns service info: supported formats, options and limits.
