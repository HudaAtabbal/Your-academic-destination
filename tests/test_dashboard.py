"""اختبارات لوحة المدير العام (dashboard) — super_admin فقط."""

from datetime import timedelta

from app import time_utils
from app.models import (
    ActivityType,
    CertificateType,
    Checkin,
    College,
    Faculty,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)


def _phone(suffix: int) -> str:
    """رقم تواصل وهمي صالح للنمط 09XXXXXXXX — مبني بالأجزاء (بدل رقم صريح)."""
    return f"09{suffix:08d}"

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
    # لا يوجد مسحات لركن الترفيه/الاتحاد في هذا السيناريو — الحقلان يظهران دائماً
    assert body["game_scans_total"] == 0
    assert body["union_scans_total"] == 0


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


def test_hall_students_list(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """قائمة الطلاب داخل قاعة محاضرة — كل دخول شيك-إن لليوم، بالترتيب الزمني."""
    student_factory("R-9001", full_name="أحمد الأول")
    student_factory("R-9002", full_name="سمير الثاني")
    assert _campus_entry(client, students_admin_headers, "R-9001").status_code == 201
    assert _lecture(client, gate_scanner_headers, "R-9001").status_code == 201
    assert _campus_entry(client, students_admin_headers, "R-9002").status_code == 201
    assert _lecture(client, gate_scanner_headers, "R-9002").status_code == 201

    resp = client.get("/admin/dashboard/rooms-occupancy/lecture_1", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["lecture_name"] == L1
    assert body["hall_label"] == "المدرج الرئيسي"
    assert body["current_count"] == 2
    assert len(body["students"]) == 2
    codes = [s["unique_code"] for s in body["students"]]
    assert codes == ["R-9001", "R-9002"]
    assert body["students"][0]["full_name"] == "أحمد الأول"
    assert all("checkin_id" in s and "checked_in_at" in s for s in body["students"])


def test_hall_students_empty(client, super_headers):
    """قاعة بلا حضور — قائمة فارغة والعدّاد صفر (بدون 404)."""
    resp = client.get("/admin/dashboard/rooms-occupancy/lecture_5", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["current_count"] == 0
    assert resp.json()["students"] == []


def test_hall_invalid_lecture_422(client, super_headers):
    resp = client.get("/admin/dashboard/rooms-occupancy/not_a_lecture", headers=super_headers)
    assert resp.status_code == 422


def test_clear_hall_occupancy(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """إفراغ قاعة درس: يمسح كل دخول المحاضرة لليوم من غير ما يمنع (وليس مقيداً بأي سعة)."""
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert _lecture(client, gate_scanner_headers, code).status_code == 201
    # محاضرة أخرى ما بتنمسح
    assert _lecture(client, gate_scanner_headers, "R-9001", "lecture_2").status_code == 201

    resp = client.delete("/admin/dashboard/rooms-occupancy/lecture_1", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_count"] == 2

    # القاعة صارت فاضية (بتختفي من الإشغال)، ومحاضرة_2 نضلت
    occ = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers).json()["rooms"]
    assert [(r["lecture_name"], r["current_count"]) for r in occ] == [("lecture_2", 1)]
    # والتأكيد المباشر: قائمة الطلاب مساوية للصفرة
    cleared = client.get(
        "/admin/dashboard/rooms-occupancy/lecture_1", headers=super_headers
    ).json()
    assert cleared["current_count"] == 0
    assert cleared["students"] == []


def test_delete_single_checkin(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """حذف دخول طالب واحد من القاعة — الحذف ينجح حتى لو القاعة (نظرياً) عندها سعة مقلصة."""
    student_factory("R-9001")
    assert _campus_entry(client, students_admin_headers, "R-9001").status_code == 201
    assert _lecture(client, gate_scanner_headers, "R-9001").status_code == 201

    students = client.get(
        "/admin/dashboard/rooms-occupancy/lecture_1", headers=super_headers
    ).json()["students"]
    assert len(students) == 1
    checkin_id = students[0]["checkin_id"]

    resp = client.delete(f"/admin/dashboard/checkins/{checkin_id}", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json() == {"checkin_id": checkin_id, "deleted": True}

    # القاعة صارت فاضية بعد الحذف
    body = client.get(
        "/admin/dashboard/rooms-occupancy/lecture_1", headers=super_headers
    ).json()
    assert body["current_count"] == 0
    assert body["students"] == []


def test_delete_unknown_checkin_404(client, super_headers):
    resp = client.delete("/admin/dashboard/checkins/99999", headers=super_headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "checkin_not_found"


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
    create_custom_staff,
    super_headers,
):
    """زيارة الكلية (ركن التوجيه) = شيكيات جولات الكلية المنفذة؛ تُعرض كل
    الكليات إلا الموسيقا (بالاتحاد) والطب البشري والصيدلة (دُمجتا بالمجمع الطبي)."""
    create_custom_staff("dent_staff2", "staff123", Faculty.dentistry)
    headers = {
        "Authorization": f"Bearer {client.post('/auth/login', json={'username':'dent_staff2','password':'staff123'}).json()['access_token']}"
    }
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert _tour_booking(client, headers, code).status_code == 201
        assert _tour_checkin(client, headers, code).status_code == 201
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    visits = resp.json()["college_visits"]
    # الموسيقا بالاتحاد، والطب البشري والصيدلة دُمجتا بالمجمع الطبي
    assert len(visits) == len(Faculty) - 3
    # زيارات طب الأسنان (المجمع الطبي) = زيارتان بعد الدمج
    by_college = {v["college"]: v["count"] for v in visits}
    assert by_college["dentistry"] == 2
    # الطب البشري والصيدلة ما عادا صفّين مستقلين بالجدول
    assert "medicine" not in by_college
    assert "pharmacy" not in by_college
    assert "music" not in by_college
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
    """حضور كل محاضرة: كل محاضرات الـ16 + الافتتاح مدرجة بترتيب enum مع تسميات
    عربية، والمحاضرات بلا حضور بصفر. بإستثناء ندوات الهندسة الثلاث فهيدي
    بيندمجن بصف واحد (الهمك والبتروكيميا) وبأرقامهن مجمّعة."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers, STUDENT).status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, "lecture_1").status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, "lecture_2").status_code == 201
    # ندوة الهندسة الموحّدة: مسح تحت أي من الثلاثة بينحسب بنفس الصف
    assert _lecture(client, gate_scanner_headers, STUDENT, "lecture_12").status_code == 201
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    rows = resp.json()["lecture_attendance"]
    # 17 - 2 (عضوان من مجموعة الدمج) = 15 صف
    assert len(rows) == 15
    # الترتيب مطابق لترتيب enum: opening ثم lecture_1 ثم lecture_2 ثم …
    assert rows[0]["lecture_name"] == "opening"
    assert rows[0]["count"] == 0
    assert [r["lecture_name"] for r in rows[1:3]] == ["lecture_1", "lecture_2"]
    assert rows[1]["count"] == 1
    assert rows[2]["count"] == 1
    # ندوة الهندسة الموحّدة موجودة باسمها المدمج وبمجموع أرقام الثلاث
    engineering = next(r for r in rows if r["lecture_name"] == "lecture_11")
    assert engineering["count"] == 1
    assert "الهمك والبتروكيميا" in engineering["label"]
    assert "lecture_12" not in [r["lecture_name"] for r in rows]
    assert "lecture_13" not in [r["lecture_name"] for r in rows]
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
    """توزيع سنة الشهادة: متراكبة تصاعدياً، الفارغة متجاهلة، وأي سنة بعد 2026 تُحسب ضمن 2026."""
    _make_student_with_bacc(db, "R-9001", bacc_year=2023)
    _make_student_with_bacc(db, "R-9002", bacc_year=2024)
    _make_student_with_bacc(db, "R-9003", bacc_year=2024)
    _make_student_with_bacc(db, "R-9004", bacc_year=None)
    _make_student_with_bacc(db, "R-9005", bacc_year=2025)
    _make_student_with_bacc(db, "R-9006", bacc_year=2026)
    _make_student_with_bacc(db, "R-9007", bacc_year=2030)  # سنة مستقبلية
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    dist = resp.json()["year_distribution"]
    assert [list(d.values()) for d in dist] == [[2023, 1], [2024, 2], [2025, 1], [2026, 2]]


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


def test_dashboard_analytics_union_sections(
    client, student_factory, students_admin_headers, union_headers, super_headers
):
    """مسحات ركن الاتحاد حسب القسم: الأقسام الثلاثة مدرجة دائماً بترتيب enum
    مع تسميات عربية، والمسح يُحتسب على قسمه فقط (الركن المركزي 2 / الباقي صفر)."""
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert (
            client.post(
                "/checkins/union",
                json={"unique_code": code, "union_section": "central"},
                headers=union_headers,
            ).status_code
            == 201
        )
    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    rows = resp.json()["union_sections"]
    assert len(rows) == 3
    by_section = {r["section"]: r for r in rows}
    assert by_section["central"]["count"] == 2
    assert by_section["major_guide"]["count"] == 0
    assert by_section["turkish_club"]["count"] == 0
    assert all(r["label"] for r in rows)


def test_dashboard_analytics_music_merges_to_union_central(
    client,
    student_factory,
    students_admin_headers,
    create_custom_staff,
    super_headers,
):
    """زيارات كلية الموسيقا تُدمج ضمن الركن المركزي في اتحاد."""
    staff = create_custom_staff("music_staff", "staff123", Faculty.music)
    headers = {"Authorization": f"Bearer {client.post('/auth/login', json={'username':'music_staff','password':'staff123'}).json()['access_token']}"}
    student_factory("R-8001")
    assert _campus_entry(client, students_admin_headers, "R-8001").status_code == 201
    assert client.post("/bookings/tour", json={"unique_code": "R-8001"}, headers=headers).status_code == 201
    assert client.post("/checkins/tour", json={"unique_code": "R-8001"}, headers=headers).status_code == 201

    resp = client.get("/admin/dashboard/analytics", headers=super_headers)
    assert resp.status_code == 200
    visits = resp.json()["college_visits"]
    by_college = {v["college"]: v["count"] for v in visits}
    assert "music" not in by_college
    union = resp.json()["union_sections"]
    by_section = {u["section"]: u for u in union}
    assert by_section["central"]["count"] == 1
    assert by_section["major_guide"]["count"] == 0
    assert by_section["turkish_club"]["count"] == 0


def test_dashboard_analytics_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/analytics", headers=students_admin_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_survey_completions_list_details(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """'أكملوا الاستبيان': كل شخص مع الاسم، الرقم، وقت الدخول، الكليات المختارة، وإجابات الاستبيان."""
    student_factory(
        "R-9001",
        full_name="أحمد الأول",
        contact_id=_phone(1),
        initial_preferred_major=[College.medicine, College.law],
    )
    student_factory("R-9002", full_name="سمير الثاني", contact_id=_phone(2))
    assert _campus_entry(client, students_admin_headers, "R-9001").status_code == 201
    assert _lecture(client, gate_scanner_headers, "R-9001").status_code == 201
    assert (
        client.post(
            "/survey/R-9001",
            json={"opinion_change": "decided", "preferred_major": "law"},
        ).status_code
        == 201
    )

    resp = client.get("/admin/dashboard/survey-completions", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["unique_code"] == "R-9001"
    assert item["full_name"] == "أحمد الأول"
    assert item["contact_id"] == _phone(1)
    assert item["registration_type"] == "registered"
    assert item["first_campus_entry_at"] is not None
    # الكليات اللي اختارها وقت التسجيل (initial_preferred_major) + إجابة الاستبيان
    assert item["chosen_colleges"] == ["medicine", "law"]
    assert item["survey_college"] == "law"
    assert item["opinion_change"] == "decided"
    assert item["answered_at"] is not None


def test_survey_completions_walkin_no_prior_choice(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """walk-in عبّى الاستبيان — registration_type=walk_in وبدون اختيار مسبق."""
    student_factory(
        "W-0001",
        full_name="وائل ووك إن",
        registration_type="walk_in",
        verification_status="verified",
        status="complete",
    )
    assert _campus_entry(client, students_admin_headers, "W-0001").status_code == 201
    assert _lecture(client, gate_scanner_headers, "W-0001").status_code == 201
    assert (
        client.post(
            "/survey/W-0001",
            json={"opinion_change": "still_confused", "preferred_major": "sharia"},
        ).status_code
        == 201
    )

    resp = client.get("/admin/dashboard/survey-completions", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["unique_code"] == "W-0001"
    assert item["registration_type"] == "walk_in"
    # ما عندو اختيار مسبق — initial_preferred_major فارغ
    assert item["chosen_colleges"] == []
    assert item["survey_college"] == "sharia"
    assert item["opinion_change"] == "still_confused"


def test_survey_completions_search(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    """بحث جزئي بالاسم/الرمز يفلتر قائمة أكملوا الاستبيان."""
    for code, name in (("R-9001", "أحمد الأول"), ("R-9002", "فاطمة الثانية")):
        student_factory(code, full_name=name)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert _lecture(client, gate_scanner_headers, code).status_code == 201
        assert (
            client.post(
                f"/survey/{code}",
                json={"opinion_change": "confirmed_choice", "preferred_major": "medicine"},
            ).status_code
            == 201
        )
    resp = client.get(
        "/admin/dashboard/survey-completions?code=فاطمة", headers=super_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["unique_code"] == "R-9002"
    # بدون بحث — الاثنان ظاهرين
    resp = client.get("/admin/dashboard/survey-completions", headers=super_headers)
    assert resp.json()["total"] == 2


def test_survey_completions_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/survey-completions", headers=students_admin_headers)
    assert resp.status_code == 403


def test_registered_no_show_stat_and_list(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    super_headers,
):
    """'مسجّلون بلا حضور': مسجّل أونلاين موثّق بدون أي دخول بوابة أو زيارة كلية يُعدّ
    بالعدّاد والقائمة — بينما من حضر من البوابة أو زار كلية ما يظهر أبداً."""
    # لا حضور إطلاقاً — لازم يظهر
    student_factory("R-9001", full_name="لا حضور", contact_id=_phone(3))
    # حضر من البوابة + جولة كلية — ما يظهر (حضور فعلي)
    student_factory("R-9002", full_name="حضر بوابة", contact_id=_phone(4))
    assert _campus_entry(client, students_admin_headers, "R-9002").status_code == 201
    assert _tour_booking(client, college_staff_headers, "R-9002").status_code == 201
    assert _tour_checkin(client, college_staff_headers, "R-9002").status_code == 201
    # دخل البوابة بدون كلية — ما يظهر (حضر من البوابة)
    student_factory("R-9003", full_name="دخل بوابة بس", contact_id=_phone(5))
    assert _campus_entry(client, students_admin_headers, "R-9003").status_code == 201
    # مسجّل أونلاين لسا موثّق (pending) — خارج النطاق (مش "موثّق")
    student_factory("R-9004", verification_status=VerificationStatus.pending)
    # walk-in — خارج النطاق (مش مسجّل أونلاين)
    student_factory(
        "W-0001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )

    stats = client.get("/admin/dashboard/stats", headers=super_headers).json()
    # R-9001..3 موثّقون => 3 (R-9004 pending وW-0001 walk-in خارج العدّاد)
    assert stats["registered_online_count"] == 3
    assert stats["registered_no_show_count"] == 1  # R-9001 فقط

    resp = client.get("/admin/dashboard/registered-no-shows", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["unique_code"] == "R-9001"
    assert item["full_name"] == "لا حضور"
    assert item["contact_id"] == _phone(3)
    assert item["created_at"] is not None


def test_registered_no_shows_search(client, student_factory, super_headers):
    """بحث جزئي بالاسم/الرمز بيفلتر قائمة مسجّلين بلا حضور."""
    student_factory("R-9001", full_name="أحمد لا حضور")
    student_factory("R-9002", full_name="سمير لا حضور")
    resp = client.get(
        "/admin/dashboard/registered-no-shows?code=R-90", headers=super_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 2
    resp = client.get(
        "/admin/dashboard/registered-no-shows?code=أحمد", headers=super_headers
    )
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["unique_code"] == "R-9001"


def test_registered_no_shows_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/registered-no-shows", headers=students_admin_headers)
    assert resp.status_code == 403


def test_students_inside_all_days_unique_across_days(
    db, client, student_factory, students_admin_headers, super_headers
):
    """'إجمالي الطلاب داخل الجامعة (كل الأيام)' — الطالب يعدّ مرة وحدة حتى لو
    دخل من البوابة بأكثر من يوم (distinct على مستوى الطالب)."""
    student = student_factory("R-9001", full_name="أحمد")
    student_factory("R-9002", full_name="سمير")

    assert _campus_entry(client, students_admin_headers, "R-9001").status_code == 201
    # دخول ثاني بيوم سابق — مسموح (f أindex فريد لكل يوم) — نفس الطالب
    past_entry = time_utils.now_naive() - timedelta(days=1)
    db.add(
        Checkin(
            student_id=student.id,
            activity_type=ActivityType.campus_entry,
            checked_in_at=past_entry,
        )
    )
    db.commit()

    stats = client.get("/admin/dashboard/stats", headers=super_headers).json()
    # دخولان لـ R-9001 بيومين مختلفين لكن العدّاد يعدّه مرة واحدة
    assert stats["students_inside_all_days"] == 1

    lst = client.get("/admin/dashboard/students-inside", headers=super_headers).json()
    assert lst["total"] == 1
    assert [item["unique_code"] for item in lst["items"]] == ["R-9001"]