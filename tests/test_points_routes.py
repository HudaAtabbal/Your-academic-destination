"""اختبارات نقاطي + لوحة الترتيب — endpoints عامة + super_admin."""

from datetime import datetime, timedelta

from app.models import ActivityType, Checkin, Faculty, Lecture, Student
from app.routers.points import point_service

CODE_A = "R-9001"
CODE_B = "R-9002"


def _get_points(client, code):
    return client.get(f"/students/{code}/points")


def _get_leaderboard(client, headers=None):
    return client.get("/admin/points/leaderboard", headers=headers)


def _insert_checkin(db, student_id, activity_type, *, lecture=None, college=None, at=None):
    checkin = Checkin(student_id=student_id, activity_type=activity_type)
    if lecture is not None:
        checkin.lecture_name = lecture
    if college is not None:
        checkin.college = college
    if at is not None:
        checkin.checked_in_at = at
    db.add(checkin)


def _recalc(db, student_id):
    db.flush()
    point_service.recalculate_and_store_points(db, student_id)
    db.commit()
    db.expire_all()


def _student_id(db, code):
    return db.query(Student).filter(Student.unique_code == code).first().id


# ---------- GET /students/{unique_code}/points ----------


def test_points_unknown_student_404(client):
    resp = _get_points(client, "R-9999")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


def test_points_zero_for_new_student(client, student_factory):
    student_factory(CODE_A)
    resp = _get_points(client, CODE_A)
    assert resp.status_code == 200
    assert resp.json()["total_points"] == 0


def test_points_after_campus_entry(client, student_factory, students_admin_headers):
    student_factory(CODE_A)
    client.post(
        "/checkins/campus-entry",
        json={"unique_code": CODE_A},
        headers=students_admin_headers,
    )
    resp = _get_points(client, CODE_A)
    assert resp.status_code == 200
    assert resp.json()["total_points"] == 5


# ---------- GET /admin/points/leaderboard ----------


def test_leaderboard_empty(client, super_headers):
    resp = _get_leaderboard(client, headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["leaderboard"] == []


def test_leaderboard_ordered_desc(
    client, student_factory, students_admin_headers,
    college_staff_headers, gate_scanner_headers, super_headers,
):
    student_factory(CODE_A, full_name="Alice")
    student_factory(CODE_B, full_name="Bob")

    for code in (CODE_A, CODE_B):
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": code},
            headers=students_admin_headers,
        )

    client.post(
        "/checkins/lecture",
        json={"unique_code": CODE_A, "lecture_name": "lecture_1"},
        headers=gate_scanner_headers,
    )

    resp = _get_leaderboard(client, headers=super_headers)
    assert resp.status_code == 200
    lb = resp.json()["leaderboard"]
    assert len(lb) == 2
    assert lb[0]["unique_code"] == CODE_A
    assert lb[0]["total_points"] == 15
    assert lb[1]["unique_code"] == CODE_B
    assert lb[1]["total_points"] == 5


def test_leaderboard_forbidden_for_non_super(client, students_admin_headers):
    resp = _get_leaderboard(client, headers=students_admin_headers)
    assert resp.status_code == 403


def test_leaderboard_unauthenticated_401(client):
    resp = _get_leaderboard(client, headers={})
    assert resp.status_code == 401


# ---------- سقوف النقاط: محاضرات (3 يومياً) + جولات (3 يومياً) ----------


def test_points_lecture_cap_per_day(client, db, student_factory):
    """3 محاضرات في نفس اليوم تُحتسب؛ المحاضرة الرابعة باليوم ما بتزيد النقاط."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    for i in range(1, 4):
        _insert_checkin(
            db, sid, ActivityType.lecture, lecture=getattr(Lecture, f"lecture_{i}"), at=now
        )
    _recalc(db, sid)

    resp = _get_points(client, CODE_A)
    body = resp.json()
    assert body["total_points"] == 30
    assert body["today_lecture_count"] == 3
    assert body["lectures_capped_today"] is True

    _insert_checkin(db, sid, ActivityType.lecture, lecture=Lecture.lecture_4, at=now)
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 30
    assert body["today_lecture_count"] == 4
    assert body["lectures_capped_today"] is True


def test_points_lecture_cap_counts_per_day_separately(client, db, student_factory):
    """سقف المحاضرات يومي: 3 اليوم + 2 أمس = 50 نقطة، والسقف فقط مفعّل لليوم."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    for i in range(1, 4):
        _insert_checkin(
            db, sid, ActivityType.lecture, lecture=getattr(Lecture, f"lecture_{i}"), at=now
        )
    for i in range(4, 6):
        _insert_checkin(
            db,
            sid,
            ActivityType.lecture,
            lecture=getattr(Lecture, f"lecture_{i}"),
            at=now - timedelta(days=1),
        )
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 50
    assert body["today_lecture_count"] == 3
    assert body["lectures_capped_today"] is True


def test_points_lecture_cap_not_met_under_three(client, db, student_factory):
    """قبل بلوغ 3 محاضرات باليوم، السقف غير مفعّل."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    _insert_checkin(db, sid, ActivityType.lecture, lecture=Lecture.lecture_1, at=now)
    _insert_checkin(db, sid, ActivityType.lecture, lecture=Lecture.lecture_2, at=now)
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 20
    assert body["today_lecture_count"] == 2
    assert body["lectures_capped_today"] is False


def test_points_tour_cap_per_day(client, db, student_factory):
    """3 جولات في نفس اليوم تُحتسب؛ الجولة الرابعة باليوم ما بتزيد النقاط."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    for college in (Faculty.medicine, Faculty.dentistry, Faculty.pharmacy):
        _insert_checkin(db, sid, ActivityType.tour, college=college, at=now)
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 30
    assert body["today_tour_count"] == 3
    assert body["tours_capped_today"] is True

    _insert_checkin(db, sid, ActivityType.tour, college=Faculty.civil_engineering, at=now)
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 30
    assert body["today_tour_count"] == 4
    assert body["tours_capped_today"] is True


def test_points_tour_cap_counts_per_day_separately(client, db, student_factory):
    """سقف الجولات يومي: 3 اليوم + 2 أمس = 50 نقطة، والسقف فقط مفعّل لليوم."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    for college in (Faculty.medicine, Faculty.dentistry, Faculty.pharmacy):
        _insert_checkin(db, sid, ActivityType.tour, college=college, at=now)
    for college in (Faculty.civil_engineering, Faculty.architecture):
        _insert_checkin(
            db, sid, ActivityType.tour, college=college, at=now - timedelta(days=1)
        )
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 50
    assert body["today_tour_count"] == 3
    assert body["tours_capped_today"] is True


def test_points_tour_below_cap_not_capped(client, db, student_factory):
    """جولتان فقط + يوم جديد: لا سقف، والنقاط 20."""
    student_factory(CODE_A)
    sid = _student_id(db, CODE_A)
    now = datetime.now()

    for college in (Faculty.medicine, Faculty.dentistry):
        _insert_checkin(db, sid, ActivityType.tour, college=college, at=now)
    _recalc(db, sid)

    body = _get_points(client, CODE_A).json()
    assert body["total_points"] == 20
    assert body["today_tour_count"] == 2
    assert body["tours_capped_today"] is False
