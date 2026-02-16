"""
Tests for ReportService - report creation, retrieval, and category update.

Properties 3, 5, 6, 11
Requirements: 1.4, 2.5, 2.6, 4.1
"""
import os
import uuid
import shutil
import pytest
from hypothesis import given, settings as h_settings, strategies as st, HealthCheck

from app.models.user import User
from app.models.report import Report, VALID_CATEGORIES
from app.services.report_service import ReportService


@pytest.fixture(autouse=True)
def _cleanup_uploads():
    """Clean up test upload directory."""
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    yield
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir, ignore_errors=True)


def _create_test_user(db_session, email="test@example.com") -> User:
    user = User(email=email, phone="+1234567890")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _minimal_jpeg() -> bytes:
    """Create minimal valid JPEG bytes for testing."""
    from PIL import Image
    import io
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_create_report(db_session):
    """Test basic report creation. Property 3: Report Data Persistence"""
    user = _create_test_user(db_session)
    service = ReportService(db_session)

    report = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=40.7128,
        longitude=-74.0060,
        category="Pothole",
        severity_score=7,
    )

    assert report.id is not None
    assert report.user_id == user.id
    assert report.latitude == 40.7128
    assert report.longitude == -74.0060
    assert report.category == "Pothole"
    assert report.severity_score == 7
    assert report.photo_url.startswith("/uploads/")


def test_initial_status_is_reported(db_session):
    """Property 11: Initial Report Status - always 'Reported'."""
    user = _create_test_user(db_session)
    service = ReportService(db_session)

    report = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=0.0,
        longitude=0.0,
    )

    assert report.status == "Reported"


def test_report_persistence_round_trip(db_session):
    """Property 3: Report Data Persistence Round Trip."""
    user = _create_test_user(db_session)
    service = ReportService(db_session)

    created = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=51.5074,
        longitude=-0.1278,
        category="Water Leak",
        severity_score=8,
    )

    retrieved = service.get_report(created.id)
    assert retrieved is not None
    assert retrieved.latitude == 51.5074
    assert retrieved.longitude == -0.1278
    assert retrieved.category == "Water Leak"
    assert retrieved.severity_score == 8
    assert retrieved.status == "Reported"


def test_user_category_override(db_session):
    """Property 6: User Category Override."""
    user = _create_test_user(db_session)
    service = ReportService(db_session)

    report = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=0.0,
        longitude=0.0,
        category="Other",
        ai_generated=True,
    )

    assert report.ai_generated is True

    updated = service.update_category(report.id, "Pothole")
    assert updated.category == "Pothole"
    assert updated.ai_generated is False


def test_get_user_reports(db_session):
    """Test filtering reports by user. Property 38."""
    user1 = _create_test_user(db_session, "user1@test.com")
    user2 = _create_test_user(db_session, "user2@test.com")
    service = ReportService(db_session)

    # Create reports for both users
    service.create_report(user_id=user1.id, photo_bytes=_minimal_jpeg(), latitude=0, longitude=0)
    service.create_report(user_id=user1.id, photo_bytes=_minimal_jpeg(), latitude=1, longitude=1)
    service.create_report(user_id=user2.id, photo_bytes=_minimal_jpeg(), latitude=2, longitude=2)

    user1_reports = service.get_user_reports(user1.id)
    user2_reports = service.get_user_reports(user2.id)

    assert len(user1_reports) == 2
    assert len(user2_reports) == 1
    assert all(r.user_id == user1.id for r in user1_reports)


def test_report_count_incremented(db_session):
    """Property 21: User Report Count Accuracy."""
    user = _create_test_user(db_session)
    service = ReportService(db_session)

    assert user.report_count == 0
    service.create_report(user_id=user.id, photo_bytes=_minimal_jpeg(), latitude=0, longitude=0)
    db_session.refresh(user)
    assert user.report_count == 1

    service.create_report(user_id=user.id, photo_bytes=_minimal_jpeg(), latitude=1, longitude=1)
    db_session.refresh(user)
    assert user.report_count == 2


def test_photo_stored_and_retrievable(db_session):
    """Property 33: Photo Storage and Retrieval."""
    user = _create_test_user(db_session)
    service = ReportService(db_session)
    photo_data = _minimal_jpeg()

    report = service.create_report(
        user_id=user.id,
        photo_bytes=photo_data,
        latitude=0.0,
        longitude=0.0,
    )

    # Photo URL should be valid
    assert report.photo_url.startswith("/uploads/")
    
    # File should exist on disk
    file_path = report.photo_url.lstrip("/")
    assert os.path.exists(file_path)
    
    # File content should match
    with open(file_path, "rb") as f:
        stored_data = f.read()
    assert stored_data == photo_data


@h_settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
    lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    category=st.sampled_from(VALID_CATEGORIES),
    severity=st.integers(min_value=1, max_value=10),
)
def test_report_persistence_property(db_session, lat, lon, category, severity):
    """Property 3: Report Data Persistence Round Trip (property-based)."""
    user = _create_test_user(db_session, f"prop_{uuid.uuid4().hex[:8]}@test.com")
    service = ReportService(db_session)

    report = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=lat,
        longitude=lon,
        category=category,
        severity_score=severity,
    )

    retrieved = service.get_report(report.id)
    assert retrieved is not None
    assert retrieved.latitude == lat
    assert retrieved.longitude == lon
    assert retrieved.category == category
    assert retrieved.severity_score == severity
    assert retrieved.status == "Reported"


@h_settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(category=st.sampled_from(VALID_CATEGORIES))
def test_category_override_property(db_session, category):
    """Property 6: User Category Override (property-based)."""
    user = _create_test_user(db_session, f"override_{uuid.uuid4().hex[:8]}@test.com")
    service = ReportService(db_session)

    report = service.create_report(
        user_id=user.id,
        photo_bytes=_minimal_jpeg(),
        latitude=0.0,
        longitude=0.0,
        category="Other",
        ai_generated=True,
    )

    updated = service.update_category(report.id, category)
    assert updated.category == category
    if category != "Other":
        assert updated.ai_generated is False
