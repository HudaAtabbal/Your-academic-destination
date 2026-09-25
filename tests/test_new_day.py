"""اختبارات سيناريو اليوم الجديد — حضور الجامعة يومي ي starts."""

from datetime import datetime


STUDENT = "R-9001"
L1 = "lecture_1"
L2 = "lecture_2"


def test_day2_lecture_before_gate_409(
    client, student_factory, students_admin_headers, gate_scanner_headers, monkeypatch
):
    student_factory(STUDENT)

    day1 = datetime(2025, 6, 15, 10, 0, 0)
    day2 = datetime(2025, 6, 16, 9, 0, 0)

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day1)

    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    r = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L1},
        headers=gate_scanner_headers,
    )
    assert r.status_code == 201, r.text

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day2)

    r = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L2},
        headers=gate_scanner_headers,
    )
    assert r.status_code == 409
    assert r.json()["error_code"] == "missing_campus_entry"

    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    r = client.post(
        "/checkins/lecture",
        json={"unique_code": STUDENT, "lecture_name": L2},
        headers=gate_scanner_headers,
    )
    assert r.status_code == 201


def test_campus_points_across_days(
    client, student_factory, students_admin_headers, monkeypatch
):
    student_factory(STUDENT)

    day1 = datetime(2025, 6, 15, 10, 0, 0)
    day2 = datetime(2025, 6, 16, 10, 0, 0)

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day1)
    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    r = client.get(f"/students/{STUDENT}/points")
    assert r.status_code == 200
    assert r.json()["total_points"] == 5

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day2)
    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    r = client.get(f"/students/{STUDENT}/points")
    assert r.status_code == 200
    assert r.json()["total_points"] == 10


def test_duplicate_campus_same_day_409(
    client, student_factory, students_admin_headers, monkeypatch
):
    student_factory(STUDENT)

    monkeypatch.setattr("app.time_utils.now_naive", lambda: datetime(2025, 6, 15, 10, 0, 0))

    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 409
    assert r.json()["error_code"] == "duplicate_checkin"


def test_duplicate_campus_different_day_ok(
    client, student_factory, students_admin_headers, monkeypatch
):
    student_factory(STUDENT)

    day1 = datetime(2025, 6, 15, 10, 0, 0)
    day2 = datetime(2025, 6, 16, 10, 0, 0)

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day1)
    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201

    monkeypatch.setattr("app.time_utils.now_naive", lambda: day2)
    r = client.post(
        "/checkins/campus-entry",
        json={"unique_code": STUDENT},
        headers=students_admin_headers,
    )
    assert r.status_code == 201
