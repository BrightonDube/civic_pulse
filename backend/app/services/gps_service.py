"""
Service for GPS extraction from EXIF metadata.

Requirements: 1.1, 1.2
"""
import logging
from typing import Optional, Tuple
import io

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger(__name__)


def _get_gps_info(image: Image.Image) -> Optional[dict]:
    """Extract GPS info dict from image EXIF data."""
    exif_data = image.getexif()
    if not exif_data:
        return None

    # GPS info is in IFD 0x8825
    gps_ifd = exif_data.get_ifd(0x8825)
    if not gps_ifd:
        return None

    gps_info = {}
    for key, val in gps_ifd.items():
        tag_name = GPSTAGS.get(key, key)
        gps_info[tag_name] = val

    return gps_info if gps_info else None


def _convert_to_degrees(value) -> float:
    """Convert GPS coordinate from EXIF format to decimal degrees."""
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0


def extract_gps_from_exif(photo_bytes: bytes) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from photo EXIF metadata.
    Returns (latitude, longitude) or None if not available.

    Requirements: 1.1
    """
    try:
        image = Image.open(io.BytesIO(photo_bytes))
        gps_info = _get_gps_info(image)
        if gps_info is None:
            return None

        lat = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if lat is None or lon is None:
            return None

        latitude = _convert_to_degrees(lat)
        longitude = _convert_to_degrees(lon)

        if lat_ref == "S":
            latitude = -latitude
        if lon_ref == "W":
            longitude = -longitude

        return (latitude, longitude)
    except (OSError, SyntaxError, ValueError) as e:
        logger.debug("Failed to extract GPS from EXIF: %s", e)
        return None
