"""
Router: students/page-visit — تتبّع فتح الدليل الأكاديمي ومدّة البقاء.

مساران عامّان (من غير توكن): المتصفح يبدأ الزيارة بعد 3 ثواني حضور فعلي
على الصفحة، ويبلّغ النهاية لما يطلع منها. الحد على visitor_id مش على الـ IP
(كل الطلبة على نفس شبكة الجامعة) — راجع rate_limit_page_visit.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_page_visit
from app.errors import AppError
from app.routers.page_visits import page_visits_service
from app.routers.page_visits.page_visits_schema import (
    PageVisitEndRequest,
    PageVisitEndResponse,
    PageVisitStartRequest,
    PageVisitStartResponse,
)

router = APIRouter(prefix="/students", tags=["students - page visit"])


@router.post("/page-visit/start", response_model=PageVisitStartResponse)
def start_page_visit(
    payload: PageVisitStartRequest,
    db: Session = Depends(get_db),
) -> PageVisitStartResponse:
    """يسجّل بداية الزيارة ويقفل حدّ المعدّل لمعرّف المتصفح هذا."""
    rate_limit_page_visit(payload.visitor_id)
    visit = page_visits_service.start_visit(
        db, payload.page, payload.visitor_id, payload.student_code
    )
    return PageVisitStartResponse(
        visit_id=visit.id, entered_at=visit.entered_at.isoformat()
    )


@router.post("/page-visit/end", response_model=PageVisitEndResponse)
def end_page_visit(
    payload: PageVisitEndRequest,
    db: Session = Depends(get_db),
) -> PageVisitEndResponse:
    """يختم الزيارة — المدّة بينحسب بالسيرفر من رقم الصف، مش من المتصفح."""
    try:
        visit, duration = page_visits_service.end_visit(db, payload.visit_id)
    except LookupError:
        raise AppError(
            status_code=404,
            error_code="page_visit_not_found",
            message="الزيارة غير موجودة",
        )
    return PageVisitEndResponse(visit_id=visit.id, duration_seconds=duration)
