"""
Report clustering service for heat map display.

Groups nearby reports into clusters with count.

Requirements: 3.3
"""
import math
from dataclasses import dataclass, field
from typing import List

from app.models.report import Report
from app.services.duplicate_service import DuplicateDetectionService


@dataclass
class Cluster:
    """A cluster of nearby reports."""
    latitude: float
    longitude: float
    count: int
    report_ids: List[str] = field(default_factory=list)


def cluster_reports(reports: List[Report], proximity_meters: float = 100.0) -> List[Cluster]:
    """
    Group reports into clusters based on proximity.
    Property 8: Report Clustering (Req 3.3)
    
    Simple greedy clustering: iterate through reports,
    assign to nearest existing cluster or create new one.
    """
    clusters: List[Cluster] = []

    for report in reports:
        assigned = False
        for cluster in clusters:
            dist = DuplicateDetectionService.calculate_distance(
                report.latitude, report.longitude,
                cluster.latitude, cluster.longitude,
            )
            if dist <= proximity_meters:
                # Update cluster centroid (weighted average)
                total = cluster.count + 1
                cluster.latitude = (cluster.latitude * cluster.count + report.latitude) / total
                cluster.longitude = (cluster.longitude * cluster.count + report.longitude) / total
                cluster.count = total
                cluster.report_ids.append(str(report.id))
                assigned = True
                break

        if not assigned:
            clusters.append(Cluster(
                latitude=report.latitude,
                longitude=report.longitude,
                count=1,
                report_ids=[str(report.id)],
            ))

    return clusters
