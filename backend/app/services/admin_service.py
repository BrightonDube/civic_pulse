"""
Admin service for report management operations.

Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 4.3, 17.2
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.report import Report, VALID_CATEGORIES, VALID_STATUSES
from app.models.admin_note import AdminNote
from app.models.audit_log import AuditLog
from app.models.status_history import StatusHistory
from app.models.notification import Notification
from app.services.report_service import ReportService


class AdminService:
    """Service for admin operations on reports."""

    def __init__(self, db: Session):
        self.db = db
        self.report_service = ReportService(db)

    def _log_audit(
        self, report_id: uuid.UUID, admin_id: uuid.UUID, action: str, details: str = None
    ) -> AuditLog:
        """Create an audit log entry. Property 32: Admin Audit Logging."""
        entry = AuditLog(
            report_id=report_id,
            admin_id=admin_id,
            action=action,
            details=details,
        )
        self.db.add(entry)
        return entry

    def update_report_status(
        self, report_id: uuid.UUID, status: str, admin_id: uuid.UUID
    ) -> Optional[Report]:
        """
        Update report status with audit logging and notifications.
        Property 29: Admin Override Capabilities
        Requirements: 9.2, 4.3, 17.2
        """
        report = self.report_service.update_status(report_id, status, admin_id)
        if report:
            self._log_audit(report_id, admin_id, "status_update", f"Changed to {status}")
            
            # Create notification for report submitter
            notification = Notification(
                user_id=report.user_id,
                report_id=report_id,
                type="status_change",
                title="Report Status Updated",
                message=f"Your report status has been changed to: {status}",
                read=False,
            )
            self.db.add(notification)
            
            # Create notifications for upvoters
            upvoters = self.report_service.get_upvoters(report_id)
            for upvote in upvoters:
                if upvote.user_id != report.user_id:  # Don't duplicate notification for submitter
                    upvoter_notification = Notification(
                        user_id=upvote.user_id,
                        report_id=report_id,
                        type="status_change",
                        title="Upvoted Report Updated",
                        message=f"A report you upvoted has been updated to: {status}",
                        read=False,
                    )
                    self.db.add(upvoter_notification)
            
            self.db.commit()
        return report

    def add_note(
        self, report_id: uuid.UUID, note_text: str, admin_id: uuid.UUID
    ) -> Optional[AdminNote]:
        """
        Add internal note to a report.
        Property 30: Admin Note Creation
        Requirements: 9.3
        """
        report = self.report_service.get_report(report_id)
        if not report:
            return None

        note = AdminNote(
            report_id=report_id,
            admin_id=admin_id,
            note=note_text,
        )
        self.db.add(note)
        self._log_audit(report_id, admin_id, "add_note", note_text[:100])
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_notes(self, report_id: uuid.UUID) -> List[AdminNote]:
        """Get all admin notes for a report."""
        return (
            self.db.query(AdminNote)
            .filter(AdminNote.report_id == report_id)
            .order_by(AdminNote.created_at.asc())
            .all()
        )

    def override_category(
        self, report_id: uuid.UUID, category: str, admin_id: uuid.UUID
    ) -> Optional[Report]:
        """
        Admin override of report category.
        Property 29: Admin Override Capabilities
        Requirements: 9.4
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        report = self.report_service.get_report(report_id)
        if not report:
            return None

        old_category = report.category
        report.category = category
        report.ai_generated = False
        report.updated_at = datetime.now(timezone.utc)
        self._log_audit(
            report_id, admin_id, "category_override",
            f"{old_category} -> {category}"
        )
        self.db.commit()
        self.db.refresh(report)
        return report

    def adjust_severity(
        self, report_id: uuid.UUID, severity: int, admin_id: uuid.UUID
    ) -> Optional[Report]:
        """
        Admin adjustment of severity score.
        Property 29: Admin Override Capabilities
        Requirements: 9.5
        """
        if not (1 <= severity <= 10):
            raise ValueError("Severity must be between 1 and 10")

        report = self.report_service.get_report(report_id)
        if not report:
            return None

        old_severity = report.severity_score
        report.severity_score = severity
        report.updated_at = datetime.now(timezone.utc)
        self._log_audit(
            report_id, admin_id, "severity_adjust",
            f"{old_severity} -> {severity}"
        )
        self.db.commit()
        self.db.refresh(report)
        return report

    def archive_report(
        self, report_id: uuid.UUID, admin_id: uuid.UUID
    ) -> Optional[Report]:
        """
        Archive a report (typically after Fixed).
        Property 31: Report Archival
        Requirements: 9.6
        """
        report = self.report_service.get_report(report_id)
        if not report:
            return None

        report.archived = True
        report.updated_at = datetime.now(timezone.utc)
        self._log_audit(report_id, admin_id, "archive", "Report archived")
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_audit_log(self, report_id: uuid.UUID) -> List[AuditLog]:
        """Get full audit trail for a report. Requirements: 9.7"""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.report_id == report_id)
            .order_by(AuditLog.created_at.asc())
            .all()
        )
