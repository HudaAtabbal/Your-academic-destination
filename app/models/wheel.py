"""
موديلات عجلة الحظ — أربع جداول لميزة وحدة، كلها خاصة بـ super_admin.

ما في "كيان جوائز" هون: لا أسماء جوايز ولا أنواع محفوظة. عمود tab هو
"الشريحة" بالقيمة Technical فقط.

الجداول:
  wheel_settings      صف واحد — وقت تجميد الأهلية (freeze_at)، قابل للتعديل.
  wheel_freeze_audit  سجل تدقيق: مين عدّل freeze_at، إمتى، القديم والجديد.
  wheel_draws         سجل عمليات السحب — كل عملية صف بحالة (revealed /
                      accepted / rejected). "سجل الفائزين" هو مجرد فلترة
                      status='accepted'، و"أعد السحب" بعد الرفض هو طلب جديد
                      على نفس التاب — بلا جدول ولا endpoint خاص.
  wheel_exclusions    الاستبعاد العالمي — القيد الفريد على student_id هو
                      اللي بيفرض القاعدة، مش كود.
"""

from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app import time_utils
from app.database import Base
from app.event_days import EVENT_DAYS
from app.models.enums import WheelDecision, WheelDrawStatus, WheelTab

# السحب بيوم السبت الساعة 4:00، والتجميد بنص ساعة قبلها. بقيم متغيّرات
# لأن الاختبارات بتحتاج تعدّلها، ولأن شاشة الأدمن بتعرضها.
DRAW_HOUR = 16
DRAW_MINUTE = 0
DEFAULT_FREEZE_HOUR = 15
DEFAULT_FREEZE_MINUTE = 30

# طول مفتاح الـ idempotency المرسل من الفرونت (أو مولّد من uuid4).
IDEMPOTENCY_KEY_LEN = 64
# طول حقل سبب تعديل وقت التجميد (اختياري، للتدقيق).
FREEZE_REASON_LEN = 255


def default_freeze_at() -> datetime:
    """
    قيمة freeze_at الافتراضية: يوم السحب (السبت) الساعة 3:30 عصراً.

    بتقرأ EVENT_DAYS وقت الاستدعاء مش وقت الاستيراد، فبتتحدّث مع أي تعديل
    على EVENT_DAYS. القيمة بتتخزّن بالصف عند أول استخدام وبعدها ما عاد
    تُحسب — أي تعديل بعدها بيتسجل بالسجل مش بيتحسب من جديد.
    """
    draw_day = EVENT_DAYS["sat"]
    return datetime.combine(draw_day, time(DEFAULT_FREEZE_HOUR, DEFAULT_FREEZE_MINUTE))


class WheelSettings(Base):
    __tablename__ = "wheel_settings"

    # صف وحيد ثابت بمعرّف 1 عمداً — نفس نمط sms_heartbeat
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # وقت تجميد الأهلية. كل استعلامات العجلة بتستخدم LEAST(now, freeze_at):
    # قبل هذا الوقت النتيجة مطابقة للوقت الحقيقي، وبعده تتجمد تلقائياً.
    freeze_at = Column(DateTime, nullable=False, default=default_freeze_at)

    # آخر تعديل: إمتى ومين. للتدقيق فقط — المصدر الرسمي هو wheel_freeze_audit.
    updated_at = Column(DateTime, nullable=True)
    updated_by = Column(
        BigInteger, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )


