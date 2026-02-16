"""
Service for report creation, retrieval, and management.

Requirements: 1.4, 4.1, 2.6
"""
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.report import Report, VALID_CATEGORIES, VALID_STATUSES
from app.models.upvote import Upvote
from app.models.status_history import StatusHistory


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


class ReportService:
    """Service for managing infrastructure reports."""

    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        user_id: uuid.UUID,
        photo_bytes: bytes,
        latitude: float,
        longitude: float,
        category: str = "Other",
        severity_score: int = 5,
        ai_generated: bool = False,
    ) -> Report:
        """
        Create a new report. Sets initial status to 'Reported'.
        Requirements: 1.4, 4.1
        """
        _ensure_upload_dir()

        # Save photo to filesystem
        photo_filename = f"{uuid.uuid4()}.jpg"
        photo_path = os.path.join(UPLOAD_DIR, photo_filename)
        try:
            with open(photo_path, "wb") as f:
                f.write(photo_bytes)
        except OSError as e:
            raise RuntimeError(f"Failed to save photo: {e}") from e

        photo_url = f"/uploads/{photo_filename}"

        report = Report(
            user_id=user_id,
            photo_url=photo_url,
            latitude=latitude,
            longitude=longitude,
            category=category,
            severity_score=severity_score,
            status="Reported",
            ai_generated=ai_generated,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # Increment user report count
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.report_count += 1
            self.db.commit()

        return report

    def get_report(self, report_id: uuid.UUID) -> Optional[Report]:
        """Get a single report by ID."""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_user_reports(self, user_id: uuid.UUID) -> List[Report]:
        """Get all reports for a user. Requirements: 12.5"""
        return (
            self.db.query(Report)
            .filter(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .all()
        )

    def update_category(
        self, report_id: uuid.UUID, category: str
    ) -> Optional[Report]:
        """
        Update report category (user override).
        Requirements: 2.6
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        report = self.get_report(report_id)
        if not report:
            return None

        report.category = category
        report.ai_generated = False
        report.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports_filtered(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        include_archived: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> List[Report]:
        """
        Get reports with optional filters including date range and bounding box.
        Property 10: Report Filtering (Req 3.5)
        """
        query = self.db.query(Report)

        if not include_archived:
            query = query.filter(Report.archived == False)
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)

        return query.order_by(Report.created_at.desc()).all()

    def add_upvote(self, report_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Report]:
        """
        Upvote a report. Idempotent: duplicate upvotes are ignored.
        Property 17: Upvote Idempotency
        Requirements: 5.3, 5.6
        """
        report = self.get_report(report_id)
        if not report:
            return None

        existing = (
            self.db.query(Upvote)
            .filter(Upvote.report_id == report_id, Upvote.user_id == user_id)
            .first()
        )
        if existing:
            return report  # Already upvoted, idempotent

        upvote = Upvote(report_id=report_id, user_id=user_id)
        self.db.add(upvote)
        report.upvote_count += 1
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_upvoters(self, report_id: uuid.UUID) -> List:
        """Get all users who upvoted a report (for notifications). Req 5.4"""
        return (
            self.db.query(Upvote)
            .filter(Upvote.report_id == report_id)
            .all()
        )

    def update_status(
        self, report_id: uuid.UUID, new_status: str, changed_by: uuid.UUID
    ) -> Optional[Report]:
        """
        Update report status and create history entry.
        Property 12: Status Update Persistence
        Property 14: Status History Logging
        Requirements: 4.2, 4.6
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        report = self.get_report(report_id)
        if not report:
            return None

        old_status = report.status
        if old_status == new_status:
            return report

        history = StatusHistory(
            report_id=report_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
        )
        self.db.add(history)

        report.status = new_status
        report.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_status_history(self, report_id: uuid.UUID) -> List[StatusHistory]:
        """Get full status history for a report. Requirements: 4.6"""
        return (
            self.db.query(StatusHistory)
            .filter(StatusHistory.report_id == report_id)
            .order_by(StatusHistory.changed_at.asc())
            .all()
        )
