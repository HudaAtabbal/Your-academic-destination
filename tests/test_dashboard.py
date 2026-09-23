"""اختبارات لوحة المدير العام (dashboard) — super_admin فقط."""

from app.models import (
    CertificateType,
    Faculty,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)

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


def _tour_booking(client, headers, code):
    return client.post("/bookings/tour", json={"unique_code": code}, headers=headers)


def _tour_checkin(client, headers, code):
    return client.post("/checkins/tour", json={"unique_code": code}, headers=headers)


def _consultation_booking(client, headers, code):
    return client.post(
        "/bookings/consultation", json={"unique_code": code}, headers=headers
    )


def _consultation_checkin(client, headers, code):
    return client.post(
        "/checkins/consultation", json={"unique_code": code}, headers=headers
    )


def _make_student_with_bacc(
    db, code, *, bacc_average=None, bacc_year=None, certificate_type=None
):
    student = Student(
        unique_code=code,
        full_name="طالب تجريبي",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
        bacc_average=bacc_average,
        bacc_year=bacc_year,
        certificate_type=certificate_type,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


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


def test_dashboard_stats_total_consultations(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    super_headers,
):
    """'إجمالي الاستشارات' يعدّ شيكيات الاستشارة المنفذة فعلياً (تراكمي)."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers, STUDENT).status_code == 201
    assert _consultation_booking(client, college_staff_headers, STUDENT).status_code == 201
    assert _consultation_checkin(client, college_staff_headers, STUDENT).status_code == 201
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["total_consultations"] == 1
    # الاستشارة مسجّلة مرة واحدة لكل طالب (unique index) — العملية نفسها ما بتزيد
    assert resp.json()["total_consultations"] == 1


def test_dashboard_analytics_college_visits_all_faculties(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    super_headers,
):
    """زيارة الكلية (ركن التوجيه) = شيكيات جولات الكلية المنفذة؛ تُعرض كل
    الكليات الـ24 حتى اللي بدون زيارات، بأعداد تنازلية."""
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert _tour_booking(client, college_staff_headers, code).status_code == 201
        assert _tour_checkin(client, college_staff_headers, code).status_code == 201
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    visits = resp.json()["college_visits"]
    assert len(visits) == len(Faculty)  # كل كليات الـ Faculty مدرجة (25) حتى بلا زيارات
    # رما (college_staff) مرتبطة بكلية الطِّب — زيارتاها تُحسبان عليها
    by_college = {v["college"]: v["count"] for v in visits}
    assert by_college["medicine"] == 2
    assert by_college["informatics"] == 0  # كلية بلا زيارات — ما زالت حاضرة بصفر
    # إجمالي الزيارات = 2، والترتيب تنازلي
    totals = [v["count"] for v in visits]
    assert sum(totals) == 2
    assert totals == sorted(totals, reverse=True)


def test_dashboard_analytics_lecture_attendance_all_16(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """حضور كل محاضرة: كل الـ16 مدرجة بترتيب enum مع تسميات عربية،
    والمحاضرات بلا حضور بصفر."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers, STUDENT).status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, "lecture_1").status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, "lecture_2").status_code == 201
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    rows = resp.json()["lecture_attendance"]
    assert len(rows) == 16
    # الترتيب مطابق لترتيب enum: lecture_1 ثم lecture_2 ثم …
    assert [r["lecture_name"] for r in rows[:2]] == ["lecture_1", "lecture_2"]
    assert rows[0]["count"] == 1
    assert rows[1]["count"] == 1
    # المحاضرة الأخيرة (حفل الختام) بلا حضور — صفر وموجودة
    assert rows[-1]["lecture_name"] == "lecture_16"
    assert rows[-1]["count"] == 0
    assert all(r["label"] for r in rows)  # كل صف عنده تسمية عربية


def test_dashboard_analytics_score_buckets(db, client, super_headers):
    """توزيع المعدل: فئات عرض 10 (0-10 … 90-100)، القيمة 100 تُصنف ضمن 90-100،
    والقيم الفارغة متجاهلة."""
    _make_student_with_bacc(db, "R-9001", bacc_average=5)    # → 0-10
    _make_student_with_bacc(db, "R-9002", bacc_average=15)   # → 10-20
    _make_student_with_bacc(db, "R-9003", bacc_average=92.5) # → 90-100
    _make_student_with_bacc(db, "R-9004", bacc_average=100)  # → 90-100 (clamped)
    _make_student_with_bacc(db, "R-9005", bacc_average=None)  # متجاهل
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    dist = resp.json()["score_distribution"]
    assert len(dist) == 10
    labels = [d["label"] for d in dist]
    assert labels[0] == "0-10"
    assert labels[-1] == "90-100"
    assert [d["count"] for d in dist] == [1, 1, 0, 0, 0, 0, 0, 0, 0, 2]


def test_dashboard_analytics_year_distribution(db, client, super_headers):
    """توزيع سنة الشهادة: مجموعة تصاعدياً، الفارغة متجاهلة."""
    _make_student_with_bacc(db, "R-9001", bacc_year=2023)
    _make_student_with_bacc(db, "R-9002", bacc_year=2024)
    _make_student_with_bacc(db, "R-9003", bacc_year=2024)
    _make_student_with_bacc(db, "R-9004", bacc_year=None)
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    dist = resp.json()["year_distribution"]
    assert [list(d.values()) for d in dist] == [[2023, 1], [2024, 2]]


def test_dashboard_analytics_certificate_distribution(db, client, super_headers):
    """علمي/أدبي: الفئتان مدرجتان دائماً حتى لو صفر."""
    _make_student_with_bacc(db, "R-9001", certificate_type=CertificateType.scientific)
    _make_student_with_bacc(db, "R-9002", certificate_type=CertificateType.scientific)
    _make_student_with_bacc(db, "R-9003", certificate_type=CertificateType.literary)
    _make_student_with_bacc(db, "R-9004", certificate_type=None)
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    dist = resp.json()["certificate_distribution"]
    by_cert = {d["certificate_type"]: d["count"] for d in dist}
    assert set(by_cert.keys()) == {"scientific", "literary"}
    assert by_cert["scientific"] == 2
    assert by_cert["literary"] == 1


def test_dashboard_analytics_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/analytics", headers=students_admin_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"