"""
Pydantic schemas لروتر registration (تسجيل الطالب العام + OTP + بطاقة).
مطابقة لحقول الفرونت الفعلية (فرع Frontend من ريبو Your-academic-destination).
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import CertificateType, ContactPlatform, College, VerificationStatus


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255, description="الاسم الثلاثي")
    birth_date: date
    certificate_year: int = Field(ge=1900, le=2100, description="bacc_year — سنة الشهادة")
    certificate_type: CertificateType
    average_score: float = Field(ge=0, le=100, description="bacc_average — نسبة مئوية 0-100")
    initial_preferred_major:list[College] = Field(min_length=1)
    contact_platform: ContactPlatform
    contact_id: str = Field(min_length=1, max_length=255, description="رقم التواصل")

    @field_validator("full_name", "contact_id", mode="before")
    @classmethod
    def strip_required_fields(cls, v):
        """تجريد المسافات — فالاسم أو رقم التواصل المكوّن من مسافات فقط يُرفض (422)."""
        if v is not None and isinstance(v, str):
            return v.strip()
        return v

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("تاريخ الميلاد لا يمكن أن يكون في المستقبل")
        return v


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
    otp: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$", description="رمز تحقق رقمي من 4 خانات")

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
    full_name: str = Field(min_length=1)


class LookupByContactResponse(BaseModel):
    unique_code: str
    full_name: str | None = None