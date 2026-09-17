"""
E2E flow tests — end-to-end journeys through the real API (TestClient).
Each test covers a complete user story from start to finish.
"""

import re

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.models import (
    AccountRole,
    Faculty,
    RegistrationType,
    SmsJob,
    SmsJobStatus,
    Student,
    StudentStatus,
    VerificationStatus,
)

_WORKER_TOKEN = "test-worker"
_WORKER_HEADERS = {"Authorization": f"Bearer {_WORKER_TOKEN}"}
_WCODE_RE = re.compile(r"^W-\d{6}$")


@pytest.fixture(autouse=True)
def _queue_mode(monkeypatch):
    monkeypatch.setenv("SMS_MODE", "queue")
    monkeypatch.setenv("WORKER_TOKEN", _WORKER_TOKEN)


# ---------------------------------------------------------------------------
# F1: Full student registration flow in queue mode
# ---------------------------------------------------------------------------


def test_f1_student_registration_flow_queue_mode(
    client, db, students_admin_headers, monkeypatch
):
    # 1. Register via public endpoint
    monkeypatch.setattr(
        "app.routers.registration.registration_service.sms_service.send_otp_sms",
        lambda *a, **k: None,
    )
    resp = client.post(
        "/students/register",
        json={
            "full_name": "طالب تجريبي",
            "birth_date": "2000-01-01",
            "certificate_year": 2025,
            "certificate_type": "scientific",
            "average_score": 90.0,
            "initial_preferred_major": ["medicine"],
            "contact_id": "0911111111",
        },
    )
    assert resp.status_code == 201, resp.text
    code = resp.json()["unique_code"]
    assert code.startswith("R-")

    # 2. SmsJob created in pending state
    job = db.query(SmsJob).one()
    assert job.status == SmsJobStatus.pending
    assert job.phone == "0911111111"
    otp_plaintext = job.otp_code

    # 3. Dequeue → international phone + plaintext OTP
    items = client.post(
        "/internal/sms/dequeue", params={"batch": 10}, headers=_WORKER_HEADERS
    ).json()
    assert len(items) == 1
    assert items[0]["phone"] == "963911111111"
    assert items[0]["otp_code"] == otp_plaintext
    job_id = items[0]["job_id"]

    # 4. Report success → sent
    report = client.post(
        "/internal/sms/report",
        json={"job_id": job_id, "success": True},
        headers=_WORKER_HEADERS,
    )
    assert report.status_code == 200
    assert report.json()["status"] == "sent"

    # 5. Verify OTP
    verify = client.post(
        "/students/otp/verify",
        json={"unique_code": code, "otp": otp_plaintext},
    )
    assert verify.status_code == 200
    assert verify.json()["verification_status"] == "verified"

    # 6. Card shows verified + qr_payload == code
    card = client.get(f"/students/card/{code}")
    assert card.status_code == 200
    assert card.json()["verification_status"] == "verified"
    assert card.json()["qr_payload"] == code

    # 7. Points start at zero
    pts = client.get(f"/students/{code}/points")
    assert pts.status_code == 200
    assert pts.json()["total_points"] == 0


# ---------------------------------------------------------------------------
# F2: Ideal student day — maximum 80 points
# ---------------------------------------------------------------------------


