"""
Property-based tests for AnalyticsService.

Property 40: Analytics Key Metrics Calculation
Requirements: 13.1
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy.orm import Session

from app.models.report import Report, VALID_CATEGORIES, VALID_STATUSES
from app.models.user import User
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_service(db_session: Session):
    """Create an AnalyticsService instance."""
    return AnalyticsService(db_session)


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


def create_report(
    db: Session,
    user_id: uuid.UUID,
    status: str = "Reported",
    category: str = "Pothole",
    created_at: datetime = None,
    updated_at: datetime = None
) -> Report:
    """Helper to create a report."""
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
    return report


class TestAnalyticsKeyMetrics:
    """
    Feature: civic-pulse, Property 40: Analytics Key Metrics Calculation
    
    For any set of reports with various statuses and timestamps, the calculated
    key metrics (total reports, resolution rate percentage, average resolution time)
    should accurately reflect the underlying data.
    
    Validates: Requirements 13.1
    """
    
    def test_empty_database_returns_zero_metrics(
        self, analytics_service: AnalyticsService
    ):
        """With no reports, all metrics should be zero or None."""
        metrics = analytics_service.get_key_metrics()
        
        assert metrics.total_reports == 0
        assert metrics.resolution_rate == 0.0
        assert metrics.average_resolution_time is None
    
    def test_total_reports_count_accuracy(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Total reports should match the actual count in database."""
        # Create 5 reports
        for _ in range(5):
            create_report(db_session, test_user.id)
        
        metrics = analytics_service.get_key_metrics()
        assert metrics.total_reports == 5
    
    def test_resolution_rate_calculation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Resolution rate should be (Fixed / Total) * 100."""
        # Create 10 reports: 3 Fixed, 7 not Fixed
        for _ in range(3):
            create_report(db_session, test_user.id, status="Fixed")
        for _ in range(4):
            create_report(db_session, test_user.id, status="Reported")
        for _ in range(3):
            create_report(db_session, test_user.id, status="In Progress")
        
        metrics = analytics_service.get_key_metrics()
        
        assert metrics.total_reports == 10
        expected_rate = (3 / 10) * 100.0
        assert abs(metrics.resolution_rate - expected_rate) < 0.01
    
    def test_average_resolution_time_calculation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Average resolution time should be mean of (updated_at - created_at) for Fixed reports."""
        base_time = datetime.now(timezone.utc)
        
        # Create Fixed reports with known resolution times
        # Report 1: 1 hour resolution time
        create_report(
            db_session, test_user.id, status="Fixed",
            created_at=base_time,
            updated_at=base_time + timedelta(hours=1)
        )
        # Report 2: 3 hours resolution time
        create_report(
            db_session, test_user.id, status="Fixed",
            created_at=base_time,
            updated_at=base_time + timedelta(hours=3)
        )
        # Report 3: Not Fixed (should not affect average)
        create_report(
            db_session, test_user.id, status="Reported",
            created_at=base_time,
            updated_at=base_time + timedelta(hours=10)
        )
        
        metrics = analytics_service.get_key_metrics()
        
        # Average should be (1 + 3) / 2 = 2 hours = 7200 seconds
        expected_avg = 7200.0
        assert metrics.average_resolution_time is not None
        assert abs(metrics.average_resolution_time - expected_avg) < 1.0
    
    def test_no_fixed_reports_returns_none_for_avg_time(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """When no Fixed reports exist, average resolution time should be None."""
        create_report(db_session, test_user.id, status="Reported")
        create_report(db_session, test_user.id, status="In Progress")
        
        metrics = analytics_service.get_key_metrics()
        
        assert metrics.total_reports == 2
        assert metrics.resolution_rate == 0.0
        assert metrics.average_resolution_time is None
    
    def test_category_filtering(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Metrics should respect category filter."""
        create_report(db_session, test_user.id, category="Pothole", status="Fixed")
        create_report(db_session, test_user.id, category="Pothole", status="Reported")
        create_report(db_session, test_user.id, category="Water Leak", status="Fixed")
        
        metrics = analytics_service.get_key_metrics(category="Pothole")
        
        assert metrics.total_reports == 2
        assert metrics.resolution_rate == 50.0
    
    def test_date_range_filtering(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Metrics should respect date range filters."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Reports in January
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=5))
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))
        
        # Reports in February
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=35))
        
        # Filter for January only
        jan_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        jan_end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        metrics = analytics_service.get_key_metrics(date_from=jan_start, date_to=jan_end)
        
        assert metrics.total_reports == 2
    
    def test_archived_reports_excluded(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Archived reports should not be included in metrics."""
        # Active report
        create_report(db_session, test_user.id, status="Fixed")
        
        # Archived report
        archived = create_report(db_session, test_user.id, status="Fixed")
        archived.archived = True
        db_session.commit()
        
        metrics = analytics_service.get_key_metrics()
        
        assert metrics.total_reports == 1
        assert metrics.resolution_rate == 100.0
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_reported=st.integers(min_value=0, max_value=20),
        num_in_progress=st.integers(min_value=0, max_value=20),
        num_fixed=st.integers(min_value=0, max_value=20),
    )
    def test_property_resolution_rate_bounds(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        num_reported: int,
        num_in_progress: int,
        num_fixed: int
    ):
        """
        Property: Resolution rate should always be between 0 and 100.
        
        For any combination of report statuses, the resolution rate percentage
        should be in the valid range [0, 100].
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        analytics_service.clear_cache()
        
        # Create reports with different statuses
        for _ in range(num_reported):
            create_report(db_session, test_user.id, status="Reported")
        for _ in range(num_in_progress):
            create_report(db_session, test_user.id, status="In Progress")
        for _ in range(num_fixed):
            create_report(db_session, test_user.id, status="Fixed")
        
        metrics = analytics_service.get_key_metrics()
        
        # Resolution rate should always be in valid range
        assert 0.0 <= metrics.resolution_rate <= 100.0
        
        # Total should match sum of all statuses
        total = num_reported + num_in_progress + num_fixed
        assert metrics.total_reports == total
        
        # If there are reports, verify resolution rate calculation
        if total > 0:
            expected_rate = (num_fixed / total) * 100.0
            assert abs(metrics.resolution_rate - expected_rate) < 0.01
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        resolution_hours=st.lists(
            st.integers(min_value=1, max_value=168),  # 1 hour to 1 week
            min_size=1,
            max_size=10
        )
    )
    def test_property_average_resolution_time_accuracy(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        resolution_hours: list
    ):
        """
        Property: Average resolution time should equal the mean of individual resolution times.
        
        For any set of Fixed reports with known resolution times, the calculated
        average should match the mathematical mean.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        analytics_service.clear_cache()
        
        base_time = datetime.now(timezone.utc)
        
        # Create Fixed reports with specified resolution times
        for hours in resolution_hours:
            create_report(
                db_session, test_user.id, status="Fixed",
                created_at=base_time,
                updated_at=base_time + timedelta(hours=hours)
            )
        
        metrics = analytics_service.get_key_metrics()
        
        # Calculate expected average in seconds
        expected_avg_seconds = sum(h * 3600 for h in resolution_hours) / len(resolution_hours)
        
        assert metrics.average_resolution_time is not None
        assert abs(metrics.average_resolution_time - expected_avg_seconds) < 1.0


class TestAnalyticsCaching:
    """Test caching functionality of AnalyticsService."""
    
    def test_cache_returns_same_result(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Cached results should match fresh calculations."""
        create_report(db_session, test_user.id, status="Fixed")
        
        # First call - calculates and caches
        metrics1 = analytics_service.get_key_metrics()
        
        # Second call - should return cached value
        metrics2 = analytics_service.get_key_metrics()
        
        assert metrics1.total_reports == metrics2.total_reports
        assert metrics1.resolution_rate == metrics2.resolution_rate
        assert metrics1.average_resolution_time == metrics2.average_resolution_time
    
    def test_cache_respects_different_filters(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Different filter combinations should have separate cache entries."""
        create_report(db_session, test_user.id, category="Pothole", status="Fixed")
        create_report(db_session, test_user.id, category="Water Leak", status="Reported")
        
        metrics_all = analytics_service.get_key_metrics()
        metrics_pothole = analytics_service.get_key_metrics(category="Pothole")
        
        assert metrics_all.total_reports == 2
        assert metrics_pothole.total_reports == 1
    
    def test_clear_cache_forces_recalculation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Clearing cache should force fresh calculation."""
        create_report(db_session, test_user.id, status="Reported")
        
        # Get initial metrics
        metrics1 = analytics_service.get_key_metrics()
        assert metrics1.total_reports == 1
        
        # Add another report
        create_report(db_session, test_user.id, status="Fixed")
        
        # Without clearing cache, should return cached value
        metrics2 = analytics_service.get_key_metrics()
        assert metrics2.total_reports == 1  # Still cached
        
        # Clear cache and recalculate
        analytics_service.clear_cache()
        metrics3 = analytics_service.get_key_metrics()
        assert metrics3.total_reports == 2  # Fresh calculation



class TestTrendDataAggregation:
    """
    Feature: civic-pulse, Property 41: Trend Data Aggregation
    
    For any set of reports and time period (daily, weekly, monthly), grouping reports
    by that period should produce counts that sum to the total number of reports.
    
    Validates: Requirements 13.2
    """
    
    def test_daily_trend_aggregation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Daily trends should group reports by day."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        # Create reports on different days
        create_report(db_session, test_user.id, created_at=base_time)  # Jan 15
        create_report(db_session, test_user.id, created_at=base_time + timedelta(hours=5))  # Jan 15
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=1))  # Jan 16
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=2))  # Jan 17
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=2, hours=3))  # Jan 17
        
        trends = analytics_service.get_trend_data(period="daily")
        
        # Convert to dict for easier testing
        trend_dict = {t.period: t.count for t in trends}
        
        assert trend_dict["2024-01-15"] == 2
        assert trend_dict["2024-01-16"] == 1
        assert trend_dict["2024-01-17"] == 2
        assert len(trends) == 3
    
    def test_weekly_trend_aggregation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Weekly trends should group reports by ISO week."""
        # Week 1 of 2024: Jan 1-7
        # Week 2 of 2024: Jan 8-14
        # Week 3 of 2024: Jan 15-21
        
        base_time = datetime(2024, 1, 5, tzinfo=timezone.utc)  # Week 1
        
        create_report(db_session, test_user.id, created_at=base_time)  # Week 1
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=1))  # Week 1
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=7))  # Week 2
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=14))  # Week 3
        
        trends = analytics_service.get_trend_data(period="weekly")
        
        trend_dict = {t.period: t.count for t in trends}
        
        assert trend_dict["2024-W01"] == 2
        assert trend_dict["2024-W02"] == 1
        assert trend_dict["2024-W03"] == 1
        assert len(trends) == 3
    
    def test_monthly_trend_aggregation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Monthly trends should group reports by month."""
        base_time = datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        # Create reports in different months
        create_report(db_session, test_user.id, created_at=base_time)  # January
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))  # January
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=30))  # February
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=60))  # March
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=65))  # March
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=70))  # March
        
        trends = analytics_service.get_trend_data(period="monthly")
        
        trend_dict = {t.period: t.count for t in trends}
        
        assert trend_dict["2024-01"] == 2
        assert trend_dict["2024-02"] == 1
        assert trend_dict["2024-03"] == 3
        assert len(trends) == 3
    
    def test_trend_counts_sum_to_total(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """
        Property: Sum of trend counts should equal total reports.
        
        This is the core property - no matter how we group reports by time period,
        the sum of all period counts should equal the total number of reports.
        """
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Create 15 reports across different time periods
        for i in range(15):
            create_report(db_session, test_user.id, created_at=base_time + timedelta(days=i*2))
        
        # Test for each period type
        for period in ["daily", "weekly", "monthly"]:
            trends = analytics_service.get_trend_data(period=period)
            total_from_trends = sum(t.count for t in trends)
            
            # Should equal the actual number of reports
            assert total_from_trends == 15, f"Failed for period: {period}"
    
    def test_trend_with_category_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Trends should respect category filter."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        create_report(db_session, test_user.id, category="Pothole", created_at=base_time)
        create_report(db_session, test_user.id, category="Pothole", created_at=base_time + timedelta(days=1))
        create_report(db_session, test_user.id, category="Water Leak", created_at=base_time)
        
        trends = analytics_service.get_trend_data(period="daily", category="Pothole")
        
        total_count = sum(t.count for t in trends)
        assert total_count == 2
    
    def test_trend_with_status_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Trends should respect status filter."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        create_report(db_session, test_user.id, status="Fixed", created_at=base_time)
        create_report(db_session, test_user.id, status="Fixed", created_at=base_time + timedelta(days=1))
        create_report(db_session, test_user.id, status="Reported", created_at=base_time)
        
        trends = analytics_service.get_trend_data(period="daily", status="Fixed")
        
        total_count = sum(t.count for t in trends)
        assert total_count == 2
    
    def test_trend_with_date_range_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Trends should respect date range filters."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Reports in January
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=5))
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))
        
        # Reports in February
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=35))
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=40))
        
        # Filter for January only
        jan_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        jan_end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        trends = analytics_service.get_trend_data(
            period="daily",
            date_from=jan_start,
            date_to=jan_end
        )
        
        total_count = sum(t.count for t in trends)
        assert total_count == 2
    
    def test_trend_excludes_archived_reports(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Archived reports should not be included in trends."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Active reports
        create_report(db_session, test_user.id, created_at=base_time)
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=1))
        
        # Archived report
        archived = create_report(db_session, test_user.id, created_at=base_time)
        archived.archived = True
        db_session.commit()
        
        trends = analytics_service.get_trend_data(period="daily")
        
        total_count = sum(t.count for t in trends)
        assert total_count == 2
    
    def test_trend_results_sorted_by_period(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Trend results should be sorted chronologically."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Create reports in non-chronological order
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=2))
        create_report(db_session, test_user.id, created_at=base_time + timedelta(days=5))
        
        trends = analytics_service.get_trend_data(period="daily")
        
        # Periods should be in ascending order
        periods = [t.period for t in trends]
        assert periods == sorted(periods)
    
    def test_invalid_period_raises_error(
        self, analytics_service: AnalyticsService
    ):
        """Invalid period parameter should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid period"):
            analytics_service.get_trend_data(period="invalid")
    
    def test_empty_database_returns_empty_trends(
        self, analytics_service: AnalyticsService
    ):
        """With no reports, trends should return empty list."""
        trends = analytics_service.get_trend_data(period="daily")
        assert len(trends) == 0
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_reports=st.integers(min_value=1, max_value=50),
        period=st.sampled_from(["daily", "weekly", "monthly"])
    )
    def test_property_trend_sum_equals_total(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        num_reports: int,
        period: str
    ):
        """
        Property: For any number of reports and any period type, the sum of trend counts
        should equal the total number of reports.
        
        This is the fundamental property that validates trend aggregation correctness.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Create reports spread across time
        for i in range(num_reports):
            # Spread reports across ~100 days
            days_offset = (i * 100) // num_reports
            create_report(
                db_session,
                test_user.id,
                created_at=base_time + timedelta(days=days_offset)
            )
        
        trends = analytics_service.get_trend_data(period=period)
        
        # Sum of all trend counts should equal total reports
        total_from_trends = sum(t.count for t in trends)
        assert total_from_trends == num_reports
        
        # Each trend point should have a positive count
        for trend in trends:
            assert trend.count > 0


class TestCategoryDistribution:
    """
    Feature: civic-pulse, Property 42: Category Distribution Accuracy
    
    For any set of reports, the sum of category counts should equal the total
    number of reports.
    
    Validates: Requirements 13.3
    """
    
    def test_empty_database_returns_empty_distribution(
        self, analytics_service: AnalyticsService
    ):
        """With no reports, distribution should be empty."""
        distribution = analytics_service.get_category_distribution()
        assert len(distribution) == 0
    
    def test_single_category_distribution(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution with single category should return correct count."""
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Pothole")
        
        distribution = analytics_service.get_category_distribution()
        
        assert distribution["Pothole"] == 3
        assert len(distribution) == 1
    
    def test_multiple_categories_distribution(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution should correctly count reports across multiple categories."""
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Water Leak")
        create_report(db_session, test_user.id, category="Vandalism")
        create_report(db_session, test_user.id, category="Vandalism")
        create_report(db_session, test_user.id, category="Vandalism")
        
        distribution = analytics_service.get_category_distribution()
        
        assert distribution["Pothole"] == 2
        assert distribution["Water Leak"] == 1
        assert distribution["Vandalism"] == 3
        assert len(distribution) == 3
    
    def test_distribution_sum_equals_total(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """
        Property: Sum of category counts should equal total reports.
        
        This is the core property - the sum of all category counts should always
        equal the total number of reports in the database.
        """
        # Create reports across all categories
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Water Leak")
        create_report(db_session, test_user.id, category="Vandalism")
        create_report(db_session, test_user.id, category="Broken Streetlight")
        create_report(db_session, test_user.id, category="Illegal Dumping")
        create_report(db_session, test_user.id, category="Other")
        
        distribution = analytics_service.get_category_distribution()
        
        # Sum of all category counts
        total_from_distribution = sum(distribution.values())
        
        # Should equal actual number of reports
        assert total_from_distribution == 7
    
    def test_distribution_with_status_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution should respect status filter."""
        create_report(db_session, test_user.id, category="Pothole", status="Fixed")
        create_report(db_session, test_user.id, category="Pothole", status="Fixed")
        create_report(db_session, test_user.id, category="Pothole", status="Reported")
        create_report(db_session, test_user.id, category="Water Leak", status="Fixed")
        
        distribution = analytics_service.get_category_distribution(status="Fixed")
        
        assert distribution["Pothole"] == 2
        assert distribution["Water Leak"] == 1
        assert "Reported" not in distribution or distribution.get("Reported", 0) == 0
        assert sum(distribution.values()) == 3
    
    def test_distribution_with_date_range_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution should respect date range filters."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Reports in January
        create_report(db_session, test_user.id, category="Pothole", created_at=base_time + timedelta(days=5))
        create_report(db_session, test_user.id, category="Water Leak", created_at=base_time + timedelta(days=10))
        
        # Reports in February
        create_report(db_session, test_user.id, category="Pothole", created_at=base_time + timedelta(days=35))
        create_report(db_session, test_user.id, category="Vandalism", created_at=base_time + timedelta(days=40))
        
        # Filter for January only
        jan_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        jan_end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        distribution = analytics_service.get_category_distribution(
            date_from=jan_start,
            date_to=jan_end
        )
        
        assert distribution["Pothole"] == 1
        assert distribution["Water Leak"] == 1
        assert "Vandalism" not in distribution
        assert sum(distribution.values()) == 2
    
    def test_distribution_with_geographic_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution should respect geographic bounds."""
        # Reports in different locations
        report1 = create_report(db_session, test_user.id, category="Pothole")
        report1.latitude = 40.7128
        report1.longitude = -74.0060
        
        report2 = create_report(db_session, test_user.id, category="Water Leak")
        report2.latitude = 40.7500
        report2.longitude = -73.9900
        
        report3 = create_report(db_session, test_user.id, category="Pothole")
        report3.latitude = 41.0000
        report3.longitude = -75.0000
        
        db_session.commit()
        
        # Filter for specific geographic area
        distribution = analytics_service.get_category_distribution(
            min_lat=40.7,
            max_lat=40.8,
            min_lon=-74.1,
            max_lon=-73.9
        )
        
        # Should only include reports within bounds
        assert sum(distribution.values()) == 2
    
    def test_distribution_excludes_archived_reports(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Archived reports should not be included in distribution."""
        # Active reports
        create_report(db_session, test_user.id, category="Pothole")
        create_report(db_session, test_user.id, category="Water Leak")
        
        # Archived report
        archived = create_report(db_session, test_user.id, category="Pothole")
        archived.archived = True
        db_session.commit()
        
        distribution = analytics_service.get_category_distribution()
        
        assert distribution["Pothole"] == 1
        assert distribution["Water Leak"] == 1
        assert sum(distribution.values()) == 2
    
    def test_all_valid_categories_can_be_counted(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Distribution should handle all valid category types."""
        # Create one report for each valid category
        for category in VALID_CATEGORIES:
            create_report(db_session, test_user.id, category=category)
        
        distribution = analytics_service.get_category_distribution()
        
        # Should have all categories
        assert len(distribution) == len(VALID_CATEGORIES)
        
        # Each category should have count of 1
        for category in VALID_CATEGORIES:
            assert distribution[category] == 1
        
        # Sum should equal total categories
        assert sum(distribution.values()) == len(VALID_CATEGORIES)
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        category_counts=st.lists(
            st.tuples(
                st.sampled_from(VALID_CATEGORIES),
                st.integers(min_value=1, max_value=10)
            ),
            min_size=1,
            max_size=len(VALID_CATEGORIES)
        )
    )
    def test_property_distribution_sum_equals_total(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        category_counts: list
    ):
        """
        Property: For any distribution of reports across categories, the sum of
        category counts should equal the total number of reports.
        
        This is the fundamental property that validates category distribution correctness.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        # Track expected counts
        expected_total = 0
        expected_by_category = {}
        
        # Create reports according to the generated distribution
        for category, count in category_counts:
            for _ in range(count):
                create_report(db_session, test_user.id, category=category)
                expected_total += 1
                expected_by_category[category] = expected_by_category.get(category, 0) + 1
        
        distribution = analytics_service.get_category_distribution()
        
        # Sum of all category counts should equal total reports
        total_from_distribution = sum(distribution.values())
        assert total_from_distribution == expected_total
        
        # Each category count should match expected
        for category, expected_count in expected_by_category.items():
            assert distribution[category] == expected_count
        
        # All counts should be positive
        for count in distribution.values():
            assert count > 0
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(
        num_reports=st.integers(min_value=1, max_value=50),
        status_filter=st.sampled_from(VALID_STATUSES + [None])
    )
    def test_property_filtered_distribution_consistency(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        num_reports: int,
        status_filter: str
    ):
        """
        Property: For any status filter, the sum of category counts should equal
        the number of reports with that status.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        # Create reports with random categories and statuses
        for i in range(num_reports):
            category = VALID_CATEGORIES[i % len(VALID_CATEGORIES)]
            status = VALID_STATUSES[i % len(VALID_STATUSES)]
            create_report(db_session, test_user.id, category=category, status=status)
        
        # Get distribution with filter
        distribution = analytics_service.get_category_distribution(status=status_filter)
        
        # Count expected reports matching filter
        query = db_session.query(Report).filter(Report.archived == False)
        if status_filter:
            query = query.filter(Report.status == status_filter)
        expected_count = query.count()
        
        # Sum of distribution should match expected count
        total_from_distribution = sum(distribution.values())
        assert total_from_distribution == expected_count



class TestSeverityTrendAccuracy:
    """
    Feature: civic-pulse, Property 43: Severity Trend Accuracy
    
    For any set of reports grouped by time period, the severity trend data should
    correctly represent the average severity scores for each period.
    
    Validates: Requirements 13.4
    """
    
    def test_empty_database_returns_empty_trends(
        self, analytics_service: AnalyticsService
    ):
        """With no reports, severity trends should be empty."""
        trends = analytics_service.get_severity_trends(period="daily")
        assert len(trends) == 0
    
    def test_single_period_single_report(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Single report should produce one trend point with that severity."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        report = create_report(db_session, test_user.id, created_at=base_time)
        report.severity_score = 7
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        assert len(trends) == 1
        assert trends[0].average_severity == 7.0
        assert trends[0].report_count == 1
        assert trends[0].period == "2024-01-15"
    
    def test_single_period_multiple_reports_average(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Multiple reports in same period should average correctly."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Create reports with different severities on same day
        report1 = create_report(db_session, test_user.id, created_at=base_time)
        report1.severity_score = 2
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(hours=3))
        report2.severity_score = 8
        
        report3 = create_report(db_session, test_user.id, created_at=base_time + timedelta(hours=6))
        report3.severity_score = 5
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        assert len(trends) == 1
        # Average of 2, 8, 5 = 15/3 = 5.0
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 3
    
    def test_multiple_periods_daily(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Reports across multiple days should create separate trend points."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Day 1: severity 6
        report1 = create_report(db_session, test_user.id, created_at=base_time)
        report1.severity_score = 6
        
        # Day 2: severity 3 and 9 (average 6)
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=1))
        report2.severity_score = 3
        
        report3 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=1, hours=5))
        report3.severity_score = 9
        
        # Day 3: severity 10
        report4 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=2))
        report4.severity_score = 10
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        assert len(trends) == 3
        
        # Verify each day's average
        assert trends[0].period == "2024-01-15"
        assert trends[0].average_severity == 6.0
        assert trends[0].report_count == 1
        
        assert trends[1].period == "2024-01-16"
        assert trends[1].average_severity == 6.0  # (3 + 9) / 2
        assert trends[1].report_count == 2
        
        assert trends[2].period == "2024-01-17"
        assert trends[2].average_severity == 10.0
        assert trends[2].report_count == 1
    
    def test_weekly_period_grouping(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Weekly period should group reports by week correctly."""
        # Week 1 (2024-W03): Jan 15-21
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        report1 = create_report(db_session, test_user.id, created_at=base_time)
        report1.severity_score = 4
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=2))
        report2.severity_score = 6
        
        # Week 2 (2024-W04): Jan 22-28
        report3 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=7))
        report3.severity_score = 8
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="weekly")
        
        assert len(trends) == 2
        
        # Week 1 average: (4 + 6) / 2 = 5.0
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 2
        
        # Week 2 average: 8.0
        assert trends[1].average_severity == 8.0
        assert trends[1].report_count == 1
    
    def test_monthly_period_grouping(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Monthly period should group reports by month correctly."""
        # January 2024
        jan_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        report1 = create_report(db_session, test_user.id, created_at=jan_time)
        report1.severity_score = 3
        
        report2 = create_report(db_session, test_user.id, created_at=jan_time + timedelta(days=10))
        report2.severity_score = 7
        
        # February 2024
        feb_time = datetime(2024, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
        
        report3 = create_report(db_session, test_user.id, created_at=feb_time)
        report3.severity_score = 9
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="monthly")
        
        assert len(trends) == 2
        
        # January average: (3 + 7) / 2 = 5.0
        assert trends[0].period == "2024-01"
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 2
        
        # February average: 9.0
        assert trends[1].period == "2024-02"
        assert trends[1].average_severity == 9.0
        assert trends[1].report_count == 1
    
    def test_trends_with_category_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Severity trends should respect category filter."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Potholes
        report1 = create_report(db_session, test_user.id, category="Pothole", created_at=base_time)
        report1.severity_score = 4
        
        report2 = create_report(db_session, test_user.id, category="Pothole", created_at=base_time + timedelta(hours=2))
        report2.severity_score = 6
        
        # Water Leak (should be excluded)
        report3 = create_report(db_session, test_user.id, category="Water Leak", created_at=base_time)
        report3.severity_score = 10
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily", category="Pothole")
        
        assert len(trends) == 1
        # Should only include potholes: (4 + 6) / 2 = 5.0
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 2
    
    def test_trends_with_status_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Severity trends should respect status filter."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Fixed reports
        report1 = create_report(db_session, test_user.id, status="Fixed", created_at=base_time)
        report1.severity_score = 2
        
        report2 = create_report(db_session, test_user.id, status="Fixed", created_at=base_time + timedelta(hours=2))
        report2.severity_score = 4
        
        # Reported (should be excluded)
        report3 = create_report(db_session, test_user.id, status="Reported", created_at=base_time)
        report3.severity_score = 10
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily", status="Fixed")
        
        assert len(trends) == 1
        # Should only include fixed: (2 + 4) / 2 = 3.0
        assert trends[0].average_severity == 3.0
        assert trends[0].report_count == 2
    
    def test_trends_with_date_range_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Severity trends should respect date range filters."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Reports in January
        report1 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=5))
        report1.severity_score = 3
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))
        report2.severity_score = 7
        
        # Reports in February (should be excluded)
        report3 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=35))
        report3.severity_score = 10
        
        db_session.commit()
        
        # Filter for January only
        jan_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        jan_end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        trends = analytics_service.get_severity_trends(
            period="daily",
            date_from=jan_start,
            date_to=jan_end
        )
        
        # Should only have 2 days from January
        assert len(trends) == 2
        assert all(trend.period.startswith("2024-01") for trend in trends)
    
    def test_trends_with_geographic_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Severity trends should respect geographic bounds."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Reports inside bounds
        report1 = create_report(db_session, test_user.id, created_at=base_time)
        report1.latitude = 40.7128
        report1.longitude = -74.0060
        report1.severity_score = 4
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(hours=2))
        report2.latitude = 40.7500
        report2.longitude = -73.9900
        report2.severity_score = 6
        
        # Report outside bounds (should be excluded)
        report3 = create_report(db_session, test_user.id, created_at=base_time)
        report3.latitude = 41.0000
        report3.longitude = -75.0000
        report3.severity_score = 10
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(
            period="daily",
            min_lat=40.7,
            max_lat=40.8,
            min_lon=-74.1,
            max_lon=-73.9
        )
        
        assert len(trends) == 1
        # Should only include reports within bounds: (4 + 6) / 2 = 5.0
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 2
    
    def test_trends_exclude_archived_reports(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Archived reports should not be included in severity trends."""
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Active reports
        report1 = create_report(db_session, test_user.id, created_at=base_time)
        report1.severity_score = 3
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(hours=2))
        report2.severity_score = 7
        
        # Archived report (should be excluded)
        archived = create_report(db_session, test_user.id, created_at=base_time)
        archived.severity_score = 10
        archived.archived = True
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        assert len(trends) == 1
        # Should only include active reports: (3 + 7) / 2 = 5.0
        assert trends[0].average_severity == 5.0
        assert trends[0].report_count == 2
    
    def test_trends_sorted_chronologically(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Trend points should be sorted by period in ascending order."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # Create reports in non-chronological order
        report3 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=20))
        report3.severity_score = 9
        
        report1 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=5))
        report1.severity_score = 3
        
        report2 = create_report(db_session, test_user.id, created_at=base_time + timedelta(days=10))
        report2.severity_score = 6
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        assert len(trends) == 3
        # Should be sorted chronologically
        assert trends[0].period < trends[1].period < trends[2].period
        assert trends[0].period == "2024-01-06"
        assert trends[1].period == "2024-01-11"
        assert trends[2].period == "2024-01-21"
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        severity_scores=st.lists(
            st.integers(min_value=1, max_value=10),
            min_size=1,
            max_size=20
        )
    )
    def test_property_average_calculation_accuracy(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        severity_scores: list
    ):
        """
        Property: For any set of severity scores in a single period, the calculated
        average should equal the sum of scores divided by the count.
        
        This is the fundamental property that validates severity trend accuracy.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        base_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # Create reports with the generated severity scores
        for i, severity in enumerate(severity_scores):
            report = create_report(
                db_session,
                test_user.id,
                created_at=base_time + timedelta(minutes=i * 10)
            )
            report.severity_score = severity
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        # Should have exactly one trend point
        assert len(trends) == 1
        
        # Calculate expected average
        expected_average = sum(severity_scores) / len(severity_scores)
        
        # Verify the calculated average matches expected
        assert abs(trends[0].average_severity - expected_average) < 0.001
        assert trends[0].report_count == len(severity_scores)
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(
        daily_severities=st.lists(
            st.lists(
                st.integers(min_value=1, max_value=10),
                min_size=1,
                max_size=10
            ),
            min_size=1,
            max_size=10
        )
    )
    def test_property_multi_period_independence(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        daily_severities: list
    ):
        """
        Property: For any set of reports across multiple periods, each period's
        average should be calculated independently and correctly.
        
        This validates that period grouping doesn't affect calculation accuracy.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Track expected averages for each day
        expected_averages = []
        
        # Create reports for each day
        for day_index, day_severities in enumerate(daily_severities):
            day_time = base_time + timedelta(days=day_index)
            
            for severity in day_severities:
                report = create_report(db_session, test_user.id, created_at=day_time)
                report.severity_score = severity
            
            # Calculate expected average for this day
            expected_avg = sum(day_severities) / len(day_severities)
            expected_averages.append(expected_avg)
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period="daily")
        
        # Should have one trend point per day
        assert len(trends) == len(daily_severities)
        
        # Verify each day's average is calculated correctly
        for i, trend in enumerate(trends):
            assert abs(trend.average_severity - expected_averages[i]) < 0.001
            assert trend.report_count == len(daily_severities[i])
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(
        period=st.sampled_from(["daily", "weekly", "monthly"]),
        num_reports=st.integers(min_value=1, max_value=30)
    )
    def test_property_all_reports_counted(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        period: str,
        num_reports: int
    ):
        """
        Property: For any period grouping, the sum of report counts across all
        trend points should equal the total number of reports.
        
        This validates that no reports are lost or double-counted during grouping.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Create reports spread across time
        for i in range(num_reports):
            # Spread reports across different periods
            days_offset = i * 2  # Every 2 days
            report_time = base_time + timedelta(days=days_offset)
            
            report = create_report(db_session, test_user.id, created_at=report_time)
            report.severity_score = (i % 10) + 1  # Vary severity 1-10
        
        db_session.commit()
        
        trends = analytics_service.get_severity_trends(period=period)
        
        # Sum of all report counts should equal total reports created
        total_counted = sum(trend.report_count for trend in trends)
        assert total_counted == num_reports
        
        # All averages should be within valid range
        for trend in trends:
            assert 1 <= trend.average_severity <= 10
            assert trend.report_count > 0



class TestHeatZoneIdentification:
    """
    Feature: civic-pulse, Property 44: Heat Zone Identification
    
    For any set of unresolved reports, geographic heat zones should correctly
    identify areas with the highest concentration of reports based on spatial clustering.
    
    Validates: Requirements 13.5
    """
    
    def test_empty_database_returns_empty_heat_zones(
        self, analytics_service: AnalyticsService
    ):
        """With no reports, heat zones should return empty list."""
        heat_zones = analytics_service.get_heat_zones()
        assert len(heat_zones) == 0
    
    def test_only_fixed_reports_returns_empty_heat_zones(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zones should only consider unresolved reports (not Fixed)."""
        # Create only Fixed reports
        create_report(db_session, test_user.id, status="Fixed")
        create_report(db_session, test_user.id, status="Fixed")
        create_report(db_session, test_user.id, status="Fixed")
        
        heat_zones = analytics_service.get_heat_zones()
        assert len(heat_zones) == 0
    
    def test_single_cluster_below_minimum_excluded(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Clusters with fewer than min_reports should be excluded."""
        # Create 2 nearby reports (default min_reports is 3)
        base_lat, base_lon = 40.7128, -74.0060
        
        report1 = create_report(db_session, test_user.id, status="Reported")
        report1.latitude = base_lat
        report1.longitude = base_lon
        
        report2 = create_report(db_session, test_user.id, status="Reported")
        report2.latitude = base_lat + 0.0001  # Very close
        report2.longitude = base_lon + 0.0001
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        assert len(heat_zones) == 0
    
    def test_single_cluster_meets_minimum(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Cluster with exactly min_reports should be included."""
        base_lat, base_lon = 40.7128, -74.0060
        
        # Create 3 nearby reports
        for i in range(3):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = base_lat + (i * 0.0001)
            report.longitude = base_lon + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        assert len(heat_zones) == 1
        assert heat_zones[0]["report_count"] == 3
        assert "latitude" in heat_zones[0]
        assert "longitude" in heat_zones[0]
        assert "report_ids" in heat_zones[0]
    
    def test_multiple_clusters_identified(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Multiple distinct clusters should be identified separately."""
        # Cluster 1: Around (40.7128, -74.0060) - 4 reports
        for i in range(4):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # Cluster 2: Around (40.7500, -73.9900) - 5 reports (far from cluster 1)
        for i in range(5):
            report = create_report(db_session, test_user.id, status="In Progress")
            report.latitude = 40.7500 + (i * 0.0001)
            report.longitude = -73.9900 + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        assert len(heat_zones) == 2
        # Should be sorted by report count descending
        assert heat_zones[0]["report_count"] == 5
        assert heat_zones[1]["report_count"] == 4
    
    def test_heat_zones_sorted_by_count_descending(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zones should be sorted by report count (highest first)."""
        # Cluster 1: 3 reports
        for i in range(3):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # Cluster 2: 7 reports (should be first)
        for i in range(7):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7500 + (i * 0.0001)
            report.longitude = -73.9900 + (i * 0.0001)
        
        # Cluster 3: 5 reports (should be second)
        for i in range(5):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7300 + (i * 0.0001)
            report.longitude = -74.0200 + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        assert len(heat_zones) == 3
        assert heat_zones[0]["report_count"] == 7
        assert heat_zones[1]["report_count"] == 5
        assert heat_zones[2]["report_count"] == 3
    
    def test_heat_zones_with_category_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zones should respect category filter."""
        # Pothole cluster: 4 reports
        for i in range(4):
            report = create_report(db_session, test_user.id, category="Pothole", status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # Water Leak cluster: 5 reports
        for i in range(5):
            report = create_report(db_session, test_user.id, category="Water Leak", status="Reported")
            report.latitude = 40.7500 + (i * 0.0001)
            report.longitude = -73.9900 + (i * 0.0001)
        
        db_session.commit()
        
        # Filter for Pothole only
        heat_zones = analytics_service.get_heat_zones(category="Pothole", min_reports=3)
        
        assert len(heat_zones) == 1
        assert heat_zones[0]["report_count"] == 4
    
    def test_heat_zones_with_date_range_filter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zones should respect date range filters."""
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        # January cluster: 4 reports
        for i in range(4):
            report = create_report(
                db_session, test_user.id, status="Reported",
                created_at=base_time + timedelta(days=i)
            )
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # February cluster: 5 reports
        for i in range(5):
            report = create_report(
                db_session, test_user.id, status="Reported",
                created_at=base_time + timedelta(days=35 + i)
            )
            report.latitude = 40.7500 + (i * 0.0001)
            report.longitude = -73.9900 + (i * 0.0001)
        
        db_session.commit()
        
        # Filter for January only
        jan_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        jan_end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        heat_zones = analytics_service.get_heat_zones(
            date_from=jan_start,
            date_to=jan_end,
            min_reports=3
        )
        
        assert len(heat_zones) == 1
        assert heat_zones[0]["report_count"] == 4
    
    def test_heat_zones_with_geographic_bounds(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zones should respect geographic boundary filters."""
        # Cluster inside bounds: 4 reports around (40.7128, -74.0060)
        for i in range(4):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # Cluster outside bounds: 5 reports around (41.0000, -75.0000)
        for i in range(5):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 41.0000 + (i * 0.0001)
            report.longitude = -75.0000 + (i * 0.0001)
        
        db_session.commit()
        
        # Filter to only include first cluster
        heat_zones = analytics_service.get_heat_zones(
            min_lat=40.7,
            max_lat=40.8,
            min_lon=-74.1,
            max_lon=-74.0,
            min_reports=3
        )
        
        assert len(heat_zones) == 1
        assert heat_zones[0]["report_count"] == 4
    
    def test_heat_zones_exclude_archived_reports(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Archived reports should not be included in heat zones."""
        # Active reports: 3 reports
        for i in range(3):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
        
        # Archived reports: 2 reports in same area
        for i in range(2):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
            report.archived = True
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        # Should only count the 3 active reports
        assert len(heat_zones) == 1
        assert heat_zones[0]["report_count"] == 3
    
    def test_heat_zones_proximity_parameter(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Proximity parameter should affect clustering."""
        base_lat, base_lon = 40.7128, -74.0060
        
        # Create 6 reports in a line, each ~50m apart
        for i in range(6):
            report = create_report(db_session, test_user.id, status="Reported")
            # ~0.0005 degrees latitude ≈ 55 meters
            report.latitude = base_lat + (i * 0.0005)
            report.longitude = base_lon
        
        db_session.commit()
        
        # With 200m proximity, should form 1 large cluster (all reports within 200m)
        heat_zones_200m = analytics_service.get_heat_zones(
            proximity_meters=200.0,
            min_reports=3
        )
        
        # With 100m proximity, might form 2 clusters (reports at ends are ~275m apart)
        heat_zones_100m = analytics_service.get_heat_zones(
            proximity_meters=100.0,
            min_reports=3
        )
        
        # 200m proximity should create fewer or equal clusters than 100m
        assert len(heat_zones_200m) <= len(heat_zones_100m)
        # With 200m, all 6 reports should be in one cluster
        assert len(heat_zones_200m) >= 1
    
    def test_heat_zone_contains_report_ids(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Each heat zone should contain the IDs of reports in that cluster."""
        report_ids = []
        
        # Create 4 nearby reports
        for i in range(4):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = 40.7128 + (i * 0.0001)
            report.longitude = -74.0060 + (i * 0.0001)
            report_ids.append(str(report.id))
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        assert len(heat_zones) == 1
        zone_report_ids = heat_zones[0]["report_ids"]
        
        # All created report IDs should be in the zone
        for report_id in report_ids:
            assert report_id in zone_report_ids
    
    def test_heat_zone_centroid_calculation(
        self, db_session: Session, analytics_service: AnalyticsService, test_user: User
    ):
        """Heat zone location should be near the centroid of clustered reports."""
        base_lat, base_lon = 40.7128, -74.0060
        
        # Create 3 reports in a tight cluster
        for i in range(3):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = base_lat + (i * 0.0001)
            report.longitude = base_lon + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        assert len(heat_zones) == 1
        zone = heat_zones[0]
        
        # Zone location should be close to the base location
        assert abs(zone["latitude"] - base_lat) < 0.001
        assert abs(zone["longitude"] - base_lon) < 0.001
    
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_reports=st.integers(min_value=3, max_value=30),
        min_reports_threshold=st.integers(min_value=2, max_value=5)
    )
    def test_property_all_zones_meet_minimum(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        num_reports: int,
        min_reports_threshold: int
    ):
        """
        Property: All returned heat zones should have at least min_reports reports.
        
        For any set of reports and any min_reports threshold, every heat zone
        in the result should have a report_count >= min_reports.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        base_lat, base_lon = 40.7128, -74.0060
        
        # Create reports in a cluster
        for i in range(num_reports):
            report = create_report(db_session, test_user.id, status="Reported")
            report.latitude = base_lat + (i * 0.0001)
            report.longitude = base_lon + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=min_reports_threshold)
        
        # Every zone should meet the minimum threshold
        for zone in heat_zones:
            assert zone["report_count"] >= min_reports_threshold
    
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        cluster_sizes=st.lists(
            st.integers(min_value=3, max_value=10),
            min_size=2,
            max_size=5
        )
    )
    def test_property_zones_sorted_descending(
        self,
        db_session: Session,
        analytics_service: AnalyticsService,
        test_user: User,
        cluster_sizes: list
    ):
        """
        Property: Heat zones should always be sorted by report count in descending order.
        
        For any set of clusters with different sizes, the returned heat zones
        should be ordered from highest to lowest report count.
        """
        # Clear any existing reports
        db_session.query(Report).delete()
        db_session.commit()
        
        # Create multiple clusters with different sizes
        base_locations = [
            (40.7128, -74.0060),
            (40.7500, -73.9900),
            (40.7300, -74.0200),
            (40.7700, -73.9700),
            (40.7000, -74.0300),
        ]
        
        for idx, size in enumerate(cluster_sizes):
            if idx >= len(base_locations):
                break
            
            base_lat, base_lon = base_locations[idx]
            for i in range(size):
                report = create_report(db_session, test_user.id, status="Reported")
                report.latitude = base_lat + (i * 0.0001)
                report.longitude = base_lon + (i * 0.0001)
        
        db_session.commit()
        
        heat_zones = analytics_service.get_heat_zones(min_reports=3)
        
        # Verify zones are sorted in descending order
        for i in range(len(heat_zones) - 1):
            assert heat_zones[i]["report_count"] >= heat_zones[i + 1]["report_count"]
