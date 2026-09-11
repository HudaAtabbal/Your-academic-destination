"""
Router: admin/dashboard — راجع قسم 9 بملف wijhatak_api_contract.md
الدور المسموح: super_admin فقط.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import AccountRole
from app.routers.dashboard import dashboard_service
from app.routers.dashboard.dashboard_schema import (
    DashboardStatsResponse,
    RoomOccupancyItem,
    RoomsOccupancyResponse,
)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin - dashboard"],
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    stats = dashboard_service.get_dashboard_stats(db)
    return DashboardStatsResponse(**stats)


@router.get("/rooms-occupancy", response_model=RoomsOccupancyResponse)
def rooms_occupancy(db: Session = Depends(get_db)) -> RoomsOccupancyResponse:
    rooms = dashboard_service.get_rooms_occupancy(db)
    return RoomsOccupancyResponse(rooms=[RoomOccupancyItem(**r) for r in rooms])