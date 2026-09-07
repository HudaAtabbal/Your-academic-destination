"""اختبارات لوحة المدير العام (dashboard) — super_admin فقط."""

from app.models import RegistrationType, VerificationStatus

STUDENT = "R-9001"
L1 = "lecture_placeholder_1"


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
            json={"opinion_change": "decided", "preferred_major": "college_placeholder_1"},
        ).status_code
        == 201
    )
    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["registered_online_count"] == 2
    assert body["campus_entries_count"] == 1
    assert body["activities_today_cumulative"] == 2
    assert body["survey_completed_count"] == 1


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