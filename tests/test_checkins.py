"""اختبارات تسجيل الحضور (check-ins) — الأنواع الأربعة + العدادات."""

from fastapi.testclient import TestClient

import main as main_module
from app.models import College

STUDENT = "R-9001"
L1 = "lecture_1"
L2 = "lecture_2"


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
    create_custom_staff("staff2", "pw456", College.dentistry)
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