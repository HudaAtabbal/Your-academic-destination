"""
استثناء موحّد لكل أخطاء قواعد العمل بالمشروع — مطابق تماماً لشكل الخطأ
الموحّد الموثّق بـ wijhatak_api_contract.md (قسم 12: Error Responses):

{
  "error_code": "duplicate_checkin",
  "message": "رسالة واضحة بالعربي للمستخدم",
  "details": { ... }
}

كل الروترات لازم ترمي AppError بدل HTTPException العادي لأي خطأ متعلق
بقواعد العمل، مشان يوصل نفس الشكل دايماً للفرونت بغض النظر عن الـ endpoint.
"""

from typing import Any
from datetime import datetime

from app import time_utils

# أسماء أيام الأسبوع بالعربي — مفتاحها رقم اليوم حسب datetime.weekday()
# (الاثنين=0 … الأحد=6). خريطة ثابتة بدل strftime("%A") لأن الأخير بيعتمد على
# لغة السيرفر وبطلع أسماء إنجليزية على أغلب الأنظمة.
_WEEKDAY_NAMES = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "أربعاء",
    3: "خميس",
    4: "جمعة",
    5: "سبت",
    6: "أحد",
}


def _first_occurrence_phrase(first_occurred_at: datetime) -> str:
    """
    متى صار أول تسجيل: "الساعة HH:MM" لو اليوم، و"يوم أربعاء الساعة HH:MM" لو
    من يوم سابق. بدون السنة لأن الفعالية بثلاثة أيام متقاربة.
    """
    time_str = first_occurred_at.strftime("%H:%M")
    if time_utils.same_day(first_occurred_at, time_utils.now_naive()):
        return f"الساعة {time_str}"
    weekday = _WEEKDAY_NAMES.get(first_occurred_at.weekday())
    if weekday is None:
        return f"الساعة {time_str}"
    return f"يوم {weekday} الساعة {time_str}"


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)


# اختصارات جاهزة لأكواد الأخطاء المتكررة بأكتر من روتر (راجع قسم 12 بالعقد)


def student_not_found() -> AppError:
    return AppError(
        status_code=404,
        error_code="student_not_found",
        message="الرمز مش موجود",
    )


def invalid_credentials() -> AppError:
    return AppError(
        status_code=401,
        error_code="invalid_credentials",
        message="اسم مستخدم أو كلمة سر غلط",
    )


def code_range_taken(codes: list[str]) -> AppError:
    return AppError(
        status_code=409,
        error_code="code_range_taken",
        message="لم نتمكن من توليد رموز فريدة، حاولي مرة أخرى",
        details={"conflicting_codes": codes},
    )


def missing_campus_entry() -> AppError:
    return AppError(
        status_code=409,
        error_code="missing_campus_entry",
        message="الطالب لسا ما فوّت من بوابة الجامعة",
    )


def missing_booking() -> AppError:
    return AppError(
        status_code=409,
        error_code="missing_booking",
        message="الطالب ما إله حجز مسبق لهاد النشاط",
    )


def game_requirements_not_met(tour_count: int, lecture_count: int) -> AppError:
    return AppError(
        status_code=409,
        error_code="game_requirements_not_met",
        message="لازم يكمل الطالب جولتين كليتين ومحاضرة واحدة على الأقل قبل ما يدخل ركن الترفيه",
        details={"tour_count": tour_count, "lecture_count": lecture_count},
    )


def duplicate_checkin(
    student_name: str,
    unique_code: str,
    activity_type: str,
    activity_label: str,
    first_occurred_at: datetime,
    ) -> AppError:
    return AppError(
        status_code=409,
        error_code="duplicate_checkin",
        message=(
            f"الطالب {student_name} سجّل {activity_label} مسبقاً "
            f"{_first_occurrence_phrase(first_occurred_at)}"
        ),
        details={
            "student_name": student_name,
            "unique_code": unique_code,
            "activity_type": activity_type,
            "activity_label": activity_label,
            "first_occurred_at": first_occurred_at.isoformat(),
        },
    )


def duplicate_booking(student_name: str, unique_code: str, booking_label: str) -> AppError:
    return AppError(
        status_code=409,
        error_code="duplicate_booking",
        message=f"الطالب {student_name} حجز {booking_label} مسبقاً",
        details={
            "student_name": student_name,
            "unique_code": unique_code,
            "booking_label": booking_label,
        },
    )


def duplicate_survey() -> AppError:
    return AppError(
        status_code=409,
        error_code="duplicate_survey",
        message="الطالب عبّى الاستبيان مسبقاً",
    )


