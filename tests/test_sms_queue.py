"""
اختبارات طابور إرسال SMS (SMS_MODE=queue) والـ endpoints الداخلية.

تغطي: تسجيل ينجح بدون إرسال فوري + صف pending، سحب المهام وتأكيد الصيغة
الدولية والرمز الصريح، منع السحب المكرر، الإبلاغ بالنجاح/الفشل (مؤقت/دائم)،
استرداد المهام العالقة واستنفاد المحاولات، استبعاد رمز منتهي الصلاحية،
الرفض بدون/بتوكن خاطئ، حالة لوحة الإدارة، وأن المسار المتزامن القديم
(sync) بقي كما هو (502 عند فشل الإرسال).
"""

import hashlib
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.models import OTP, SmsHeartbeat, SmsJob, SmsJobStatus

_WORKER_TOKEN = "test-worker-token"


@pytest.fixture(autouse=True)
def _worker_token_env(monkeypatch):
    # يُضبط لكل اختبارات الملف حتى تعمل /internal/sms؛ اختبار الرفض بدون توكن
    # يحذفه صراحة عبر monkeypatch.delenv فوراً
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)

_REGISTER_PAYLOAD = {
    "full_name": "طالب تجريبي",
    "birth_date": "2001-05-05",
    "certificate_year": 2024,
    "certificate_type": "scientific",
    "average_score": 88.5,
"initial_preferred_major": ["medicine"],
        "contact_id": "0912345678",
}


