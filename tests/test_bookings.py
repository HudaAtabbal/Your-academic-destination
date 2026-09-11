"""اختبارات الحجوزات (bookings) — زج جولة / استشارة."""

from fastapi.testclient import TestClient

import main as main_module

STUDENT = "R-9001"


def _campus_entry(client, headers, code=STUDENT):
    return client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=headers
    )


# ---------- tour ----------


def test_tour_booking_without_campus_entry_409(client, student_factory, college_staff_headers):
    student_factory(STUDENT)
    resp = client.post("/bookings/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_tour_booking_happy(client, student_factory, students_admin_headers, college_staff_headers):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post("/bookings/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["college"] == "medicine"
    assert "booking_id" in body
    assert "booked_at" in body


def test_tour_booking_duplicate_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    assert (
        client.post("/bookings/tour", json={"unique_code": STUDENT}, headers=college_staff_headers).status_code
        == 201
    )
    resp = client.post("/bookings/tour", json={"unique_code": STUDENT}, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_booking"


def test_tour_booking_unknown_code_404(client, students_admin_headers, college_staff_headers):
    resp = client.post("/bookings/tour", json={"unique_code": "R-9999"}, headers=college_staff_headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


def test_tour_booking_staff_without_college_400(
    client, students_admin_headers, create_custom_staff, auth_headers
):
    create_custom_staff("no_college_staff", "pw123", None)
    headers = auth_headers("no_college_staff", "pw123")
    resp = client.post("/bookings/tour", json={"unique_code": STUDENT}, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "validation_error"


# ---------- consultation ----------


def test_consultation_booking_without_campus_entry_409(
    client, student_factory, college_staff_headers
):
    student_factory(STUDENT)
    resp = client.post(
        "/bookings/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "missing_campus_entry"


def test_consultation_booking_happy(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    resp = client.post(
        "/bookings/consultation", json={"unique_code": STUDENT}, headers=college_staff_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["college"] is None
    assert "booking_id" in body


def test_consultation_booking_duplicate_409(
    client, student_factory, students_admin_headers, college_staff_headers
):
    student_factory(STUDENT)
    assert _campus_entry(client, students_admin_headers).status_code == 201
    payload = {"unique_code": STUDENT}
    assert (
        client.post("/bookings/consultation", json=payload, headers=college_staff_headers).status_code
        == 201
    )
    resp = client.post("/bookings/consultation", json=payload, headers=college_staff_headers)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_booking"


# ---------- auth / roles ----------


def test_booking_forbidden_for_students_admin(client, students_admin_headers):
    resp = client.post(
        "/bookings/tour", json={"unique_code": STUDENT}, headers=students_admin_headers
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_booking_unauthenticated_401(client):
    resp = client.post("/bookings/tour", json={"unique_code": STUDENT})
    assert resp.status_code == 401


# ---------- counts ----------


def test_booking_count_today(
    client, student_factory, students_admin_headers, college_staff_headers
):
    for code in ("R-9001", "R-9002"):
        student_factory(code)
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
        assert (
            client.post("/bookings/tour", json={"unique_code": code}, headers=college_staff_headers).status_code
            == 201
        )
    r_tour = client.get(
        "/bookings/count/today",
        params={"booking_type": "tour"},
        headers=college_staff_headers,
    )
    assert r_tour.json()["count"] == 2
    r_cons = client.get(
        "/bookings/count/today",
        params={"booking_type": "consultation"},
        headers=college_staff_headers,
    )
    assert r_cons.json()["count"] == 0


def test_booking_count_invalid_type_422(client, college_staff_headers):
    resp = client.get(
        "/bookings/count/today",
        params={"booking_type": "bogus"},
        headers=college_staff_headers,
    )
    assert resp.status_code == 422


def test_booking_count_invalid_college_422_after_fix(client, college_staff_headers):
    """محدّث بعد إصلاح A5: college قيمة غير صالحة = 422 validation بدل 500"""
    with TestClient(main_module.app, raise_server_exceptions=False) as c:
        resp = c.get(
            "/bookings/count/today",
            params={"booking_type": "tour", "college": "bogus"},
            headers=college_staff_headers,
        )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"