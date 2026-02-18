"""
Comment model for report discussions.

Requirements: 14.1, 14.2
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import GUID


class Comment(Base):
    """
    Comment model representing user comments on reports.
    Supports threaded discussions via parent_comment_id.
    """
    __tablename__ = "comments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID(), ForeignKey("reports.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(GUID(), ForeignKey("comments.id"), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_comments_report_id", "report_id"),
        Index("ix_comments_created_at", "created_at"),
        Index("ix_comments_parent_id", "parent_comment_id"),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, report_id={self.report_id}, user_id={self.user_id})>"
