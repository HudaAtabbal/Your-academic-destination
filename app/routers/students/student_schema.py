"""
Pydantic schemas لروتر admin/students — مطابقة لقسم 6 بملف wijhatak_api_contract.md
"""

from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import (
    CertificateType,
    College,
    ContactPlatform,
    RegistrationType,
    StudentStatus,
    VerificationStatus,
)


class StudentDetail(BaseModel):
    id: int
    unique_code: str
    full_name: str | None = None
    birth_date: date | None = None
    contact_platform: ContactPlatform | None = None
    contact_id: str | None = None
    bacc_year: int | None = None
    bacc_average: float | None = None
    certificate_type: CertificateType | None = None
    initial_preferred_major: College | None = None
    verification_status: VerificationStatus
    registration_type: RegistrationType
    status: StudentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class StudentUpdateRequest(BaseModel):
    """
    أي subset من الحقول القابلة للتعديل. ⚠️ registration_type ممنوع تعديله
    عمداً — حتى لو انبعت بالطلب، بيتجاهل بالكامل بمستوى الـ service.
    """

    full_name: str | None = None
    birth_date: date | None = None
    contact_platform: ContactPlatform | None = None
    contact_id: str | None = None
    bacc_year: int | None = None
    bacc_average: float | None = None
    certificate_type: CertificateType | None = None
    initial_preferred_major: College | None = None
    verification_status: VerificationStatus | None = None
    status: StudentStatus | None = None


class StudentStatsResponse(BaseModel):
    total_registered: int
    walkin_pending_count: int


class WalkinIncompleteItem(BaseModel):
    unique_code: str
    full_name: str | None = None
    contact_id: str | None = None
    status: str  # "no_data" | "partial"


class WalkinIncompleteListResponse(BaseModel):
    items: list[WalkinIncompleteItem]
    page: int
    limit: int
    total: int
    total_pages: int