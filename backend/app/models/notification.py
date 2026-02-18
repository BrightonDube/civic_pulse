"""
Notification model for in-app notifications.

Requirements: 4.3, 17.2, 17.3
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base
from app.models.user import GUID


class Notification(Base):
    """
    In-app notification model for status changes and updates.
    
    Requirements: 4.3 - Notify users of status changes
    Requirements: 17.2 - In-app notification center
    Requirements: 17.3 - Display notifications in reverse chronological order
    """
    __tablename__ = "notifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=True, index=True)
    type = Column(String, nullable=False)  # "status_change", "comment", "upvote", etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, read={self.read})>"
