"""اختبارات حدود توكنات JWT: الانتهاء، المفتاح، المطالبات الناقصة، ودور قاعدة البيانات."""

import datetime

import jwt as pyjwt

from app.models import Account
from app.security import JWT_ALGORITHM, JWT_SECRET_KEY


def _get_account_token_version(db, username):
    acc = db.query(Account).filter(Account.username == username).first()
    assert acc is not None
    return acc.token_version


def _build_token(payload, secret=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM):
    return pyjwt.encode(payload, secret, algorithm=algorithm)


def _make_token(db, username, *, exp=None, secret=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM, extra=None):
    token_version = _get_account_token_version(db, username)
    now = datetime.datetime.now(datetime.timezone.utc)
    if exp is None:
        exp = now + datetime.timedelta(minutes=30)
    payload = {
        "sub": username,
        "role": "gate_scanner",
        "college": None,
        "token_version": token_version,
        "exp": exp,
    }
    if extra:
        payload.update(extra)
    return _build_token(payload, secret=secret, algorithm=algorithm)


def test_expired_token_returns_401(client, db):
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
    token = _make_token(db, "taher_super", exp=past)
    resp = client.get("/admin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_token_signed_with_different_secret_returns_401(client, db):
    token = _make_token(db, "taher_super", secret="a-completely-different-secret-key")
    resp = client.get("/admin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_token_missing_sub_claim_returns_401(client, db):
    token_version = _get_account_token_version(db, "taher_super")
    payload = {
        "role": "super_admin",
        "college": None,
        "token_version": token_version,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
    }
    token = _build_token(payload)
    resp = client.get("/admin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_token_missing_token_version_claim_returns_401(client, db):
    payload = {
        "sub": "taher_super",
        "role": "super_admin",
        "college": None,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
    }
    token = _build_token(payload)
    resp = client.get("/admin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_forged_role_claim_ignored_db_role_wins(client, db):
    """ادّعاء role='super_admin' المزوّر في التوكن لا يمنح صلاحيات —
    الدور الفعلي يُقرأ من قاعدة البيانات."""
    token = _make_token(
        db, "sedra_admin", extra={"role": "super_admin"}
    )
    resp = client.get("/admin/accounts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"