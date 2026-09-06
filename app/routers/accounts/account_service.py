"""
منطق العمل لإدارة حسابات فريق العمل — راجع قسم 7 بملف wijhatak_api_contract.md.

قواعد العمل المطبّقة:
- ما في قيد "حساب واحد لكل كلية" — مسموح أكتر من حساب college_staff لنفس الكلية.
- college مطلوبة بس لو role=college_staff، وبتنمسح تلقائياً لأي دور تاني.
- كلمة السر: لو ما انبعتت، بتتولّد عشوائياً وبترجع مرة وحدة بس بالـ response.
"""

import secrets
import string

from sqlalchemy.orm import Session

from app.errors import account_not_found, duplicate_username
from app.models import Account, AccountRole, College
from app.security import hash_password

_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def _generate_password(length: int = 8) -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


def _resolve_college(role: AccountRole, college: College | None) -> College | None:
    """college منطقية بس لو الدور college_staff — أي دور تاني بيتجاهلها."""
    return college if role == AccountRole.college_staff else None


def list_accounts(db: Session, page: int, limit: int) -> tuple[list[Account], int]:
    total = db.query(Account).count()
    items = (
        db.query(Account)
        .order_by(Account.id)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def create_account(
    db: Session,
    username: str,
    password: str | None,
    role: AccountRole,
    college: College | None,
) -> tuple[Account, str | None]:
    existing = db.query(Account).filter(Account.username == username).first()
    if existing is not None:
        raise duplicate_username()

    generated_password = None
    if not password:
        generated_password = _generate_password()
        password = generated_password

    resolved_college = _resolve_college(role, college)

    account = Account(
        username=username,
        password_hash=hash_password(password),
        role=role,
        college=resolved_college,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account, generated_password


def update_account(
    db: Session,
    username: str,
    role: AccountRole | None,
    college: College | None,
    password: str | None,
) -> Account:
    account = db.query(Account).filter(Account.username == username).first()
    if account is None:
        raise account_not_found()

    new_role = role if role is not None else account.role

    if role is not None:
        account.role = role
    if college is not None or role is not None:
        # لو تغيّر الدور أو انبعتت كلية جديدة، منعيد حساب الكلية المنطقية
        account.college = _resolve_college(new_role, college if college is not None else account.college)
    if password:
        account.password_hash = hash_password(password)

    db.commit()
    db.refresh(account)
    return account