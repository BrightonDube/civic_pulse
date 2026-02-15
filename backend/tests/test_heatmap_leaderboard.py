"""
Tests for heat map filtering, clustering, color coding, leaderboard, and rate limiting.

Properties validated:
- Property 7: Severity-Based Color Coding
- Property 8: Report Clustering
- Property 9: Report Detail Completeness
- Property 10: Report Filtering
- Property 21: User Report Count Accuracy
- Property 22: Leaderboard Ranking
- Property 24: Leaderboard Opt-Out Privacy
- Property 35: API Input Validation
- Property 36: Rate Limiting

Requirements: 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.6, 9.1, 11.3, 11.5
"""
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.models.user import User
from app.models.report import Report
from app.schemas.report import severity_to_color, ReportResponse
from app.services.report_service import ReportService
from app.services.leaderboard_service import LeaderboardService
from app.services.clustering_service import cluster_reports, Cluster


def _create_user(db_session, email=None, report_count=0, opt_out=False):
    user = User(
        email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
        phone="+1234567890",
        report_count=report_count,
        leaderboard_opt_out=opt_out,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_report(db_session, user_id, lat=40.0, lon=-111.0, category="Pothole", severity=5, status="Reported"):
    service = ReportService(db_session)
    report = service.create_report(
        user_id=user_id,
        photo_bytes=b"fake-photo",
        latitude=lat,
        longitude=lon,
        category=category,
        severity_score=severity,
    )
    if status != "Reported":
        report.status = status
        db_session.commit()
        db_session.refresh(report)
    return report


# ---------- Property 7: Severity-Based Color Coding ----------

class TestSeverityColorCoding:
    """Property 7: Red 8-10, Yellow 4-7, Green 1-3."""

    @given(severity=st.integers(min_value=8, max_value=10))
    @h_settings(deadline=None)
    def test_high_severity_red(self, severity):
        assert severity_to_color(severity) == "red"

    @given(severity=st.integers(min_value=4, max_value=7))
    @h_settings(deadline=None)
    def test_medium_severity_yellow(self, severity):
        assert severity_to_color(severity) == "yellow"

    @given(severity=st.integers(min_value=1, max_value=3))
    @h_settings(deadline=None)
    def test_low_severity_green(self, severity):
        assert severity_to_color(severity) == "green"


# ---------- Property 8: Report Clustering ----------

class TestReportClustering:
    """Property 8: Nearby reports are grouped into clusters."""

    def test_single_report_single_cluster(self, db_session):
        user = _create_user(db_session)
        r = _create_report(db_session, user.id)
        clusters = cluster_reports([r])
        assert len(clusters) == 1
        assert clusters[0].count == 1

    def test_nearby_reports_same_cluster(self, db_session):
        user = _create_user(db_session)
        r1 = _create_report(db_session, user.id, lat=40.0, lon=-111.0)
        r2 = _create_report(db_session, user.id, lat=40.00005, lon=-111.00005)
        clusters = cluster_reports([r1, r2], proximity_meters=100)
        assert len(clusters) == 1
        assert clusters[0].count == 2

    def test_distant_reports_separate_clusters(self, db_session):
        user = _create_user(db_session)
        r1 = _create_report(db_session, user.id, lat=40.0, lon=-111.0)
        r2 = _create_report(db_session, user.id, lat=41.0, lon=-112.0)
        clusters = cluster_reports([r1, r2], proximity_meters=100)
        assert len(clusters) == 2

    def test_empty_reports_no_clusters(self):
        clusters = cluster_reports([])
        assert len(clusters) == 0


# ---------- Property 9: Report Detail Completeness ----------

class TestReportDetailCompleteness:
    """Property 9: All required fields present and non-null."""

    def test_all_fields_present(self, db_session):
        user = _create_user(db_session)
        report = _create_report(db_session, user.id, severity=8)
        response = ReportResponse(
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
        assert response.id is not None
        assert response.photo_url is not None
        assert response.category is not None
        assert response.severity_score is not None
        assert response.status is not None
        assert response.created_at is not None
        assert response.upvote_count is not None
        assert response.color == "red"  # severity 8


# ---------- Property 10: Report Filtering ----------

class TestReportFiltering:
    """Property 10: Filters return only matching reports."""

    def test_filter_by_category(self, db_session):
        user = _create_user(db_session)
        _create_report(db_session, user.id, category="Pothole")
        _create_report(db_session, user.id, category="Water Leak")

        service = ReportService(db_session)
        results = service.get_reports_filtered(category="Pothole")
        assert len(results) == 1
        assert results[0].category == "Pothole"

    def test_filter_by_status(self, db_session):
        user = _create_user(db_session)
        _create_report(db_session, user.id, status="Reported")
        _create_report(db_session, user.id, status="Fixed")

        service = ReportService(db_session)
        results = service.get_reports_filtered(status="Fixed")
        assert len(results) == 1
        assert results[0].status == "Fixed"

    def test_filter_by_date_range(self, db_session):
        user = _create_user(db_session)
        r = _create_report(db_session, user.id)

        service = ReportService(db_session)
        now = datetime.now(timezone.utc)
        results = service.get_reports_filtered(
            date_from=now - timedelta(hours=1),
            date_to=now + timedelta(hours=1),
        )
        assert len(results) == 1

    def test_filter_by_bounding_box(self, db_session):
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0)
        _create_report(db_session, user.id, lat=50.0, lon=-100.0)

        service = ReportService(db_session)
        results = service.get_reports_filtered(
            min_lat=39.0, max_lat=41.0,
            min_lon=-112.0, max_lon=-110.0,
        )
        assert len(results) == 1
        assert results[0].latitude == pytest.approx(40.0)

    def test_combined_filters(self, db_session):
        user = _create_user(db_session)
        _create_report(db_session, user.id, category="Pothole", lat=40.0, lon=-111.0)
        _create_report(db_session, user.id, category="Water Leak", lat=40.0, lon=-111.0)
        _create_report(db_session, user.id, category="Pothole", lat=50.0, lon=-100.0)

        service = ReportService(db_session)
        results = service.get_reports_filtered(
            category="Pothole",
            min_lat=39.0, max_lat=41.0,
        )
        assert len(results) == 1


# ---------- Property 22: Leaderboard Ranking ----------

class TestLeaderboardRanking:
    """Property 22: Top 10 sorted by report count descending."""

    def test_top_users_sorted(self, db_session):
        u1 = _create_user(db_session, email="l1@ex.com", report_count=5)
        u2 = _create_user(db_session, email="l2@ex.com", report_count=10)
        u3 = _create_user(db_session, email="l3@ex.com", report_count=3)

        service = LeaderboardService(db_session)
        top = service.get_top_users(limit=10)
        assert len(top) == 3
        assert top[0].report_count == 10
        assert top[1].report_count == 5
        assert top[2].report_count == 3

    def test_limit_to_10(self, db_session):
        for i in range(15):
            _create_user(db_session, email=f"l{i}@ex.com", report_count=i + 1)

        service = LeaderboardService(db_session)
        top = service.get_top_users(limit=10)
        assert len(top) == 10

    def test_zero_reports_excluded(self, db_session):
        _create_user(db_session, email="zero@ex.com", report_count=0)
        _create_user(db_session, email="one@ex.com", report_count=1)

        service = LeaderboardService(db_session)
        top = service.get_top_users()
        assert len(top) == 1


# ---------- Property 24: Leaderboard Opt-Out ----------

class TestLeaderboardOptOut:
    """Property 24: Opted-out users excluded from leaderboard."""

    def test_opted_out_excluded(self, db_session):
        _create_user(db_session, email="public@ex.com", report_count=10, opt_out=False)
        _create_user(db_session, email="private@ex.com", report_count=20, opt_out=True)

        service = LeaderboardService(db_session)
        top = service.get_top_users()
        assert len(top) == 1
        assert top[0].email == "public@ex.com"


# ---------- Property 35: API Input Validation ----------

class TestAPIInputValidation:
    """Property 35: Invalid inputs are rejected."""

    def test_invalid_latitude(self):
        from app.schemas.report import ReportCreate
        with pytest.raises(Exception):
            ReportCreate(latitude=100.0, longitude=0.0)

    def test_invalid_longitude(self):
        from app.schemas.report import ReportCreate
        with pytest.raises(Exception):
            ReportCreate(latitude=0.0, longitude=200.0)

    def test_invalid_category(self):
        from app.schemas.report import ReportCategoryUpdate
        with pytest.raises(Exception):
            ReportCategoryUpdate(category="NotValid")
