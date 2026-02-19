"""
Duplicate detection service using spatial search and image hashing.

Uses Haversine formula for distance calculation (SQLite compatible).
For PostgreSQL+PostGIS, this would use ST_DWithin.
Uses SHA-256 hashing for exact image duplicate detection.

Requirements: 5.1, 5.2
"""
import hashlib
import math
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import Report


EARTH_RADIUS_METERS = 6_371_000  # Mean Earth radius in meters
DEFAULT_RADIUS_METERS = 50.0


class DuplicateDetectionService:
    """Service for finding nearby reports and detecting duplicates."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def compute_image_hash(photo_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of image bytes for duplicate detection.
        Returns hex string of the hash.
        """
        return hashlib.sha256(photo_bytes).hexdigest()

    def check_image_duplicate(
        self, photo_bytes: bytes, user_id: uuid.UUID
    ) -> Optional[Report]:
        """
        Check if the exact same image has already been submitted by this user.
        This check happens BEFORE AI analysis to save tokens.
        Returns the existing report if duplicate found, None otherwise.
        """
        image_hash = self.compute_image_hash(photo_bytes)
        
        existing = (
            self.db.query(Report)
            .filter(
                Report.user_id == user_id,
                Report.image_hash == image_hash,
                Report.archived == False,
            )
            .first()
        )
        
        return existing

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.
        Returns distance in meters.
        """
        lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return EARTH_RADIUS_METERS * c

    def find_nearby_reports(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = DEFAULT_RADIUS_METERS,
    ) -> List[Report]:
        """
        Find all active reports within the given radius of coordinates.
        Property 15: Spatial Search Within Radius
        Requirements: 5.1
        """
        # Rough bounding box filter to reduce candidates (1 degree ≈ 111km)
        lat_delta = radius_meters / 111_000
        lon_delta = radius_meters / (111_000 * max(math.cos(math.radians(latitude)), 0.01))

        candidates = (
            self.db.query(Report)
            .filter(
                Report.archived == False,
                Report.latitude.between(latitude - lat_delta, latitude + lat_delta),
                Report.longitude.between(longitude - lon_delta, longitude + lon_delta),
            )
            .all()
        )

        # Precise Haversine filter
        return [
            r for r in candidates
            if self.calculate_distance(latitude, longitude, r.latitude, r.longitude) <= radius_meters
        ]

    def check_for_duplicates(
        self,
        latitude: float,
        longitude: float,
        category: str,
        radius_meters: float = DEFAULT_RADIUS_METERS,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Report]:
        """
        Check if a report with the same category exists nearby.
        If user_id is provided, only checks for duplicates from that specific user
        (to prevent accidental re-submissions while allowing multiple users to report same issue).
        Returns the closest matching report or None.
        Property 16: Duplicate Detection
        Requirements: 5.2
        """
        nearby = self.find_nearby_reports(latitude, longitude, radius_meters)
        matching = [r for r in nearby if r.category == category]
        
        # If user_id provided, only consider duplicates from the same user
        if user_id is not None:
            matching = [r for r in matching if r.user_id == user_id]

        if not matching:
            return None

        # Return the closest match
        matching.sort(
            key=lambda r: self.calculate_distance(latitude, longitude, r.latitude, r.longitude)
        )
        return matching[0]
