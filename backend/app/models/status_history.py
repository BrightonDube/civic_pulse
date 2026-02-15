"""
StatusHistory model for tracking report status changes.

Requirements: 4.6
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class StatusHistory(Base):
    """Audit log entry for report status changes."""
    __tablename__ = "status_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=False)
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    changed_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<StatusHistory(report={self.report_id}, {self.old_status}->{self.new_status})>"
