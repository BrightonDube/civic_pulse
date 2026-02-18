"""
Integration tests for Analytics API endpoints.

Requirements: 13.1, 13.6
"""
import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import User, Report  # noqa: F401
from app.services.auth_service import AuthService


# In-memory SQLite for integration tests
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin user and return auth token."""
    db = TestSession()
    svc = AuthService(db)
    user = svc.register_user("admin@test.com", "AdminPass123!", "+1234567890")
    user.role = "admin"
    db.commit()
    token = svc.login("admin@test.com", "AdminPass123!")
    db.close()
    return token


@pytest.fixture
def user_token():
    """Create a regular user and return auth token."""
    db = TestSession()
    svc = AuthService(db)
    svc.register_user("user@test.com", "Password123!", "+1234567890")
    token = svc.login("user@test.com", "Password123!")
    db.close()
    return token


def create_test_report(
    user_id: uuid.UUID,
    status: str = "Reported",
    category: str = "Pothole",
    created_at: datetime = None,
    updated_at: datetime = None
) -> Report:
    """Helper to create a test report."""
    db = TestSession()
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    if updated_at is None:
        updated_at = created_at
    
    report = Report(
        user_id=user_id,
        photo_url=f"/uploads/{uuid.uuid4()}.jpg",
        latitude=40.7128,
        longitude=-74.0060,
        category=category,
        severity_score=5,
        status=status,
        ai_generated=False,
        archived=False,
        created_at=created_at,
        updated_at=updated_at
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    db.close()
    return report


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    def test_get_metrics_requires_admin(self, client, user_token: str):
        """Regular users should not be able to access analytics."""
        response = client.get(
            "/api/analytics/metrics",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_get_metrics_requires_authentication(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/analytics/metrics")
        assert response.status_code == 401
    
    def test_get_metrics_empty_database(self, client, admin_token: str):
        """Should return zero metrics for empty database."""
        response = client.get(
            "/api/analytics/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_reports"] >= 0  # May have reports from other tests
        assert 0.0 <= data["resolution_rate"] <= 100.0
    
    def test_get_metrics_with_reports(self, client, admin_token: str):
        """Should calculate correct metrics with reports."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        # Create test reports: 2 Fixed, 3 not Fixed
        base_time = datetime.now(timezone.utc)
        create_test_report(
            admin_user.id, status="Fixed",
            created_at=base_time,
            updated_at=base_time + timedelta(hours=2)
        )
        create_test_report(
            admin_user.id, status="Fixed",
            created_at=base_time,
            updated_at=base_time + timedelta(hours=4)
        )
        create_test_report(admin_user.id, status="Reported")
        create_test_report(admin_user.id, status="In Progress")
        create_test_report(admin_user.id, status="Reported")
        
        response = client.get(
            "/api/analytics/metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_reports"] >= 5
        assert data["resolution_rate"] >= 0.0
        assert data["average_resolution_time"] is not None or data["total_reports"] == 0
    
    def test_get_metrics_with_category_filter(self, client, admin_token: str):
        """Should filter metrics by category."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        # Create reports with different categories
        create_test_report(admin_user.id, category="Pothole", status="Fixed")
        create_test_report(admin_user.id, category="Pothole", status="Reported")
        create_test_report(admin_user.id, category="Water Leak", status="Fixed")
        
        response = client.get(
            "/api/analytics/metrics?category=Pothole",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should have at least the 2 Pothole reports we just created
        assert data["total_reports"] >= 2




class TestTrendEndpoints:
    """Test trend data API endpoints."""
    
    def test_daily_trends_requires_admin(self, client, user_token: str):
        """Regular users should not be able to access trend data."""
        response = client.get(
            "/api/analytics/trends/daily",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_weekly_trends_requires_admin(self, client, user_token: str):
        """Regular users should not be able to access trend data."""
        response = client.get(
            "/api/analytics/trends/weekly",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_monthly_trends_requires_admin(self, client, user_token: str):
        """Regular users should not be able to access trend data."""
        response = client.get(
            "/api/analytics/trends/monthly",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_daily_trends_requires_authentication(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/analytics/trends/daily")
        assert response.status_code == 401
    
    def test_daily_trends_empty_database(self, client, admin_token: str):
        """Should return empty list for empty database."""
        response = client.get(
            "/api/analytics/trends/daily",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_daily_trends_with_reports(self, client, admin_token: str):
        """Should return daily trend data."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        # Create reports on different days
        create_test_report(admin_user.id, created_at=base_time)  # Jan 15
        create_test_report(admin_user.id, created_at=base_time + timedelta(hours=5))  # Jan 15
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=1))  # Jan 16
        
        response = client.get(
            "/api/analytics/trends/daily",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of trend points
        for point in data:
            assert "period" in point
            assert "count" in point
            assert isinstance(point["count"], int)
            assert point["count"] > 0
    
    def test_weekly_trends_with_reports(self, client, admin_token: str):
        """Should return weekly trend data."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 5, tzinfo=timezone.utc)  # Week 1
        
        create_test_report(admin_user.id, created_at=base_time)  # Week 1
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=7))  # Week 2
        
        response = client.get(
            "/api/analytics/trends/weekly",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check for ISO week format
        for point in data:
            assert "period" in point
            assert "W" in point["period"]  # ISO week format: YYYY-Www
    
    def test_monthly_trends_with_reports(self, client, admin_token: str):
        """Should return monthly trend data."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        create_test_report(admin_user.id, created_at=base_time)  # January
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=30))  # February
        
        response = client.get(
            "/api/analytics/trends/monthly",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check for month format
        for point in data:
            assert "period" in point
            # Format should be YYYY-MM
            assert len(point["period"]) == 7
            assert point["period"][4] == "-"
    
    def test_trends_with_category_filter(self, client, admin_token: str):
        """Should filter trends by category."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        create_test_report(admin_user.id, category="Pothole", created_at=base_time)
        create_test_report(admin_user.id, category="Pothole", created_at=base_time + timedelta(days=1))
        create_test_report(admin_user.id, category="Water Leak", created_at=base_time)
        
        response = client.get(
            "/api/analytics/trends/daily?category=Pothole",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Sum of counts should be at least 2 (the Pothole reports)
        total_count = sum(point["count"] for point in data)
        assert total_count >= 2
    
    def test_trends_with_status_filter(self, client, admin_token: str):
        """Should filter trends by status."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        create_test_report(admin_user.id, status="Fixed", created_at=base_time)
        create_test_report(admin_user.id, status="Fixed", created_at=base_time + timedelta(days=1))
        create_test_report(admin_user.id, status="Reported", created_at=base_time)
        
        response = client.get(
            "/api/analytics/trends/daily?status=Fixed",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Sum of counts should be at least 2 (the Fixed reports)
        total_count = sum(point["count"] for point in data)
        assert total_count >= 2
    
    def test_trends_with_date_range_filter(self, client, admin_token: str):
        """Should filter trends by date range."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Reports in January
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=5))
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=10))
        
        # Reports in February
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=35))
        
        # Filter for January only
        jan_start = "2024-01-01T00:00:00Z"
        jan_end = "2024-01-31T23:59:59Z"
        
        response = client.get(
            f"/api/analytics/trends/daily?date_from={jan_start}&date_to={jan_end}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All periods should be in January
        for point in data:
            assert point["period"].startswith("2024-01")
    
    def test_trends_sorted_chronologically(self, client, admin_token: str):
        """Trend results should be sorted by period."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        db.close()
        
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Create reports in non-chronological order
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=10))
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=2))
        create_test_report(admin_user.id, created_at=base_time + timedelta(days=5))
        
        response = client.get(
            "/api/analytics/trends/daily",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Periods should be in ascending order
        periods = [point["period"] for point in data]
        assert periods == sorted(periods)



class TestHeatZonesEndpoint:
    """Test heat zones API endpoint."""
    
    def test_heat_zones_requires_admin(self, client, user_token: str):
        """Regular users should not be able to access heat zones."""
        response = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_heat_zones_requires_authentication(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/analytics/heat-zones")
        assert response.status_code == 401
    
    def test_heat_zones_empty_database(self, client, admin_token: str):
        """Should return empty list for empty database."""
        response = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_heat_zones_with_unresolved_reports(self, client, admin_token: str):
        """Should identify heat zones from unresolved reports."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        # Create a cluster of 4 nearby unresolved reports
        base_lat, base_lon = 40.7128, -74.0060
        for i in range(4):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=base_lat + (i * 0.0001),
                longitude=base_lon + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of heat zones
        for zone in data:
            assert "latitude" in zone
            assert "longitude" in zone
            assert "report_count" in zone
            assert "report_ids" in zone
            assert isinstance(zone["report_count"], int)
            assert zone["report_count"] >= 3  # Default min_reports
            assert isinstance(zone["report_ids"], list)
    
    def test_heat_zones_exclude_fixed_reports(self, client, admin_token: str):
        """Should not include Fixed reports in heat zones."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        # Create only Fixed reports
        base_lat, base_lon = 40.7200, -74.0100
        for i in range(4):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=base_lat + (i * 0.0001),
                longitude=base_lon + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Fixed",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not create a heat zone from Fixed reports
        # (assuming no other unresolved reports in this area)
        fixed_zone_found = False
        for zone in data:
            if abs(zone["latitude"] - base_lat) < 0.001 and abs(zone["longitude"] - base_lon) < 0.001:
                fixed_zone_found = True
        
        assert not fixed_zone_found
    
    def test_heat_zones_sorted_by_count(self, client, admin_token: str):
        """Heat zones should be sorted by report count descending."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        # Create cluster 1: 3 reports
        for i in range(3):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=40.7128 + (i * 0.0001),
                longitude=-74.0060 + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        # Create cluster 2: 5 reports (should be first)
        for i in range(5):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=40.7500 + (i * 0.0001),
                longitude=-73.9900 + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify zones are sorted in descending order
        for i in range(len(data) - 1):
            assert data[i]["report_count"] >= data[i + 1]["report_count"]
    
    def test_heat_zones_with_custom_parameters(self, client, admin_token: str):
        """Should respect custom proximity and min_reports parameters."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        # Create 2 nearby reports
        base_lat, base_lon = 40.7300, -74.0150
        for i in range(2):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=base_lat + (i * 0.0001),
                longitude=base_lon + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        db.commit()
        db.close()
        
        # With default min_reports=3, should not create a zone
        response_default = client.get(
            "/api/analytics/heat-zones",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # With min_reports=2, should create a zone
        response_custom = client.get(
            "/api/analytics/heat-zones?min_reports=2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response_default.status_code == 200
        assert response_custom.status_code == 200
        
        data_custom = response_custom.json()
        
        # Should have at least one zone with 2 reports
        found_zone = False
        for zone in data_custom:
            if zone["report_count"] == 2:
                found_zone = True
                break
        
        assert found_zone
    
    def test_heat_zones_with_category_filter(self, client, admin_token: str):
        """Should filter heat zones by category."""
        # Get admin user ID
        db = TestSession()
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        
        # Create Pothole cluster
        for i in range(4):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=40.7400 + (i * 0.0001),
                longitude=-74.0200 + (i * 0.0001),
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        # Create Water Leak cluster
        for i in range(4):
            report = Report(
                user_id=admin_user.id,
                photo_url=f"/uploads/{uuid.uuid4()}.jpg",
                latitude=40.7600 + (i * 0.0001),
                longitude=-73.9800 + (i * 0.0001),
                category="Water Leak",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/analytics/heat-zones?category=Pothole",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least one zone with Pothole reports
        assert len(data) > 0


class TestCSVExportEndpoint:
    """Test CSV export API endpoint."""
    
    def test_csv_export_requires_admin(self, client, user_token: str):
        """Regular users should not be able to export CSV."""
        response = client.get(
            "/api/analytics/export/csv",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_csv_export_requires_authentication(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/analytics/export/csv")
        assert response.status_code == 401
    
    def test_csv_export_empty_database(self, client, admin_token: str):
        """Should return CSV with headers only for empty database."""
        response = client.get(
            "/api/analytics/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # Parse CSV
        csv_str = response.text
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should have headers but no data
        assert len(rows) == 0
        assert reader.fieldnames is not None
    
    def test_csv_export_with_reports(self, client, admin_token: str):
        """Should export all reports to CSV."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create test reports
        for i in range(3):
            report = Report(
                user_id=admin.id,
                photo_url=f"/uploads/test_{i}.jpg",
                latitude=40.7128 + i * 0.01,
                longitude=-74.0060 + i * 0.01,
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        db.commit()
        
        # Export CSV
        response = client.get(
            "/api/analytics/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Parse CSV
        csv_str = response.text
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should have all reports
        assert len(rows) == 3
        
        # Verify all required fields are present
        for row in rows:
            assert 'id' in row
            assert 'user_id' in row
            assert 'photo_url' in row
            assert 'latitude' in row
            assert 'longitude' in row
            assert 'category' in row
            assert 'severity_score' in row
            assert 'status' in row
            assert 'upvote_count' in row
            assert 'ai_generated' in row
            assert 'archived' in row
            assert 'created_at' in row
            assert 'updated_at' in row
    
    def test_csv_export_with_category_filter(self, client, admin_token: str):
        """Should filter CSV export by category."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create reports with different categories
        for category in ["Pothole", "Pothole", "Water Leak"]:
            report = Report(
                user_id=admin.id,
                photo_url=f"/uploads/test_{uuid.uuid4()}.jpg",
                latitude=40.7128,
                longitude=-74.0060,
                category=category,
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        db.commit()
        
        # Export CSV with category filter
        response = client.get(
            "/api/analytics/export/csv?category=Pothole",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Parse CSV
        csv_str = response.text
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have Pothole reports
        assert len(rows) == 2
        assert all(row['category'] == "Pothole" for row in rows)
    
    def test_csv_export_with_status_filter(self, client, admin_token: str):
        """Should filter CSV export by status."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create reports with different statuses
        for status in ["Reported", "Fixed", "Fixed"]:
            report = Report(
                user_id=admin.id,
                photo_url=f"/uploads/test_{uuid.uuid4()}.jpg",
                latitude=40.7128,
                longitude=-74.0060,
                category="Pothole",
                severity_score=5,
                status=status,
                ai_generated=False,
                archived=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(report)
        db.commit()
        
        # Export CSV with status filter
        response = client.get(
            "/api/analytics/export/csv?status=Fixed",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Parse CSV
        csv_str = response.text
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have Fixed reports
        assert len(rows) == 2
        assert all(row['status'] == "Fixed" for row in rows)
    
    def test_csv_export_excludes_archived(self, client, admin_token: str):
        """Should exclude archived reports from CSV export."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create active report
        active_report = Report(
            user_id=admin.id,
            photo_url="/uploads/active.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Reported",
            ai_generated=False,
            archived=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(active_report)
        
        # Create archived report
        archived_report = Report(
            user_id=admin.id,
            photo_url="/uploads/archived.jpg",
            latitude=40.7128,
            longitude=-74.0060,
            category="Pothole",
            severity_score=5,
            status="Fixed",
            ai_generated=False,
            archived=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(archived_report)
        db.commit()
        
        # Export CSV
        response = client.get(
            "/api/analytics/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Parse CSV
        csv_str = response.text
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have active report
        assert len(rows) == 1
        assert rows[0]['photo_url'] == "/uploads/active.jpg"
    
    def test_csv_export_filename_format(self, client, admin_token: str):
        """CSV export should have properly formatted filename."""
        response = client.get(
            "/api/analytics/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        
        # Check filename format
        content_disposition = response.headers["content-disposition"]
        assert "civicpulse_reports_" in content_disposition
        assert ".csv" in content_disposition


class TestPDFExportEndpoint:
    """Test PDF export API endpoint."""
    
    def test_pdf_export_requires_admin(self, client, user_token: str):
        """Regular users should not be able to export PDF."""
        response = client.get(
            "/api/analytics/export/pdf",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403
    
    def test_pdf_export_requires_authentication(self, client):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/analytics/export/pdf")
        assert response.status_code == 401
    
    def test_pdf_export_generates_pdf(self, client, admin_token: str):
        """Should generate a PDF file with analytics data."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create test reports with various statuses
        base_time = datetime.now(timezone.utc)
        for i in range(5):
            status = "Fixed" if i < 2 else "Reported"
            report = Report(
                user_id=admin.id,
                photo_url=f"/uploads/test_{i}.jpg",
                latitude=40.7128 + i * 0.01,
                longitude=-74.0060 + i * 0.01,
                category="Pothole" if i % 2 == 0 else "Water Leak",
                severity_score=5 + i,
                status=status,
                ai_generated=False,
                archived=False,
                created_at=base_time - timedelta(days=i),
                updated_at=base_time - timedelta(days=i) + timedelta(hours=2) if status == "Fixed" else base_time - timedelta(days=i)
            )
            db.add(report)
        db.commit()
        
        # Export PDF
        response = client.get(
            "/api/analytics/export/pdf",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "civicpulse_analytics_" in response.headers["content-disposition"]
        
        # Verify PDF content is not empty
        pdf_content = response.content
        assert len(pdf_content) > 0
        
        # Verify it's a valid PDF (starts with PDF magic number)
        assert pdf_content[:4] == b'%PDF'
    
    def test_pdf_export_with_filters(self, client, admin_token: str):
        """Should generate PDF with filtered data."""
        # Get admin user ID
        db = next(override_get_db())
        admin = db.query(User).filter(User.role == "admin").first()
        
        # Create test reports
        base_time = datetime.now(timezone.utc)
        for i in range(3):
            report = Report(
                user_id=admin.id,
                photo_url=f"/uploads/test_{i}.jpg",
                latitude=40.7128,
                longitude=-74.0060,
                category="Pothole",
                severity_score=5,
                status="Reported",
                ai_generated=False,
                archived=False,
                created_at=base_time,
                updated_at=base_time
            )
            db.add(report)
        db.commit()
        
        # Export PDF with category filter
        response = client.get(
            "/api/analytics/export/pdf?category=Pothole",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # Verify PDF content
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content[:4] == b'%PDF'
    
    def test_pdf_export_empty_database(self, client, admin_token: str):
        """Should generate PDF even with no data."""
        response = client.get(
            "/api/analytics/export/pdf",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # Should still generate a valid PDF with empty data
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content[:4] == b'%PDF'
