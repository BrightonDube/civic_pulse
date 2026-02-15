"""
Service for report creation, retrieval, and management.

Requirements: 1.4, 4.1, 2.6
"""
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.report import Report, VALID_CATEGORIES


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
        with open(photo_path, "wb") as f:
            f.write(photo_bytes)

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
    ) -> List[Report]:
        """Get reports with optional filters."""
        query = self.db.query(Report)

        if not include_archived:
            query = query.filter(Report.archived == False)
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)

        return query.order_by(Report.created_at.desc()).all()
