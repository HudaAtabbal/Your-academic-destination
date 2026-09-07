"""
Router: admin/students — راجع قسم 6 بملف wijhatak_api_contract.md
الدور المسموح: students_admin أو super_admin.
"""

import math

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import AccountRole
from app.routers.students import student_service
from app.routers.students.student_schema import (
    StudentDetail,
    StudentStatsResponse,
    StudentUpdateRequest,
    WalkinIncompleteItem,
    WalkinIncompleteListResponse,
)

router = APIRouter(
    prefix="/admin/students",
    tags=["admin - students"],
    dependencies=[Depends(require_role(AccountRole.students_admin, AccountRole.super_admin))],
)


@router.get("/search", response_model=StudentDetail)
def search_student(code: str, db: Session = Depends(get_db)) -> StudentDetail:
    student = student_service.find_student_by_code(db, code)
    return StudentDetail.model_validate(student)


@router.patch("/{student_id}", response_model=StudentDetail)
def update_student(
    student_id: int, payload: StudentUpdateRequest, db: Session = Depends(get_db)
) -> StudentDetail:
    updates = payload.model_dump(exclude_unset=True)
    student = student_service.update_student(db, student_id, updates)
    return StudentDetail.model_validate(student)


@router.get("/stats", response_model=StudentStatsResponse)
def student_stats(db: Session = Depends(get_db)) -> StudentStatsResponse:
    total_registered, walkin_pending_count = student_service.get_student_stats(db)
    return StudentStatsResponse(
        total_registered=total_registered, walkin_pending_count=walkin_pending_count
    )


@router.get("/walkin-incomplete", response_model=WalkinIncompleteListResponse)
def walkin_incomplete(
    page: int = 1, limit: int = 20, db: Session = Depends(get_db)
) -> WalkinIncompleteListResponse:
    items, total = student_service.list_walkin_incomplete(db, page, limit)
    return WalkinIncompleteListResponse(
        items=[WalkinIncompleteItem(**item) for item in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, math.ceil(total / limit)),
    )