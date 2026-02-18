"""
Report API endpoints.

Requirements: 1.4, 2.6, 11.2, 14.4, 19.1
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import ReportResponse, ReportCategoryUpdate, severity_to_color, ReportPhotoResponse
from app.schemas.comment import CommentCreate, CommentResponse, ThreadedCommentResponse
from app.services.report_service import ReportService
from app.services.comment_service import CommentService
from app.services.gps_service import extract_gps_from_exif
from app.services.ai_service import AIService
from app.services.duplicate_service import DuplicateDetectionService
from app.services.websocket_manager import manager

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
        color=severity_to_color(report.severity_score),
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
    additional_photos: Optional[list[UploadFile]] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    user_override_category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new report with photo(s) and location.
    Supports up to 5 photos with 25MB combined size limit.
    GPS is extracted from EXIF if not provided.
    Requirements: 1.1, 1.2, 1.4, 14.4, 19.1
    """
    photo_bytes = await photo.read()
    if not photo_bytes:
        raise HTTPException(status_code=400, detail="Photo is required")

    # Read additional photos if provided
    additional_photo_bytes = []
    if additional_photos:
        for add_photo in additional_photos:
            add_bytes = await add_photo.read()
            if add_bytes:
                additional_photo_bytes.append(add_bytes)

    # Validate photo count (up to 5 total)
    total_photos = 1 + len(additional_photo_bytes)
    if total_photos > 5:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum 5 photos allowed per report, received {total_photos}"
        )

    # Validate combined size (25MB limit)
    total_size = len(photo_bytes) + sum(len(p) for p in additional_photo_bytes)
    max_size_bytes = 25 * 1024 * 1024  # 25MB
    if total_size > max_size_bytes:
        size_mb = total_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Combined photo size ({size_mb:.2f}MB) exceeds 25MB limit"
        )

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

    # AI analysis (Req 2.1, 2.5)
    ai_service = AIService()
    analysis = ai_service.analyze_image(photo_bytes)

    # User override takes priority (Req 2.6)
    category = user_override_category or analysis.category
    severity_score = analysis.severity_score
    ai_generated = analysis.ai_generated and (user_override_category is None)

    # Duplicate detection (Req 5.1, 5.2)
    dup_service = DuplicateDetectionService(db)
    duplicate = dup_service.check_for_duplicates(latitude, longitude, category)
    if duplicate:
        return _report_to_response(duplicate)

    service = ReportService(db)
    try:
        report = service.create_report(
            user_id=current_user.id,
            photo_bytes=photo_bytes,
            latitude=latitude,
            longitude=longitude,
            category=category,
            severity_score=severity_score,
            ai_generated=ai_generated,
            additional_photos=additional_photo_bytes if additional_photo_bytes else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    response = _report_to_response(report)
    # Broadcast new report via WebSocket (Req 3.6)
    await manager.broadcast({"event": "new_report", "data": response.model_dump(mode="json")})
    return response


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    category: Optional[str] = None,
    report_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all reports with optional filters. Property 10 (Req 3.5)"""
    from datetime import datetime
    d_from = datetime.fromisoformat(date_from) if date_from else None
    d_to = datetime.fromisoformat(date_to) if date_to else None

    service = ReportService(db)
    reports = service.get_reports_filtered(
        category=category, status=report_status,
        date_from=d_from, date_to=d_to,
        min_lat=min_lat, max_lat=max_lat,
        min_lon=min_lon, max_lon=max_lon,
    )
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


@router.post("/{report_id}/upvote", response_model=ReportResponse)
def upvote_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upvote a report. Idempotent. Requirements: 5.3, 5.6"""
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = ReportService(db)
    report = service.add_upvote(rid, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)


@router.get("/nearby", response_model=list[ReportResponse])
def find_nearby_reports(
    latitude: float,
    longitude: float,
    radius: float = 50.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find reports near a location. Requirements: 5.1"""
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid GPS coordinates")

    dup_service = DuplicateDetectionService(db)
    reports = dup_service.find_nearby_reports(latitude, longitude, radius)
    return [_report_to_response(r) for r in reports]



@router.post("/{report_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    report_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a comment to a report.
    Supports threaded discussions via parent_comment_id.
    
    Requirements: 14.1, 14.2, 14.3
    """
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    # Parse parent_comment_id if provided
    parent_id = None
    if data.parent_comment_id:
        try:
            parent_id = _uuid.UUID(data.parent_comment_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent comment ID")

    service = CommentService(db)
    try:
        comment = service.create_comment(
            report_id=rid,
            user_id=current_user.id,
            text=data.text,
            parent_comment_id=parent_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CommentResponse(
        id=str(comment.id),
        report_id=str(comment.report_id),
        user_id=str(comment.user_id),
        parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
        text=comment.text,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/{report_id}/comments", response_model=list[CommentResponse])
def get_comments(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all comments for a report in chronological order.
    
    Requirements: 14.1 - Comments displayed in chronological order
    """
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = CommentService(db)
    comments = service.get_comments(rid)
    
    return [
        CommentResponse(
            id=str(c.id),
            report_id=str(c.report_id),
            user_id=str(c.user_id),
            parent_comment_id=str(c.parent_comment_id) if c.parent_comment_id else None,
            text=c.text,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.get("/{report_id}/comments/tree", response_model=list[ThreadedCommentResponse])
def get_comments_tree(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all comments for a report organized as a threaded tree structure.
    
    Top-level comments are returned at the root level, with replies nested
    under their parent comments in the 'replies' field.
    
    Requirements: 14.3 - Support threaded discussions
    """
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = CommentService(db)
    tree = service.build_comment_tree(rid)
    
    def convert_to_response(comment_dict):
        """Recursively convert comment dict to ThreadedCommentResponse."""
        return ThreadedCommentResponse(
            id=str(comment_dict["id"]),
            report_id=str(comment_dict["report_id"]),
            user_id=str(comment_dict["user_id"]),
            parent_comment_id=str(comment_dict["parent_comment_id"]) if comment_dict["parent_comment_id"] else None,
            text=comment_dict["text"],
            created_at=comment_dict["created_at"],
            updated_at=comment_dict["updated_at"],
            replies=[convert_to_response(reply) for reply in comment_dict["replies"]],
        )
    
    return [convert_to_response(comment) for comment in tree]


@router.get("/{report_id}/photos", response_model=list[ReportPhotoResponse])
def get_report_photos(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all photos for a report in upload order.
    
    Requirements: 14.4, 14.5 - Multiple photos with gallery ordering
    """
    import uuid as _uuid
    try:
        rid = _uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    service = ReportService(db)
    photos = service.get_report_photos(rid)
    
    return [
        ReportPhotoResponse(
            id=str(p.id),
            report_id=str(p.report_id),
            photo_url=p.photo_url,
            is_before_photo=p.is_before_photo,
            upload_order=p.upload_order,
            created_at=p.created_at,
        )
        for p in photos
    ]
