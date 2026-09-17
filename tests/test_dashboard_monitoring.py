"""
اختبارات متابعة الموقع (تبعية الموقع) — لوحة الإدارة الحية:
إحصائيات dashboard بحالة فارغة، حالة المُرسِل (sms-status) مع النبضة،
إشغال الغرف عبر عدّة محاضرات، ومتسابقو النقاط بعد جلسة يوم كامل.
"""

from datetime import datetime, timedelta

import pytest

from app.routers.internal import internal_service

_WORKER_TOKEN = "test-worker"
_WORKER_HEADERS = {"Authorization": f"Bearer {_WORKER_TOKEN}"}
STUDENT = "R-9001"
SECOND = "R-9002"
L1 = "lecture_1"
L2 = "lecture_2"


@pytest.fixture(autouse=True)
def _queue_mode(monkeypatch):
    monkeypatch.setenv("SMS_MODE", "queue")
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)


# ---------- helpers ----------


def _register(client, contact="0911111111"):
    resp = client.post(
        "/students/register",
        json={
            "full_name": "طالب تجريبي",
            "birth_date": "2000-01-01",
            "certificate_year": 2025,
            "certificate_type": "scientific",
            "average_score": 90.0,
            "initial_preferred_major": ["medicine"],
            "contact_id": contact,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["unique_code"]


def _campus(client, headers, code):
    return client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=headers
    )


def _lecture(client, headers, code, lecture=L1):
    return client.post(
        "/checkins/lecture",
        json={"unique_code": code, "lecture_name": lecture},
        headers=headers,
    )


# ---------- dashboard/stats ----------


def test_stats_empty_db_all_zeros(client, super_headers):
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered_online_count"] == 0
    assert body["students_inside_today"] == 0
    assert body["students_inside_all_days"] == 0
    assert body["survey_completed_count"] == 0
    assert body["walkin_pending_count"] == 0


# ---------- sms-status ----------


def test_sms_status_empty_db(client, super_headers):
    resp = client.get("/admin/dashboard/sms-status", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["counts"] == {"pending": 0, "sending": 0, "sent": 0, "failed": 0}
    assert body["last_heartbeat"] is None
    assert body["worker_online"] is False


def test_sms_status_unauthenticated_401(client):
    resp = client.get("/admin/dashboard/sms-status")
    assert resp.status_code == 401


def test_sms_status_forbidden_for_non_super(client, students_admin_headers):
    resp = client.get("/admin/dashboard/sms-status", headers=students_admin_headers)
    assert resp.status_code == 403


def test_sms_status_tracks_queue_states(client, db, super_headers):
    """تسجيل طالبَين بوضع queue → مهمتان pending؛ سحب واحدة → إرسال؛
    بلاغ نجاح → sent. الـ counts تعكس الحالة لحظياً."""
    _register(client, "0911111111")
    _register(client, "0922222222")

    status = client.get("/admin/dashboard/sms-status", headers=super_headers).json()
    assert status["counts"]["pending"] == 2

    items = client.post(
        "/internal/sms/dequeue", params={"batch": 1}, headers=_WORKER_HEADERS
    ).json()
    assert len(items) == 1
    job_id = items[0]["job_id"]

    status = client.get("/admin/dashboard/sms-status", headers=super_headers).json()
    assert status["counts"]["sending"] == 1
    assert status["counts"]["pending"] == 1

    report = client.post(
        "/internal/sms/report",
        json={"job_id": job_id, "success": True},
        headers=_WORKER_HEADERS,
    )
    assert report.status_code == 200

    status = client.get("/admin/dashboard/sms-status", headers=super_headers).json()
    assert status["counts"]["sent"] == 1
    assert status["counts"]["pending"] == 1
    assert status["counts"]["failed"] == 0


def test_sms_status_heartbeat_online_and_stale(
    client, db, super_headers, monkeypatch
):
    """نبضة حديثة → worker_online=True؛ نبضة أقدم من نافذة 180 ثانية → False."""
    _register(client, "0911111111")
    heartbeat = client.post("/internal/sms/heartbeat", headers=_WORKER_HEADERS)
    assert heartbeat.status_code == 200
    assert heartbeat.json()["status"] == "ok"

    status = client.get("/admin/dashboard/sms-status", headers=super_headers).json()
    assert status["worker_online"] is True
    last_heartbeat = datetime.fromisoformat(status["last_heartbeat"])

    # تقدم الزمن المرجعي 4 دقائق — النبضة صارت قديمة (>180s) → غير متصل
    monkeypatch.setattr(
        internal_service, "_now", lambda: last_heartbeat + timedelta(minutes=4)
    )
    status = client.get("/admin/dashboard/sms-status", headers=super_headers).json()
    assert status["worker_online"] is False
    assert datetime.fromisoformat(status["last_heartbeat"]) == last_heartbeat


# ---------- rooms-occupancy ----------


def test_rooms_occupancy_empty(client, super_headers):
    resp = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["rooms"] == []


def test_rooms_occupancy_multiple_lectures(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
):
    for code in (STUDENT, SECOND, "R-9003"):
        student_factory(code)
        assert _campus(client, students_admin_headers, code).status_code == 201

    # STUDENT + SECOND في المحاضرة الأولى، R-9003 في الثانية
    assert _lecture(client, gate_scanner_headers, STUDENT, L1).status_code == 201
    assert _lecture(client, gate_scanner_headers, SECOND, L1).status_code == 201
    assert _lecture(client, gate_scanner_headers, "R-9003", L2).status_code == 201

    resp = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers)
    assert resp.status_code == 200
    rooms = resp.json()["rooms"]
    assert len(rooms) == 2

    by_lecture = {room["lecture_name"]: room for room in rooms}
    assert by_lecture[L1]["current_count"] == 2
    assert by_lecture[L2]["current_count"] == 1
    for room in rooms:
        assert room["hall_label"] == "المدرج الرئيسي"
        assert room["last_updated"] is not None


def test_rooms_occupancy_ignores_previous_days(
    client,
    student_factory,
    students_admin_headers,
    gate_scanner_headers,
    super_headers,
    monkeypatch,
):
    """محدّث بعد إصلاح الملاحظة 3: محاضرات أمس ما تدخل عداد current_count."""
    student_factory(STUDENT)

    day1 = datetime(2025, 6, 15, 10, 0, 0)
    day2 = datetime(2025, 6, 16, 10, 0, 0)

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day1)
    assert _campus(client, students_admin_headers, STUDENT).status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, L1).status_code == 201

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day2)
    resp = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers)
    assert resp.status_code == 200
    assert resp.json()["rooms"] == []

    assert _campus(client, students_admin_headers, STUDENT).status_code == 201
    assert _lecture(client, gate_scanner_headers, STUDENT, L2).status_code == 201

    resp = client.get("/admin/dashboard/rooms-occupancy", headers=super_headers)
    assert resp.status_code == 200
    rooms = resp.json()["rooms"]
    assert len(rooms) == 1
    assert rooms[0]["lecture_name"] == L2
    assert rooms[0]["current_count"] == 1


