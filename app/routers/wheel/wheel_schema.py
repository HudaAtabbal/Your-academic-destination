"""
Pydantic schemas لروتر عجلة الحظ.

مقسوم ع قسمين مقصودين:

  * شاشات الأدمن — فيها كل التفاصيل: الأرقام المجمّدة، وقت التجميد، أسماء
    المؤهلين (لحفل التحقق اليدوي).
  * شاشة الجمهور — LiveDrawResponse بس، وفيها **ست حقول فقط**. ما في
    freeze_at ولا counts ولا حالة تجميد: المواصفة بتمنع كشفها للجمهور،
    والقاعدة هون مفروضة بالـschema نفسه مش بالمطّ-obligations.

كل موديل بدون response_model بيرجع JSON عادي — الباقي من الراوتر مربوط
بـresponse_model صريح.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import WheelDecision, WheelDrawStatus, WheelTab
from app.routers.wheel.wheel_service import decision_requirements


class WheelTabInfo(BaseModel):
    """تاب واحد للوحة الأدمن: الوصف + عدد المؤهلين لحظياً."""

    tab: WheelTab
    tab_label: str
    criteria: list[str]
    eligible_count: int


class WheelTabsResponse(BaseModel):
    tabs: list[WheelTabInfo]
    decision_requirements: dict[str, bool] = Field(
        default_factory=decision_requirements
    )


class WheelFreezeSettingsResponse(BaseModel):
    """إعدادات التجميد + معاينة الأثر بدون حفظ."""

    freeze_at: str
    frozen: bool
    is_default: bool
    effective_freeze_at: str
    min_allowed: str
    max_allowed: str
    tabs: list[WheelTabInfo]
    preview: WheelFreezePreview | None = None


class WheelFreezePreview(BaseModel):
    prospective_freeze_at: str
    tabs: list[WheelTabPreview]


class WheelTabPreview(BaseModel):
    tab: WheelTab
    tab_label: str
    eligible_count: int
    delta: int


class WheelFreezeUpdateRequest(BaseModel):
    freeze_at: datetime
    reason: str | None = Field(default=None, max_length=255)


class WheelDrawRequest(BaseModel):
    tab: WheelTab
    # مفتاح تكرار من الفرونت: لو الطلب وصل مرتين (انقطاع شبكة بعد الحفظ)
    # بيرجع نفس السحبة بدل ما يسحب طالب ثاني.
    idempotency_key: str | None = Field(default=None, max_length=64)


class WheelDrawResponse(BaseModel):
    draw_id: int
    tab: WheelTab
    tab_label: str
    student_id: int
    unique_code: str | None = None
    full_name: str | None = None
    status: WheelDrawStatus
    created_at: str | None = None
    # true يعني هاد الطلب تكرر (idempotency_key موجود مسبقاً) — بيخلي
    # الفرونت يفهم إنه نفس السحبة مش وحدة جديدة.
    replayed: bool = False


class WheelDecisionRequest(BaseModel):
    decision: WheelDecision
    # التحقق اليدوي: إجباري للقبول، اختياري للرفض.
    presence_verified: bool = False
    # تأكيد الرفض: إجباري للرفض. للقبول مش مطلوب أصلاً.
    confirmed: bool = False


class WheelDecisionResponse(BaseModel):
    draw_id: int
    tab: WheelTab
    tab_label: str
    student_id: int
    unique_code: str | None = None
    full_name: str | None = None
    status: WheelDrawStatus
    presence_verified: bool
    decided_at: str | None = None
    # ملاحظة تشغيلية: بعد أي قرار (قبول أو رفض) بينكتب صف wheel_exclusions،
    # فالطالب مستبعد من كل التابات — حتى لو كان قراره رفضاً.
    excluded_globally: bool = True


class WheelArchiveEntry(BaseModel):
    draw_id: int
    tab: WheelTab
    tab_label: str
    student_id: int
    unique_code: str | None = None
    full_name: str | None = None
    presence_verified: bool
    decided_at: str | None = None


class WheelArchiveResponse(BaseModel):
    winners: list[WheelArchiveEntry]


class WheelCandidate(BaseModel):
    """مؤهل واحد بلقطة الحفل."""

    student_id: int
    unique_code: str
    full_name: str | None = None
    freeze_points: int
    raw_lectures: int
    max_span_minutes: int
    rank: int | None = None


class WheelCeremonyTab(BaseModel):
    tab: WheelTab
    tab_label: str
    criteria: list[str]
    eligible_count: int
    winners: list[WheelCandidate]


class WheelCeremonySnapshot(BaseModel):
    """لقطة الحفل الكاملة — super_admin بس، الأسماء مطلوبة للتحقق اليدوي."""

    generated_at: str
    effective_freeze_at: str
    frozen: bool
    tabs: list[WheelCeremonyTab]


class LiveDrawResponse(BaseModel):
    """
    اللي على شاشة الجمهور. **ست حقول فقط** — ممنوع إضافة freeze_at أو
    counts أو حالة تجميد لهون: شاشة الجمهور ما بتعرف إن الأهلية مجمّدة.

    كل الحقول null لما ما في اسم معروض، والجواب 200 (مش 404) لأن الواجهة
    بتسأل كل ثانيتين.
    """

    draw_id: int | None = None
    tab: WheelTab | None = None
    tab_label: str | None = None
    winner_name: str | None = None
    winner_code: str | None = None
    revealed_at: str | None = None
