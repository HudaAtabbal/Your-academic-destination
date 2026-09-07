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
        message="بعض الرموز بهاد النطاق مستخدمة مسبقاً",
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


def duplicate_checkin(
    student_name: str,
    unique_code: str,
    activity_type: str,
    activity_label: str,
    first_occurred_at,
) -> AppError:
    time_str = first_occurred_at.strftime("%H:%M")
    return AppError(
        status_code=409,
        error_code="duplicate_checkin",
        message=f"الطالب {student_name} سجّل {activity_label} مسبقاً الساعة {time_str}",
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

<<<<<<< HEAD

def validation_error(message: str) -> AppError:
    return AppError(status_code=400, error_code="validation_error", message=message)
=======
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
>>>>>>> 94060cad11a8b210e98a4d99dca377d5b2107c95