def _register(client: TestClient, monkeypatch, **overrides) -> dict:
    payload = {**_REGISTER_PAYLOAD, **overrides}
    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms",
        lambda *a, **k: None,
    )
    resp = client.post("/students/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _add_job(
    db,
    *,
    student,
    phone: str = "0991234567",
    otp_code: str = "1234",
    status: SmsJobStatus = SmsJobStatus.pending,
    attempts: int = 0,
    claimed_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> tuple[OTP, SmsJob]:
    otp = OTP(
        student_id=student.id,
        code=hashlib.sha256(otp_code.encode()).hexdigest(),
        expires_at=expires_at or (datetime.now() + timedelta(minutes=10)),
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    job = SmsJob(
        otp_id=otp.id,
        phone=phone,
        otp_code=otp_code,
        status=status,
        attempts=attempts,
        claimed_at=claimed_at,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return otp, job


def _worker_headers() -> dict:
    return {"Authorization": f"Bearer {_WORKER_TOKEN}"}


def _dequeue(client: TestClient, batch: int = 10) -> list[dict]:
    resp = client.post(
        "/internal/sms/dequeue", params={"batch": batch}, headers=_worker_headers()
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Q1: تسجيل بوضع queue + فشل send لو حُدّث — 201 فوراً، صف pending، بدون إرسال
# ---------------------------------------------------------------------------


def test_queue_mode_registration_creates_pending_job_without_sending(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")

    calls: list = []
    def _boom(*a, **k):
        calls.append(a)
        raise RuntimeError("should never be called")

    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms", _boom
    )

    resp = client.post("/students/register", json=_REGISTER_PAYLOAD)
    assert resp.status_code == 201, resp.text
    assert calls == []  # الإرسال الفوري لم يُستدعَ إطلاقاً

    job = db.query(SmsJob).one()
    assert job.status == SmsJobStatus.pending
    assert job.attempts == 0
    assert job.phone == "0912345678"
    assert len(job.otp_code) == 4
    assert job.otp is not None


# ---------------------------------------------------------------------------
# Q2: dequeue — بيانات الإرسال + انتقال الحالة
# ---------------------------------------------------------------------------


def test_dequeue_returns_job_with_international_phone_and_plaintext_code(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    otp, job = _add_job(db, student=student, phone="0912345678", otp_code="4321")

    items = _dequeue(client)

    assert len(items) == 1
    item = items[0]
    assert item["job_id"] == job.id
    assert item["phone"] == "963912345678"
    assert item["otp_code"] == "4321"
    assert "expires_at" in item

    db.refresh(job)
    assert job.status == SmsJobStatus.sending
    assert job.attempts == 1
    assert job.claimed_at is not None


# ---------------------------------------------------------------------------
# Q3: dequeue ثانٍ أثناء sending — فارغ
# ---------------------------------------------------------------------------


def test_second_dequeue_is_empty_while_job_sending(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    _add_job(db, student=student)

    assert len(_dequeue(client)) == 1
    assert _dequeue(client) == []


# ---------------------------------------------------------------------------
# Q4: report نجاح → sent
# ---------------------------------------------------------------------------


def test_report_success_marks_job_sent(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    otp, job = _add_job(db, student=student)
    job_id = _dequeue(client)[0]["job_id"]

    resp = client.post(
        "/internal/sms/report",
        json={"job_id": job_id, "success": True},
        headers=_worker_headers(),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "sent"

    db.refresh(job)
    assert job.status == SmsJobStatus.sent
    assert job.sent_at is not None


# ---------------------------------------------------------------------------
# Q5: report فشل دائم → failed
# ---------------------------------------------------------------------------


def test_report_permanent_failure_marks_job_failed(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    otp, job = _add_job(db, student=student)
    job_id = _dequeue(client)[0]["job_id"]

    resp = client.post(
        "/internal/sms/report",
        json={"job_id": job_id, "success": False, "transient": False, "error": "User isn't active"},
        headers=_worker_headers(),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "failed"

    db.refresh(job)
    assert job.status == SmsJobStatus.failed
    assert job.error == "User isn't active"


def test_report_transient_failure_returns_job_to_pending(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    otp, job = _add_job(db, student=student)
    job_id = _dequeue(client)[0]["job_id"]

    resp = client.post(
        "/internal/sms/report",
        json={"job_id": job_id, "success": False, "transient": True, "error": "timeout"},
        headers=_worker_headers(),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "pending"

    db.refresh(job)
    assert job.status == SmsJobStatus.pending
    assert job.attempts == 1
    assert job.claimed_at is None


# ---------------------------------------------------------------------------
# Q6: صف عالق (claimed_at قديم) + مرسِل ميت → يستردَّن؛ استنفاد المحاولات → failed
# ---------------------------------------------------------------------------


def test_stale_sending_job_reclaimed_when_worker_dead(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    stale_at = datetime.now() - timedelta(seconds=180)
    otp, job = _add_job(
        db, student=student, status=SmsJobStatus.sending, attempts=1, claimed_at=stale_at
    )

    # لا نبضة قلب إطلاقاً → المرسل ميت → يُستردّ الصف ويعاد للسحب
    items = _dequeue(client)
    assert len(items) == 1
    assert items[0]["job_id"] == job.id

    db.refresh(job)
    assert job.status == SmsJobStatus.sending
    assert job.attempts == 2


def test_sending_job_with_exhausted_attempts_marked_failed(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    stale_at = datetime.now() - timedelta(seconds=180)
    otp, job = _add_job(
        db, student=student, status=SmsJobStatus.sending, attempts=5, claimed_at=stale_at
    )

    assert _dequeue(client) == []

    db.refresh(job)
    assert job.status == SmsJobStatus.failed


def test_stale_sending_job_reclaimed_even_when_worker_alive(
    client, db, student_factory, monkeypatch
):
    """إبلاغ ضائع والمُرسِل حيّ (نبضات مستمرة) — المهمة لازم تُستردّ بعد المهلة،
    ما تبقى محتجزة إلى الأبد. هاد الفرق يلي بيمنع رمز ما يوصل أبداً."""
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    # نبضة حديثة → المُرسِل "حي" تماماً كحالة إبلاغ ضاع فيه اتصال الخادم
    heartbeat = client.post("/internal/sms/heartbeat", headers=_worker_headers())
    assert heartbeat.status_code == 200

    stale_at = datetime.now() - timedelta(seconds=180)
    otp, job = _add_job(
        db, student=student, status=SmsJobStatus.sending, attempts=1, claimed_at=stale_at
    )

    items = _dequeue(client)
    assert len(items) == 1
    assert items[0]["job_id"] == job.id

    db.refresh(job)
    assert job.status == SmsJobStatus.sending
    assert job.attempts == 2


# ---------------------------------------------------------------------------
# Q7: OTP منتهي الصلاحية — لا يُمرَّر أبداً
# ---------------------------------------------------------------------------


def test_expired_otp_job_never_dispatched(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    expires_past = datetime.now() - timedelta(minutes=1)
    otp, job = _add_job(db, student=student, expires_at=expires_past)

    assert _dequeue(client) == []

    db.refresh(job)
    assert job.status == SmsJobStatus.pending


# ---------------------------------------------------------------------------
# Q8: 401 بدون توكن / بتوكن خاطئ / بدون WORKER_TOKEN
# ---------------------------------------------------------------------------


def test_internal_endpoints_reject_missing_token(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)
    student = student_factory("R-9001", contact_id="0912345678")
    _add_job(db, student=student)

    for path, payload in (
        ("/internal/sms/dequeue?batch=1", None),
        ("/internal/sms/report", {"job_id": 999, "success": True}),
        ("/internal/sms/heartbeat", None),
    ):
        resp = client.post(path, json=payload) if payload is not None else client.post(path)
        assert resp.status_code == 401, (path, resp.text)
        assert resp.json()["error_code"] == "invalid_credentials"


def test_internal_endpoints_reject_wrong_token(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)
    student = student_factory("R-9001", contact_id="0912345678")
    _add_job(db, student=student)

    bad = {"Authorization": "Bearer wrong-token"}
    resp = client.post("/internal/sms/dequeue?batch=1", headers=bad)
    assert resp.status_code == 401


def test_internal_endpoints_reject_when_worker_token_unset(
    client, db, student_factory, monkeypatch
):
    monkeypatch.delenv("WORKER_TOKEN", raising=False)
    student = student_factory("R-9001", contact_id="0912345678")
    _add_job(db, student=student)

    resp = client.post("/internal/sms/dequeue?batch=1", headers=_worker_headers())
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Q9: لوحة الإدارة — sms-status
# ---------------------------------------------------------------------------

def test_dashboard_sms_status_counts_and_worker_online(
    client, db, student_factory, super_headers, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)
    student = student_factory("R-9001", contact_id="0912345678")

    # صف خُلّق pending وآخر وصل sent — لنفحص الأعداد
    otp, pending_job = _add_job(db, student=student)
    otp2, sent_job = _add_job(db, student=student, otp_code="9999")
    db.query(SmsJob).filter(SmsJob.id == sent_job.id).update(
        {"status": SmsJobStatus.sent}
    )
    db.commit()

    resp = client.get("/admin/dashboard/sms-status", headers=super_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["counts"]["pending"] == 1
    assert body["counts"]["sent"] == 1
    assert body["last_heartbeat"] is None
    assert body["worker_online"] is False

    client.post("/internal/sms/heartbeat", headers=_worker_headers())
    resp = client.get("/admin/dashboard/sms-status", headers=super_headers)
    body = resp.json()
    assert body["worker_online"] is True
    assert body["last_heartbeat"] is not None


def test_dashboard_sms_status_forbidden_for_non_super(
    client, college_staff_headers, monkeypatch
):
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)
    resp = client.get("/admin/dashboard/sms-status", headers=college_staff_headers)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Q10: وضع sync الافتراضي + send يرمي → 502 (المسار القديم سليم)
# ---------------------------------------------------------------------------


def test_sync_mode_default_still_fails_with_502_when_send_raises(
    client, monkeypatch
):
    monkeypatch.delenv("SMS_MODE", raising=False)  # يبقى الوضع الافتراضي sync

    from app import sms_service as sms_service_module

    def _boom(*a, **k):
        raise sms_service_module.SmsSendError("User isn't active")

    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms", _boom
    )

    resp = client.post("/students/register", json=_REGISTER_PAYLOAD)
    assert resp.status_code == 502
    assert resp.json()["error_code"] == "sms_send_failed"


# ---------------------------------------------------------------------------
# Q11: report لعملية غير موجودة → 404 job_not_found
# ---------------------------------------------------------------------------


def test_report_nonexistent_job_404(client, monkeypatch):
    monkeypatch.setenv("SMS_MODE", "queue")
    resp = client.post(
        "/internal/sms/report",
        json={"job_id": 999999, "success": True},
        headers=_worker_headers(),
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "job_not_found"


# ---------------------------------------------------------------------------
# Q12: dequeue batch=0 و batch=11 → 422
# ---------------------------------------------------------------------------


def test_dequeue_batch_zero_422(client, monkeypatch):
    monkeypatch.setenv("SMS_MODE", "queue")
    resp = client.post(
        "/internal/sms/dequeue", params={"batch": 0}, headers=_worker_headers()
    )
    assert resp.status_code == 422


def test_dequeue_batch_eleven_422(client, monkeypatch):
    monkeypatch.setenv("SMS_MODE", "queue")
    resp = client.post(
        "/internal/sms/dequeue", params={"batch": 11}, headers=_worker_headers()
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Q13: report على صف pending (مش sending) → idempotent (يترجع كما هو)
# ---------------------------------------------------------------------------


def test_report_pending_job_idempotent(
    client, db, student_factory, monkeypatch
):
    monkeypatch.setenv("SMS_MODE", "queue")
    student = student_factory("R-9001", contact_id="0912345678")
    otp, job = _add_job(db, student=student, status=SmsJobStatus.pending)

    resp = client.post(
        "/internal/sms/report",
        json={"job_id": job.id, "success": True},
        headers=_worker_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    db.refresh(job)
    assert job.status == SmsJobStatus.pending
    assert job.sent_at is None
