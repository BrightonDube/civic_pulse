"""
ReportPhoto model for storing multiple photos per report.

Requirements: 14.4, 19.1
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class ReportPhoto(Base):
    """
    ReportPhoto model for storing multiple photos associated with a report.
    Supports up to 5 photos per report with ordering.
    """
    __tablename__ = "report_photos"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    photo_url = Column(String, nullable=False)
    is_before_photo = Column(Boolean, nullable=False, default=True)
    upload_order = Column(Integer, nullable=False)  # 1-5 for multiple photos
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_report_photos_report_id", "report_id"),
        Index("ix_report_photos_upload_order", "report_id", "upload_order"),
    )

    def __repr__(self) -> str:
        return f"<ReportPhoto(id={self.id}, report_id={self.report_id}, order={self.upload_order})>"
