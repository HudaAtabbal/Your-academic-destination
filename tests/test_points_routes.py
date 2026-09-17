"""اختبارات نقاطي + لوحة الترتيب — endpoints عامة + super_admin."""

CODE_A = "R-9001"
CODE_B = "R-9002"


def _get_points(client, code):
    return client.get(f"/students/{code}/points")


def _get_leaderboard(client, headers=None):
    return client.get("/admin/points/leaderboard", headers=headers)


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
