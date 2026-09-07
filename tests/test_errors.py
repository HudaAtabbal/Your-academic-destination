"""اختبارات توحيد شكل الخطأ {error_code, message, details} عبر كل الروترات."""


def _assert_shape(resp):
    assert resp.status_code >= 400
    assert set(resp.json().keys()) == {"error_code", "message", "details"}


def test_shape_login_failure(client):
    _assert_shape(
        client.post("/auth/login", json={"username": "x", "password": "y"})
    )


def test_shape_missing_auth_header(client):
    _assert_shape(client.get("/admin/accounts"))


def test_shape_forbidden(client, students_admin_headers):
    _assert_shape(client.get("/admin/accounts", headers=students_admin_headers))


def test_shape_unknown_student(client, students_admin_headers):
    _assert_shape(
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9999"},
            headers=students_admin_headers,
        )
    )


def test_shape_duplicate_business_rule(
    client, student_factory, students_admin_headers
):
    student_factory("R-9001")
    assert (
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9001"},
            headers=students_admin_headers,
        ).status_code
        == 201
    )
    _assert_shape(
        client.post(
            "/checkins/campus-entry",
            json={"unique_code": "R-9001"},
            headers=students_admin_headers,
        )
    )


def test_shape_duplicate_survey(client, student_factory):
    student_factory("R-9001")
    assert (
        client.post(
            "/survey/R-9001",
            json={"opinion_change": "decided", "preferred_major": "college_placeholder_1"},
        ).status_code
        == 201
    )
    _assert_shape(
        client.post(
            "/survey/R-9001",
            json={"opinion_change": "decided", "preferred_major": "college_placeholder_1"},
        )
    )


def test_shape_staff_without_college(
    client, create_custom_staff, auth_headers
):
    create_custom_staff("no_college_staff", "pw123", None)
    headers = auth_headers("no_college_staff", "pw123")
    _assert_shape(
        client.post("/bookings/tour", json={"unique_code": "R-9001"}, headers=headers)
    )