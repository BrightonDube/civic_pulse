"""
Pydantic schemas for reports.

Requirements: 11.3
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


VALID_CATEGORIES = [
    "Pothole", "Water Leak", "Vandalism",
    "Broken Streetlight", "Illegal Dumping", "Other"
]


class ReportCreate(BaseModel):
    """Schema for creating a report (without photo - photo sent as multipart)."""
    latitude: float
    longitude: float
    user_override_category: Optional[str] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("user_override_category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {VALID_CATEGORIES}")
        return v


class ReportResponse(BaseModel):
    """Schema for report response. Property 9: Report Detail Completeness."""
    id: str
    user_id: str
    photo_url: str
    latitude: float
    longitude: float
    category: str
    severity_score: int
    color: str = "green"
    status: str
    upvote_count: int
    ai_generated: bool
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportCategoryUpdate(BaseModel):
    """Schema for updating report category."""
    category: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {VALID_CATEGORIES}")
        return v


def severity_to_color(severity: int) -> str:
    """Map severity score to color. Requirements: 3.2"""
    if severity >= 8:
        return "red"
    elif severity >= 4:
        return "yellow"
    return "green"
