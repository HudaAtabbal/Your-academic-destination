"""اختبارات سلامة البيانات ومنطق النقاط وسباقات التزامن."""

import threading
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.errors import AppError
from app.models import (
    ActivityType,
    Checkin,
    College,
    Lecture,
    OpinionChange,
    PostSurvey,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)
from app.routers.checkins import checkin_service
from app.routers.points import point_service
from app.routers.survey import survey_service


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
    db.flush()  # autoflush=False — إدراجات في الانتظار لازم تُطير قبل إعادة الحساب
    points = point_service.recalculate_and_store_points(db, student_id)
    db.commit()
    db.expire_all()
    return points


def _student_id(db, code):
    return db.query(Student).filter(Student.unique_code == code).first().id


def _student_points(client, code):
    resp = client.get(f"/students/{code}/points")
    assert resp.status_code == 200, resp.text
    return resp.json()["total_points"]


def test_points_formula_full_matrix(client, db, student_factory):
    """المعادلة الكاملة: حضور 2 يوم + محاضرات (سقف 3/يوم) + جولتان + استشارة + استبيان = 95."""
    student_factory("R-9001")
    sid = _student_id(db, "R-9001")
    now = datetime.now()

    _insert_checkin(db, sid, ActivityType.campus_entry, at=now)
    _insert_checkin(db, sid, ActivityType.campus_entry, at=now - timedelta(days=1))
    for i in range(1, 6):  # 5 محاضرات اليوم نفسه → تُحتسب 3 فقط
        _insert_checkin(
            db, sid, ActivityType.lecture, lecture=getattr(Lecture, f"lecture_{i}"), at=now
        )
    _insert_checkin(db, sid, ActivityType.tour, college=College.medicine, at=now)
    _insert_checkin(db, sid, ActivityType.tour, college=College.dentistry, at=now)
    _insert_checkin(db, sid, ActivityType.consultation, at=now)
    db.add(
        PostSurvey(
            student_id=sid,
            opinion_change=OpinionChange.decided,
            preferred_major=College.medicine,
        )
    )
    db.commit()

    _recalc(db, sid)
    assert _student_points(client, "R-9001") == 95  # 10 + 30 + 20 + 15 + 20


def test_lecture_daily_cap_counted_per_day(client, db, student_factory):
    """سقف 3 محاضرات يومياً: 5 اليوم + 2 أمس = 5×10 نقاط محتسبة فعلياً 3×10 + 2×10 = 50."""
    student_factory("R-9001")
    sid = _student_id(db, "R-9001")
    now = datetime.now()
    for i in range(1, 6):
        _insert_checkin(
            db, sid, ActivityType.lecture, lecture=getattr(Lecture, f"lecture_{i}"), at=now
        )
    for i in range(6, 8):
        _insert_checkin(
            db,
            sid,
            ActivityType.lecture,
            lecture=getattr(Lecture, f"lecture_{i}"),
            at=now - timedelta(days=1),
        )
    db.commit()

    _recalc(db, sid)
    assert _student_points(client, "R-9001") == 50


def test_campus_entry_once_per_day_points(client, db, student_factory, students_admin_headers):
    student_factory("R-9001")
    body = {"unique_code": "R-9001"}

    r1 = client.post("/checkins/campus-entry", json=body, headers=students_admin_headers)
    assert r1.status_code == 201
    assert _student_points(client, "R-9001") == 5

    r2 = client.post("/checkins/campus-entry", json=body, headers=students_admin_headers)
    assert r2.status_code == 409
    assert r2.json()["error_code"] == "duplicate_checkin"
    assert _student_points(client, "R-9001") == 5

    sid = _student_id(db, "R-9001")
    _insert_checkin(db, sid, ActivityType.campus_entry, at=datetime.now() - timedelta(days=1))
    _recalc(db, sid)
    assert _student_points(client, "R-9001") == 10


