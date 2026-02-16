"""
Tests for admin dashboard functionality.

Properties validated:
- Property 29: Admin Override Capabilities
- Property 30: Admin Note Creation
- Property 31: Report Archival
- Property 32: Admin Audit Logging

Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
"""
import uuid

import pytest

from app.models.user import User
from app.models.report import VALID_CATEGORIES
from app.services.admin_service import AdminService
from app.services.report_service import ReportService


def _create_user(db_session, email=None, role="user"):
    user = User(
        email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
        phone="+1234567890",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_report(db_session, user_id, category="Pothole", severity=5):
    service = ReportService(db_session)
    return service.create_report(
        user_id=user_id,
        photo_bytes=b"fake-photo",
        latitude=40.0,
        longitude=-111.0,
        category=category,
        severity_score=severity,
        ai_generated=True,
    )


# ---------- Property 29: Admin Override Capabilities ----------

class TestAdminOverrides:
    """Property 29: Admin can override status, category, severity."""

    def test_admin_update_status(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        updated = service.update_report_status(report.id, "In Progress", admin.id)
        assert updated.status == "In Progress"

    def test_admin_override_category(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id, category="Pothole")

        service = AdminService(db_session)
        updated = service.override_category(report.id, "Vandalism", admin.id)
        assert updated.category == "Vandalism"
        assert updated.ai_generated is False

    def test_admin_adjust_severity(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id, severity=5)

        service = AdminService(db_session)
        updated = service.adjust_severity(report.id, 9, admin.id)
        assert updated.severity_score == 9

    def test_invalid_category_raises(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        with pytest.raises(ValueError, match="Invalid category"):
            service.override_category(report.id, "NotACategory", admin.id)

    def test_invalid_severity_raises(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        with pytest.raises(ValueError, match="Severity must be"):
            service.adjust_severity(report.id, 11, admin.id)

    def test_override_nonexistent_report(self, db_session):
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        service = AdminService(db_session)
        assert service.override_category(uuid.uuid4(), "Pothole", admin.id) is None
        assert service.adjust_severity(uuid.uuid4(), 5, admin.id) is None


# ---------- Property 30: Admin Note Creation ----------

class TestAdminNoteCreation:
    """Property 30: Admin notes are created and retrievable."""

    def test_add_note(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        note = service.add_note(report.id, "Dispatched crew to location", admin.id)
        assert note is not None
        assert note.note == "Dispatched crew to location"
        assert str(note.admin_id) == str(admin.id)

    def test_multiple_notes(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.add_note(report.id, "Note 1", admin.id)
        service.add_note(report.id, "Note 2", admin.id)

        notes = service.get_notes(report.id)
        assert len(notes) == 2

    def test_add_note_nonexistent_report(self, db_session):
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        service = AdminService(db_session)
        note = service.add_note(uuid.uuid4(), "Should fail", admin.id)
        assert note is None


# ---------- Property 31: Report Archival ----------

class TestReportArchival:
    """Property 31: Archived reports excluded from active queries."""

    def test_archive_report(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)
        assert report.archived is False

        service = AdminService(db_session)
        archived = service.archive_report(report.id, admin.id)
        assert archived.archived is True

    def test_archived_excluded_from_active(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        admin_service = AdminService(db_session)
        admin_service.archive_report(report.id, admin.id)

        report_service = ReportService(db_session)
        active = report_service.get_reports_filtered(include_archived=False)
        assert len(active) == 0

    def test_archived_included_when_requested(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        admin_service = AdminService(db_session)
        admin_service.archive_report(report.id, admin.id)

        report_service = ReportService(db_session)
        all_reports = report_service.get_reports_filtered(include_archived=True)
        assert len(all_reports) == 1

    def test_archive_nonexistent(self, db_session):
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        service = AdminService(db_session)
        assert service.archive_report(uuid.uuid4(), admin.id) is None


# ---------- Property 32: Admin Audit Logging ----------

class TestAdminAuditLogging:
    """Property 32: All admin actions create audit entries."""

    def test_status_update_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.update_report_status(report.id, "In Progress", admin.id)

        logs = service.get_audit_log(report.id)
        assert len(logs) == 1
        assert logs[0].action == "status_update"
        assert str(logs[0].admin_id) == str(admin.id)

    def test_category_override_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.override_category(report.id, "Vandalism", admin.id)

        logs = service.get_audit_log(report.id)
        assert any(l.action == "category_override" for l in logs)

    def test_severity_adjust_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.adjust_severity(report.id, 9, admin.id)

        logs = service.get_audit_log(report.id)
        assert any(l.action == "severity_adjust" for l in logs)

    def test_note_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.add_note(report.id, "Test note", admin.id)

        logs = service.get_audit_log(report.id)
        assert any(l.action == "add_note" for l in logs)

    def test_archive_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.archive_report(report.id, admin.id)

        logs = service.get_audit_log(report.id)
        assert any(l.action == "archive" for l in logs)

    def test_multiple_actions_all_logged(self, db_session):
        user = _create_user(db_session)
        admin = _create_user(db_session, email="admin@ex.com", role="admin")
        report = _create_report(db_session, user.id)

        service = AdminService(db_session)
        service.update_report_status(report.id, "In Progress", admin.id)
        service.override_category(report.id, "Water Leak", admin.id)
        service.adjust_severity(report.id, 8, admin.id)
        service.add_note(report.id, "Investigated", admin.id)
        service.archive_report(report.id, admin.id)

        logs = service.get_audit_log(report.id)
        assert len(logs) == 5
        actions = {l.action for l in logs}
        assert actions == {"status_update", "category_override", "severity_adjust", "add_note", "archive"}
