"""
Router: admin/accounts — راجع قسم 7 بملف wijhatak_api_contract.md
كل الـ endpoints هون محصورة بدور super_admin فقط.
"""

import math

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role , get_current_account
from app.models import AccountRole , Account
from app.routers.accounts import account_service
from app.routers.accounts.account_schema import (
    AccountCreateRequest,
    AccountCreateResponse,
    AccountListResponse,
    AccountPublic,
    AccountUpdateRequest,
)

router = APIRouter(
    prefix="/admin/accounts",
    tags=["admin - accounts"],
    dependencies=[Depends(require_role(AccountRole.super_admin))],
)


@router.get("", response_model=AccountListResponse)
def list_accounts(page: int = 1, limit: int = 20, db: Session = Depends(get_db)) -> AccountListResponse:
    items, total = account_service.list_accounts(db, page, limit)
    return AccountListResponse(
        items=[AccountPublic(username=a.username, role=a.role, college=a.college) for a in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=max(1, math.ceil(total / limit)),
    )


@router.post("", response_model=AccountCreateResponse, status_code=201)
def create_account(
    payload: AccountCreateRequest, db: Session = Depends(get_db)
) -> AccountCreateResponse:
    account, generated_password = account_service.create_account(
        db, payload.username, payload.password, payload.role, payload.college
    )
    return AccountCreateResponse(
        username=account.username,
        generated_password=generated_password,
        role=account.role,
        college=account.college,
    )


@router.patch("/{username}", response_model=AccountPublic)
def update_account(
    username: str, payload: AccountUpdateRequest, db: Session = Depends(get_db)
) -> AccountPublic:
    account = account_service.update_account(
        db, username, payload.role, payload.college, payload.password
    )
    return AccountPublic(username=account.username, role=account.role, college=account.college)

@router.delete("/{username}", status_code=204)
def delete_account(
    username: str,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account),
) -> None:
    account_service.delete_account(db, username, current_account.username)