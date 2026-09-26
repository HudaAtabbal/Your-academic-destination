"""اختبارات تسجيل الحضور (check-ins) — الأنواع الأربعة + العدادات."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

import main as main_module
from app import time_utils
from app.models import ActivityType, Booking, BookingType, Checkin, College, Faculty, Lecture, Student, UnionSection

STUDENT = "R-9001"
L1 = "lecture_1"
L2 = "lecture_2"

# أسماء أيام الأسبوع بالعربي — نسخة مستقلة عن خريطة التطبيق، عشان الاختبار
# يتحقق من اسم اليوم الحقيقي مش من نفس المصدر يلي بيفحصه.
_WEEKDAY_AR = ("الاثنين", "الثلاثاء", "أربعاء", "خميس", "جمعة", "سبت", "أحد")


def _campus_entry(client, headers, code=STUDENT):
    return client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=headers
    )


def _tour_booking(client, headers, code=STUDENT):
    return client.post("/bookings/tour", json={"unique_code": code}, headers=headers)


def _consultation_booking(client, headers, code=STUDENT):
    return client.post(
        "/bookings/consultation", json={"unique_code": code}, headers=headers
    )


# ---------- campus-entry (students_admin) ----------


def test_campus_entry_happy(client, student_factory, students_admin_headers):
    student_factory(STUDENT)
    resp = _campus_entry(client, students_admin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["student_name"] == "طالب تجريبي"
    assert body["college"] is None
    assert body["lecture_name"] is None
    assert "checked_in_at" in body


def test_campus_entry_duplicate_409(client, student_factory, students_admin_headers):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = _campus_entry(client, students_admin_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


def test_campus_entry_unknown_code_404(client, students_admin_headers):
    resp = _campus_entry(client, students_admin_headers, code="R-9999")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


def test_campus_entry_forbidden_for_gate_scanner(
    client, student_factory, gate_scanner_headers
):
    student_factory(STUDENT)
    resp = _campus_entry(client, gate_scanner_headers)
    assert resp.status_code == 403


def test_campus_entry_unauthenticated_401(client, student_factory):
    student_factory(STUDENT)
    resp = _campus_entry(client, {})
    assert resp.status_code == 401


# ---------- lecture (gate_scanner) ----------


def test_lecture_without_campus_entry_409(client, student_factory, gate_scanner_headers):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L1},
        headers=gate_scanner_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_lecture_happy(client, student_factory, students_admin_headers, gate_scanner_headers):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L1},
        headers=gate_scanner_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["lecture_name"] == L1


def test_lecture_same_lecture_duplicate_409(
    client, student_factory, students_admin_headers, gate_scanner_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    payload = {"unique_code": STUDENT, "lecture_name": L1}
    assert (
        client.post("/checkins/lecture", json=payload, headers=gate_scanner_headers).status_code
        == 201
    )
    resp = client.post("/checkins/lecture", json=payload, headers=gate_scanner_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


def test_lecture_different_lecture_ok(
    client, student_factory, students_admin_headers, gate_scanner_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert (
        client.post(
            "/checkins/lecture", json={"unique_code": STUDENT, "lecture_name": L1}, headers=gate_scanner_headers
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/checkins/lecture", json={"unique_code": STUDENT, "lecture_name": L2}, headers=gate_scanner_headers
        ).status_code
        == 201
    )


def test_lecture_forbidden_for_students_admin(client, student_factory, students_admin_headers):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L1},
        headers=students_admin_headers,
    )
    assert resp.status_code == 403


def test_opening_lecture_happy(client, student_factory, students_admin_headers, gate_scanner_headers):
    """محاضرة الافتتاح (opening) تعمل مثل أي محاضرة عادية."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": "opening"},
        headers=gate_scanner_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["lecture_name"] == "opening"


