"""
Router: عجلة الحظ — لقطب الأدمن + شاشة الجمهور.

تقسيم النطاقات مقصود ومش صدفة:

  /admin/wheel/**  → super_admin فقط. كل التفاصيل: الأرقام المجمّدة، وقت
                      التجميد، أسماء المؤهلين.
  /wheel/live      → أي حساب مسجّل دخوله (حتى بدون دور إداري) لأنه شاشة
                      عرض مش بيانات إدارية. ست حقول فقط.

كل الـendpoints بدون أقواس {} يعني صفر قفل على الحفل: الأربعة تابات
مفتوحة ومستقلة والجمهور يقرأ نفس المعلومة.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_account, require_role
from app.errors import validation_error
from app.models import Account, AccountRole
from app.routers.wheel import wheel_service
from app.routers.wheel.wheel_schema import (
    LiveDrawResponse,
    WheelArchiveResponse,
    WheelCeremonySnapshot,
    WheelDecisionRequest,
    WheelDecisionResponse,
    WheelDrawRequest,
    WheelDrawResponse,
    WheelFreezeSettingsResponse,
    WheelFreezeUpdateRequest,
    WheelTabsResponse,
)

router = APIRouter(tags=["wheel"])
admin_router = APIRouter(
    prefix="/admin/wheel",
    tags=["wheel"],
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)


def _parse_prospective(raw: str | None) -> datetime | None:
    """حوّل معامل الاستعلام لنص ISO إلى datetime، أو 400 إذا مش صيغة صحيحة."""
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise validation_error(
            "prospective_freeze_at لازم يكون تاريخ ISO صحيح، مثل "
            "2026-09-26T15:30:00"
        ) from exc


# ── لوحة الأدمن ─────────────────────────────────────────────────────────────


@admin_router.get("/tabs", response_model=WheelTabsResponse)
def list_tabs(db: Session = Depends(get_db)) -> WheelTabsResponse:
    """الأربعة تابات بوصفها وعدد المؤهلين بكل واحد — لحظي، ما بينجمّد."""
    return WheelTabsResponse(
        tabs=wheel_service.tabs_payload(db),
        decision_requirements=wheel_service.decision_requirements(),
    )


@admin_router.get("/settings", response_model=WheelFreezeSettingsResponse)
def get_settings(
    prospective_freeze_at: str | None = Query(
        default=None,
        description=(
            "معاينة بدون حفظ: ISO datetime. بتبيّن عدد المؤهلين بالتابات لو "
            "وقت التجميد صار هالوقت. لازم يكون جوه نافذة الفعالية وإلا 400."
        ),
    ),
    db: Session = Depends(get_db),
) -> WheelFreezeSettingsResponse:
    return WheelFreezeSettingsResponse(
        **wheel_service.settings_payload(db, _parse_prospective(prospective_freeze_at))
    )


@admin_router.put("/settings", response_model=WheelFreezeSettingsResponse)
def update_settings(
    payload: WheelFreezeUpdateRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_role(AccountRole.super_admin)),
) -> WheelFreezeSettingsResponse:
    """حفظ وقت تجميد جديد. الأثر بينحسب مباشرة وبسطر تدقيق بالقيمة القديمة."""
    wheel_service.update_freeze(
        db, payload.freeze_at, current_account.id, payload.reason
    )
    return WheelFreezeSettingsResponse(**wheel_service.settings_payload(db))


@admin_router.post("/draws", response_model=WheelDrawResponse)
def create_draw(
    payload: WheelDrawRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_role(AccountRole.super_admin)),
) -> WheelDrawResponse:
    """
    سحب فائز من تاب. التوزيع منتظم داخل الـpool المجمّد.

    القواعد اللي بتُطبّق بالخدمة مش بالراوتر: الاستبعاد العالمي، شرط السبت،
    حد الـ100/50. لو ما في مؤهلين 409. لو في اسم معروض بنفس التاب وبانتظار
    قرار 409 (حارس ضد الضغط المزدوج — الفرونت بيحذفه لو بدكسلت).
    """
    draw, replayed = wheel_service.draw_winner(
        db, payload.tab, current_account.id, payload.idempotency_key
    )
    return WheelDrawResponse(
        **wheel_service.draw_payload(db, draw), replayed=replayed
    )


@admin_router.post(
    "/draws/{draw_id}/decision", response_model=WheelDecisionResponse
)
def decide_draw(
    draw_id: int,
    payload: WheelDecisionRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_role(AccountRole.super_admin)),
) -> WheelDecisionResponse:
    """
    قبول أو رفض الاسم المكشوف. أي قرار بينكتب استبعاد عالمي، فالطالب
    بيطلع من كل التابات بعده.

    المتطلبات مختلفة purposefully بين الحالتين: القبول يلزمه
    presence_verified، والرفض يلزمه confirmed. أي نقص بيرجع 400/409
    من الخدمة.
    """
    draw = wheel_service.submit_decision(
        db,
        draw_id,
        payload.decision,
        payload.presence_verified,
        payload.confirmed,
        current_account.id,
    )
    return WheelDecisionResponse(
        draw_id=draw.id,
        tab=draw.tab,
        tab_label=wheel_service.TAB_LABELS[draw.tab],
        student_id=draw.student_id,
        status=draw.status,
        presence_verified=draw.presence_verified,
        decided_at=draw.decided_at.isoformat() if draw.decided_at else None,
    )


@admin_router.get("/archive", response_model=WheelArchiveResponse)
def archive(db: Session = Depends(get_db)) -> WheelArchiveResponse:
    """أرشيف الفائزين بعد الحفل — كل السحوبات المقبولة."""
    return WheelArchiveResponse(winners=wheel_service.archive_rows(db))


@admin_router.get("/ceremony-snapshot", response_model=WheelCeremonySnapshot)
def ceremony_snapshot(db: Session = Depends(get_db)) -> WheelCeremonySnapshot:
    """
    لقطة الحفل: كل المؤهلين بالتابات الأربعة بأسمائهم ورقمهم ودرجاتهم.
    ليتخزّن محلياً بجهاز التشغيل قبل الحفل ويشتغل لحاله وقت انقطاع الشبكة.
    """
    return WheelCeremonySnapshot(**wheel_service.ceremony_snapshot(db))


# ── شاشة الجمهور ────────────────────────────────────────────────────────────


@router.get("/wheel/live", response_model=LiveDrawResponse)
def live_draw(
    db: Session = Depends(get_db),
    _: Account = Depends(get_current_account),
) -> LiveDrawResponse:
    """
    الاسم المعروض على الشاشة الآن. أي حساب مسجّل — بدون أدوار إدارية.

    **ما في بيانات تجميد بالجواب**: ست حقول فقط (الاسم، الكود، التاب، وقت
    الكشف). 200 بحقول null بدل 404 لأن الواجهة بتسأل كل ثانيتين.
    """
    return LiveDrawResponse(**wheel_service.live_draw_payload(db))
