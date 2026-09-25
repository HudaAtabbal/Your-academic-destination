"""
Router: auth — راجع قسم 1 بملف wijhatak_api_contract.md
هاد الملف بس طبقة الـ HTTP (thin layer): يقرا الـ request، يستدعي auth_service
للمنطق الفعلي، ويبني الـ response. أي منطق تحقق أو استعلام DB بيروح على
auth_service.py مش هون.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_public_lookup
from app.routers.auth import auth_service
from app.routers.auth.auth_schema import LoginRequest, LoginResponse
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_public_lookup),
) -> LoginResponse:
    account = auth_service.authenticate_account(db, payload.username, payload.password)

    token = create_access_token(
        data={
            "sub": account.username,
            "role": account.role.value,
            "college": account.college.value if account.college else None,
            "token_version": account.token_version,
        }
    )

    return LoginResponse(
        access_token=token,
        role=account.role,
        college=account.college,
    )