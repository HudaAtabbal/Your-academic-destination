"""
Dependencies مشتركة عبر كل الروترات:
- get_current_account: بتقرا التوكن من الهيدر Authorization وترجع الحساب المسجّل دخوله
- require_role: بتتحقق إنه صاحب التوكن عنده واحد من الأدوار المسموحة، وإلا بترمي 403
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import Account
from app.models.enums import AccountRole
from app.security import decode_access_token

# HTTPBearer بيفرض وجود الهيدر: Authorization: Bearer <token>
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """
    ...
    """
    if credentials is None:
        raise AppError(
            status_code=401,
            error_code="invalid_credentials",
            message="التوكن غير صالح أو منتهي الصلاحية",
        )
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise AppError(
            status_code=401,
            error_code="invalid_credentials",
            message="التوكن غير صالح أو منتهي الصلاحية",
        )

    username: str | None = payload.get("sub")
    if username is None:
        raise AppError(
            status_code=401,
            error_code="invalid_credentials",
            message="التوكن غير صالح",
        )

    account = db.query(Account).filter(Account.username == username).first()
    if account is None:
        raise AppError(
            status_code=401,
            error_code="invalid_credentials",
            message="الحساب غير موجود",
        )

    return account


def require_role(*allowed_roles: AccountRole):
    """
    مصنع dependencies — بيرجّع دالة بتتحقق إنه دور الحساب الحالي ضمن الأدوار
    المسموحة لهاد الـ endpoint.

    الاستخدام بالروتر:
        @router.get("/admin/dashboard/stats", dependencies=[Depends(require_role(AccountRole.super_admin))])
    """

    def _checker(current_account: Account = Depends(get_current_account)) -> Account:
        if current_account.role not in allowed_roles:
            raise AppError(
                status_code=403,
                error_code="forbidden",
                message="ما عندك صلاحية للوصول لهاد الـ endpoint",
            )
        return current_account

    return _checker