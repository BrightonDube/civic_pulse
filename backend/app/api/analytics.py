"""
Analytics API endpoints for key metrics and reporting.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/metrics")
def get_key_metrics(
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get key analytics metrics: total reports, resolution rate, average resolution time.
    
    Admin-only endpoint.
    Requirements: 13.1
    """
    analytics_service = AnalyticsService(db)
    
    try:
        metrics = analytics_service.get_key_metrics(
            category=category,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return metrics.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@router.get("/trends/daily")
def get_daily_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get daily trend data showing report counts grouped by day.
    
    Admin-only endpoint.
    Requirements: 13.2
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_trend_data(
            period="daily",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")


@router.get("/trends/weekly")
def get_weekly_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get weekly trend data showing report counts grouped by week.
    
    Admin-only endpoint.
    Requirements: 13.2
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_trend_data(
            period="weekly",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")


@router.get("/trends/monthly")
def get_monthly_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get monthly trend data showing report counts grouped by month.
    
    Admin-only endpoint.
    Requirements: 13.2
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_trend_data(
            period="monthly",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")


@router.get("/category-distribution")
def get_category_distribution(
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get category distribution showing report counts by category.
    
    Returns a dictionary mapping category names to report counts,
    useful for generating distribution charts.
    
    Admin-only endpoint.
    Requirements: 13.3
    """
    analytics_service = AnalyticsService(db)
    
    try:
        distribution = analytics_service.get_category_distribution(
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return distribution
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate category distribution: {str(e)}")


@router.get("/severity-trends/daily")
def get_daily_severity_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get daily severity trend data showing average severity scores grouped by day.
    
    Admin-only endpoint.
    Requirements: 13.4
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_severity_trends(
            period="daily",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate severity trends: {str(e)}")


@router.get("/severity-trends/weekly")
def get_weekly_severity_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get weekly severity trend data showing average severity scores grouped by week.
    
    Admin-only endpoint.
    Requirements: 13.4
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_severity_trends(
            period="weekly",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate severity trends: {str(e)}")


@router.get("/severity-trends/monthly")
def get_monthly_severity_trends(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get monthly severity trend data showing average severity scores grouped by month.
    
    Admin-only endpoint.
    Requirements: 13.4
    """
    analytics_service = AnalyticsService(db)
    
    try:
        trends = analytics_service.get_severity_trends(
            period="monthly",
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        return [trend.to_dict() for trend in trends]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate severity trends: {str(e)}")


@router.get("/heat-zones")
def get_heat_zones(
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    proximity_meters: float = 200.0,
    min_reports: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get geographic heat zones identifying areas with high concentrations of unresolved reports.
    
    Uses spatial clustering to group nearby reports and returns zones sorted by
    report count (highest concentration first). Only includes zones with at least
    min_reports reports.
    
    Admin-only endpoint.
    Requirements: 13.5
    
    Args:
        category: Optional category filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
        proximity_meters: Distance threshold for clustering (default: 200 meters)
        min_reports: Minimum reports required to form a heat zone (default: 3)
    
    Returns:
        List of heat zones with latitude, longitude, report_count, and report_ids,
        sorted by report count in descending order
    """
    analytics_service = AnalyticsService(db)
    
    try:
        heat_zones = analytics_service.get_heat_zones(
            category=category,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            proximity_meters=proximity_meters,
            min_reports=min_reports,
        )
        return heat_zones
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify heat zones: {str(e)}")


@router.get("/export/csv")
def export_reports_csv(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Export filtered report data to CSV file.
    
    Generates a CSV file containing all report fields for reports matching
    the specified filter criteria. The CSV includes:
    - id, user_id, photo_url
    - latitude, longitude
    - category, severity_score, status
    - upvote_count, ai_generated, archived
    - created_at, updated_at
    
    Admin-only endpoint.
    Requirements: 13.6
    
    Args:
        category: Optional category filter
        status: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
    
    Returns:
        CSV file as downloadable attachment
    """
    from fastapi.responses import Response
    
    analytics_service = AnalyticsService(db)
    
    try:
        csv_content = analytics_service.export_to_csv(
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"civicpulse_reports_{timestamp}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get("/export/pdf")
def export_reports_pdf(
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Export analytics report to PDF file with summary statistics and visualizations.
    
    Generates a comprehensive PDF report containing:
    - Key metrics (total reports, resolution rate, average resolution time)
    - Category distribution chart (pie chart)
    - Report trends chart (last 30 days)
    - Severity trends chart (last 30 days)
    - Top heat zones table
    
    Admin-only endpoint.
    Requirements: 13.7
    
    Args:
        category: Optional category filter
        status: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        min_lat, max_lat, min_lon, max_lon: Optional geographic bounds
    
    Returns:
        PDF file as downloadable attachment
    """
    from fastapi.responses import Response
    
    analytics_service = AnalyticsService(db)
    
    try:
        pdf_content = analytics_service.export_to_pdf(
            category=category,
            status=status,
            date_from=date_from,
            date_to=date_to,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"civicpulse_analytics_{timestamp}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")
