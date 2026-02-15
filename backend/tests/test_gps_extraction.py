"""
Tests for GPS extraction from EXIF metadata.

Properties 1, 2
Requirements: 1.1, 1.2
"""
import io
import struct
import pytest
from PIL import Image

from app.services.gps_service import extract_gps_from_exif


def _create_jpeg_with_gps(lat: float, lon: float) -> bytes:
    """Create a JPEG image with GPS EXIF data."""
    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()

    import piexif

    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    abs_lat = abs(lat)
    abs_lon = abs(lon)

    lat_d = int(abs_lat)
    lat_m = int((abs_lat - lat_d) * 60)
    lat_s = int(((abs_lat - lat_d) * 60 - lat_m) * 60 * 10000)

    lon_d = int(abs_lon)
    lon_m = int((abs_lon - lon_d) * 60)
    lon_s = int(((abs_lon - lon_d) * 60 - lon_m) * 60 * 10000)

    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: lat_ref.encode(),
        piexif.GPSIFD.GPSLatitude: ((lat_d, 1), (lat_m, 1), (lat_s, 10000)),
        piexif.GPSIFD.GPSLongitudeRef: lon_ref.encode(),
        piexif.GPSIFD.GPSLongitude: ((lon_d, 1), (lon_m, 1), (lon_s, 10000)),
    }
    exif_dict = {"GPS": gps_ifd}
    exif_bytes = piexif.dump(exif_dict)

    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


def _create_jpeg_without_gps() -> bytes:
    """Create a JPEG image without GPS EXIF data."""
    img = Image.new("RGB", (10, 10), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# Only run these if piexif is available
try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False


@pytest.mark.skipif(not HAS_PIEXIF, reason="piexif not installed")
def test_extract_gps_from_exif():
    """Property 1: GPS Extraction from EXIF - basic test."""
    photo = _create_jpeg_with_gps(40.7128, -74.0060)
    coords = extract_gps_from_exif(photo)

    assert coords is not None
    lat, lon = coords
    assert abs(lat - 40.7128) < 0.01
    assert abs(lon - (-74.0060)) < 0.01


@pytest.mark.skipif(not HAS_PIEXIF, reason="piexif not installed")
def test_extract_gps_southern_hemisphere():
    """Property 1: GPS Extraction for southern hemisphere."""
    photo = _create_jpeg_with_gps(-33.8688, 151.2093)
    coords = extract_gps_from_exif(photo)

    assert coords is not None
    lat, lon = coords
    assert abs(lat - (-33.8688)) < 0.01
    assert abs(lon - 151.2093) < 0.01


def test_no_gps_in_exif():
    """Property 2: GPS Fallback - returns None when no EXIF GPS data."""
    photo = _create_jpeg_without_gps()
    coords = extract_gps_from_exif(photo)
    assert coords is None


def test_invalid_photo_data():
    """GPS extraction should handle invalid data gracefully."""
    coords = extract_gps_from_exif(b"not a real photo")
    assert coords is None


def test_empty_photo():
    """GPS extraction should handle empty data gracefully."""
    coords = extract_gps_from_exif(b"")
    assert coords is None
