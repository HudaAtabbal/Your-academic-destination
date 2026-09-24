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
    AnalyticsResponse,
    CertificateCountItem,
    CheckinDeleteResponse,
    CollegeVisitItem,
    DashboardStatsResponse,
    HallClearResponse,
    HallStudentItem,
    HallStudentsResponse,
    LectureAttendanceItem,
    RegisteredNoShowItem,
    RegisteredNoShowListResponse,
    RoomOccupancyItem,
    RoomsOccupancyResponse,
    ScoreBucketItem,
    SmsCounts,
    SmsStatusResponse,
    StudentsInsideItem,
    StudentsInsideListResponse,
    SurveyCompletionItem,
    SurveyCompletionsResponse,
    UnionSectionCountItem,
    YearCountItem,
)
from app.models import Lecture

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


@router.get("/rooms-occupancy/{lecture_name}", response_model=HallStudentsResponse)
def hall_students(
    lecture_name: Lecture, db: Session = Depends(get_db)
) -> HallStudentsResponse:
    students = dashboard_service.list_hall_students(db, lecture_name)
    return HallStudentsResponse(
        lecture_name=lecture_name,
        hall_label=dashboard_service.get_hall_label(),
        current_count=len(students),
        students=[HallStudentItem(**s) for s in students],
    )


@router.delete("/rooms-occupancy/{lecture_name}", response_model=HallClearResponse)
def clear_hall(
    lecture_name: Lecture, db: Session = Depends(get_db)
) -> HallClearResponse:
    deleted_count = dashboard_service.clear_hall_occupancy(db, lecture_name)
    return HallClearResponse(
        lecture_name=lecture_name,
        hall_label=dashboard_service.get_hall_label(),
        deleted_count=deleted_count,
    )


@router.delete("/checkins/{checkin_id}", response_model=CheckinDeleteResponse)
def delete_checkin(checkin_id: int, db: Session = Depends(get_db)) -> CheckinDeleteResponse:
    dashboard_service.delete_checkin_by_id(db, checkin_id)
    return CheckinDeleteResponse(checkin_id=checkin_id, deleted=True)


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


@router.get("/survey-completions", response_model=SurveyCompletionsResponse)
def survey_completions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    code: str | None = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
) -> SurveyCompletionsResponse:
    items, total = dashboard_service.list_survey_completions(
        db, page, limit, code=code
    )
    return SurveyCompletionsResponse(
        items=[SurveyCompletionItem(**item) for item in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, math.ceil(total / limit)),
    )


@router.get("/registered-no-shows", response_model=RegisteredNoShowListResponse)
def registered_no_shows(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    code: str | None = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
) -> RegisteredNoShowListResponse:
    items, total = dashboard_service.list_registered_no_shows(
        db, page, limit, code=code
    )
    return RegisteredNoShowListResponse(
        items=[RegisteredNoShowItem(**item) for item in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, math.ceil(total / limit)),
    )


@router.get("/analytics", response_model=AnalyticsResponse)
def dashboard_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    analytics = dashboard_service.get_dashboard_analytics(db)
    return AnalyticsResponse(
        college_visits=[CollegeVisitItem(**i) for i in analytics["college_visits"]],
        lecture_attendance=[
            LectureAttendanceItem(**i) for i in analytics["lecture_attendance"]
        ],
        score_distribution=[ScoreBucketItem(**i) for i in analytics["score_distribution"]],
        year_distribution=[YearCountItem(**i) for i in analytics["year_distribution"]],
        certificate_distribution=[
            CertificateCountItem(**i) for i in analytics["certificate_distribution"]
        ],
        union_sections=[
            UnionSectionCountItem(**i) for i in analytics["union_sections"]
        ],
    )