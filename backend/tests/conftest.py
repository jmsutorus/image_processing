import io
from pathlib import Path

import pytest
from PIL import Image

SAMPLES = Path(__file__).resolve().parent.parent / "test_images"

EXIF_ORIENTATION = 0x0112
EXIF_MAKE = 0x010F
EXIF_GPS_IFD = 0x8825


def open_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def has_gps(data: bytes) -> bool:
    return EXIF_GPS_IFD in open_bytes(data).getexif()


@pytest.fixture
def rotated_jpeg() -> bytes:
    """400x200 JPEG, left half red / right half blue, tagged Orientation=6 with GPS."""
    image = Image.new("RGB", (400, 200), (220, 30, 30))
    image.paste((30, 30, 220), (200, 0, 400, 200))
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = 6
    exif[EXIF_MAKE] = "TestCam"
    exif[EXIF_GPS_IFD] = {1: "N", 2: (40.0, 26.0, 46.0), 3: "W", 4: (79.0, 58.0, 56.0)}
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", exif=exif, quality=95)
    return buffer.getvalue()


@pytest.fixture
def transparent_png() -> bytes:
    image = Image.new("RGBA", (300, 300), (0, 0, 255, 0))
    image.paste((0, 255, 0, 255), (100, 100, 200, 200))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


@pytest.fixture(scope="session")
def sample_heic() -> bytes:
    return (SAMPLES / "sample.heic").read_bytes()


@pytest.fixture(scope="session")
def sample_dng() -> bytes:
    return (SAMPLES / "sample.DNG").read_bytes()
