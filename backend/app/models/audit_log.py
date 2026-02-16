"""
AuditLog model for tracking all admin actions.

Requirements: 9.7
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Text

from app.core.database import Base
from app.models.user import GUID


class AuditLog(Base):
    """Audit trail for admin actions."""
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=False)
    admin_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g. "status_update", "category_override", "severity_adjust", "add_note", "archive"
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<AuditLog(report={self.report_id}, action={self.action})>"