def test_survey_double_submit_serial(client, db, student_factory):
    student_factory("R-9001")
    payload = {"opinion_change": "decided", "preferred_major": "medicine"}

    r1 = client.post("/survey/R-9001", json=payload)
    assert r1.status_code == 201, r1.text
    r2 = client.post("/survey/R-9001", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error_code"] == "duplicate_survey"

    assert db.query(PostSurvey).count() == 1
    assert _student_points(client, "R-9001") == 20


def test_survey_concurrent_submit_single_winner(client, db, student_factory):
    """سباق التزامن على إرسال الاستبيان: طلب واحد ينجح والثاني يحصل 409 duplicate_survey."""
    student_factory("R-9001")
    results = []
    barrier = threading.Barrier(2)

    def _submit():
        session = SessionLocal()
        try:
            barrier.wait(timeout=5)
            survey_service.submit_survey(
                session, "R-9001", OpinionChange.decided, College.medicine
            )
            session.commit()
            results.append(("ok", None))
        except AppError as exc:
            results.append(("error", exc.error_code))
        finally:
            session.close()

    threads = [threading.Thread(target=_submit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    oks = [r for r in results if r[0] == "ok"]
    errors = [r for r in results if r[0] == "error"]
    assert len(oks) == 1
    assert len(errors) == 1
    assert errors[0][1] == "duplicate_survey"

    assert db.query(PostSurvey).count() == 1
    assert _student_points(client, "R-9001") == 20


def test_lecture_concurrent_checkin_single_winner(client, db, student_factory, students_admin_headers):
    student_factory("R-9001")
    r = client.post(
        "/checkins/campus-entry", json={"unique_code": "R-9001"}, headers=students_admin_headers
    )
    assert r.status_code == 201
    results = []
    barrier = threading.Barrier(2)

    def _checkin():
        session = SessionLocal()
        try:
            barrier.wait(timeout=5)
            checkin_service.create_lecture_checkin(session, "R-9001", Lecture.lecture_1)
            session.commit()
            results.append(("ok", None))
        except AppError as exc:
            results.append(("error", exc.error_code))
        finally:
            session.close()

    threads = [threading.Thread(target=_checkin) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    oks = [r for r in results if r[0] == "ok"]
    errors = [r for r in results if r[0] == "error"]
    assert len(oks) == 1
    assert len(errors) == 1
    assert errors[0][1] == "duplicate_checkin"

    sid = _student_id(db, "R-9001")
    rows = (
        db.query(Checkin)
        .filter(Checkin.student_id == sid, Checkin.activity_type == ActivityType.lecture)
        .count()
    )
    assert rows == 1
    assert _student_points(client, "R-9001") == 15  # 5 حضور + 10 محاضرة


def test_walkin_completeness_transition(client, db, super_headers, students_admin_headers):
    r = client.post("/admin/walkin-codes/generate", json={"count": 1}, headers=super_headers)
    assert r.status_code == 201
    code = r.json()["codes"][0]

    resp = client.get("/admin/students/walkin-incomplete", headers=students_admin_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["unique_code"] == code and i["status"] == "no_data" for i in items)

    st = db.query(Student).filter(Student.unique_code == code).first()
    assert st.registration_type == RegistrationType.walk_in
    assert st.status == StudentStatus.pending

    patch = {
        "full_name": "طالب مشي",
        "contact_platform": "whatsapp",
        "contact_id": "0999999999",
        "birth_date": "2002-02-02",
        "bacc_year": 2023,
        "bacc_average": 80.0,
        "certificate_type": "scientific",
        "initial_preferred_major": ["medicine"],
    }
    r2 = client.patch(f"/admin/students/{st.id}", json=patch, headers=students_admin_headers)
    assert r2.status_code == 200, r2.text

    db.refresh(st)
    assert st.status == StudentStatus.complete

    resp3 = client.get("/admin/students/walkin-incomplete", headers=students_admin_headers)
    assert all(i["unique_code"] != code for i in resp3.json()["items"])


def test_dashboard_counter_accuracy(
    client, db, student_factory, super_headers, students_admin_headers, gate_scanner_headers
):
    for code in ("R-9001", "R-9002", "R-9003"):
        student_factory(code)
    student_factory(
        "W-0001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )

    for code in ("R-9001", "R-9002"):
        r = client.post(
            "/checkins/campus-entry", json={"unique_code": code}, headers=students_admin_headers
        )
        assert r.status_code == 201

    sid = _student_id(db, "R-9001")
    _insert_checkin(db, sid, ActivityType.campus_entry, at=datetime.now() - timedelta(days=1))
    db.commit()

    r = client.post(
        "/checkins/lecture",
        json={"unique_code": "R-9001", "lecture_name": "lecture_1"},
        headers=gate_scanner_headers,
    )
    assert r.status_code == 201

    r = client.post(
        "/survey/R-9001", json={"opinion_change": "decided", "preferred_major": "medicine"}
    )
    assert r.status_code == 201

    stats = client.get("/admin/dashboard/stats", headers=super_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["registered_online_count"] == 3
    assert body["campus_entries_count"] == 3  # 2 اليوم + 1 أمس (تراكمي بكل التواريخ)
    assert body["activities_today_cumulative"] == 3  # 2 حضور + 1 محاضرة
    assert body["survey_completed_count"] == 1