# ---------- leaderboard بعد يوم كامل ----------


def test_leaderboard_after_full_day_session(
    client,
    super_headers,
    students_admin_headers,
    gate_scanner_headers,
    college_staff_headers,
):
    """نجمة اليوم الكاملة (80 نقطة) تحتل قمة المتسابقين أولاً."""
    gen = client.post(
        "/admin/walkin-codes/generate", json={"count": 1}, headers=super_headers
    )
    assert gen.status_code == 201
    wcode = gen.json()["codes"][0]

    student_id = client.get(
        "/admin/students/search", params={"code": wcode}, headers=students_admin_headers
    ).json()["id"]
    patch = client.patch(
        f"/admin/students/{student_id}",
        json={
            "full_name": "طالب مثالي",
            "contact_id": "0912345678",
            "birth_date": "2005-06-15",
            "bacc_year": 2025,
            "certificate_type": "scientific",
            "bacc_average": 95.0,
            "initial_preferred_major": ["medicine"],
        },
        headers=students_admin_headers,
    )
    assert patch.status_code == 200
    assert patch.json()["status"] == "complete"

    assert _campus(client, students_admin_headers, wcode).status_code == 201
    for lecture in ("lecture_1", "lecture_2", "lecture_3"):
        assert _lecture(client, gate_scanner_headers, wcode, lecture).status_code == 201

    assert (
        client.post(
            "/bookings/tour", json={"unique_code": wcode}, headers=college_staff_headers
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/checkins/tour", json={"unique_code": wcode}, headers=college_staff_headers
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/bookings/consultation",
            json={"unique_code": wcode},
            headers=college_staff_headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/checkins/consultation",
            json={"unique_code": wcode},
            headers=college_staff_headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/survey/{wcode}",
            json={"opinion_change": "decided", "preferred_major": "medicine"},
        ).status_code
        == 201
    )

    pts = client.get(f"/students/{wcode}/points").json()["total_points"]
    assert pts == 80

    lb = client.get("/admin/points/leaderboard", headers=super_headers).json()[
        "leaderboard"
    ]
    assert len(lb) == 1
    assert lb[0]["unique_code"] == wcode
    assert lb[0]["total_points"] == 80