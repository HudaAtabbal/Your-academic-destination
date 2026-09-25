"""
Router: students/page-visit — تتبّع فتح الدليل الأكاديمي ومدّة البقاء.

مساران عامّان (من غير توكن): المتصفح يبدأ الزيارة بعد 3 ثواني حضور فعلي
على الصفحة، ويبلّغ النهاية لما يطلع منها. الحد على visitor_id مش على الـ IP
(كل الطلبة على نفس شبكة الجامعة) — راجع rate_limit_page_visit.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import cache
from app.database import get_db
from app.dependencies import rate_limit_page_visit, require_role
from app.errors import AppError
from app.models import AccountRole
from app.models.page_visit import PageVisit
from app.routers.page_visits import page_visits_service
from app.routers.page_visits.page_visits_schema import (
    PageVisitEndRequest,
    PageVisitEndResponse,
    PageVisitStartRequest,
    PageVisitStartResponse,
)

router = APIRouter(prefix="/students", tags=["students - page visit"])

# TEMPORARY maintenance endpoint (2026-09-26). Wipes page_visits so the guide
# stats start from real student traffic only. DELETE THIS ROUTE AFTER USE.
_PURGE_CONFIRM_PHRASE = "reset-guide-stats-2026-09-26"


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


# ---------------------------------------------------------------------------
# TEMPORARY — صيانة لمرة واحدة (2026-09-26). احذف هذا المسار بعد الاستخدام.
# ---------------------------------------------------------------------------


@router.delete(
    "/page-visits",
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)
def purge_page_visits(confirm: str, db: Session = Depends(get_db)) -> dict:
    """يحذف كل سجلات تتبّع الزيارات ويفرّغ كاش اللوحة — super_admin فقط."""
    if confirm != _PURGE_CONFIRM_PHRASE:
        raise AppError(
            status_code=400,
            error_code="confirm_mismatch",
            message="عبارة التأكيد غير مطابقة — ما انعمل شي",
        )
    deleted = db.query(PageVisit).delete()
    db.commit()
    cache.clear_cache()
    return {"deleted": int(deleted)}
