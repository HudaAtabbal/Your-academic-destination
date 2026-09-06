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