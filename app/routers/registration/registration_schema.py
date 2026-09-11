"""
Pydantic schemas لروتر registration (تسجيل الطالب العام + OTP + بطاقة).
مطابقة لحقول الفرونت الفعلية (فرع Frontend من ريبو Your-academic-destination).
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import CertificateType, ContactPlatform, College, VerificationStatus


class RegisterRequest(BaseModel):
    full_name: str
    birth_date: date
    certificate_year: int = Field(description="bacc_year — سنة الشهادة")
    certificate_type: CertificateType
    average_score: float = Field(ge=0, le=100, description="bacc_average — نسبة مئوية 0-100")
    initial_preferred_major:list[College] = Field(min_length=1)
    contact_platform: ContactPlatform
    contact_id: str


class RegisterResponse(BaseModel):
    unique_code: str
    full_name: str
    otp_sent: bool = True


class ResendOtpRequest(BaseModel):
    unique_code: str


class ResendOtpResponse(BaseModel):
    expires_at: datetime


class VerifyOtpRequest(BaseModel):
    unique_code: str
    otp: str = Field(min_length=4, max_length=4)

class VerifyOtpResponse(BaseModel):
    unique_code: str
    full_name: str
    verification_status: VerificationStatus


class StudentCardResponse(BaseModel):
    unique_code: str
    full_name: str | None = None
    verification_status: VerificationStatus
    qr_payload: str


class LookupByContactRequest(BaseModel):
    contact_platform: ContactPlatform
    contact_id: str


class LookupByContactResponse(BaseModel):
    unique_code: str
    full_name: str | None = None