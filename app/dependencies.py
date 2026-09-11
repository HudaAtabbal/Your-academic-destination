"""
Dependencies مشتركة عبر كل الروترات:
- get_current_account: بتقرا التوكن من الهيدر Authorization وترجع الحساب المسجّل دخوله
- require_role: بتتحقق إنه صاحب التوكن عنده واحد من الأدوار المسموحة، وإلا بترمي 403
- rate_limit_public_lookup: بتحدد عدد الطلبات المسموحة لكل IP على الـ endpoints
  العامة يلي بتعتمد على unique_code بس (بدون تسجيل دخول)
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError, too_many_requests
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


# --- Rate limiting للـ endpoints العامة (بدون تسجيل دخول) ---
#
# مربوط بعنوان IP، مش بـ unique_code نفسه — لأنه يلي بده يخمّن أكواد طلاب
# غيره بيجرب أكواد مختلفة كل مرة (R-0001, R-0002...)، فتحديد حد لكل كود
# لحاله ما بيمنع هيك تخمين متسلسل.
#
# ⚠️ مخزّن بالذاكرة (مش Redis) — كافي لحجم فعالية واحدة بسيرفر واحد، بس
# بينصفّر لو انعاد تشغيل السيرفر، وما بيشتغل صح لو في أكتر من worker/instance
# بنفس الوقت (كل process إله نسخته الخاصة من الذاكرة). لو صار عندك أكتر من
# instance على Render، لازم تتحول لحل مركزي (Redis مثلاً).
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 20

_request_log: dict[str, list[float]] = defaultdict(list)
_rate_limit_lock = Lock()


def rate_limit_public_lookup(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    with _rate_limit_lock:
        timestamps = _request_log[client_ip]
        cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
            raise too_many_requests()

        timestamps.append(now)