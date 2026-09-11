"""
Pydantic schemas لروتر auth — مطابقة تماماً لقسم 1 (Auth) بملف wijhatak_api_contract.md
"""

from pydantic import BaseModel

from app.models.enums import AccountRole, College


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: AccountRole
    college: College | None = None