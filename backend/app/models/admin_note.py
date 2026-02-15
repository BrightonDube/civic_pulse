"""
AdminNote model for internal notes on reports.

Requirements: 9.3
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text

from app.core.database import Base
from app.models.user import GUID


class AdminNote(Base):
    """Internal admin note attached to a report."""
    __tablename__ = "admin_notes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=False)
    admin_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<AdminNote(report={self.report_id}, admin={self.admin_id})>"
