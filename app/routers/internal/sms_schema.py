"""
Pydantic schemas لروتر internal/sms — تواصل المُراسل الداخلي مع الخادم.
"""

from datetime import datetime

from pydantic import BaseModel

from app.models import SmsJobStatus


class DequeueItem(BaseModel):
    """مهمة إرسال واحدة تم سحبها — الرمز نصاً صريحاً لأنه ضروري للإرسال."""

    job_id: int
    phone: str  # بصيغة 963 الدولية — جاهزة للإرسال
    otp_code: str
    expires_at: datetime


class ReportRequest(BaseModel):
    """نتيجة محاولة الإرسال من المُرسِل — idempotent من الطرف الآخر."""

    job_id: int
    success: bool
    transient: bool = False  # مؤقت (اتصال/شبكة) → يعاد للمحاولة  |  دائم (رسالة خطأ سيرياتيل) → يفشل فوراً
    error: str | None = None


class ReportResponse(BaseModel):
    job_id: int
    status: SmsJobStatus
