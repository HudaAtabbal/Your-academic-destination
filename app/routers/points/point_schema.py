"""
Pydantic schemas لروتر points — صفحة "نقاطي" ولوحة ترتيب المسابقة.
"""

from pydantic import BaseModel


class PointsResponse(BaseModel):
    total_points: int
    today_lecture_count: int = 0
    lectures_capped_today: bool = False
    today_tour_count: int = 0
    tours_capped_today: bool = False


class LeaderboardEntry(BaseModel):
    unique_code: str
    full_name: str | None = None
    total_points: int


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]