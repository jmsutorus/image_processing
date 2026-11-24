import pytest

from converter import convert_image, ConversionError
from conftest import open_bytes, has_gps, EXIF_ORIENTATION, EXIF_MAKE


# --- Orientation ----------------------------------------------------------

@pytest.mark.parametrize("fmt", ["jpeg", "webp"])
def test_orientation_is_applied_to_pixels_and_reset(rotated_jpeg, fmt):
    out = open_bytes(convert_image(rotated_jpeg, "a.jpg", fmt))
    assert out.size == (200, 400)  # Orientation 6 = rotate 90° clockwise
    assert out.getexif().get(EXIF_ORIENTATION) == 1
    # Red (left half of the source) ends up on top after a clockwise turn
    r, g, b = out.convert("RGB").getpixel((100, 50))
    assert r > 150 and b < 100


def test_dng_is_not_rotated_twice(sample_dng):
    # Sample is a portrait iPhone shot: sensor 4032x3024 with flip=6.
    # rawpy applies the flip, so the output must stay portrait.
    out = open_bytes(convert_image(sample_dng, "s.dng", "webp", max_dimension=1024))
    assert out.size[0] < out.size[1]
    assert out.getexif().get(EXIF_ORIENTATION) == 1


def test_heic_stays_portrait(sample_heic):
    out = open_bytes(convert_image(sample_heic, "s.heic", "webp", max_dimension=1024))
    assert out.size == (768, 1024)
    assert out.getexif().get(EXIF_ORIENTATION) in (None, 1)


# --- Metadata --------------------------------------------------------------

def test_gps_stripped_by_default(rotated_jpeg):
    assert has_gps(rotated_jpeg)
    out = convert_image(rotated_jpeg, "a.jpg", "webp")
    assert not has_gps(out)
    assert open_bytes(out).getexif().get(EXIF_MAKE) == "TestCam"  # Other EXIF kept


def test_gps_kept_when_requested(rotated_jpeg):
    assert has_gps(convert_image(rotated_jpeg, "a.jpg", "webp", strip_gps=False))


def test_dng_metadata(sample_dng):
    out = convert_image(sample_dng, "s.dng", "jpeg", max_dimension=512)
    exif = open_bytes(out).getexif()
    assert exif.get(EXIF_MAKE) == "Apple"
    assert exif.get_ifd(0x8769).get(0x9003)  # DateTimeOriginal
    assert not has_gps(out)
    assert has_gps(convert_image(sample_dng, "s.dng", "jpeg", max_dimension=512, strip_gps=False))


# --- Resizing --------------------------------------------------------------

def test_resize_limits_longest_edge(rotated_jpeg):
    out = open_bytes(convert_image(rotated_jpeg, "a.jpg", "jpeg", max_dimension=100))
    assert out.size == (50, 100)


def test_never_upscales(rotated_jpeg):
    out = open_bytes(convert_image(rotated_jpeg, "a.jpg", "jpeg", max_dimension=5000))
    assert out.size == (200, 400)


def test_resizing_shrinks_heic(sample_heic):
    full = convert_image(sample_heic, "s.heic", "webp")
    small = convert_image(sample_heic, "s.heic", "webp", max_dimension=2048)
    assert len(small) < len(full) / 2


# --- Transparency / modes ---------------------------------------------------

def test_png_alpha_kept_in_webp(transparent_png):
    out = open_bytes(convert_image(transparent_png, "x.png", "webp", lossless=True))
    assert out.mode == "RGBA"
    assert out.getpixel((0, 0))[3] == 0
    assert out.getpixel((150, 150))[3] == 255


def test_png_alpha_flattened_to_white_in_jpeg(transparent_png):
    out = open_bytes(convert_image(transparent_png, "x.png", "jpeg"))
    assert out.mode == "RGB"
    assert all(c > 245 for c in out.getpixel((0, 0)))


def test_webp_input(transparent_png):
    webp = convert_image(transparent_png, "x.png", "webp")
    out = open_bytes(convert_image(webp, "x.webp", "jpeg"))
    assert out.format == "JPEG"


# --- Errors ----------------------------------------------------------------

def test_corrupt_input_raises():
    with pytest.raises(ConversionError):
        convert_image(b"not an image", "x.jpg", "webp")


def test_unsupported_extension_raises():
    with pytest.raises(ConversionError):
        convert_image(b"GIF89a", "x.gif", "webp")
