"""
Report model for infrastructure issue tracking.

Requirements: 10.2, 10.4, 10.5
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


VALID_CATEGORIES = [
    "Pothole", "Water Leak", "Vandalism",
    "Broken Streetlight", "Illegal Dumping", "Other"
]
VALID_STATUSES = ["Reported", "In Progress", "Fixed"]


class Report(Base):
    """
    Report model representing an infrastructure issue.
    Uses latitude/longitude floats for cross-DB compatibility.
    """
    __tablename__ = "reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    photo_url = Column(String, nullable=False)
    image_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    category = Column(String, nullable=False, default="Other")
    severity_score = Column(Integer, nullable=False, default=5)
    status = Column(String, nullable=False, default="Reported")
    upvote_count = Column(Integer, nullable=False, default=0)
    ai_generated = Column(Boolean, nullable=False, default=False)
    archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    photos = relationship("ReportPhoto", backref="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reports_status", "status"),
        Index("ix_reports_category", "category"),
        Index("ix_reports_created_at", "created_at"),
        Index("ix_reports_lat_lon", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, category={self.category}, status={self.status})>"
