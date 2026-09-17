import pytest
from app.models import RegistrationType, VerificationStatus, StudentStatus


def test_search_student_happy(client, student_factory, super_headers):
    student_factory("R-9001", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.get("/admin/students/search?code=R-9001", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["unique_code"] == "R-9001"


def test_search_student_404(client, super_headers):
    resp = client.get("/admin/students/search?code=R-9999", headers=super_headers)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "student_not_found"


def test_search_student_forbidden_for_college_staff(client, student_factory, college_staff_headers):
    student_factory("R-9002", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.get("/admin/students/search?code=R-9002", headers=college_staff_headers)
    assert resp.status_code == 403


def test_student_stats_empty(client, super_headers):
    resp = client.get("/admin/students/stats", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_registered"] == 0
    assert data["walkin_pending_count"] == 0


def test_student_stats_registered_counted(client, student_factory, super_headers):
    student_factory("R-1001", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    student_factory("R-1002", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    student_factory("R-1003", registration_type=RegistrationType.registered, verification_status=VerificationStatus.pending, status=StudentStatus.pending)
    resp = client.get("/admin/students/stats", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_registered"] == 2


def test_student_stats_walkin_pending_counted(client, student_factory, super_headers):
    student_factory("W-1001", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    student_factory("W-1002", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.get("/admin/students/stats", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["walkin_pending_count"] == 1
    assert data["walkin_completed_count"] == 1


def test_walkin_incomplete_empty(client, super_headers):
    resp = client.get("/admin/students/walkin-incomplete?page=1&limit=20", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 1


def test_walkin_incomplete_no_data(client, student_factory, super_headers):
    student_factory("W-2001", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    resp = client.get("/admin/students/walkin-incomplete?page=1&limit=20", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "no_data"


def test_walkin_incomplete_partial(client, student_factory, students_admin_headers, super_headers):
    student_factory("W-2002", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    client.post("/checkins/campus-entry", headers=students_admin_headers, json={"unique_code": "W-2002"})
    resp = client.get("/admin/students/walkin-incomplete?page=1&limit=20", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "partial"


def test_walkin_incomplete_pagination(client, student_factory, super_headers):
    student_factory("W-3001", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    student_factory("W-3002", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    student_factory("W-3003", registration_type=RegistrationType.walk_in, verification_status=VerificationStatus.verified, status=StudentStatus.pending)
    resp = client.get("/admin/students/walkin-incomplete?page=1&limit=2", headers=super_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2


def test_update_student_contact(client, student_factory, students_admin_headers, db):
    student = student_factory("R-4001", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.patch(f"/admin/students/{student.id}", headers=students_admin_headers, json={"contact_id": "0912345678"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_id"] == "0912345678"


def test_update_student_empty_422(client, student_factory, students_admin_headers):
    student = student_factory("R-4002", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.patch(f"/admin/students/{student.id}", headers=students_admin_headers, json={})
    assert resp.status_code == 422


def test_update_student_invalid_contact_422(client, student_factory, students_admin_headers):
    student = student_factory("R-4003", registration_type=RegistrationType.registered, verification_status=VerificationStatus.verified, status=StudentStatus.complete)
    resp = client.patch(f"/admin/students/{student.id}", headers=students_admin_headers, json={"contact_id": "123"})
    assert resp.status_code == 422


def test_walkin_patching_verified_registered_contact_409(
    client, student_factory, students_admin_headers
):
    """تصادم رقم تواصل: walk-in يملأ بياناته برقم مسجَّل موثّق مسبقاً → 409."""
    student_factory(
        "R-4004",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
        contact_id="0911111111",
    )
    walkin = student_factory(
        "W-3001",
        registration_type=RegistrationType.walk_in,
        status=StudentStatus.pending,
    )
    resp = client.patch(
        f"/admin/students/{walkin.id}",
        headers=students_admin_headers,
        json={"contact_id": "0911111111"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "duplicate_contact"


def test_student_keeps_own_contact_when_updating(
    client, student_factory, students_admin_headers
):
    """نفس الطالب يحدّث رقمه الخاص (مطابق لرقمه الحالي) → مسموح، لا اصطدام."""
    student = student_factory(
        "R-4005",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
        contact_id="0922222222",
    )
    resp = client.patch(
        f"/admin/students/{student.id}",
        headers=students_admin_headers,
        json={"contact_id": "0922222222"},
    )
    assert resp.status_code == 200
    resp = client.get(
        f"/admin/students/search", params={"code": "R-4005"}, headers=students_admin_headers
    )
    assert resp.json()["contact_id"] == "0922222222"


def test_search_returns_completion_fields_registered_verified(
    client, student_factory, students_admin_headers
):
    """registered + verified → completion_status=complete و is_complete=true بالبحث."""
    student_factory(
        "R-5001",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
    )
    resp = client.get(
        "/admin/students/search", params={"code": "R-5001"}, headers=students_admin_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_status"] == "complete"
    assert data["is_complete"] is True


def test_registered_unverified_incomplete(client, student_factory, students_admin_headers):
    """registered بدون تحقق OTP → سجل غير مكتمل."""
    student_factory(
        "R-5002",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.pending,
        status=StudentStatus.pending,
    )
    resp = client.get(
        "/admin/students/search", params={"code": "R-5002"}, headers=students_admin_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_status"] == "incomplete"
    assert data["is_complete"] is False


def test_walkin_no_data_incomplete(client, student_factory, students_admin_headers):
    """walk-in بلا بيانات (status=pending) → غير مكتمل رغم verification verified."""
    student_factory(
        "W-5003",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.pending,
    )
    resp = client.get(
        "/admin/students/search", params={"code": "W-5003"}, headers=students_admin_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_status"] == "incomplete"
    assert data["is_complete"] is False


def test_walkin_partial_patch_then_full_complete(
    client, student_factory, students_admin_headers
):
    """تعبئة جزئية لبيانات walk-in تبقيه incomplete؛ اكتمال الحقول الستة (بدون التخصص المفضّل) → complete."""
    walkin = student_factory(
        "W-5004",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.pending,
    )

    partial = client.patch(
        f"/admin/students/{walkin.id}",
        headers=students_admin_headers,
        json={"full_name": "طالب الميدان"},
    )
    assert partial.status_code == 200
    assert partial.json()["completion_status"] == "incomplete"
    assert partial.json()["is_complete"] is False

    full = client.patch(
        f"/admin/students/{walkin.id}",
        headers=students_admin_headers,
        json={
            "contact_id": "0912345678",
            "birth_date": "2005-01-15",
            "bacc_year": 2024,
            "bacc_average": 92.5,
            "certificate_type": "scientific",
        },
    )
    assert full.status_code == 200
    data = full.json()
    assert data["completion_status"] == "complete"
    assert data["is_complete"] is True
    assert data["status"] == "complete"

    search = client.get(
        "/admin/students/search", params={"code": "W-5004"}, headers=students_admin_headers
    )
    assert search.status_code == 200
    assert search.json()["is_complete"] is True


def test_patch_response_has_completion_fields(client, student_factory, students_admin_headers):
    """كل استجابة PATCH تحمل حقلي الاكتمال، وverification_status محصّن ضد التعديل."""
    student = student_factory(
        "R-5005",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.pending,
        status=StudentStatus.pending,
    )
    resp = client.patch(
        f"/admin/students/{student.id}",
        headers=students_admin_headers,
        json={"verification_status": "verified", "full_name": "اسم محدّث"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "completion_status" in data
    assert "is_complete" in data
    assert data["full_name"] == "اسم محدّث"
    # verification_status محصّن: الحقل يُتجاهل بصمت فلا يُختَم الطالب كموثّق
    assert data["verification_status"] == "pending"
    assert data["completion_status"] == "incomplete"
    assert data["is_complete"] is False


def test_walkin_complete_tab_lists_completed_records(
    client, student_factory, super_headers
):
    """تبويب "مكتملة": status=complete يرجّع السجلات المكتملة فقط بحالة complete."""
    student_factory(
        "W-6001",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
    )
    student_factory(
        "W-6002",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.pending,
    )
    resp = client.get(
        "/admin/students/walkin-incomplete?status=complete&page=1&limit=20",
        headers=super_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["unique_code"] == "W-6001"
    assert data["items"][0]["status"] == "complete"


def test_walkin_incomplete_tab_excludes_completed_records(
    client, student_factory, super_headers
):
    """تبويب "غير مكتملة": ما يظهر السجل المكتمل."""
    student_factory(
        "W-6003",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
    )
    student_factory(
        "W-6004",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.pending,
    )
    resp = client.get(
        "/admin/students/walkin-incomplete?status=incomplete&page=1&limit=20",
        headers=super_headers,
    )
    assert resp.status_code == 200
    codes = [item["unique_code"] for item in resp.json()["items"]]
    assert codes == ["W-6004"]


def test_walkin_status_param_invalid_422(client, super_headers):
    """قيمة status غير مسموحة → 422."""
    resp = client.get(
        "/admin/students/walkin-incomplete?status=bogus", headers=super_headers
    )
    assert resp.status_code == 422


def test_walkin_completion_updates_stats_counters(
    client, student_factory, students_admin_headers, super_headers
):
    """إكمال سجل walk-in: العدد المكتمل يرتفع والمعلّق ينقص فوراً."""
    walkin = student_factory(
        "W-6005",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.pending,
    )
    before = client.get("/admin/students/stats", headers=super_headers).json()
    assert before["walkin_pending_count"] == 1
    assert before["walkin_completed_count"] == 0

    resp = client.patch(
        f"/admin/students/{walkin.id}",
        headers=students_admin_headers,
        json={
            "full_name": "طالب مكتمل",
            "contact_id": "0912345678",
            "birth_date": "2005-01-15",
            "bacc_year": 2024,
            "bacc_average": 88.0,
            "certificate_type": "literary",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"

    after = client.get("/admin/students/stats", headers=super_headers).json()
    assert after["walkin_pending_count"] == 0
    assert after["walkin_completed_count"] == 1

    completed = client.get(
        "/admin/students/walkin-incomplete?status=complete&page=1&limit=20",
        headers=super_headers,
    ).json()
    assert [item["unique_code"] for item in completed["items"]] == ["W-6005"]
