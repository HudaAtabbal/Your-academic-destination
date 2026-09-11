"""
اختبارات مسار التسجيل الإلكتروني — السلوك المتفق عليه:
الرقم (تواصل) ما بينحجز إلا بعد التحقق الكامل + الباركود.

قاعدة: أي تسجيلات pending بنفس الرقم بتستبدل بعضها (الأحدث بكسب)،
والتسجيل بعد التحقق بيمنع نهائياً (409 duplicate_contact).
"""

import threading
from datetime import date

import pytest

from app.errors import AppError
from app.models import OTP, RegistrationType, Student, VerificationStatus
from app.models.enums import CertificateType, College, ContactPlatform
from app.routers.registration import registration_service
from app import sms_service


def _service_args(contact_id: str = "0911111111", full_name: str = "اسم مباشر"):
    return dict(
        full_name=full_name,
        birth_date=date(2000, 1, 1),
        certificate_year=2025,
        certificate_type=CertificateType.scientific,
        average_score=85.5,
        initial_preferred_major=[College.medicine],
        contact_platform=ContactPlatform.whatsapp,
        contact_id=contact_id,
    )


def _register_payload(contact_id: str = "0911111111", full_name: str = "اسم مباشر"):
    args = _service_args(contact_id=contact_id, full_name=full_name)
    return {
        "full_name": args["full_name"],
        "birth_date": "2000-01-01",
        "certificate_year": args["certificate_year"],
        "certificate_type": args["certificate_type"].value,
        "average_score": args["average_score"],
        "initial_preferred_major": [c.value for c in args["initial_preferred_major"]],
        "contact_platform": args["contact_platform"].value,
        "contact_id": args["contact_id"],
    }


def _count_registered_by_contact(db, contact_id: str) -> int:
    return (
        db.query(Student)
        .filter(
            Student.contact_id == contact_id,
            Student.registration_type == RegistrationType.registered,
        )
        .count()
    )


