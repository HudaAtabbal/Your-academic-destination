"""اختبارات توليد رموز walk-in (super_admin فقط)."""

import re

from app.models import RegistrationType, Student, VerificationStatus

_CODE_RE = re.compile(r"^W-\d{6}$")


def _walkin_students(db):
    return db.query(Student).filter(Student.unique_code.like("W-%")).all()


def test_generate_walkin_codes(client, super_headers, db):
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 3}, headers=super_headers
    )
    assert resp.status_code == 201

    codes = resp.json()["codes"]
    assert len(codes) == 3
    # كل رمز عشوائي بالصيغة W-XXXXXX — مش تسلسلي
    assert all(_CODE_RE.match(code) for code in codes)
    assert len(set(codes)) == 3  # فريدة جوا الدفعة

    students = _walkin_students(db)
    assert len(students) == 3
    for student in students:
        assert student.registration_type == RegistrationType.walk_in
        assert student.verification_status == VerificationStatus.verified


def test_generate_avoids_existing_codes(client, super_headers, db, student_factory):
    # رمز موجود مسبقاً بالـ DB — التوليد لازم ما يكرّره
    existing_code = "W-123456"
    student_factory(
        existing_code,
        full_name=None,
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )
    resp = client.post(
        "/admin/walkin-codes/generate", json={"count": 3}, headers=super_headers
    )
    assert resp.status_code == 201
    codes = resp.json()["codes"]
    assert existing_code not in codes
    assert all(_CODE_RE.match(code) for code in codes)
    assert len(set(codes)) == 3


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