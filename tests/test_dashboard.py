"""اختبارات لوحة المدير العام (dashboard) — super_admin فقط."""

from app.models import RegistrationType, VerificationStatus

STUDENT = "R-9001"
L1 = "lecture_1"


def _campus_entry(client, headers, code):
    return client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=headers
    )


def _lecture(client, headers, code, lecture=L1):
    return client.post(
        "/checkins/lecture",
        json={"unique_code": code, "lecture_name": lecture},
        headers=headers,
    )


def test_dashboard_stats(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    student_factory(STUDENT)
    student_factory("R-9002")
    student_factory(
        "W-0001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )
    assert _campus_entry(client, students_admin_headers, STUDENT).status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT).status_code == 201
    assert (
        client.post(
            f"/survey/{STUDENT}",
            json={"opinion_change": "decided", "preferred_major": "medicine"},
        ).status_code
        == 201
    )
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered_online_count"] == 2
    # الطالب الوحيد اللي عنده campus_entry اليوم هو R-9001 (مرة واحدة) —
    # يُحسب مرة واحدة (distinct) سواء باليوم أو بكل الأيام.
    assert body["students_inside_today"] == 1
    assert body["students_inside_all_days"] == 1
    assert body["survey_completed_count"] == 1
    assert body["walkin_pending_count"] == 0


def test_dashboard_stats_walkin_pending_count(
    client, student_factory, super_headers
):
    student_factory(  # walk-in pending — مكتمل ناقص بيانات، لازم يُحصى بانتظار الإكمال
        "W-0001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.pending,
        status="pending",
    )
    student_factory(
        "W-0002",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status="complete",
    )
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["walkin_pending_count"] == 1


def test_dashboard_rooms_occupancy(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert _lecture(client, gate_scanner_headers, code).status_code == 201
    resp = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers)
    assert resp.status_code == 200
    rooms = resp.json()["rooms"]
    assert len(rooms) == 1
    room = rooms[0]
    assert room["lecture_name"] == L1
    assert room["hall_label"] == "المدرج الرئيسي"
    assert room["current_count"] == 2
    assert "last_updated" in room


def test_dashboard_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/stats", headers=students_admin_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_dashboard_counts_only_verified_registered(
    client, student_factory, super_headers
):
    """'مسجّلون إلكترونياً' يِحسب فقط الموثَّق (دخل الـ OTP وشاف البطاقة)،
    لا من سُدّد تسجيلُه وأُرسل له الرمز فقط."""
    student_factory("R-9001", verification_status=VerificationStatus.verified)
    student_factory(  # مسجّل إلكترونياً لكنه لسا موثّق (بعد إرسال الـ OTP فقط)
        "R-9002", verification_status=VerificationStatus.pending
    )
    student_factory(  # walk-in موثّق — ليس "إلكترونياً"
        "W-0001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["registered_online_count"] == 1