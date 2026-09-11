# -*- coding: utf-8 -*-
"""
اختبارات الإصلاحات الأمنية (مرحلة A+B+C):
- A1: rate limit على /register و/lookup-by-contact (429 بعد تجاوز الحد)
- A2: rate limit لكل طالب على /otp/verify و/otp/resend (429)
- A3: resend يبطل الـ OTPs القديمة غير المحققة
- A4: OTP مخزّن كهاش SHA-256 (الرمز الصريح غير موجود بالـ DB)
- A5: أعمدة enum بالـ query params ترجع 422 بدل 500
- A6: token_version — تغيير كلمة السر يبطل التوكنات القديمة
- B1-a: رموز R عشوائية 6 خانات (بدل المتسلسل R-0001)
"""
import hashlib
import hmac
import re

import pytest

from app.dependencies import _RATE_LIMIT_OTP_VERIFY_MAX, rate_limit_student_otp
from app.models import OTP, Student, VerificationStatus


def _register_payload(contact_id: str = "0915550001", full_name: str = "طالب أمني"):
    return {
        "full_name": full_name,
        "birth_date": "2001-05-05",
        "certificate_year": 2024,
        "certificate_type": "scientific",
        "average_score": 88.5,
        "initial_preferred_major": ["medicine"],
        "contact_platform": "whatsapp",
        "contact_id": contact_id,
    }


class TestRateLimit:
    def test_register_returns_429_after_limit(self, client, db, monkeypatch):
        monkeypatch.setattr("app.dependencies._RATE_LIMIT_MAX_REQUESTS", 3)
        from app.routers.registration import registration_service

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        # أول 3 طلبات عادية، الرابع لازم يتصد مع 429 (نفس الـ IP)
        for i in range(3):
            r = client.post(
                "/students/register",
                json=_register_payload(contact_id=f"0915550{i:03d}"),
            )
            assert r.status_code == 201, r.text
        r4 = client.post("/students/register", json=_register_payload(contact_id="091555999"))
        assert r4.status_code == 429, r4.text
        assert r4.json()["error_code"] == "too_many_requests"

    def test_lookup_by_contact_returns_429(self, client, db, monkeypatch):
        monkeypatch.setattr("app.dependencies._RATE_LIMIT_MAX_REQUESTS", 2)
        for _ in range(2):
            r = client.post(
                "/students/lookup-by-contact",
                json={"contact_platform": "whatsapp", "contact_id": "0911111111", "full_name": "طالب تجريبي"},
            )
            assert r.status_code == 404, r.text  # مش موجود — مش مشكلة، الـ limiter بيشتغل قبله
        r3 = client.post(
            "/students/lookup-by-contact",
            json={"contact_platform": "whatsapp", "contact_id": "0911111111", "full_name": "طالب تجريبي"},
        )
        assert r3.status_code == 429, r3.text


class TestPerStudentOtpLimit:
    def test_verify_limited_per_student(self, client, db, monkeypatch):
        monkeypatch.setattr("app.dependencies._RATE_LIMIT_OTP_VERIFY_MAX", 2)
        from app.routers.registration import registration_service

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r = client.post("/students/register", json=_register_payload())
        code = r.json()["unique_code"]

        # أول محاولتين: خطأ OTP (400) — الثالثة: 429
        for i in range(2):
            resp = client.post(
                "/students/otp/verify",
                json={"unique_code": code, "otp": "0000"},
            )
            assert resp.status_code == 400, resp.text
        resp3 = client.post(
            "/students/otp/verify",
            json={"unique_code": code, "otp": "0000"},
        )
        assert resp3.status_code == 429, resp3.text
        assert resp3.json()["error_code"] == "too_many_requests"

    def test_resend_limited_per_student(self, client, db, monkeypatch):
        monkeypatch.setattr("app.dependencies._RATE_LIMIT_OTP_VERIFY_MAX", 100)
        from app.routers.registration import registration_service

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r = client.post("/students/register", json=_register_payload())
        code = r.json()["unique_code"]
        # مسح سجل الطالب من الـ limiter — المشكلة أن الـ resend له max=2 ثابت بالـ router
        db.query(OTP).delete()
        db.commit()
        # 2 resends عادية، الثالثة لازم 429 (حد الـ resend: 2/دقيقة)
        for _ in range(2):
            resp = client.post("/students/otp/resend", json={"unique_code": code})
            assert resp.status_code == 200, resp.text
        resp3 = client.post("/students/otp/resend", json={"unique_code": code})
        assert resp3.status_code == 429, resp3.text


