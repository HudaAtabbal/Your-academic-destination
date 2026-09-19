"""
Router: admin/dashboard — راجع قسم 9 بملف wijhatak_api_contract.md
الدور المسموح: super_admin فقط.
"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import AccountRole
from app.routers.dashboard import dashboard_service
from app.routers.dashboard.dashboard_schema import (
    DashboardStatsResponse,
    RoomOccupancyItem,
    RoomsOccupancyResponse,
    SmsCounts,
    SmsStatusResponse,
    StudentsInsideItem,
    StudentsInsideListResponse,
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


@router.get("/sms-status", response_model=SmsStatusResponse)
def sms_status(db: Session = Depends(get_db)) -> SmsStatusResponse:
    status = dashboard_service.get_sms_status(db)
    return SmsStatusResponse(
        counts=SmsCounts(**status["counts"]),
        last_heartbeat=status["last_heartbeat"],
        worker_online=status["worker_online"],
    )


@router.get("/rooms-occupancy", response_model=RoomsOccupancyResponse)
def rooms_occupancy(db: Session = Depends(get_db)) -> RoomsOccupancyResponse:
    rooms = dashboard_service.get_rooms_occupancy(db)
    return RoomsOccupancyResponse(rooms=[RoomOccupancyItem(**r) for r in rooms])


@router.get("/students-inside", response_model=StudentsInsideListResponse)
def students_inside(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    code: str | None = Query(default=None, max_length=20),
    reg_type: str | None = Query(default=None, pattern="^(R|W)$"),
    order: str = Query("desc", pattern="^(desc|asc)$"),
    db: Session = Depends(get_db),
) -> StudentsInsideListResponse:
    items, total = dashboard_service.list_students_inside_all_days(
        db, page, limit, code=code, reg_type=reg_type, order=order
    )
    return StudentsInsideListResponse(
        items=[StudentsInsideItem(**item) for item in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, math.ceil(total / limit)),
    )