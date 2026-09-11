"""
Router: points — صفحة "نقاطي" (عام) + لوحة ترتيب المسابقة (super_admin فقط).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_public_lookup, require_role
from app.models import AccountRole
from app.routers.points import point_service
from app.routers.points.point_schema import LeaderboardResponse, PointsResponse

router = APIRouter(tags=["points"])


@router.get(
    "/students/{unique_code}/points",
    response_model=PointsResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def get_points(unique_code: str, db: Session = Depends(get_db)) -> PointsResponse:
    total_points = point_service.get_points(db, unique_code)
    return PointsResponse(total_points=total_points)


@router.get(
    "/admin/points/leaderboard",
    response_model=LeaderboardResponse,
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)
def get_leaderboard(db: Session = Depends(get_db)) -> LeaderboardResponse:
    leaderboard = point_service.get_leaderboard(db)
    return LeaderboardResponse(leaderboard=leaderboard)