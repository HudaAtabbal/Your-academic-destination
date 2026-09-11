"""
Pydantic schemas لروتر accounts — مطابقة لقسم 7 بملف wijhatak_api_contract.md
"""

from pydantic import BaseModel, Field, model_validator

from app.models.enums import AccountRole, College


class AccountPublic(BaseModel):
    """شكل الحساب العام — بدون password_hash أبداً."""

    username: str
    role: AccountRole
    college: College | None = None


class AccountListResponse(BaseModel):
    items: list[AccountPublic]
    page: int
    limit: int
    total: int
    total_pages: int


class AccountCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str | None = None  # لو فاضي/None، بتتولّد تلقائياً
    role: AccountRole
    college: College | None = None  # مطلوب بس لو role=college_staff


class AccountCreateResponse(BaseModel):
    username: str
    generated_password: str | None = None  # بترجع مرة وحدة بس، عند الإنشاء
    role: AccountRole
    college: College | None = None


class AccountUpdateRequest(BaseModel):
    role: AccountRole | None = None
    college: College | None = None
    password: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        """منع طلب تحديث فارغ — {} يُرفض بـ 422 بدل تحديث صامت بلا تأثير."""
        if self.role is None and self.college is None and self.password is None:
            raise ValueError("لازم تحددي حقل واحد على الأقل للتعديل")
        return self