"""اختبارات المدخلات السلبية والضارة على واجهات النظام.

تؤكد أن فجوات التحقق السابقة أصبحت مغلقة: كل بيانات غير صالحة تُرفض
بشكل موحّد (422) بدل قبولها أو تسريب 500 خام من قاعدة البيانات.
"""

import pytest

from fastapi.testclient import TestClient

import main as main_module
from app.models import Student


@pytest.fixture
def _soft_client():
    """TestClient بدون raise_server_exceptions — الوحيد القادر على التقاط استجابات
    500 القادمة من معالج الأخطاء العام (Starlette يعيد رفع الاستثناء دائماً)."""
    return TestClient(main_module.app, raise_server_exceptions=False)


def _register_payload(**overrides):
    payload = {
        "full_name": "طالب تجريبي",
        "birth_date": "2001-05-05",
        "certificate_year": 2024,
        "certificate_type": "scientific",
        "average_score": 88.5,
        "initial_preferred_major": ["medicine"],
        "contact_platform": "whatsapp",
        "contact_id": "0912345678",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def _no_sms(monkeypatch):
    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms",
        lambda *a, **k: None,
    )


def test_register_empty_body_422(client):
    resp = client.post("/students/register", json={})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_full_name_empty_string_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(full_name=""))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_full_name_whitespace_only_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(full_name="   "))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_full_name_over_255_chars_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(full_name="أ" * 256))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_contact_id_over_255_chars_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(contact_id="9" * 256))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_certificate_year_out_of_bounds_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(certificate_year=40000))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_negative_average_score_422(client):
    resp = client.post("/students/register", json=_register_payload(average_score=-1))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_future_birth_date_422(client, _no_sms):
    resp = client.post("/students/register", json=_register_payload(birth_date="2999-01-01"))
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def _make_student_with_otp(client, **overrides):
    resp = client.post("/students/register", json=_register_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()["unique_code"]


def test_otp_rejects_non_digit_code_422(client, _no_sms):
    code = _make_student_with_otp(client)
    resp = client.post("/students/otp/verify", json={"unique_code": code, "otp": "abcd"})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_otp_rejects_wrong_digits_400(client, db, monkeypatch, _no_sms):
    """رمز رقمي صحيح الشكل لكن خاطئ → 400 otp_invalid (يفشل بمقارنة الـ hash)."""
    monkeypatch.setattr(
        "app.routers.registration.registration_service._generate_otp_code", lambda: "1234"
    )
    code = _make_student_with_otp(client)
    resp = client.post("/students/otp/verify", json={"unique_code": code, "otp": "0000"})
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "otp_invalid"


def test_otp_rejects_too_long_code_422(client, _no_sms):
    code = _make_student_with_otp(client)
    resp = client.post("/students/otp/verify", json={"unique_code": code, "otp": "12345"})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_otp_rejects_too_short_code_422(client, _no_sms):
    code = _make_student_with_otp(client)
    resp = client.post("/students/otp/verify", json={"unique_code": code, "otp": "12"})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_register_missing_contact_id_422(client):
    payload = _register_payload()
    del payload["contact_id"]
    resp = client.post("/students/register", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_patch_account_empty_body_422(client, super_headers):
    resp = client.patch("/admin/accounts/taher_super", json={}, headers=super_headers)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_patch_student_empty_body_422(client, student_factory, students_admin_headers):
    s = student_factory("R-9001")
    resp = client.patch(f"/admin/students/{s.id}", json={}, headers=students_admin_headers)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_patch_student_bacc_average_out_of_bounds_422(client, student_factory, students_admin_headers):
    s = student_factory("R-9001")
    resp = client.patch(
        f"/admin/students/{s.id}", json={"bacc_average": 500}, headers=students_admin_headers
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_staff_and_scanner_forbidden_on_admin_accounts(client, college_staff_headers, gate_scanner_headers):
    for headers in (college_staff_headers, gate_scanner_headers):
        resp = client.get("/admin/accounts", headers=headers)
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "forbidden"


def test_sql_injection_strings_stored_verbatim(client, db, _no_sms):
    """التسجيل يستخدم استعلامات مقيّدة: نصوص إدخال ضارة تُخزَّن نصاً حرفياً دون تنفيذ."""
    evil_name = "x'; DROP TABLE students;--"
    evil_contact = "091' OR '1'='1"
    resp = client.post(
        "/students/register",
        json=_register_payload(full_name=evil_name, contact_id=evil_contact),
    )
    assert resp.status_code == 201, resp.text
    assert db.query(Student).count() == 1
    st = db.query(Student).first()
    assert st.full_name == evil_name
    assert st.contact_id == evil_contact


def test_register_non_json_body_422(client):
    resp = client.post(
        "/students/register",
        content="this is not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_unexpected_error_returns_structured_500(_soft_client, monkeypatch, _no_sms):
    """شبكة الأمان العامة: خطأ غير متوقع لم يُعالَج → 500 موحّد الشكل لا 500 خام."""
    def boom(*args, **kwargs):
        raise RuntimeError("internal unexpected failure")

    monkeypatch.setattr(
        "app.routers.registration.registration_service.register_student", boom
    )
    resp = _soft_client.post("/students/register", json=_register_payload())
    assert resp.status_code == 500
    body = resp.json()
    assert body["error_code"] == "internal_error"
    assert body["message"]
    assert body["details"] == {}