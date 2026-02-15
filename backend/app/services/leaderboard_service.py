"""
Leaderboard service for ranking users by report count.

Requirements: 7.1, 7.2, 7.4, 7.6
"""
from typing import List

from sqlalchemy.orm import Session

from app.models.user import User


class LeaderboardService:
    """Service for leaderboard ranking and filtering."""

    def __init__(self, db: Session):
        self.db = db

    def get_top_users(self, limit: int = 10) -> List[User]:
        """
        Get top users by report count, excluding opted-out users.
        Property 22: Leaderboard Ranking (Req 7.2)
        Property 24: Leaderboard Opt-Out Privacy (Req 7.6)
        """
        return (
            self.db.query(User)
            .filter(User.leaderboard_opt_out == False)
            .filter(User.report_count > 0)
            .order_by(User.report_count.desc())
            .limit(limit)
            .all()
        )
