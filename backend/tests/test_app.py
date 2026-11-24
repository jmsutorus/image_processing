import pytest
from fastapi.testclient import TestClient

from app import app, MAX_UPLOAD_SIZE
from conftest import open_bytes, has_gps

client = TestClient(app)


def test_webp_endpoint(rotated_jpeg):
    r = client.post("/convert-to-webp?max_dimension=100", files={"file": ("photo.jpg", rotated_jpeg)})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/webp"
    out = open_bytes(r.content)
    assert out.format == "WEBP" and out.size == (50, 100)
    assert not has_gps(r.content)


def test_jpeg_endpoint(transparent_png):
    r = client.post("/convert", files={"file": ("x.png", transparent_png)})
    assert r.status_code == 200
    assert open_bytes(r.content).format == "JPEG"


def test_download_filename_is_sanitized(rotated_jpeg):
    r = client.post("/convert-to-webp", files={"file": ("../../my evil photo.jpg", rotated_jpeg)})
    assert r.status_code == 200
    assert r.headers["content-disposition"] == 'attachment; filename="my_evil_photo.webp"'


def test_unsupported_extension():
    r = client.post("/convert-to-webp", files={"file": ("x.gif", b"GIF89a")})
    assert r.status_code == 400


def test_content_must_match_extension(rotated_jpeg):
    r = client.post("/convert-to-webp", files={"file": ("x.png", rotated_jpeg)})
    assert r.status_code == 400


def test_undecodable_image_is_422():
    r = client.post("/convert-to-webp", files={"file": ("x.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64)})
    assert r.status_code == 422


@pytest.mark.parametrize("query", ["quality=150", "quality=-1", "max_dimension=5"])
def test_invalid_parameters_are_422(rotated_jpeg, query):
    r = client.post(f"/convert-to-webp?{query}", files={"file": ("a.jpg", rotated_jpeg)})
    assert r.status_code == 422


def test_oversized_upload_rejected_early():
    r = client.post(
        "/convert-to-webp",
        headers={"content-length": str(MAX_UPLOAD_SIZE * 2)},
        content=b"x",
    )
    assert r.status_code == 413


def test_health():
    assert client.get("/health").json() == {"status": "healthy"}