def test_opening_lecture_duplicate_409(
    client, student_factory, students_admin_headers, gate_scanner_headers
):
    """محاضرة الافتتاح محسوبة ضمن المحاضرات — التكرار له محظور."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    payload = {"unique_code": STUDENT, "lecture_name": "opening"}
    assert (
        client.post("/checkins/lecture", json=payload, headers=gate_scanner_headers).status_code
        == 201
    )
    resp = client.post("/checkins/lecture", json=payload, headers=gate_scanner_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


# ---------- tour (college_staff) ----------


def test_tour_without_campus_entry_409(client, student_factory, college_staff_headers):
    student_factory(STUDENT)
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_tour_without_booking_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_booking"


def test_tour_happy(client, student_factory, students_admin_headers, college_staff_headers):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 201
    assert resp.json()["college"] == "medicine"


def test_tour_duplicate_same_college_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


def test_tour_duplicate_today_message_has_time_only(
    client, student_factory, students_admin_headers, college_staff_headers
):
    """
    أول مسحة اليوم = نفس اليوم، فالرسالة بتذكر الوقت بس بدون اسم اليوم.
    واسم الكلية بالعربي مش الرمز التقني.
    """
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    message = resp.json()["message"]
    assert "جولة كلية (كلية الطب البشري)" in message
    assert "medicine" not in message
    assert "الساعة" in message
    assert " يوم " not in message


def test_tour_same_college_different_day_201(
    client, db, student_factory, students_admin_headers, college_staff_headers
):
    """
    نفس الكلية بيومين مختلفين = 201 بالمرة الثانية —     القاعدة "مرة لكل كلية
    باليوم" مش "مرة لكل كلية بطول الفعالية". حجز ومسحة الأمبارح بينكتبوا
    مباشرة بالـ DB، واليوم الحالي الطالب بيدخل من البوابة وبيحجز وبيضح.
    """
    student = student_factory(STUDENT)
    yesterday = time_utils.today_start() - timedelta(hours=1)
    db.add(
        Booking(
            student_id=student.id,
            booking_type=BookingType.tour,
            college=Faculty.medicine,
            booked_at=yesterday,
        )
    )
    db.add(
        Checkin(
            student_id=student.id,
            activity_type=ActivityType.tour,
            college=Faculty.medicine,
            checked_in_at=yesterday,
        )
    )
    db.commit()

    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )


def test_tour_checkin_today_with_yesterday_booking_only_409(
    client, db, student_factory, students_admin_headers, college_staff_headers
):
    """
    حجز الأمبارح لنفس الكلية ما بيبرر مسحة اليوم — الحجز لازم يكون من اليوم
    نفسه، وإلا 409 missing_booking.
    """
    student = student_factory(STUDENT)
    db.add(
        Booking(
            student_id=student.id,
            booking_type=BookingType.tour,
            college=Faculty.medicine,
            booked_at=time_utils.today_start() - timedelta(hours=1),
        )
    )
    db.commit()

    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_booking"


def test_consultation_duplicate_other_day_message_mentions_weekday(
    client, db, student_factory, students_admin_headers, college_staff_headers
):
    """
    نشاط "مرة وحدة طول الفعالية" (الاستشارة) أول مسحة له كانت بيوم تاني،
    فالرسالة بتذكر اسم اليوم العربي (أربعاء/خميس/سبت...) مع الوقت — مش وقت
    لحاله. تكرار الجولة ما بيقدر يجرب هالشي لأن تكرارها صار يومي.
    """
    student = student_factory(STUDENT)
    yesterday = time_utils.today_start() - timedelta(hours=2)
    db.add(
        Booking(
            student_id=student.id,
            booking_type=BookingType.consultation,
            college=Faculty.medicine,
            booked_at=yesterday,
        )
    )
    db.add(
        Checkin(
            student_id=student.id,
            activity_type=ActivityType.consultation,
            college=Faculty.medicine,
            checked_in_at=yesterday,
        )
    )
    db.commit()

    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/checkins/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"
    message = resp.json()["message"]
    weekday = _WEEKDAY_AR[yesterday.weekday()]
    assert f"مسبقاً يوم {weekday} الساعة {yesterday.strftime('%H:%M')}" in message


def test_tour_duplicate_other_day_is_allowed_again(
    client, db, student_factory, students_admin_headers, college_staff_headers
):
    """
    مسحة الأمبارح لنفس الكلية ما بتولّد رسالة تكرار اليوم — الطالب بيرجع
    اليوم وبيمسح عادي (201)، وبيتأكد إن الرسالة ما بتذكر يوماً تاني.
    """
    student = student_factory(STUDENT)
    yesterday = time_utils.today_start() - timedelta(hours=2)
    db.add(
        Checkin(
            student_id=student.id,
            activity_type=ActivityType.tour,
            college=Faculty.medicine,
            checked_in_at=yesterday,
        )
    )
    db.commit()

    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )


def test_tour_staff_without_college_400(
    client, student_factory, students_admin_headers, create_custom_staff, auth_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    create_custom_staff("no_college_staff", "pw123", None)
    headers = auth_headers("no_college_staff", "pw123")
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "validation_error"


def test_tour_booking_other_college_does_not_satisfy(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    create_custom_staff,
    auth_headers,
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    create_custom_staff("staff2", "pw456", Faculty.dentistry)
    headers = auth_headers("staff2", "pw456")
    resp = client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_booking"


# ---------- consultation (college_staff) ----------


def test_consultation_without_booking_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/checkins/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_booking"


def test_consultation_happy(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _consultation_booking(client, college_staff_headers).status_code == 201
    resp = client.post(
        "/checkins/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 201


def test_consultation_duplicate_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _consultation_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post(
            "/checkins/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
        ).status_code
        == 201
    )
    resp = client.post(
        "/checkins/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


# ---------- game (game_corner_manager) ----------


def _make_eligible_for_game(
    client,
    students_admin_headers,
    college_staff_headers,
    gate_scanner_headers,
    create_custom_staff,
    auth_headers,
):
    """يهيّئ طالباً مؤهلاً لركن الترفيه: دخول بوابة + جولتان (كليتان مختلفتان) + محاضرة."""
    assert _campus_entry(client, students_admin_headers).status_code == 201

    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post(
            "/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers
        ).status_code
        == 201
    )

    create_custom_staff("dent_staff2", "pw456", Faculty.dentistry)
    dent_headers = auth_headers("dent_staff2", "pw456")
    assert _tour_booking(client, dent_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=dent_headers).status_code
        == 201
    )

    assert (
        client.post(
            "/checkins/lecture",
            json={"unique_code": STUDENT, "lecture_name": L1},
            headers=gate_scanner_headers,
        ).status_code
        == 201
    )


def test_game_happy(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    gate_scanner_headers,
    create_custom_staff,
    auth_headers,
    game_corner_headers,
):
    student_factory(STUDENT)
    _make_eligible_for_game(
        client,
        students_admin_headers,
        college_staff_headers,
        gate_scanner_headers,
        create_custom_staff,
        auth_headers,
    )
    resp = client.post("/checkins/game", json={"unique_code": STUDENT}, headers=game_corner_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["student_name"] == "طالب تجريبي"
    assert body["college"] is None
    assert body["lecture_name"] is None
    assert "checked_in_at" in body

    # ركن الترفيه بتاعي 0 نقاط: 5 بوابة + 10 + 10 جولتين + 10 محاضرة = 35
    pts = client.get(f"/students/{STUDENT}/points")
    assert pts.json()["total_points"] == 35


def test_game_without_prerequisites_409(
    client, student_factory, students_admin_headers, game_corner_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post("/checkins/game", json={"unique_code": STUDENT}, headers=game_corner_headers)
    assert resp.status_code == 409
    body = resp.json()
    assert body["error_code"] == "game_requirements_not_met"
    assert body["details"]["tour_count"] == 0
    assert body["details"]["lecture_count"] == 0


def test_game_without_campus_entry_409(client, db, student_factory, game_corner_headers):
    """جولتان ومحاضرة مسجّلين بس ما فات من البوابة اليوم → 409 missing_campus_entry."""
    student_factory(STUDENT)
    sid = db.query(Student).filter(Student.unique_code == STUDENT).first().id
    now = datetime.now()
    for college in (Faculty.medicine, Faculty.dentistry):
        db.add(
            Checkin(
                student_id=sid,
                activity_type=ActivityType.tour,
                college=college,
                checked_in_at=now,
            )
        )
    db.add(
        Checkin(
            student_id=sid,
            activity_type=ActivityType.lecture,
            lecture_name=Lecture.lecture_1,
            checked_in_at=now,
        )
    )
    db.commit()

    resp = client.post("/checkins/game", json={"unique_code": STUDENT}, headers=game_corner_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_game_duplicate_409(
    client,
    student_factory,
    students_admin_headers,
    college_staff_headers,
    gate_scanner_headers,
    create_custom_staff,
    auth_headers,
    game_corner_headers,
):
    student_factory(STUDENT)
    _make_eligible_for_game(
        client,
        students_admin_headers,
        college_staff_headers,
        gate_scanner_headers,
        create_custom_staff,
        auth_headers,
    )
    payload = {"unique_code": STUDENT}
    assert (
        client.post("/checkins/game", json=payload, headers=game_corner_headers).status_code == 201
    )
    resp = client.post("/checkins/game", json=payload, headers=game_corner_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"


def test_game_forbidden_for_other_roles(client, student_factory, students_admin_headers):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/game", json={"unique_code": STUDENT}, headers=students_admin_headers
    )
    assert resp.status_code == 403


def test_game_unauthenticated_401(client, student_factory):
    student_factory(STUDENT)
    resp = client.post("/checkins/game", json={"unique_code": STUDENT}, headers={})
    assert resp.status_code == 401


# ---------- union (مسؤول الاتحاد) ----------
# شروط المسح عند الاتحاد: يكفي دخول الحرم بنفس اليوم (بدون حجز/جولات) — بدون نقاط.
# قاعدة التكرار: مرة وحدة لكل قسم (union_section) وبنفس اليوم — الطالب فيه يزور
# الأقسام الثلاثة (3 سجلات منفصلة) بنفس اليوم، وبإمكانه يرجع لنفس القسم بيوم تاني.


def test_union_happy(client, student_factory, students_admin_headers, union_headers):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/checkins/union",
        json={"unique_code": STUDENT, "union_section": "central"},
        headers=union_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["student_name"] == "طالب تجريبي"
    assert body["college"] is None
    assert body["lecture_name"] is None
    assert body["union_section"] == "central"
    assert "checked_in_at" in body

    # الاتحاد بدون نقاط: 5 بوابة فقط
    pts = client.get(f"/students/{STUDENT}/points")
    assert pts.json()["total_points"] == 5


def test_union_all_sections_same_student(
    client, student_factory, students_admin_headers, union_headers
):
    """نفس الطالب يزور الأقسام الثلاثة — 3 سجلات checkins منفصلة مسموحة."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    for section in ("central", "major_guide", "turkish_club"):
        resp = client.post(
            "/checkins/union",
            json={"unique_code": STUDENT, "union_section": section},
            headers=union_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["union_section"] == section


def test_union_without_campus_entry_409(client, student_factory, union_headers):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/union",
        json={"unique_code": STUDENT, "union_section": "central"},
        headers=union_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_union_duplicate_same_section_409(
    client, student_factory, students_admin_headers, union_headers
):
    """نفس القسم مرتين بنفس اليوم = 409 — القاعدة "مرة لكل قسم باليوم"."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    payload = {"unique_code": STUDENT, "union_section": "central"}
    assert client.post("/checkins/union", json=payload, headers=union_headers).status_code == 201
    resp = client.post("/checkins/union", json=payload, headers=union_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_checkin"
    assert "الركن المركزي" in resp.json()["message"]


def test_union_same_section_different_day_201(
    client, db, student_factory, students_admin_headers, union_headers
):
    """
    نفس القسم بيومين مختلفين = 201 بالمرة الثانية — القاعدة "مرة لكل قسم باليوم"
    مش "مرة لكل القسم بطول الفعالية". مسحة الأمبارح بتنكتب مباشرة بالـ DB، واليوم
    الحالي الطالب بيدخل من البوابة وبيمسح.
    """
    student = student_factory(STUDENT)
    db.add(
        Checkin(
            student_id=student.id,
            activity_type=ActivityType.union,
            union_section=UnionSection.central,
            checked_in_at=time_utils.today_start() - timedelta(hours=1),
        )
    )
    db.commit()

    assert _campus_entry(client, students_admin_headers).status_code == 201
    payload = {"unique_code": STUDENT, "union_section": "central"}
    assert client.post("/checkins/union", json=payload, headers=union_headers).status_code == 201


def test_union_forbidden_for_other_roles(client, student_factory, students_admin_headers):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/union",
        json={"unique_code": STUDENT, "union_section": "central"},
        headers=students_admin_headers,
    )
    assert resp.status_code == 403


def test_union_unauthenticated_401(client, student_factory):
    student_factory(STUDENT)
    resp = client.post(
        "/checkins/union",
        json={"unique_code": STUDENT, "union_section": "central"},
        headers={},
    )
    assert resp.status_code == 401


def test_union_missing_section_422(client, student_factory, union_headers):
    """union_section حقل إلزامي — بدونو الطلب مرفوض (FastAPI 422 موحّد)."""
    student_factory(STUDENT)
    resp = client.post("/checkins/union", json={"unique_code": STUDENT}, headers=union_headers)
    assert resp.status_code == 422


# ---------- counts ----------


def test_count_campus_entry_today(
    client, student_factory, students_admin_headers, gate_scanner_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.get(
        "/checkins/count/today",
        params={"activity_type": "campus_entry"},
        headers=gate_scanner_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


def test_count_tour_filtered_by_college(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert (
        client.post("/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )
    r1 = client.get(
        "/checkins/count/today",
        params={"activity_type": "tour", "college": "medicine"},
        headers=college_staff_headers,
    )
    assert r1.json()["count"] == 1
    r2 = client.get(
        "/checkins/count/today",
        params={"activity_type": "tour", "college": "dentistry"},
        headers=college_staff_headers,
    )
    assert r2.json()["count"] == 0


def test_count_lecture_filtered(
    client, student_factory, students_admin_headers, gate_scanner_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    for lecture in (L1, L2):
        assert (
            client.post(
                "/checkins/lecture",
                json={"unique_code": STUDENT, "lecture_name": lecture},
                headers=gate_scanner_headers,
            ).status_code
            == 201
        )
    r1 = client.get(
        "/checkins/count/today",
        params={"activity_type": "lecture", "lecture_name": L1},
        headers=gate_scanner_headers,
    )
    assert r1.json()["count"] == 1


def test_count_union_filtered_by_section(
    client, student_factory, students_admin_headers, union_headers
):
    """عداد ركن الاتحاد لليوم ينفلتر حسب القسم — العد الكلي 2 والفرز حسب القسم 1 / 0."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    for section in ("central", "major_guide"):
        assert (
            client.post(
                "/checkins/union",
                json={"unique_code": STUDENT, "union_section": section},
                headers=union_headers,
            ).status_code
            == 201
        )
    total = client.get(
        "/checkins/count/today",
        params={"activity_type": "union"},
        headers=union_headers,
    )
    assert total.json()["count"] == 2
    r1 = client.get(
        "/checkins/count/today",
        params={"activity_type": "union", "union_section": "central"},
        headers=union_headers,
    )
    assert r1.json()["count"] == 1
    r2 = client.get(
        "/checkins/count/today",
        params={"activity_type": "union", "union_section": "turkish_club"},
        headers=union_headers,
    )
    assert r2.json()["count"] == 0


def test_count_invalid_activity_type_422(client, gate_scanner_headers):
    resp = client.get(
        "/checkins/count/today",
        params={"activity_type": "bogus"},
        headers=gate_scanner_headers,
    )
    assert resp.status_code == 422


def test_count_invalid_college_422_after_fix(client, super_headers):
    """محدّث بعد إصلاح A5: college قيمة غير صالحة = 422 validation بدل 500"""
    with TestClient(main_module.app, raise_server_exceptions=False) as c:
        resp = c.get(
            "/checkins/count/today",
            params={"activity_type": "campus_entry", "college": "bogus"},
            headers=super_headers,
        )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


# ---------- tour+consultation coexisting ----------


def test_tour_and_consultation_coexist(
    client, student_factory, students_admin_headers, college_staff_headers
):
    """جولة + استشارة لنفس الطالب كليهما ينجح (10 + 15 = 25 نقطة)."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert _tour_booking(client, college_staff_headers).status_code == 201
    assert _consultation_booking(client, college_staff_headers).status_code == 201

    tour_resp = client.post(
        "/checkins/tour", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert tour_resp.status_code == 201

    cons_resp = client.post(
        "/checkins/consultation",
        json={"unique_code": STUDENT},
        headers=college_staff_headers,
    )
    assert cons_resp.status_code == 201

    pts = client.get(f"/students/{STUDENT}/points")
    assert pts.json()["total_points"] == 30


# ---------- cross-college tours ----------


def test_cross_college_tours_different_staff(
    client, student_factory, students_admin_headers,
    create_custom_staff, auth_headers,
):
    """طالب يحجز جولة في كلية مختلفة — الكوليج يُحدّد حسب من يسجّل لا حسب الحجز."""
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201

    create_custom_staff("dent_staff", "pw456", Faculty.dentistry)
    dent_headers = auth_headers("dent_staff", "pw456")

    # حجز جولة بـ dentistry staff → college = dentistry
    tour_book = client.post(
        "/bookings/tour", json={"unique_code": STUDENT}, headers=dent_headers
    )
    assert tour_book.status_code == 201

    tour_check = client.post(
        "/checkins/tour", json={"unique_code": STUDENT}, headers=dent_headers
    )
    assert tour_check.status_code == 201
    assert tour_check.json()["college"] == "dentistry"

    pts = client.get(f"/students/{STUDENT}/points")
    assert pts.json()["total_points"] == 15


# ---------- walkin pending (status=pending, verification=verified) ----------


def test_walkin_pending_campus_entry(
    client, student_factory, students_admin_headers, super_headers
):
    """طالب walk-in بحالة pending (ما عبيتو معلومات) — campus-entry ينجح."""
    student_factory("W-7777")
    resp = _campus_entry(client, students_admin_headers, code="W-7777")
    assert resp.status_code == 201
    body = resp.json()
    assert body["student_name"] == "طالب تجريبي"