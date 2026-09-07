"""اختبارات تسجيل الدخول (auth)."""

from app.models import AccountRole


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_login_super_admin(client):
    resp = client.post("/auth/login", json={"username": "taher_super", "password": "super123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == AccountRole.super_admin.value
    assert body["college"] is None
    assert body["access_token"]


def test_login_college_staff_returns_college(client):
    resp = client.post("/auth/login", json={"username": "rima_staff", "password": "staff123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == AccountRole.college_staff.value
    assert body["college"] == "college_placeholder_1"


def test_login_any_role_accepts_all_seeded(client):
    for username, password, role in [
        ("taher_super", "super123", AccountRole.super_admin),
        ("sedra_admin", "admin123", AccountRole.students_admin),
        ("rima_staff", "staff123", AccountRole.college_staff),
        ("hadi_gate", "gate123", AccountRole.gate_scanner),
    ]:
        resp = client.post("/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200
        assert resp.json()["role"] == role.value


def test_login_wrong_password(client):
    resp = client.post("/auth/login", json={"username": "taher_super", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_login_unknown_user(client):
    resp = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_login_missing_field_422(client):
    resp = client.post("/auth/login", json={"username": "taher_super"})
    assert resp.status_code == 422


def test_missing_authorization_header_401(client):
    resp = client.get("/admin/accounts")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"


def test_invalid_token_401(client):
    resp = client.get("/admin/accounts", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "invalid_credentials"