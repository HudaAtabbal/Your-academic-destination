"""اختبارات بطاقة الطالب — endpoint عام يرجع بيانات البطاقة + qr_payload."""

from app.models import VerificationStatus


STUDENT = "R-9001"
CARD_URL = f"/students/card/{STUDENT}"


# ---------- happy path ----------


def test_card_happy(client, student_factory):
    """طالب موثّق → البطاقة ترجع كل الحقول الصحيحة."""
    student_factory(STUDENT, verification_status=VerificationStatus.verified)
    resp = client.get(CARD_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["unique_code"] == STUDENT
    assert body["full_name"] == "طالب تجريبي"
    assert body["verification_status"] == "verified"
    assert body["qr_payload"] == STUDENT


def test_card_pending_student(client, student_factory):
    """طالب قيد الانتظار → verification_status = pending."""
    student_factory(STUDENT, verification_status=VerificationStatus.pending)
    resp = client.get(CARD_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["verification_status"] == "pending"
    assert body["qr_payload"] == STUDENT


# ---------- 404 ----------


def test_card_unknown_404(client):
    """كود غير موجود → 404 student_not_found."""
    resp = client.get("/students/card/R-9999")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


# ---------- qr_payload ----------


def test_card_qr_payload_matches_unique_code(client, student_factory):
    """qr_payload لازم يكون دايمًا مطابق لـ unique_code."""
    student_factory(STUDENT, verification_status=VerificationStatus.verified)
    body = client.get(CARD_URL).json()
    assert body["qr_payload"] == body["unique_code"]


# ---------- سلاسل الحقول عبر endpoints ----------


def test_card_chain_to_campus_entry(client, student_factory, students_admin_headers):
    """الكود من البطاقة يُستخدم لدخول الحرم (campus-entry) بنجاح."""
    student_factory(STUDENT, verification_status=VerificationStatus.verified)
    # ناخد الكود من الـ card endpoint
    card = client.get(CARD_URL).json()
    code = card["qr_payload"]
    # نستخدمه لتسجيل الدخول
    resp = client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=students_admin_headers
    )
    assert resp.status_code == 201


# ---------- عام بدون مصادقة ----------


def test_card_unauthenticated_ok(client, student_factory):
    """البطاقة endpoint عام — بدون توكن يرجع 200."""
    student_factory(STUDENT, verification_status=VerificationStatus.verified)
    resp = client.get(CARD_URL)
    assert resp.status_code == 200