class WheelFreezeAudit(Base):
    __tablename__ = "wheel_freeze_audit"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # القيمة الجديدة المحفوظة بعد التعديل
    freeze_at = Column(DateTime, nullable=False)
    # القيمة القديمة قبل التعديل — None بأول تعديل (القيمة الافتراضية)
    previous_freeze_at = Column(DateTime, nullable=True)

    changed_by = Column(
        BigInteger, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    changed_at = Column(
        DateTime, nullable=False, default=lambda: time_utils.now_naive()
    )
    reason = Column(String(FREEZE_REASON_LEN), nullable=True)

    __table_args__ = (Index("idx_wheel_freeze_audit_changed_at", "changed_at"),)


class WheelDraw(Base):
    """عملية سحب واحدة — صف واحد لكل ضغطة على "ابدأ السحب"."""

    __tablename__ = "wheel_draws"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    tab = Column(SAEnum(WheelTab, name="wheel_tab_enum"), nullable=False)

    # RESTRICT مش CASCADE: الفائز نهائي وأرشيف الحفل لازم يضل صحيح حتى لو
    # حدا حاول يحذف الطالب من القاعدة.
    student_id = Column(
        BigInteger, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )

    # revealed = انكشف الاسم وبانتظار قرار الأدمن (لحظة التشويق).
    # accepted = فوز نهائي (بيظهر بأرشيف الفائزين).
    # rejected = رفض نهائي بدون فوز (الطالب مستبعد، و"أعد السحب" بيظهر).
    status = Column(
        SAEnum(WheelDrawStatus, name="wheel_draw_status_enum"),
        nullable=False,
        default=WheelDrawStatus.revealed,
    )

    # قيمة freeze_at الفعلية المستعملة بهاد السحب — بتتخزّن مع كل عملية
    # عشان تظل قابلة للتدقيق حتى لو الـ admin غيّر الإعداد بعدين.
    freeze_at_snapshot = Column(DateTime, nullable=False)

    # مفتاح فريد من الفرونت لطلب السحب (تكرار آمن بعد انقطاع الشبكة).
    # فريد جزئياً: NULL لازم يضل مسموح لأكتر من عملية.
    idempotency_key = Column(String(IDEMPOTENCY_KEY_LEN), nullable=True)

    # التحقق اليدوي لحضور الفائز — الطبقة الثانية فوق شرط دخول السبت.
    # إجباري للقبول وغير مطلوب للرفض. بينحفظ عشان الأرشيف يبيّن أي قرار مرّ
    # بالتحقق اليدوي.
    presence_verified = Column(Boolean, nullable=False, default=False)

    # وقت السحب + من ضغط الزر
    created_at = Column(DateTime, nullable=False, default=lambda: time_utils.now_naive())
    created_by = Column(
        BigInteger, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )

    # وقت القرار + من اتخذه (NULL لحد ما ينحسم)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(
        BigInteger, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )

    student = relationship("Student")
    created_by_account = relationship("Account", foreign_keys=[created_by])
    decided_by_account = relationship("Account", foreign_keys=[decided_by])

    __table_args__ = (
        Index(
            "unique_wheel_draw_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where=(idempotency_key.isnot(None)),
        ),
        Index("idx_wheel_draws_tab_status", "tab", "status"),
        Index("idx_wheel_draws_status_created_at", "status", "created_at"),
    )


class WheelExclusion(Base):
    """
    الاستبعاد العالمي — أي طالب اتُّخذ بحقه قرار (قبول أو رفض) بأي تاب.

    القيد الفريد على student_id هو مُنفّذ القاعدة: لو في صف هون للطالب، ما
    بيطلع بأي استعلام أهلية لاحق — بالتوازي على الأربعة تابات.
    """

    __tablename__ = "wheel_exclusions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # فريد + RESTRICT: الاستبعاد نهائي بحسب المواصفة. CASCADE كان بيمسح الصف
    # مع الطالب وبيرجّعه للأهلية لو انحذف — ناقض المقصود.
    student_id = Column(
        BigInteger,
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    # التاب يلي اتخّذ فيه القرار (للتقارير) — مش شرط: الاستبعاد عالمي.
    tab = Column(SAEnum(WheelTab, name="wheel_tab_enum"), nullable=False)

    decision = Column(SAEnum(WheelDecision, name="wheel_decision_enum"), nullable=False)

    # عملية السحب يلي انبنى عليها الاستبعاد
    draw_id = Column(
        BigInteger, ForeignKey("wheel_draws.id", ondelete="RESTRICT"), nullable=False
    )

    decided_at = Column(DateTime, nullable=False, default=lambda: time_utils.now_naive())
    decided_by = Column(
        BigInteger, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )

    student = relationship("Student")
