"""اختبارات توليد رموز walk-in (super_admin فقط)."""

from app.models import RegistrationType, Student, VerificationStatus


def _walkin_students(db):
    return (
        db.query(Student)
        .filter(Student.unique_code.like("W-%"))
        .order_by(Student.unique_code)
        .all()
    )


def test_generate_walkin_codes(client, super_headers, db):
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 3}, headers=super_headers
    )
    assert resp.status_code == 201
    assert resp.json()["codes"] == ["W-0001", "W-0002", "W-0003"]

    students = _walkin_students(db)
    assert len(students) == 3
    for student in students:
        assert student.registration_type == RegistrationType.walk_in
        assert student.verification_status == VerificationStatus.verified


def test_sequence_continues_from_existing(client, super_headers, db, student_factory):
    student_factory(
        "W-0023",
        full_name=None,
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 2}, headers=super_headers
    )
    assert resp.status_code == 201
    assert resp.json()["codes"] == ["W-0024", "W-0025"]


def test_generate_count_zero_422(client, super_headers):
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 0}, headers=super_headers
    )
    assert resp.status_code == 422


def test_generate_count_above_limit_422(client, super_headers):
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 501}, headers=super_headers
    )
    assert resp.status_code == 422


def test_generate_forbidden_for_non_super(client, students_admin_headers):
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 1}, headers=students_admin_headers
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_generate_unauthenticated_401(client):
    resp = client.post("/admin/walkin-codes/generate", json={"count": 1})
    assert resp.status_code == 401