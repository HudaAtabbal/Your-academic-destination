"""
Pydantic schemas لروتر points — صفحة "نقاطي" ولوحة ترتيب المسابقة.
"""

from pydantic import BaseModel


class PointsResponse(BaseModel):
    total_points: int


class LeaderboardEntry(BaseModel):
    unique_code: str
    full_name: str | None = None
    total_points: int


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]