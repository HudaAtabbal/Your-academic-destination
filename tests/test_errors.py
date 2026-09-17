"""اختبارات توحيد شكل الخطأ {error_code, message, details} عبر كل الروترات."""


def _assert_shape(resp):
    assert resp.status_code >= 400
    assert set(resp.json().keys()) == {"error_code", "message", "details"}


def test_shape_login_failure(client):
    _assert_shape(
        client.post("/auth/login", json={"username": "x", "password": "y"})
    )


def test_shape_missing_auth_header(client):
    _assert_shape(client.get("/admin/accounts"))


def test_shape_forbidden(client, students_admin_headers):
    _assert_shape(client.get("/admin/accounts", headers=students_admin_headers))


def test_shape_unknown_student(client, students_admin_headers):
    _assert_shape(
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9999"},
            headers=students_admin_headers,
        )
    )


def test_shape_duplicate_business_rule(
    client, student_factory, students_admin_headers
):
    student_factory("R-9001")
    assert (
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9001"},
            headers=students_admin_headers,
        ).status_code
        == 201
    )
    _assert_shape(
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9001"},
            headers=students_admin_headers,
        )
    )


def test_shape_duplicate_survey(client, student_factory):
    student_factory("R-9001")
    assert (
        client.post(
            "/survey/R-9001",
            json={"opinion_change": "decided", "preferred_major": "medicine"},
        ).status_code
        == 201
    )
    _assert_shape(
        client.post(
            "/survey/R-9001",
            json={"opinion_change": "decided", "preferred_major": "medicine"},
        )
    )


def test_shape_staff_without_college(
    client, create_custom_staff, auth_headers
):
    create_custom_staff("no_college_staff", "pw123", None)
    headers = auth_headers("no_college_staff", "pw123")
    _assert_shape(
        client.post("/bookings/tour", json={"unique_code": "R-9001"}, headers=headers)
    )


def test_shape_502_sms_send_failed(client, monkeypatch):
    monkeypatch.delenv("SMS_MODE", raising=False)
    from app import sms_service as sms_service_module

    def _boom(*a, **k):
        raise sms_service_module.SmsSendError("User isn't active")

    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms", _boom
    )
    resp = client.post(
        "/students/register",
        json={
            "full_name": "طالب",
            "birth_date": "2000-01-01",
            "certificate_year": 2025,
            "certificate_type": "scientific",
            "average_score": 90.0,
            "initial_preferred_major": ["medicine"],
            "contact_id": "0912345678",
        },
    )
    _assert_shape(resp)
    assert resp.json()["error_code"] == "sms_send_failed"


def test_shape_429_too_many_requests(client, monkeypatch):
    monkeypatch.setattr("app.dependencies._RATE_LIMIT_MAX_REQUESTS", 1)
    client.post(
        "/students/lookup-by-contact",
        json={"contact_id": "0911111111", "full_name": "x"},
    )
    resp = client.post(
        "/students/lookup-by-contact",
        json={"contact_id": "0911111111", "full_name": "x"},
    )
    _assert_shape(resp)
    assert resp.json()["error_code"] == "too_many_requests"


def test_duplicate_checkin_rich_details(
    client, student_factory, students_admin_headers
):
    student_factory("R-8888")
    client.post(
        "/checkins/campus-entry",
        json={"unique_code": "R-8888"},
        headers=students_admin_headers,
    )
    resp = client.post(
        "/checkins/campus-entry",
        json={"unique_code": "R-8888"},
        headers=students_admin_headers,
    )
    assert resp.status_code == 409
    body = resp.json()
    _assert_shape(resp)
    assert body["error_code"] == "duplicate_checkin"
    details = body["details"]
    assert details["unique_code"] == "R-8888"
    assert details["activity_type"] == "campus_entry"
    assert "student_name" in details
    assert "first_occurred_at" in details