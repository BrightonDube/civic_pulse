"""
Configuration API endpoints.
Provides system configuration data like valid categories and statuses.
"""
from fastapi import APIRouter

from app.models.report import VALID_CATEGORIES, VALID_STATUSES

router = APIRouter(prefix="/api/config", tags=["Config"])


@router.get("/categories")
def get_categories():
    """Get all valid report categories."""
    return {"categories": VALID_CATEGORIES}


@router.get("/statuses")
def get_statuses():
    """Get all valid report statuses."""
    return {"statuses": VALID_STATUSES}
