"""
Analytics service for calculating key metrics and generating reports.

Requirements: 13.1, 13.2, 13.3, 13.4
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
from functools import lru_cache
import hashlib
import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.report import Report, VALID_STATUSES


class KeyMetrics:
    """Data class for key analytics metrics."""
    
    def __init__(
        self,
        total_reports: int,
        resolution_rate: float,
        average_resolution_time: Optional[float]
    ):
        self.total_reports = total_reports
        self.resolution_rate = resolution_rate
        self.average_resolution_time = average_resolution_time
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "total_reports": self.total_reports,
            "resolution_rate": self.resolution_rate,
            "average_resolution_time": self.average_resolution_time
        }


class TrendPoint:
    """Data class for a single point in trend data."""
    
    def __init__(self, period: str, count: int):
        self.period = period
        self.count = count
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "period": self.period,
            "count": self.count
        }


class SeverityTrendPoint:
    """Data class for a single point in severity trend data."""
    
    def __init__(self, period: str, average_severity: float, report_count: int):
        self.period = period
        self.average_severity = average_severity
        self.report_count = report_count
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "period": self.period,
            "average_severity": self.average_severity,
            "report_count": self.report_count
        }


class AnalyticsService:
    """
    Service for calculating analytics metrics with caching support.
    
    Property 40: Analytics Key Metrics Calculation
    For any set of reports with various statuses and timestamps, the calculated
    key metrics (total reports, resolution rate percentage, average resolution time)
    should accurately reflect the underlying data.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, tuple] = {}  # cache_key -> (value, timestamp)
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def _get_cache_key(self, filters: Dict) -> str:
        """Generate a cache key from filter parameters."""
        # Sort keys for consistent hashing
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        return hashlib.md5(filter_str.encode()).hexdigest()
    
    def _get_cached(self, cache_key: str) -> Optional[KeyMetrics]:
        """Get cached value if still valid."""
        if cache_key in self._cache:
            value, timestamp = self._cache[cache_key]
            age = (datetime.now(timezone.utc) - timestamp).total_seconds()
            if age < self._cache_ttl:
                return value
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, value: KeyMetrics) -> None:
        """Store value in cache with current timestamp."""
        self._cache[cache_key] = (value, datetime.now(timezone.utc))
    
    def clear_cache(self) -> None:
        """Clear all cached values. Useful for testing or after bulk updates."""
        self._cache.clear()
    
    def get_key_metrics(
        self,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> KeyMetrics:
        """
        Calculate key metrics: total reports, resolution rate, average resolution time.
        
        Resolution rate = (Fixed reports / Total reports) * 100
        Average resolution time = Average time from created_at to updated_at for Fixed reports
        
        Implements caching for expensive calculations.
        Requirements: 13.1
        """
        # Build cache key from filters
        filters = {
            "category": category,
            "date_from": date_from,
            "date_to": date_to,
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        }
        cache_key = self._get_cache_key(filters)
        
        # Check cache
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)
        
        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Calculate total reports
        total_reports = query.count()
        
        # Calculate resolution rate
        if total_reports > 0:
            fixed_count = query.filter(Report.status == "Fixed").count()
            resolution_rate = (fixed_count / total_reports) * 100.0
        else:
            resolution_rate = 0.0
        
        # Calculate average resolution time for Fixed reports
        fixed_reports = query.filter(Report.status == "Fixed").all()
        if fixed_reports:
            total_resolution_time = 0.0
            for report in fixed_reports:
                resolution_time = (report.updated_at - report.created_at).total_seconds()
                total_resolution_time += resolution_time
            average_resolution_time = total_resolution_time / len(fixed_reports)
        else:
            average_resolution_time = None
        
        # Create metrics object
        metrics = KeyMetrics(
            total_reports=total_reports,
            resolution_rate=resolution_rate,
            average_resolution_time=average_resolution_time
        )
        
        # Cache the result
        self._set_cache(cache_key, metrics)
        
        return metrics
    
    def get_trend_data(
        self,
        period: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> List[TrendPoint]:
        """
        Get trend data aggregated by time period (daily, weekly, monthly).
        
        Groups reports by the specified time period and returns counts for each period.
        
        Property 41: Trend Data Aggregation
        For any set of reports and time period (daily, weekly, monthly), grouping reports
        by that period should produce counts that sum to the total number of reports.
        
        Args:
            period: One of "daily", "weekly", "monthly"
            category: Optional category filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        
        Returns:
            List of TrendPoint objects with period labels and counts
        
        Requirements: 13.2
        """
        if period not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid period: {period}. Must be 'daily', 'weekly', or 'monthly'")
        
        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)
        
        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Get all reports matching filters
        reports = query.all()
        
        # Group reports by time period
        period_counts: Dict[str, int] = {}
        
        for report in reports:
            period_key = self._get_period_key(report.created_at, period)
            period_counts[period_key] = period_counts.get(period_key, 0) + 1
        
        # Convert to list of TrendPoint objects, sorted by period
        trend_points = [
            TrendPoint(period=period_key, count=count)
            for period_key, count in sorted(period_counts.items())
        ]
        
        return trend_points
    
    def _get_period_key(self, dt: datetime, period: str) -> str:
        """
        Generate a period key for grouping reports.
        
        Args:
            dt: Datetime to convert to period key
            period: One of "daily", "weekly", "monthly"
        
        Returns:
            String representation of the period (e.g., "2024-01-15", "2024-W03", "2024-01")
        """
        if period == "daily":
            return dt.strftime("%Y-%m-%d")
        elif period == "weekly":
            # ISO week format: YYYY-Www
            year, week, _ = dt.isocalendar()
            return f"{year}-W{week:02d}"
        elif period == "monthly":
            return dt.strftime("%Y-%m")
        else:
            raise ValueError(f"Invalid period: {period}")
    
    def get_category_distribution(
        self,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> Dict[str, int]:
        """
        Calculate report counts by category for distribution analysis.
        
        Property 42: Category Distribution Accuracy
        For any set of reports, the sum of category counts should equal the total
        number of reports.
        
        Args:
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        
        Returns:
            Dictionary mapping category names to report counts
        
        Requirements: 13.3
        """
        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)
        
        # Apply filters
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Get all reports matching filters
        reports = query.all()
        
        # Count reports by category
        category_counts: Dict[str, int] = {}
        for report in reports:
            category = report.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts


    def get_severity_trends(
        self,
        period: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> List['SeverityTrendPoint']:
        """
        Calculate average severity by time period and track severity changes over time.
        
        Property 43: Severity Trend Accuracy
        For any set of reports grouped by time period, the severity trend data should
        correctly represent the average severity scores for each period.
        
        Args:
            period: One of "daily", "weekly", "monthly"
            category: Optional category filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        
        Returns:
            List of SeverityTrendPoint objects with period labels, average severity, and report counts
        
        Requirements: 13.4
        """
        if period not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"Invalid period: {period}. Must be 'daily', 'weekly', or 'monthly'")
        
        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)
        
        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Get all reports matching filters
        reports = query.all()
        
        # Group reports by time period and calculate average severity
        period_data: Dict[str, Dict[str, any]] = {}
        
        for report in reports:
            period_key = self._get_period_key(report.created_at, period)
            
            if period_key not in period_data:
                period_data[period_key] = {
                    'total_severity': 0,
                    'count': 0
                }
            
            period_data[period_key]['total_severity'] += report.severity_score
            period_data[period_key]['count'] += 1
        
        # Calculate average severity for each period and create SeverityTrendPoint objects
        severity_trends = []
        for period_key in sorted(period_data.keys()):
            data = period_data[period_key]
            average_severity = data['total_severity'] / data['count']
            
            severity_trends.append(
                SeverityTrendPoint(
                    period=period_key,
                    average_severity=average_severity,
                    report_count=data['count']
                )
            )
        
        return severity_trends

    def get_heat_zones(
        self,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        proximity_meters: float = 200.0,
        min_reports: int = 3
    ) -> List[Dict]:
        """
        Identify geographic heat zones with high concentrations of unresolved reports.
        
        Uses spatial clustering to group nearby reports and identify areas with
        the highest concentration of issues. Only returns zones with at least
        min_reports reports.
        
        Property 44: Heat Zone Identification
        For any set of unresolved reports, geographic heat zones should correctly
        identify areas with the highest concentration of reports based on spatial clustering.
        
        Args:
            category: Optional category filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
            proximity_meters: Distance threshold for clustering (default: 200 meters)
            min_reports: Minimum reports required to form a heat zone (default: 3)
        
        Returns:
            List of heat zone dictionaries with latitude, longitude, and report_count,
            sorted by report count in descending order
        
        Requirements: 13.5
        """
        # Build base query - focus on unresolved reports (not Fixed)
        query = self.db.query(Report).filter(
            Report.archived == False,
            Report.status != "Fixed"
        )
        
        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Get all unresolved reports matching filters
        reports = query.all()
        
        if not reports:
            return []
        
        # Use spatial clustering to identify high-concentration areas
        from app.services.clustering_service import cluster_reports
        
        clusters = cluster_reports(reports, proximity_meters=proximity_meters)
        
        # Filter clusters to only include heat zones with minimum report count
        heat_zones = [
            {
                "latitude": cluster.latitude,
                "longitude": cluster.longitude,
                "report_count": cluster.count,
                "report_ids": cluster.report_ids
            }
            for cluster in clusters
            if cluster.count >= min_reports
        ]
        
        # Sort by report count in descending order (highest concentration first)
        heat_zones.sort(key=lambda x: x["report_count"], reverse=True)
        
        return heat_zones

    def export_to_csv(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> bytes:
        """
        Generate CSV file from filtered report data.
        
        Exports all report fields including:
        - id, user_id, photo_url
        - latitude, longitude
        - category, severity_score, status
        - upvote_count, ai_generated, archived
        - created_at, updated_at
        
        Property 45: CSV Export Round Trip
        For any set of filtered reports, exporting to CSV then parsing the CSV
        should produce equivalent report data.
        
        Args:
            category: Optional category filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        
        Returns:
            CSV file content as bytes
        
        Requirements: 13.6
        """
        import csv
        import io
        
        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)
        
        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)
        
        # Get all reports matching filters
        reports = query.all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row with all report fields
        writer.writerow([
            'id',
            'user_id',
            'photo_url',
            'latitude',
            'longitude',
            'category',
            'severity_score',
            'status',
            'upvote_count',
            'ai_generated',
            'archived',
            'created_at',
            'updated_at'
        ])
        
        # Write data rows
        for report in reports:
            writer.writerow([
                str(report.id),
                str(report.user_id),
                report.photo_url,
                report.latitude,
                report.longitude,
                report.category,
                report.severity_score,
                report.status,
                report.upvote_count,
                report.ai_generated,
                report.archived,
                report.created_at.isoformat(),
                report.updated_at.isoformat()
            ])
        
        # Get CSV content as bytes
        csv_content = output.getvalue()
        output.close()
        
        return csv_content.encode('utf-8')

    def export_to_csv(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> bytes:
        """
        Generate CSV file from filtered report data.

        Exports all report fields including:
        - id, user_id, photo_url
        - latitude, longitude
        - category, severity_score, status
        - upvote_count, ai_generated, archived
        - created_at, updated_at

        Property 45: CSV Export Round Trip
        For any set of filtered reports, exporting to CSV then parsing the CSV
        should produce equivalent report data.

        Args:
            category: Optional category filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds

        Returns:
            CSV file content as bytes

        Requirements: 13.6
        """
        import csv
        import io

        # Build base query
        query = self.db.query(Report).filter(Report.archived == False)

        # Apply filters
        if category:
            query = query.filter(Report.category == category)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= date_from)
        if date_to:
            query = query.filter(Report.created_at <= date_to)
        if min_lat is not None:
            query = query.filter(Report.latitude >= min_lat)
        if max_lat is not None:
            query = query.filter(Report.latitude <= max_lat)
        if min_lon is not None:
            query = query.filter(Report.longitude >= min_lon)
        if max_lon is not None:
            query = query.filter(Report.longitude <= max_lon)

        # Get all reports matching filters
        reports = query.all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row with all report fields
        writer.writerow([
            'id',
            'user_id',
            'photo_url',
            'latitude',
            'longitude',
            'category',
            'severity_score',
            'status',
            'upvote_count',
            'ai_generated',
            'archived',
            'created_at',
            'updated_at'
        ])

        # Write data rows
        for report in reports:
            writer.writerow([
                str(report.id),
                str(report.user_id),
                report.photo_url,
                report.latitude,
                report.longitude,
                report.category,
                report.severity_score,
                report.status,
                report.upvote_count,
                report.ai_generated,
                report.archived,
                report.created_at.isoformat(),
                report.updated_at.isoformat()
            ])

        # Get CSV content as bytes
        csv_content = output.getvalue()
        output.close()

        return csv_content.encode('utf-8')


    def export_to_pdf(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> bytes:
        """
        Generate PDF report with summary statistics and visualizations.
        
        The PDF includes:
        - Key metrics (total reports, resolution rate, average resolution time)
        - Category distribution chart
        - Trend analysis chart (last 30 days)
        - Severity trends chart
        - Heat zones table
        
        Args:
            category: Optional category filter
            status: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        
        Returns:
            PDF file content as bytes
        
        Requirements: 13.7
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.linecharts import HorizontalLineChart
        from reportlab.lib.enums import TA_CENTER
        import io
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("CivicPulse Analytics Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Report metadata
        report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        story.append(Paragraph(f"Generated: {report_date}", styles['Normal']))
        
        # Add filter information if any
        filter_info = []
        if category:
            filter_info.append(f"Category: {category}")
        if status:
            filter_info.append(f"Status: {status}")
        if date_from:
            filter_info.append(f"From: {date_from.strftime('%Y-%m-%d')}")
        if date_to:
            filter_info.append(f"To: {date_to.strftime('%Y-%m-%d')}")
        
        if filter_info:
            story.append(Paragraph(f"Filters: {', '.join(filter_info)}", styles['Normal']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # 1. Key Metrics Section
        story.append(Paragraph("Key Metrics", heading_style))
        
        metrics = self.get_key_metrics(
            category=category,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        # Format average resolution time
        if metrics.average_resolution_time is not None:
            hours = metrics.average_resolution_time / 3600
            avg_time_str = f"{hours:.1f} hours"
        else:
            avg_time_str = "N/A"
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Reports', str(metrics.total_reports)],
            ['Resolution Rate', f"{metrics.resolution_rate:.1f}%"],
            ['Average Resolution Time', avg_time_str],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3 * inch, 2 * inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # 2. Category Distribution Section
        story.append(Paragraph("Category Distribution", heading_style))
        
        category_dist = self.get_category_distribution(
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        if category_dist:
            # Create pie chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            
            # Prepare data
            categories = list(category_dist.keys())
            values = list(category_dist.values())
            pie.data = values
            pie.labels = categories
            
            # Color scheme
            colors_list = [
                colors.HexColor('#1a73e8'),
                colors.HexColor('#34a853'),
                colors.HexColor('#fbbc04'),
                colors.HexColor('#ea4335'),
                colors.HexColor('#9334e6'),
                colors.HexColor('#ff6d00'),
            ]
            pie.slices.strokeWidth = 0.5
            for i, color in enumerate(colors_list[:len(values)]):
                pie.slices[i].fillColor = color
            
            drawing.add(pie)
            story.append(drawing)
            
            # Add table with counts
            cat_table_data = [['Category', 'Count']]
            for cat, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
                cat_table_data.append([cat, str(count)])
            
            cat_table = Table(cat_table_data, colWidths=[3 * inch, 2 * inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(Spacer(1, 0.2 * inch))
            story.append(cat_table)
        else:
            story.append(Paragraph("No data available", styles['Normal']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # 3. Trend Analysis Section (Last 30 days)
        story.append(Paragraph("Report Trends (Last 30 Days)", heading_style))
        
        # Calculate date range for last 30 days
        trend_date_to = datetime.now(timezone.utc)
        trend_date_from = trend_date_to - timedelta(days=30)
        
        trends = self.get_trend_data(
            period="daily",
            category=category,
            status=status,
            date_from=trend_date_from,
            date_to=trend_date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        if trends:
            # Create line chart
            drawing = Drawing(500, 200)
            lc = HorizontalLineChart()
            lc.x = 50
            lc.y = 50
            lc.height = 125
            lc.width = 400
            
            # Prepare data
            lc.data = [[trend.count for trend in trends]]
            lc.categoryAxis.categoryNames = [trend.period for trend in trends]
            lc.categoryAxis.labels.angle = 45
            lc.categoryAxis.labels.fontSize = 6
            lc.valueAxis.valueMin = 0
            lc.valueAxis.valueMax = max([trend.count for trend in trends]) * 1.2 if trends else 10
            lc.lines[0].strokeColor = colors.HexColor('#1a73e8')
            lc.lines[0].strokeWidth = 2
            
            drawing.add(lc)
            story.append(drawing)
        else:
            story.append(Paragraph("No trend data available", styles['Normal']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # 4. Severity Trends Section
        story.append(Paragraph("Severity Trends (Last 30 Days)", heading_style))
        
        severity_trends = self.get_severity_trends(
            period="daily",
            category=category,
            status=status,
            date_from=trend_date_from,
            date_to=trend_date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        if severity_trends:
            # Create line chart for severity
            drawing = Drawing(500, 200)
            lc = HorizontalLineChart()
            lc.x = 50
            lc.y = 50
            lc.height = 125
            lc.width = 400
            
            # Prepare data
            lc.data = [[trend.average_severity for trend in severity_trends]]
            lc.categoryAxis.categoryNames = [trend.period for trend in severity_trends]
            lc.categoryAxis.labels.angle = 45
            lc.categoryAxis.labels.fontSize = 6
            lc.valueAxis.valueMin = 0
            lc.valueAxis.valueMax = 10
            lc.lines[0].strokeColor = colors.HexColor('#ea4335')
            lc.lines[0].strokeWidth = 2
            
            drawing.add(lc)
            story.append(drawing)
        else:
            story.append(Paragraph("No severity trend data available", styles['Normal']))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # 5. Heat Zones Section
        story.append(Paragraph("Top Heat Zones (Unresolved Reports)", heading_style))
        
        heat_zones = self.get_heat_zones(
            category=category,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            proximity_meters=200.0,
            min_reports=3
        )
        
        if heat_zones:
            # Show top 10 heat zones
            heat_table_data = [['Rank', 'Location (Lat, Lon)', 'Report Count']]
            for i, zone in enumerate(heat_zones[:10], 1):
                lat = f"{zone['latitude']:.4f}"
                lon = f"{zone['longitude']:.4f}"
                heat_table_data.append([
                    str(i),
                    f"({lat}, {lon})",
                    str(zone['report_count'])
                ])
            
            heat_table = Table(heat_table_data, colWidths=[0.8 * inch, 3 * inch, 1.5 * inch])
            heat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(heat_table)
        else:
            story.append(Paragraph("No heat zones identified", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
