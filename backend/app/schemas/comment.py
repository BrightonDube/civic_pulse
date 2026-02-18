"""
Pydantic schemas for comments.

Requirements: 11.3, 14.1, 14.2, 14.3
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    text: str
    parent_comment_id: Optional[str] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Comment text cannot be empty")
        if len(v) > 5000:
            raise ValueError("Comment text cannot exceed 5000 characters")
        return v.strip()

    @field_validator("parent_comment_id")
    @classmethod
    def validate_parent_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                import uuid
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Invalid parent comment ID format")
        return v


class CommentResponse(BaseModel):
    """Schema for comment response."""
    id: str
    report_id: str
    user_id: str
    parent_comment_id: Optional[str]
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThreadedCommentResponse(BaseModel):
    """
    Schema for threaded comment response with nested replies.
    
    Requirements: 14.3 - Support threaded discussions
    """
    id: str
    report_id: str
    user_id: str
    parent_comment_id: Optional[str]
    text: str
    created_at: datetime
    updated_at: datetime
    replies: List["ThreadedCommentResponse"] = []

    model_config = {"from_attributes": True}