def test_f2_ideal_student_day_80_points(
    client,
    db,
    super_headers,
    students_admin_headers,
    gate_scanner_headers,
    college_staff_headers,
    auth_headers,
):
    # Setup: generate a walk-in code
    gen = client.post(
        "/admin/walkin-codes/generate", json={"count": 1}, headers=super_headers
    )
    assert gen.status_code == 201
    wcode = gen.json()["codes"][0]
    assert _WCODE_RE.match(wcode)

    # Find student via search
    search = client.get(
        "/admin/students/search", params={"code": wcode}, headers=students_admin_headers
    )
    assert search.status_code == 200
    student_id = search.json()["id"]

    # 1. Fill complete student data via PATCH
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

    # 2. Campus entry → 5 pts
    assert (
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": wcode},
            headers=students_admin_headers,
        ).status_code
        == 201
    )

    # 3. Three different lectures → 30 pts (max 3/day × 10)
    for lecture in ("lecture_1", "lecture_2", "lecture_3"):
        r = client.post(
            "/checkins/lecture",
            json={"unique_code": wcode, "lecture_name": lecture},
            headers=gate_scanner_headers,
        )
        assert r.status_code == 201, r.text

    # 4. Book tour for medicine → tour checkin → 10 pts
    tour_book = client.post(
        "/bookings/tour",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert tour_book.status_code == 201, tour_book.text
    tour_check = client.post(
        "/checkins/tour",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert tour_check.status_code == 201, tour_check.text

    # 5. Book consultation → consultation checkin → 15 pts
    cons_book = client.post(
        "/bookings/consultation",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert cons_book.status_code == 201, cons_book.text
    cons_check = client.post(
        "/checkins/consultation",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert cons_check.status_code == 201, cons_check.text

    # 6. Submit survey → 20 pts
    survey = client.post(
        f"/survey/{wcode}",
        json={"opinion_change": "decided", "preferred_major": "medicine"},
    )
    assert survey.status_code == 201

    # 7. Total = 80
    pts = client.get(f"/students/{wcode}/points")
    assert pts.status_code == 200
    assert pts.json()["total_points"] == 80

    # 8. Duplicate lecture → 409
    dup_lecture = client.post(
        "/checkins/lecture",
        json={"unique_code": wcode, "lecture_name": "lecture_1"},
        headers=gate_scanner_headers,
    )
    assert dup_lecture.status_code == 409
    assert dup_lecture.json()["error_code"] == "duplicate_checkin"

    # 9. Duplicate tour → 409
    dup_tour = client.post(
        "/checkins/tour",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert dup_tour.status_code == 409
    assert dup_tour.json()["error_code"] == "duplicate_checkin"

    # 10. Duplicate consultation → 409
    dup_cons = client.post(
        "/checkins/consultation",
        json={"unique_code": wcode},
        headers=college_staff_headers,
    )
    assert dup_cons.status_code == 409
    assert dup_cons.json()["error_code"] == "duplicate_checkin"

    # 11. Duplicate survey → 409
    dup_survey = client.post(
        f"/survey/{wcode}",
        json={"opinion_change": "decided", "preferred_major": "medicine"},
    )
    assert dup_survey.status_code == 409
    assert dup_survey.json()["error_code"] == "duplicate_survey"


# ---------------------------------------------------------------------------
# F3: Walk-in field gate flow — generate, fill data, checkin
# ---------------------------------------------------------------------------


def test_f3_walkin_field_gate_flow(
    client, db, super_headers, students_admin_headers, gate_scanner_headers
):
    # 1. Super generates 3 walk-in codes
    gen = client.post(
        "/admin/walkin-codes/generate", json={"count": 3}, headers=super_headers
    )
    assert gen.status_code == 201
    codes = gen.json()["codes"]
    assert len(codes) == 3
    wcode = codes[0]

    # Student exists but has no data
    search = client.get(
        "/admin/students/search", params={"code": wcode}, headers=students_admin_headers
    )
    assert search.status_code == 200
    student_id = search.json()["id"]
    assert search.json()["status"] == "pending"
    assert search.json()["full_name"] is None

    # 2. Gate staff fills data via PATCH (students_admin role)
    patch = client.patch(
        f"/admin/students/{student_id}",
        json={
            "full_name": "طالب بوابة",
            "contact_id": "0922222222",
            "birth_date": "2004-03-10",
            "bacc_year": 2025,
            "certificate_type": "literary",
            "bacc_average": 80.0,
            "initial_preferred_major": ["tourism"],
        },
        headers=students_admin_headers,
    )
    assert patch.status_code == 200
    assert patch.json()["status"] == "complete"

    # 3. Checkin works after data is complete
    entry = client.post(
        "/checkins/campus-entry",
        json={"unique_code": wcode},
        headers=students_admin_headers,
    )
    assert entry.status_code == 201
    assert entry.json()["student_name"] == "طالب بوابة"

    # 4. Verify student is complete via search
    final = client.get(
        "/admin/students/search", params={"code": wcode}, headers=students_admin_headers
    )
    assert final.status_code == 200
    assert final.json()["status"] == "complete"


# ---------------------------------------------------------------------------
# F4: Full admin session — create staff, book, scan, dashboard
# ---------------------------------------------------------------------------


def test_f4_full_admin_session(
    client, db, super_headers, students_admin_headers, gate_scanner_headers, auth_headers
):
    # 1. Super creates a new college_staff for medicine
    create_resp = client.post(
        "/admin/accounts",
        json={
            "username": "new_staff",
            "password": "newpass123",
            "role": "college_staff",
            "college": "medicine",
        },
        headers=super_headers,
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["college"] == "medicine"

    # 2. New staff logs in
    login = client.post(
        "/auth/login", json={"username": "new_staff", "password": "newpass123"}
    )
    assert login.status_code == 200
    new_staff_headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    # Create a verified student and do campus entry
    from app.models import Student

    student = Student(
        unique_code="R-9001",
        full_name="طالب الفحص",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
        contact_id="0933333333",
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Campus entry
    entry = client.post(
        "/checkins/campus-entry",
        json={"unique_code": "R-9001"},
        headers=students_admin_headers,
    )
    assert entry.status_code == 201

    # New staff books tour
    tour_book = client.post(
        "/bookings/tour",
        json={"unique_code": "R-9001"},
        headers=new_staff_headers,
    )
    assert tour_book.status_code == 201
    assert tour_book.json()["college"] == "medicine"

    # Gate scans for lecture
    lecture = client.post(
        "/checkins/lecture",
        json={"unique_code": "R-9001", "lecture_name": "lecture_1"},
        headers=gate_scanner_headers,
    )
    assert lecture.status_code == 201

    # Tour checkin by new staff
    tour_check = client.post(
        "/checkins/tour",
        json={"unique_code": "R-9001"},
        headers=new_staff_headers,
    )
    assert tour_check.status_code == 201

    # 4. Dashboard stats reflect everything
    stats = client.get("/admin/dashboard/stats", headers=super_headers)
    assert stats.status_code == 200
    body = stats.json()
    assert body["registered_online_count"] == 1
    assert body["campus_entries_count"] == 1
    # campus(1) + lecture(1) + tour(1) = 3 cumulative activities
    assert body["activities_today_cumulative"] == 3


# ---------------------------------------------------------------------------
# F5: Session lifecycle — password change invalidates old token
# ---------------------------------------------------------------------------


def test_f5_session_lifecycle_password_change(client, super_headers):
    # 1. Login as super admin
    login = client.post(
        "/auth/login", json={"username": "taher_super", "password": "super123"}
    )
    assert login.status_code == 200
    old_token = login.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}

    # 2. Old token works — access an endpoint
    dash = client.get("/admin/dashboard/stats", headers=old_headers)
    assert dash.status_code == 200

    # 3. Change password
    patch = client.patch(
        "/admin/accounts/taher_super",
        json={"password": "super456"},
        headers=super_headers,
    )
    assert patch.status_code == 200

    # 4. Old token is rejected
    expired = client.get("/admin/dashboard/stats", headers=old_headers)
    assert expired.status_code == 401

    # 5. Login with new password → new token works
    login2 = client.post(
        "/auth/login", json={"username": "taher_super", "password": "super456"}
    )
    assert login2.status_code == 200
    new_headers = {"Authorization": f"Bearer {login2.json()['access_token']}"}
    dash2 = client.get("/admin/dashboard/stats", headers=new_headers)
    assert dash2.status_code == 200
