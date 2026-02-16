"""
Tests for duplicate detection service and upvoting.

Properties validated:
- Property 15: Spatial Search Within Radius
- Property 16: Duplicate Detection
- Property 17: Upvote Idempotency

Requirements: 5.1, 5.2, 5.3, 5.6
"""
import uuid

import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st

from app.models.user import User
from app.models.report import Report
from app.services.duplicate_service import DuplicateDetectionService
from app.services.report_service import ReportService


def _create_user(db_session, email=None):
    """Helper to create a test user."""
    user = User(
        email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$LJ3m4ys3Lzgqoif3gk3sYuTTqXlPYRBJOT9.XCNpiKkVfMCfuIELe",
        phone="+1234567890",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_report(db_session, user_id, lat=40.0, lon=-111.0, category="Pothole"):
    """Helper to create a test report directly."""
    service = ReportService(db_session)
    return service.create_report(
        user_id=user_id,
        photo_bytes=b"fake-photo",
        latitude=lat,
        longitude=lon,
        category=category,
        severity_score=5,
    )


# ---------- Property 15: Spatial Search Within Radius ----------

class TestSpatialSearch:
    """Property 15: Spatial search returns reports within radius."""

    def test_find_report_within_radius(self, db_session):
        """A report 10m away is found within 50m radius."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0)

        service = DuplicateDetectionService(db_session)
        # ~11m north of (40.0, -111.0)
        nearby = service.find_nearby_reports(40.0001, -111.0, radius_meters=50)
        assert len(nearby) == 1

    def test_report_outside_radius_not_found(self, db_session):
        """A report 1km away is NOT found within 50m radius."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0)

        service = DuplicateDetectionService(db_session)
        # ~1km north
        nearby = service.find_nearby_reports(40.009, -111.0, radius_meters=50)
        assert len(nearby) == 0

    def test_find_multiple_nearby_reports(self, db_session):
        """Multiple reports within radius are all found."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0)
        _create_report(db_session, user.id, lat=40.00005, lon=-111.00005, category="Water Leak")

        service = DuplicateDetectionService(db_session)
        nearby = service.find_nearby_reports(40.0, -111.0, radius_meters=50)
        assert len(nearby) == 2

    def test_archived_reports_excluded(self, db_session):
        """Archived reports are not returned by spatial search."""
        user = _create_user(db_session)
        report = _create_report(db_session, user.id, lat=40.0, lon=-111.0)
        report.archived = True
        db_session.commit()

        service = DuplicateDetectionService(db_session)
        nearby = service.find_nearby_reports(40.0, -111.0, radius_meters=50)
        assert len(nearby) == 0

    def test_exact_same_location(self, db_session):
        """A report at the exact same coordinates is found."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0)

        service = DuplicateDetectionService(db_session)
        nearby = service.find_nearby_reports(40.0, -111.0, radius_meters=50)
        assert len(nearby) == 1


# ---------- Haversine Distance ----------

class TestHaversineDistance:
    """Test distance calculation accuracy."""

    def test_same_point_distance_zero(self):
        d = DuplicateDetectionService.calculate_distance(40.0, -111.0, 40.0, -111.0)
        assert d == 0.0

    def test_known_distance(self):
        """~111km between 1 degree latitude at equator."""
        d = DuplicateDetectionService.calculate_distance(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 112_000

    @given(
        lat=st.floats(min_value=-89.9, max_value=89.9),
        lon=st.floats(min_value=-179.9, max_value=179.9),
    )
    @h_settings(deadline=None)
    def test_distance_to_self_is_zero(self, lat, lon):
        d = DuplicateDetectionService.calculate_distance(lat, lon, lat, lon)
        assert abs(d) < 0.001


# ---------- Property 16: Duplicate Detection ----------

class TestDuplicateDetection:
    """Property 16: Duplicate detection finds same-category reports nearby."""

    def test_duplicate_found_same_category_nearby(self, db_session):
        """Same category within 50m is detected as duplicate."""
        user = _create_user(db_session)
        original = _create_report(db_session, user.id, lat=40.0, lon=-111.0, category="Pothole")

        service = DuplicateDetectionService(db_session)
        dup = service.check_for_duplicates(40.00001, -111.0, "Pothole")
        assert dup is not None
        assert str(dup.id) == str(original.id)

    def test_no_duplicate_different_category(self, db_session):
        """Different category within 50m is NOT a duplicate."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0, category="Pothole")

        service = DuplicateDetectionService(db_session)
        dup = service.check_for_duplicates(40.00001, -111.0, "Water Leak")
        assert dup is None

    def test_no_duplicate_same_category_far(self, db_session):
        """Same category but >50m away is NOT a duplicate."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0, category="Pothole")

        service = DuplicateDetectionService(db_session)
        dup = service.check_for_duplicates(40.01, -111.0, "Pothole")
        assert dup is None

    def test_returns_closest_duplicate(self, db_session):
        """When multiple duplicates exist, returns the closest one."""
        user = _create_user(db_session)
        _create_report(db_session, user.id, lat=40.0, lon=-111.0, category="Pothole")
        closer = _create_report(db_session, user.id, lat=40.00002, lon=-111.0, category="Pothole")

        service = DuplicateDetectionService(db_session)
        dup = service.check_for_duplicates(40.00003, -111.0, "Pothole")
        assert dup is not None
        assert str(dup.id) == str(closer.id)


# ---------- Property 17: Upvote Idempotency ----------

class TestUpvoteIdempotency:
    """Property 17: Upvoting same report multiple times = one upvote."""

    def test_first_upvote_increments(self, db_session):
        """First upvote increments count by 1."""
        user = _create_user(db_session)
        report = _create_report(db_session, user.id)
        assert report.upvote_count == 0

        voter = _create_user(db_session, email="voter@example.com")
        service = ReportService(db_session)
        updated = service.add_upvote(report.id, voter.id)
        assert updated.upvote_count == 1

    def test_duplicate_upvote_is_idempotent(self, db_session):
        """Second upvote by same user does NOT increment count."""
        user = _create_user(db_session)
        report = _create_report(db_session, user.id)

        voter = _create_user(db_session, email="voter2@example.com")
        service = ReportService(db_session)
        service.add_upvote(report.id, voter.id)
        updated = service.add_upvote(report.id, voter.id)
        assert updated.upvote_count == 1

    def test_different_users_can_upvote(self, db_session):
        """Different users each add 1 upvote."""
        user = _create_user(db_session)
        report = _create_report(db_session, user.id)

        voter1 = _create_user(db_session, email="v1@example.com")
        voter2 = _create_user(db_session, email="v2@example.com")
        service = ReportService(db_session)
        service.add_upvote(report.id, voter1.id)
        updated = service.add_upvote(report.id, voter2.id)
        assert updated.upvote_count == 2

    def test_upvote_nonexistent_report(self, db_session):
        """Upvoting a non-existent report returns None."""
        user = _create_user(db_session)
        service = ReportService(db_session)
        result = service.add_upvote(uuid.uuid4(), user.id)
        assert result is None

    def test_get_upvoters(self, db_session):
        """get_upvoters returns all upvote records for notification."""
        user = _create_user(db_session)
        report = _create_report(db_session, user.id)

        voter1 = _create_user(db_session, email="uv1@example.com")
        voter2 = _create_user(db_session, email="uv2@example.com")
        service = ReportService(db_session)
        service.add_upvote(report.id, voter1.id)
        service.add_upvote(report.id, voter2.id)

        upvoters = service.get_upvoters(report.id)
        assert len(upvoters) == 2
        user_ids = {str(u.user_id) for u in upvoters}
        assert str(voter1.id) in user_ids
        assert str(voter2.id) in user_ids
