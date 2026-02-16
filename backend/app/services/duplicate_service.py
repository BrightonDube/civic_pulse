"""
Duplicate detection service using spatial search.

Uses Haversine formula for distance calculation (SQLite compatible).
For PostgreSQL+PostGIS, this would use ST_DWithin.

Requirements: 5.1, 5.2
"""
import math
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.report import Report


EARTH_RADIUS_METERS = 6_371_000  # Mean Earth radius in meters
DEFAULT_RADIUS_METERS = 50.0


class DuplicateDetectionService:
    """Service for finding nearby reports and detecting duplicates."""

    def __init__(self, db: Session):
        self.db = db

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
    ) -> Optional[Report]:
        """
        Check if a report with the same category exists nearby.
        Returns the closest matching report or None.
        Property 16: Duplicate Detection
        Requirements: 5.2
        """
        nearby = self.find_nearby_reports(latitude, longitude, radius_meters)
        matching = [r for r in nearby if r.category == category]

        if not matching:
            return None

        # Return the closest match
        matching.sort(
            key=lambda r: self.calculate_distance(latitude, longitude, r.latitude, r.longitude)
        )
        return matching[0]
