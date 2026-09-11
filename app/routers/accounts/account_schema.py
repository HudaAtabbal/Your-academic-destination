"""
Pydantic schemas لروتر accounts — مطابقة لقسم 7 بملف wijhatak_api_contract.md
"""

from pydantic import BaseModel

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
    username: str
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