class TestOtpInvalidation:
    def test_resend_invalidates_old_unverified_otps(self, client, db, monkeypatch):
        from app.routers.registration import registration_service

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r = client.post("/students/register", json=_register_payload())
        code = r.json()["unique_code"]
        st = db.query(Student).filter(Student.unique_code == code).first()

        first_otp = db.query(OTP).filter(OTP.student_id == st.id).all()
        assert len(first_otp) == 1
        old_id = first_otp[0].id

        r2 = client.post("/students/otp/resend", json={"unique_code": code})
        assert r2.status_code == 200, r2.text

        remaining = db.query(OTP).filter(OTP.student_id == st.id).all()
        # القديم انمسح، والجديد وحده موجود
        assert len(remaining) == 1
        assert remaining[0].id != old_id


class TestOtpHashing:
    def test_otp_stored_as_hash_not_plaintext(self, client, db, monkeypatch):
        captured = {}
        from app.routers.registration import registration_service

        def _capture(phone, code):
            captured["code"] = code

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", _capture)
        r = client.post("/students/register", json=_register_payload())
        code = r.json()["unique_code"]
        st = db.query(Student).filter(Student.unique_code == code).first()
        otp = db.query(OTP).filter(OTP.student_id == st.id).first()

        # الرمز الصريح اللي انبعت بـ SMS مش موجود كنص بالـ DB
        assert otp.code != captured["code"]
        assert re.fullmatch(r"[0-9a-f]{64}", otp.code) is not None
        assert hmac.compare_digest(
            otp.code, hashlib.sha256(captured["code"].encode()).hexdigest()
        )

    def test_verify_with_correct_code_still_works(self, client, db, monkeypatch):
        captured = {}
        from app.routers.registration import registration_service

        def _capture(phone, code):
            captured["code"] = code

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", _capture)
        r = client.post("/students/register", json=_register_payload())
        code = r.json()["unique_code"]

        resp = client.post(
            "/students/otp/verify",
            json={"unique_code": code, "otp": captured["code"]},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["verification_status"] == "verified"

        st = db.query(Student).filter(Student.unique_code == code).first()
        assert st.verification_status == VerificationStatus.verified


class TestEnumQueryParams:
    def test_invalid_college_returns_422_not_500(self, client, students_admin_headers):
        resp = client.get(
            "/checkins/count/today",
            params={"activity_type": "lecture", "college": "not_a_college"},
            headers=students_admin_headers,
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "validation_error"

    def test_invalid_lecture_returns_422(self, client, students_admin_headers):
        resp = client.get(
            "/checkins/count/today",
            params={"activity_type": "lecture", "lecture_name": "not_a_lecture"},
            headers=students_admin_headers,
        )
        assert resp.status_code == 422, resp.text

    def test_invalid_college_booking_count_returns_422(self, client, super_headers):
        resp = client.get(
            "/bookings/count/today",
            params={"booking_type": "tour", "college": "not_a_college"},
            headers=super_headers,
        )
        assert resp.status_code == 422, resp.text


class TestTokenVersion:
    def test_password_change_invalidates_old_token(self, client, super_headers, db):
        # توكن قديم (صادر قبل تغيير كلمة السر)
        old_token = super_headers["Authorization"]

        # تغيير كلمة سر taher_super عبر PATCH
        resp = client.patch(
            "/admin/accounts/taher_super",
            json={"password": "new-super-pass-123"},
            headers={"Authorization": old_token},
        )
        assert resp.status_code == 200, resp.text

        # التوكن القديم صار مرفوض على أي endpoint محمي
        resp2 = client.get(
            "/admin/accounts",
            headers={"Authorization": old_token},
        )
        assert resp2.status_code == 401, resp2.text
        assert resp2.json()["error_code"] == "invalid_credentials"


class TestRandomCodes:
    def test_registration_code_is_random_6_digit(self, client, db, monkeypatch):
        from app.routers.registration import registration_service

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        seen = set()
        for i in range(5):
            r = client.post(
                "/students/register",
                json=_register_payload(contact_id=f"091600{i:04d}"),
            )
            assert r.status_code == 201, r.text
            code = r.json()["unique_code"]
            # الشكل R-XXXXXX (6 خانات) — نفس الشكل القديم أمام الفرونت
            assert re.fullmatch(r"R-\d{6}", code) is not None, code
            seen.add(code)
        # عشوائية فعلية: 5 رموز مختلفة (احتمال التكرار بالصدفة ≈ صفر)
        assert len(seen) == 5
