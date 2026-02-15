"""
Tests for report status tracking and notifications.

Properties validated:
- Property 12: Status Update Persistence
- Property 13: Status Change Notifications
- Property 14: Status History Logging

Requirements: 4.2, 4.3, 4.4, 4.6, 5.4
"""
import uuid

import pytest

from app.models.user import User
from app.models.report import VALID_STATUSES
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService


def _create_user(db_session, email=None, phone="+1234567890"):
    user = User(
        email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
        phone=phone,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_report(db_session, user_id):
    service = ReportService(db_session)
    return service.create_report(
        user_id=user_id,
        photo_bytes=b"fake-photo",
        latitude=40.0,
        longitude=-111.0,
        category="Pothole",
        severity_score=5,
    )


# ---------- Property 12: Status Update Persistence ----------

class TestStatusUpdatePersistence:
    """Property 12: Status changes are stored and retrievable."""

    def test_update_status_reported_to_in_progress(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)
        assert report.status == "Reported"

        service = ReportService(db_session)
        updated = service.update_status(report.id, "In Progress", admin.id)
        assert updated.status == "In Progress"

        # Verify persistence
        fetched = service.get_report(report.id)
        assert fetched.status == "In Progress"

    def test_update_status_in_progress_to_fixed(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        service.update_status(report.id, "In Progress", admin.id)
        updated = service.update_status(report.id, "Fixed", admin.id)
        assert updated.status == "Fixed"

    def test_invalid_status_raises(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        with pytest.raises(ValueError, match="Invalid status"):
            service.update_status(report.id, "Invalid", admin.id)

    def test_same_status_no_op(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        updated = service.update_status(report.id, "Reported", admin.id)
        assert updated.status == "Reported"
        # No history entry for same-status update
        history = service.get_status_history(report.id)
        assert len(history) == 0

    def test_update_nonexistent_report(self, db_session):
        user = _create_user(db_session)
        service = ReportService(db_session)
        result = service.update_status(uuid.uuid4(), "In Progress", user.id)
        assert result is None


# ---------- Property 14: Status History Logging ----------

class TestStatusHistoryLogging:
    """Property 14: History entry created for every status change."""

    def test_single_status_change_creates_history(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        service.update_status(report.id, "In Progress", admin.id)

        history = service.get_status_history(report.id)
        assert len(history) == 1
        assert history[0].old_status == "Reported"
        assert history[0].new_status == "In Progress"
        assert str(history[0].changed_by) == str(admin.id)
        assert history[0].changed_at is not None

    def test_multiple_status_changes_create_history(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        service.update_status(report.id, "In Progress", admin.id)
        service.update_status(report.id, "Fixed", admin.id)

        history = service.get_status_history(report.id)
        assert len(history) == 2
        assert history[0].old_status == "Reported"
        assert history[0].new_status == "In Progress"
        assert history[1].old_status == "In Progress"
        assert history[1].new_status == "Fixed"

    def test_history_preserves_admin_id(self, db_session):
        user = _create_user(db_session)
        admin1 = _create_user(db_session, email="admin1@example.com")
        admin2 = _create_user(db_session, email="admin2@example.com")
        report = _create_report(db_session, user.id)

        service = ReportService(db_session)
        service.update_status(report.id, "In Progress", admin1.id)
        service.update_status(report.id, "Fixed", admin2.id)

        history = service.get_status_history(report.id)
        assert str(history[0].changed_by) == str(admin1.id)
        assert str(history[1].changed_by) == str(admin2.id)


# ---------- Property 13: Status Change Notifications ----------

class TestStatusChangeNotifications:
    """Property 13: Email and SMS sent on status change."""

    def test_notify_submitter_email_and_sms(self):
        ns = NotificationService()
        ns.notify_status_change(
            report_id="r1",
            new_status="In Progress",
            submitter_email="user@example.com",
            submitter_phone="+1234567890",
        )
        assert len(ns.sent_notifications) == 2
        types = {n["type"] for n in ns.sent_notifications}
        assert types == {"email", "sms"}

    def test_notify_submitter_email_only_no_phone(self):
        ns = NotificationService()
        ns.notify_status_change(
            report_id="r1",
            new_status="Fixed",
            submitter_email="user@example.com",
            submitter_phone=None,
        )
        assert len(ns.sent_notifications) == 1
        assert ns.sent_notifications[0]["type"] == "email"

    def test_notify_upvoters_too(self):
        """Upvoters also receive notifications (Req 5.4)."""
        ns = NotificationService()
        ns.notify_status_change(
            report_id="r1",
            new_status="Fixed",
            submitter_email="user@example.com",
            submitter_phone="+1000000000",
            upvoter_emails=["v1@example.com", "v2@example.com"],
            upvoter_phones=["+1111111111", "+2222222222"],
        )
        # 1 email + 1 sms (submitter) + 2 emails + 2 sms (upvoters) = 6
        assert len(ns.sent_notifications) == 6

    def test_notification_contains_status(self):
        ns = NotificationService()
        ns.notify_status_change(
            report_id="r1",
            new_status="Fixed",
            submitter_email="user@example.com",
            submitter_phone=None,
        )
        assert "Fixed" in ns.sent_notifications[0]["subject"]
        assert "Fixed" in ns.sent_notifications[0]["body"]
