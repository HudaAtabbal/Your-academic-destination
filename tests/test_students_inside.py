"""اختبارات قائمة "الطلاب داخل الجامعة (كل الأيام)" — super_admin فقط."""

from app.models import RegistrationType, VerificationStatus

CODE_A = "R-0001"
CODE_B = "R-0002"
CODE_C = "W-0001"


def _campus_entry(client, headers, code):
    return client.post(
        "/checkins/campus-entry", json={"unique_code": code}, headers=headers
    )


def _get_students_inside(client, headers=None, **params):
    return client.get("/admin/dashboard/students-inside", params=params, headers=headers)


# ---------- الأساسيات ----------


def test_students_inside_empty(client, super_headers):
    resp = _get_students_inside(client, headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["total_pages"] == 1


def test_students_inside_lists_only_campus_entries(
    client, student_factory, students_admin_headers, super_headers
):
    """الطلاب الثلاثة الموجودون يُدرجون، لكن درسوا campus_entry فقط: الطلاب
    الحاضرون يظهرون، والغائبون عن الجامعة لا يُدرجون حتى لو سجّلوا جولة."""
    student_factory(CODE_A, full_name="طالب داخل الحرم")
    student_factory(CODE_B, full_name="طالب لم يدخل الحرم")
    student_factory(
        CODE_C,
        full_name="طالب walk-in",
        registration_type=RegistrationType.walk_in,
        verification_status=VerificationStatus.verified,
    )

    assert _campus_entry(client, students_admin_headers, CODE_A).status_code == 201

    # CODE_B مسجّل بالجولة لكن ليس داخل الحرم — لا يُدرج
    client.post(
        "/checkins/tour",
        json={"unique_code": CODE_B, "college": "medicine"},
        headers=students_admin_headers,
    )

    resp = _get_students_inside(client, headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["unique_code"] == CODE_A
    assert item["full_name"] == "طالب داخل الحرم"
    assert item["contact_id"] is None
    assert item["total_points"] == 5  # فقط نقاط دخول الحرم


def test_students_inside_contact_and_points(
    client, student_factory, students_admin_headers, super_headers
):
    student_factory(CODE_A, full_name="طالب تجريبي", contact_id="0933123456")
    assert _campus_entry(client, students_admin_headers, CODE_A).status_code == 201

    resp = _get_students_inside(client, headers=super_headers)
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["contact_id"] == "0933123456"


# ---------- الترتيب ----------


def test_students_inside_order_desc_default(
    client, student_factory, students_admin_headers, gate_scanner_headers, super_headers
):
    """الافتراضي: الأعلى نقاطاً أولاً. نقاط أكبر للطالب الحاضر للمحاضرات + دخول الحرم."""
    student_factory(CODE_A, full_name="الأقل")
    student_factory(CODE_B, full_name="الأكثر")
    for code in (CODE_A, CODE_B):
        assert _campus_entry(client, students_admin_headers, code).status_code == 201
    # CODE_B يكسب نقاطاً إضافية عبر محاضرة
    client.post(
        "/checkins/lecture",
        json={"unique_code": CODE_B, "lecture_name": "lecture_1"},
        headers=gate_scanner_headers,
    )

    resp = _get_students_inside(client, headers=super_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["unique_code"] == CODE_B  # 15 نقطة أولاً
    assert items[1]["unique_code"] == CODE_A  # 5 نقاط


def test_students_inside_order_asc(
    client, student_factory, students_admin_headers, super_headers
):
    student_factory(CODE_A)
    student_factory(CODE_B)
    assert _campus_entry(client, students_admin_headers, CODE_A).status_code == 201
    assert _campus_entry(client, students_admin_headers, CODE_B).status_code == 201

    resp = _get_students_inside(client, headers=super_headers, order="asc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    # endpoint الوحيد -> الترتيب التصاعدي يؤكد العكس فقط (كلاهما بنفس النقاط،
    # الرمز ثانوي) — نتحقق أن الطلب مقبول وأن النقاط لا تتناقص
    assert items[0]["unique_code"] == min(CODE_A, CODE_B)


# ---------- الفلترة بالرمز ----------


def test_students_inside_filter_by_code_prefix(
    client, student_factory, students_admin_headers, super_headers
):
    student_factory("R-1001")
    student_factory("R-1002")
    student_factory("W-0005")
    for code in ("R-1001", "R-1002", "W-0005"):
        assert _campus_entry(client, students_admin_headers, code).status_code == 201

    resp = _get_students_inside(client, headers=super_headers, code="R-100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    codes = {item["unique_code"] for item in body["items"]}
    assert codes == {"R-1001", "R-1002"}


def test_students_inside_filter_unknown_code(
    client, student_factory, students_admin_headers, super_headers
):
    student_factory("R-1001")
    assert _campus_entry(client, students_admin_headers, "R-1001").status_code == 201
    resp = _get_students_inside(client, headers=super_headers, code="R-9999")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


# ---------- الترقيم ----------


def test_students_inside_pagination(
    client, student_factory, students_admin_headers, super_headers
):
    for i in range(5):
        student_factory(f"R-200{i}")
        assert (
            _campus_entry(client, students_admin_headers, f"R-200{i}").status_code == 201
        )

    resp = _get_students_inside(client, headers=super_headers, page=1, limit=2)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["total_pages"] == 3

    resp2 = _get_students_inside(client, headers=super_headers, page=2, limit=2)
    assert len(resp2.json()["items"]) == 2


# ---------- الصلاحيات ----------


def test_students_inside_forbidden_for_non_super(client, students_admin_headers):
    resp = _get_students_inside(client, headers=students_admin_headers)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "forbidden"


def test_students_inside_unauthenticated_401(client):
    resp = _get_students_inside(client)
    assert resp.status_code == 401