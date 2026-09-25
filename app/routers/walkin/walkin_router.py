"""
Router: admin/walkin-codes — راجع قسم 8 بملف wijhatak_api_contract.md
الدور المسموح: super_admin فقط.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import AccountRole
from app.routers.walkin import walkin_service
from app.routers.walkin.walkin_schema import (
    WalkinCodesGenerateRequest,
    WalkinCodesGenerateResponse,
)

router = APIRouter(
    prefix="/admin/walkin-codes",
    tags=["admin - walkin codes"],
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)


@router.post("/generate", response_model=WalkinCodesGenerateResponse, status_code=201)
def generate_walkin_codes(
    payload: WalkinCodesGenerateRequest, db: Session = Depends(get_db)
) -> WalkinCodesGenerateResponse:
    codes = walkin_service.generate_walkin_codes(db, payload.count)
    return WalkinCodesGenerateResponse(codes=codes)