"""
Pydantic schemas لروتر admin/students — مطابقة لقسم 6 بملف wijhatak_api_contract.md
"""

from datetime import date, datetime
import re

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import (
    CertificateType,
    College,
    RegistrationType,
    StudentStatus,
    VerificationStatus,
)


class StudentDetail(BaseModel):
    id: int
    unique_code: str
    full_name: str | None = None
    birth_date: date | None = None
    contact_id: str | None = None
    bacc_year: int | None = None
    bacc_average: float | None = None
    certificate_type: CertificateType | None = None
    initial_preferred_major: list[College] | None = None
    verification_status: VerificationStatus
    registration_type: RegistrationType
    status: StudentStatus
    is_complete: bool
    completion_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentUpdateRequest(BaseModel):
    """
    أي subset من الحقول القابلة للتعديل. ⚠️ registration_type ممنوع تعديله
    عمداً — حتى لو انبعت بالطلب، بيتجاهل بالكامل بمستوى الـ service.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birth_date: date | None = None
    contact_id: str | None = Field(default=None, min_length=1, max_length=255)
    bacc_year: int | None = Field(default=None, ge=1900, le=2100)
    bacc_average: float | None = Field(default=None, ge=0, le=100)
    certificate_type: CertificateType | None = None
    initial_preferred_major: list[College] | None = None
    verification_status: VerificationStatus | None = None
    status: StudentStatus | None = None

    @field_validator("full_name", "contact_id", mode="before")
    @classmethod
    def strip_optional_fields(cls, v):
        if v is not None and isinstance(v, str):
            return v.strip()
        return v

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_in_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("تاريخ الميلاد لا يمكن أن يكون في المستقبل")
        return v

    @field_validator("contact_id", mode="after")
    @classmethod
    def validate_contact_format(cls, v: str | None) -> str | None:
        """رقم الهاتف لازم يكون 10 أرقام تبدأ بـ 09."""
        if v is None:
            return None
        clean = v.replace(" ", "") if isinstance(v, str) else v
        if not re.fullmatch(r"09\d{8}", clean):
            raise ValueError("رقم الهاتف لازم يكون 10 أرقام تبدأ بـ 09")
        return clean

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        """منع طلب تحديث فارغ — {} يُرفض بـ 422 بدل تحديث صامت بلا تأثير."""
        if all(
            v is None
            for v in (
                self.full_name,
                self.birth_date,
                self.contact_id,
                self.bacc_year,
                self.bacc_average,
                self.certificate_type,
                self.initial_preferred_major,
                self.verification_status,
                self.status,
            )
        ):
            raise ValueError("لازم تحددي حقل واحد على الأقل للتعديل")
        return self


class StudentStatsResponse(BaseModel):
    total_registered: int
    walkin_pending_count: int
    walkin_completed_count: int


class WalkinIncompleteItem(BaseModel):
    unique_code: str
    full_name: str | None = None
    contact_id: str | None = None
    status: str  # "no_data" | "partial" | "complete"


class WalkinIncompleteListResponse(BaseModel):
    items: list[WalkinIncompleteItem]
    page: int
    limit: int
    total: int
    total_pages: int