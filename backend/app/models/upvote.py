"""
Upvote model for report upvoting.

Requirements: 5.3, 5.4, 5.6
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class Upvote(Base):
    """Tracks user upvotes on reports. Unique constraint prevents double-voting."""
    __tablename__ = "upvotes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("report_id", "user_id", name="uq_upvote_report_user"),
    )

    def __repr__(self) -> str:
        return f"<Upvote(report_id={self.report_id}, user_id={self.user_id})>"
