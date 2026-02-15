"""
Admin API endpoints for report management.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import ReportResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin/reports", tags=["Admin"])


class StatusUpdateRequest(BaseModel):
    status: str


class NoteRequest(BaseModel):
    note: str


class CategoryOverrideRequest(BaseModel):
    category: str


class SeverityAdjustRequest(BaseModel):
    severity: int


class NoteResponse(BaseModel):
    id: str
    report_id: str
    admin_id: str
    note: str
    created_at: str


class AuditLogResponse(BaseModel):
    id: str
    report_id: str
    admin_id: str
    action: str
    details: str | None
    created_at: str


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


@router.post("/{report_id}/status", response_model=ReportResponse)
def update_status(
    report_id: str,
    data: StatusUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update report status (admin only). Requirements: 9.2"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    try:
        report = service.update_report_status(rid, data.status, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.post("/{report_id}/notes", response_model=NoteResponse)
def add_note(
    report_id: str,
    data: NoteRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Add internal note to report (admin only). Requirements: 9.3"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    note = service.add_note(rid, data.note, admin.id)
    if not note:
        raise HTTPException(status_code=404, detail="Report not found")

    return NoteResponse(
        id=str(note.id),
        report_id=str(note.report_id),
        admin_id=str(note.admin_id),
        note=note.note,
        created_at=str(note.created_at),
    )


@router.patch("/{report_id}/category", response_model=ReportResponse)
def override_category(
    report_id: str,
    data: CategoryOverrideRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Override report category (admin only). Requirements: 9.4"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    try:
        report = service.override_category(rid, data.category, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.patch("/{report_id}/severity", response_model=ReportResponse)
def adjust_severity(
    report_id: str,
    data: SeverityAdjustRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Adjust report severity (admin only). Requirements: 9.5"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    try:
        report = service.adjust_severity(rid, data.severity, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.post("/{report_id}/archive", response_model=ReportResponse)
def archive_report(
    report_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Archive a report (admin only). Requirements: 9.6"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    report = service.archive_report(rid, admin.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.get("/{report_id}/audit", response_model=list[AuditLogResponse])
def get_audit_log(
    report_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get audit trail for a report (admin only). Requirements: 9.7"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    logs = service.get_audit_log(rid)
    return [
        AuditLogResponse(
            id=str(log.id),
            report_id=str(log.report_id),
            admin_id=str(log.admin_id),
            action=log.action,
            details=log.details,
            created_at=str(log.created_at),
        )
        for log in logs
    ]


@router.get("/{report_id}/notes", response_model=list[NoteResponse])
def get_notes(
    report_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get admin notes for a report (admin only). Requirements: 9.3"""
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = AdminService(db)
    notes = service.get_notes(rid)
    return [
        NoteResponse(
            id=str(n.id),
            report_id=str(n.report_id),
            admin_id=str(n.admin_id),
            note=n.note,
            created_at=str(n.created_at),
        )
        for n in notes
    ]
