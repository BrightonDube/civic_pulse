"""
Test CSV export functionality.

Requirements: 13.6
Property 45: CSV Export Round Trip
"""
import csv
import io
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.user import User
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        password_hash="hashed",
        phone="+1234567890",
        role="user",
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def analytics_service(db_session: Session):
    """Create an AnalyticsService instance."""
    return AnalyticsService(db_session)


def create_report(
    db: Session,
    user_id: uuid.UUID,
    status: str = "Reported",
    category: str = "Pothole",
    severity: int = 5,
    latitude: float = 40.7128,
    longitude: float = -74.0060
) -> Report:
    """Helper to create a report."""
    report = Report(
        user_id=user_id,
        photo_url=f"/uploads/{uuid.uuid4()}.jpg",
        latitude=latitude,
        longitude=longitude,
        category=category,
        severity_score=severity,
        status=status,
        ai_generated=False,
        archived=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


class TestCSVExport:
    """
    Feature: civic-pulse, Property 45: CSV Export Round Trip
    
    For any set of filtered reports, exporting to CSV then parsing the CSV
    should produce equivalent report data.
    
    Validates: Requirements 13.6
    """
    
    def test_empty_database_returns_empty_csv(
        self, analytics_service: AnalyticsService
    ):
        """CSV export with no reports should return only headers."""
        csv_content = analytics_service.export_to_csv()
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should have headers but no data rows
        assert len(rows) == 0
        assert reader.fieldnames == [
            'id', 'user_id', 'photo_url', 'latitude', 'longitude',
            'category', 'severity_score', 'status', 'upvote_count',
            'ai_generated', 'archived', 'created_at', 'updated_at'
        ]
    
    def test_single_report_export(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """CSV export should include all report fields."""
        # Create a report
        report = create_report(db_session, test_user.id)
        
        # Export to CSV
        csv_content = analytics_service.export_to_csv()
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should have exactly one row
        assert len(rows) == 1
        
        # Verify all fields are present and correct
        row = rows[0]
        assert row['id'] == str(report.id)
        assert row['user_id'] == str(report.user_id)
        assert row['photo_url'] == report.photo_url
        assert float(row['latitude']) == report.latitude
        assert float(row['longitude']) == report.longitude
        assert row['category'] == report.category
        assert int(row['severity_score']) == report.severity_score
        assert row['status'] == report.status
        assert int(row['upvote_count']) == report.upvote_count
        assert row['ai_generated'] == str(report.ai_generated)
        assert row['archived'] == str(report.archived)
    
    def test_multiple_reports_export(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """CSV export should include all reports."""
        # Create multiple reports
        reports = []
        for i in range(5):
            report = create_report(
                db_session,
                test_user.id,
                category="Pothole" if i % 2 == 0 else "Water Leak",
                severity=i + 1
            )
            reports.append(report)
        
        # Export to CSV
        csv_content = analytics_service.export_to_csv()
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should have all reports
        assert len(rows) == 5
        
        # Verify report IDs are present
        exported_ids = {row['id'] for row in rows}
        expected_ids = {str(r.id) for r in reports}
        assert exported_ids == expected_ids
    
    def test_csv_export_with_category_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """CSV export should respect category filter."""
        # Create reports with different categories
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Water Leak")
        
        # Export with category filter
        csv_content = analytics_service.export_to_csv(category="Pothole")
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have Pothole reports
        assert len(rows) == 2
        assert all(row['category'] == "Pothole" for row in rows)
    
    def test_csv_export_with_status_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """CSV export should respect status filter."""
        # Create reports with different statuses
        create_report(db_session, test_user.id, status="Reported")
        create_report(db_session, test_user.id, status="Fixed")
        create_report(db_session, test_user.id, status="Fixed")
        
        # Export with status filter
        csv_content = analytics_service.export_to_csv(status="Fixed")
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have Fixed reports
        assert len(rows) == 2
        assert all(row['status'] == "Fixed" for row in rows)
    
    def test_csv_export_excludes_archived_reports(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """CSV export should exclude archived reports."""
        # Create active and archived reports
        active_report = create_report(db_session, test_user.id)
        
        archived_report = create_report(db_session, test_user.id)
        archived_report.archived = True
        db_session.commit()
        
        # Export to CSV
        csv_content = analytics_service.export_to_csv()
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Should only have active report
        assert len(rows) == 1
        assert rows[0]['id'] == str(active_report.id)
    
    def test_csv_export_round_trip_data_integrity(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """
        Property 45: CSV Export Round Trip
        
        Exporting to CSV and parsing should preserve all report data accurately.
        """
        # Create a report with specific values
        original_report = create_report(
            db_session,
            test_user.id,
            category="Broken Streetlight",
            status="In Progress",
            severity=8,
            latitude=34.0522,
            longitude=-118.2437
        )
        original_report.upvote_count = 5
        original_report.ai_generated = True
        db_session.commit()
        
        # Export to CSV
        csv_content = analytics_service.export_to_csv()
        
        # Parse CSV
        csv_str = csv_content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        
        # Verify data integrity
        assert len(rows) == 1
        row = rows[0]
        
        # All fields should match exactly
        assert row['id'] == str(original_report.id)
        assert row['user_id'] == str(original_report.user_id)
        assert row['photo_url'] == original_report.photo_url
        assert float(row['latitude']) == pytest.approx(original_report.latitude)
        assert float(row['longitude']) == pytest.approx(original_report.longitude)
        assert row['category'] == original_report.category
        assert int(row['severity_score']) == original_report.severity_score
        assert row['status'] == original_report.status
        assert int(row['upvote_count']) == original_report.upvote_count
        assert row['ai_generated'] == str(original_report.ai_generated)
        assert row['archived'] == str(original_report.archived)
        
        # Timestamps should be parseable
        created_at = datetime.fromisoformat(row['created_at'])
        updated_at = datetime.fromisoformat(row['updated_at'])
        assert isinstance(created_at, datetime)
        assert isinstance(updated_at, datetime)
