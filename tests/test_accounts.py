"""اختبارات إدارة حسابات فريق العمل — super_admin فقط."""


def test_list_accounts(client, super_headers):
    resp = client.get("/admin/accounts", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    assert body["page"] == 1
    assert body["limit"] == 20


def test_list_pagination(client, super_headers):
    resp = client.get(
        "/admin/accounts", params={"page": 1, "limit": 2}, headers=super_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 4
    assert body["total_pages"] == 2


def test_create_account_with_password(client, super_headers):
    resp = client.post(
        "/admin/accounts",
        json={
            "username": "new_staff",
            "password": "pw12345",
            "role": "college_staff",
            "college": "dentistry",
        },
        headers=super_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["generated_password"] is None
    assert body["college"] == "dentistry"
    login = client.post(
        "/auth/login", json={"username": "new_staff", "password": "pw12345"}
    )
    assert login.status_code == 200
    assert login.json()["role"] == "college_staff"


def test_create_account_auto_password(client, super_headers):
    resp = client.post(
        "/admin/accounts",
        json={"username": "auto_admin", "role": "students_admin"},
        headers=super_headers,
    )
    assert resp.status_code == 201
    generated = resp.json()["generated_password"]
    assert isinstance(generated, str) and generated
    login = client.post(
        "/auth/login", json={"username": "auto_admin", "password": generated}
    )
    assert login.status_code == 200


def test_create_duplicate_username_409(client, super_headers):
    payload = {"username": "dup_user", "role": "gate_scanner"}
    assert client.post("/admin/accounts", json=payload, headers=super_headers).status_code == 201
    resp = client.post("/admin/accounts", json=payload, headers=super_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_username"


def test_create_college_stripped_for_non_staff(client, super_headers):
    resp = client.post(
        "/admin/accounts",
        json={"username": "gate_x", "role": "gate_scanner", "college": "medicine"},
        headers=super_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["college"] is None


def test_create_invalid_role_422(client, super_headers):
    resp = client.post(
        "/admin/accounts", json={"username": "x", "role": "bogus"}, headers=super_headers
    )
    assert resp.status_code == 422


def test_patch_account_role(client, super_headers):
    resp = client.patch(
        "/admin/accounts/sedra_admin", json={"role": "super_admin"}, headers=super_headers
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "super_admin"


def test_patch_account_password(client, super_headers):
    assert (
        client.patch(
            "/admin/accounts/sedra_admin", json={"password": "brand_new"}, headers=super_headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/auth/login", json={"username": "sedra_admin", "password": "brand_new"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/auth/login", json={"username": "sedra_admin", "password": "admin123"}
        ).status_code
        == 401
    )


def test_patch_unknown_account_404(client, super_headers):
    resp = client.patch(
        "/admin/accounts/ghost", json={"role": "gate_scanner"}, headers=super_headers
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "account_not_found"


def test_accounts_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/accounts", headers=students_admin_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_accounts_unauthenticated_401(client):
    resp = client.get("/admin/accounts")
    assert resp.status_code == 401