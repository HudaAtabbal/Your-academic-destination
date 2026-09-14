"""
Router: internal/sms — تواصل المُرسِل المحلي (لابتوب في سوريا) مع الخادم.

كل المسارات محمية بتوكن المُرسِل (WORKER_TOKEN) عبر require_worker_token —
مش توكن JWT للفريق، عشان المُرسِل ما يحتاج حساب قاعدة بيانات إطلاقاً.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_worker_token
from app.errors import AppError
from app.routers.internal import internal_service
from app.routers.internal.sms_schema import DequeueItem, ReportRequest, ReportResponse

router = APIRouter(
    prefix="/internal/sms",
    tags=["internal - sms"],
    dependencies=[Depends(require_worker_token)],
)


@router.post("/dequeue", response_model=list[DequeueItem])
def dequeue(
    batch: int = Query(1, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[dict]:
    """يسحب حتى batch مهمة pending — الرمز نصاً صريحاً جاهز للإرسال."""
    return internal_service.dequeue_jobs(db, batch)


@router.post("/report", response_model=ReportResponse)
def report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
) -> ReportResponse:
    try:
        job = internal_service.report_job(db, payload.job_id, payload.success, payload.transient, payload.error)
    except LookupError:
        raise AppError(
            status_code=404,
            error_code="job_not_found",
            message="مهمة الإرسال غير موجودة",
        )
    return ReportResponse(job_id=job.id, status=job.status)


@router.post("/heartbeat")
def heartbeat(db: Session = Depends(get_db)) -> dict:
    """نبضة حياة — جدول أحادي الصف؛ لوحة الإدارة تراقبها لتحديد حالة المرسل."""
    internal_service.record_heartbeat(db)
    return {"status": "ok"}