def survey_not_eligible() -> AppError:
    return AppError(
        status_code=409,
        error_code="survey_not_eligible",
        message="لازم يفوّت الطالب من بوابة الجامعة ويحضر نشاط واحد على الأقل "
        "(محاضرة أو جولة بالكلية أو استشارة فردية) قبل ما يعبّي الاستبيان",
    )


def duplicate_username() -> AppError:
    return AppError(
        status_code=409,
        error_code="duplicate_username",
        message="اسم المستخدم موجود مسبقاً",
    )


def account_not_found() -> AppError:
    return AppError(
        status_code=404,
        error_code="account_not_found",
        message="الحساب مش موجود",
    )


def checkin_not_found() -> AppError:
    return AppError(
        status_code=404,
        error_code="checkin_not_found",
        message="سجل الدخول مش موجود",
    )


def cannot_delete_self() -> AppError:
    return AppError(
        status_code=400,
        error_code="cannot_delete_self",
        message="ما فيك تحذفي حسابك أنتِ بنفسك",
    )


def sms_send_failed(reason: str | None = None) -> AppError:
    return AppError(
        status_code=502,
        error_code="sms_send_failed",
        message="تعذّر إرسال رمز التحقق حالياً، حاولي مرة تانية بعد شوي",
        details={"reason": reason} if reason else {},
    )


def validation_error(message: str) -> AppError:
    return AppError(status_code=400, error_code="validation_error", message=message)


def duplicate_contact() -> AppError:
    return AppError(
        status_code=409,
        error_code="duplicate_contact",
        message="رقم التواصل هاد مسجّل مسبقاً",
    )


def otp_invalid() -> AppError:
    return AppError(
        status_code=400,
        error_code="otp_invalid",
        message="الرمز غلط أو منتهي الصلاحية",
    )

def otp_too_many_attempts() -> AppError:
    return AppError(
        status_code=429,
        error_code="otp_too_many_attempts",
        message="تجاوزت الحد الأقصى للمحاولات، اطلبي رمز جديد",
    )


def too_many_requests() -> AppError:
    return AppError(
        status_code=429,
        error_code="too_many_requests",
        message="عدد كبير من الطلبات، حاولي بعد شوي",
    )


# ── عجلة الحظ ────────────────────────────────────────────────────────────────
# روتر العجلة بيعتمد على AppError بدل HTTPException مثل باقي الروترات، فبتوصل
# كل الأخطاء بالشكل الموحّد {error_code, message, details} المذكور بقسم 12.


def wheel_tab_empty(tab_label: str, required_points: int | None = None) -> AppError:
    return AppError(
        status_code=409,
        error_code="wheel_tab_empty",
        message=f"ما في طلاب مؤهلين بـ«{tab_label}»",
        details={"tab": tab_label, "required_points": required_points},
    )


def wheel_draw_not_found() -> AppError:
    return AppError(
        status_code=404,
        error_code="wheel_draw_not_found",
        message="عملية السحب مش موجودة",
    )


def wheel_draw_already_decided() -> AppError:
    return AppError(
        status_code=409,
        error_code="wheel_draw_already_decided",
        message="هاد السحب اتحسم مسبقاً — ما في قرار جديد",
    )


def wheel_presence_verification_required() -> AppError:
    return AppError(
        status_code=409,
        error_code="wheel_presence_verification_required",
        message="لازم تتأكد من حضور الطالب يدوياً قبل قبوله كفائز",
    )


def wheel_reject_confirmation_required() -> AppError:
    return AppError(
        status_code=400,
        error_code="wheel_reject_confirmation_required",
        message="الرفض لازم يتأكد منه — الطالب رح ينستبعد نهائياً من كل التابات",
    )


def wheel_freeze_out_of_range(message: str) -> AppError:
    return AppError(
        status_code=400,
        error_code="wheel_freeze_out_of_range",
        message=message,
    )


def wheel_student_already_excluded() -> AppError:
    return AppError(
        status_code=409,
        error_code="wheel_student_already_excluded",
        message="الطالب مستبعد سابقاً من العجلة",
    )


def wheel_pending_draw_exists(tab_label: str) -> AppError:
    """ضغط "ابدأ السحب" مرتين بنفس التاب — فيه اسم معروض وبانتظار قرار."""
    return AppError(
        status_code=409,
        error_code="wheel_pending_draw_exists",
        message=f"فيه اسم معروض حالياً بـ«{tab_label}» وبانتظار قرارك — "
        "اقبله أو ارفضه قبل ما تسحب مرة تانية",
    )