"""
Report API endpoints.

Requirements: 1.4, 2.6, 11.2
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import ReportResponse, ReportCategoryUpdate, severity_to_color
from app.services.report_service import ReportService
from app.services.gps_service import extract_gps_from_exif

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _report_to_response(report) -> ReportResponse:
    return ReportResponse(
        id=str(report.id),
        user_id=str(report.user_id),
        photo_url=report.photo_url,
        latitude=report.latitude,
        longitude=report.longitude,
        category=report.category,
        severity_score=report.severity_score,
        status=report.status,
        upvote_count=report.upvote_count,
        ai_generated=report.ai_generated,
        archived=report.archived,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    photo: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    user_override_category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new report with photo and location.
    GPS is extracted from EXIF if not provided.
    Requirements: 1.1, 1.2, 1.4
    """
    photo_bytes = await photo.read()
    if not photo_bytes:
        raise HTTPException(status_code=400, detail="Photo is required")

    # Try EXIF extraction if coordinates not provided
    if latitude is None or longitude is None:
        coords = extract_gps_from_exif(photo_bytes)
        if coords:
            latitude, longitude = coords
        else:
            raise HTTPException(
                status_code=400,
                detail="GPS coordinates required. No EXIF GPS data found in photo.",
            )

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid GPS coordinates")

    category = user_override_category or "Other"
    service = ReportService(db)
    report = service.create_report(
        user_id=current_user.id,
        photo_bytes=photo_bytes,
        latitude=latitude,
        longitude=longitude,
        category=category,
        severity_score=5,
        ai_generated=False,
    )
    return _report_to_response(report)


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    category: Optional[str] = None,
    report_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all reports with optional filters."""
    service = ReportService(db)
    reports = service.get_reports_filtered(category=category, status=report_status)
    return [_report_to_response(r) for r in reports]


@router.get("/my", response_model=list[ReportResponse])
def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get reports submitted by the current user. Requirements: 12.5"""
    service = ReportService(db)
    reports = service.get_user_reports(current_user.id)
    return [_report_to_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single report by ID."""
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = ReportService(db)
    report = service.get_report(rid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.patch("/{report_id}/category", response_model=ReportResponse)
def update_category(
    report_id: str,
    data: ReportCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update report category (user override). Requirements: 2.6"""
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = ReportService(db)
    try:
        report = service.update_category(rid, data.category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)
