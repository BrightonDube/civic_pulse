"""
Leaderboard API endpoints.

Requirements: 7.2, 7.4, 7.6
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    email: str
    report_count: int


@router.get("/", response_model=list[LeaderboardEntry])
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get top users by report count. Requirements: 7.2, 7.6"""
    service = LeaderboardService(db)
    users = service.get_top_users(limit=min(limit, 100))
    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=str(u.id),
            email=u.email,
            report_count=u.report_count,
        )
        for i, u in enumerate(users)
    ]