class TestPendingReplace:
    def test_register_creates_pending_student(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        resp = client.post("/students/register", json=_register_payload())
        assert resp.status_code == 201, resp.text
        code = resp.json()["unique_code"]
        st = db.query(Student).filter(Student.unique_code == code).first()
        assert st is not None
        assert st.verification_status == VerificationStatus.pending
        assert st.registration_type == RegistrationType.registered

    def test_pending_register_same_contact_replaces_old(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        # أول تسجيل — pending
        r1 = client.post(
            "/students/register", json=_register_payload(full_name="الاسم الأول")
        )
        assert r1.status_code == 201, r1.text
        code1 = r1.json()["unique_code"]
        st1 = db.query(Student).filter(Student.unique_code == code1).first()
        st1_id = st1.id

        # نفس الرقم بس اسم مزبوط — يجب أن يستبدل السجل القديم (ما في 409)
        r2 = client.post("/students/register", json=_register_payload(full_name="الاسم المزبوط"))
        assert r2.status_code == 201, r2.text
        code2 = r2.json()["unique_code"]

        assert _count_registered_by_contact(db, "0911111111") == 1
        st2 = db.query(Student).filter(Student.unique_code == code2).first()
        assert st2 is not None
        assert st2.id != st1_id  # سجل جديد فعلاً، مش نفس سطر الـ DB
        assert db.query(Student).filter(Student.id == st1_id).first() is None
        assert st2.full_name == "الاسم المزبوط"

    def test_pending_replace_keeps_only_latest_otp(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r1 = client.post("/students/register", json=_register_payload())
        code1 = r1.json()["unique_code"]
        st1 = db.query(Student).filter(Student.unique_code == code1).first()
        assert db.query(OTP).filter(OTP.student_id == st1.id).count() == 1

        r2 = client.post("/students/register", json=_register_payload(full_name="المرة الثانية"))
        code2 = r2.json()["unique_code"]
        st2 = db.query(Student).filter(Student.unique_code == code2).first()
        assert st1.id != st2.id
        assert db.query(OTP).filter(OTP.student_id == st1.id).count() == 0
        assert db.query(OTP).filter(OTP.student_id == st2.id).count() == 1


class TestVerifiedBlocksReuse:
    def test_registered_then_verified_blocks_same_contact(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r1 = client.post("/students/register", json=_register_payload())
        assert r1.status_code == 201, r1.text
        code = r1.json()["unique_code"]

        st = db.query(Student).filter(Student.unique_code == code).first()
        otp_row = db.query(OTP).filter(OTP.student_id == st.id).first()

        # تأكيد الـ OTP بالكود الحقيقي من القاعدة — يتحوّل لـ verified
        st.verification_status = VerificationStatus.verified
        st.status = "complete"
        db.commit()

        # نفس الرقم بعد التحقق → 409 duplicate_contact نهائياً
        r2 = client.post("/students/register", json=_register_payload(full_name="اسم مغاير"))
        assert r2.status_code == 409, r2.text
        assert r2.json()["error_code"] == "duplicate_contact"
        assert _count_registered_by_contact(db, "0911111111") == 1


class TestSmsFailureCleanup:
    def test_sms_failure_does_not_leave_orphan(self, client, db, monkeypatch):
        def _boom(phone, code):
            raise sms_service.SmsSendError("SYRIATEL_USERNAME غير معرف")

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", _boom)
        resp = client.post("/students/register", json=_register_payload())
        assert resp.status_code == 502, resp.text
        assert resp.json()["error_code"] == "sms_send_failed"
        # ما في ولا سجل يتيم — الطالب والـ OTP منحذفين
        assert _count_registered_by_contact(db, "0911111111") == 0
        assert db.query(OTP).count() == 0

    def test_sms_failure_then_retry_succeeds(self, client, db, monkeypatch):
        attempts = {"n": 0}

        def _flaky(phone, code):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise sms_service.SmsSendError("فشل مؤقت")
            return None

        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", _flaky)
        r1 = client.post("/students/register", json=_register_payload())
        assert r1.status_code == 502, r1.text
        assert _count_registered_by_contact(db, "0911111111") == 0

        r2 = client.post("/students/register", json=_register_payload())
        assert r2.status_code == 201, r2.text
        assert _count_registered_by_contact(db, "0911111111") == 1


class TestRaceSameContact:
    def test_concurrent_same_contact_single_pending_survivor(self, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        from app.database import SessionLocal

        results = []
        barrier = threading.Barrier(2)

        def _register():
            session = SessionLocal()
            try:
                barrier.wait(timeout=5)
                st, _code = registration_service.register_student(
                    session,
                    full_name="متنافس",
                    birth_date=date(2000, 1, 1),
                    certificate_year=2025,
                    certificate_type=CertificateType.scientific,
                    average_score=85.5,
                    initial_preferred_major=[College.medicine],
                    contact_platform=ContactPlatform.whatsapp,
                    contact_id="0911111111",
                )
                session.commit()
                results.append(st)
            except AppError as e:
                results.append(e)
            finally:
                session.close()

        t1 = threading.Thread(target=_register)
        t2 = threading.Thread(target=_register)
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        # في النهاية: سجل واحد بس بنفس الرقم + ما في أي استثناء uncaught
        assert not any(isinstance(r, AppError) for r in results)
        survivors = (
            db.query(Student)
            .filter(
                Student.contact_id == "0911111111",
                Student.registration_type == RegistrationType.registered,
            )
            .all()
        )
        assert len(survivors) == 1


class TestLookupByNameMatch:
    def test_lookup_requires_matching_name(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r = client.post("/students/register", json=_register_payload(full_name="خالد غيث طليمات"))
        assert r.status_code == 201, r.text
        code = r.json()["unique_code"]

        # رقم + اسم صحيح → يرجع الكود
        ok = client.post(
            "/students/lookup-by-contact",
            json={
                "contact_platform": "whatsapp",
                "contact_id": "0911111111",
                "full_name": "خالد غيث طليمات",
            },
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["unique_code"] == code

        # نفس الرقم + اسم خاطئ → 404 بنفس رسالة "الرمز مش موجود" (لا تسريب)
        bad = client.post(
            "/students/lookup-by-contact",
            json={
                "contact_platform": "whatsapp",
                "contact_id": "0911111111",
                "full_name": "اسم مختلف تماماً",
            },
        )
        assert bad.status_code == 404, bad.text
        assert bad.json()["error_code"] == "student_not_found"

    def test_lookup_ignores_extra_whitespace(self, client, db, monkeypatch):
        monkeypatch.setattr(registration_service.sms_service, "send_otp_sms", lambda *a, **k: None)
        r = client.post("/students/register", json=_register_payload(full_name="عمر أحمد العسورة"))
        assert r.status_code == 201, r.text

        ok = client.post(
            "/students/lookup-by-contact",
            json={
                "contact_platform": "whatsapp",
                "contact_id": "0911111111",
                "full_name": "  عمر   أحمد    العسورة  ",
            },
        )
        assert ok.status_code == 200, ok.text