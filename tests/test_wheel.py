"""
اختبارات عجلة الحظ.

تركيز الملف على حاجتين:

1. **اختبارات الانحدار الأربعة** يلي لقيتهم بمراجعة الـSQL قبل التنفيذ. كل
   واحد بينهار لو رجعنا غلط بستatement من الـCTEs — وثلاثة منهم أخطاء كانت
   بتعدّي المراجعة العادية لأن SQL بيترجم وبيشتغل، بس بيطلع غلط.
2. **عقد الـAPI** — الأدوار، متطلبات كل قرار، الاستبعاد العالمي، وخصوصية
   شاشة الجمهور (اللي ما بتنكشف إلا بالاختبار).

الثبات الزمني: كل الاختبارات بتثبّت "الآن" لحظة بعد وقت التجميد عشان
`LEAST(now, freeze_at)` ترجّع freeze_at مهما كان وقت التشغيل الحقيقي. بدون
هاد التثبيت كانت نتائج التاب تعتمد على الساعة اللي بيتشغّل فيها الـsويت.

ملاحظة على البيانات: الـindexes الفريدة بـcheckins بتسمح بـcampus_entry واحد
بس لكل طالب باليوم، ومحاضرة وحدة بس لكل (طالب، محاضرة، يوم). فمسح المدى
اليومي بينعمل بسطر union (ما بيحسب نقاط) مو سطر campus_entry تاني.
"""

from datetime import datetime, time, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app import time_utils
from app.event_days import EVENT_DAYS
from app.models import (
    ActivityType,
    Checkin,
    Lecture,
    UnionSection,
    WheelDecision,
    WheelDraw,
    WheelDrawStatus,
    WheelExclusion,
    WheelFreezeAudit,
    WheelSettings,
    WheelTab,
)
from app.routers.points import point_service
from app.routers.wheel import wheel_service

WED = EVENT_DAYS["wed"]
THU = EVENT_DAYS["thu"]
SAT = EVENT_DAYS["sat"]
# يوم خارج أيام الفعالية: بيحسب بالنقاط (مثل point_service) وما بيحسب بالمدى.
TUE_BEFORE_EVENT = WED - timedelta(days=1)

FREEZE_DEFAULT = datetime.combine(SAT, time(15, 30))
# تثبيت "الآن" بعد التجميد بـ15 دقيقة: LEAST(now, freeze) = freeze.
NOW_AFTER_FREEZE = FREEZE_DEFAULT + timedelta(minutes=15)

# مفتاح اليوم الأحد: 08:00 → 15:00 = 7 ساعات = 420 دقيقة
WED_SPAN_MINUTES = 420


def _at(day, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute))


@pytest.fixture(autouse=True)
def _pin_now(monkeypatch):
    """يثبّت now_naive() وdefault_freeze_at() — كل الاختبارات حتمية زمنياً."""
    monkeypatch.setattr(time_utils, "now_naive", lambda: NOW_AFTER_FREEZE)
    monkeypatch.setattr(wheel_service, "default_freeze_at", lambda: FREEZE_DEFAULT)


@pytest.fixture
def add_checkin(db):
    """ضيف حضور لطالب. الـindexes الفريدة بتمنع تكرار النوع نفسه باليوم."""

    def _add(
        student,
        when: datetime,
        activity_type: ActivityType = ActivityType.campus_entry,
        lecture_name: Lecture | None = None,
        union_section: UnionSection | None = None,
    ) -> Checkin:
        checkin = Checkin(
            student_id=student.id,
            activity_type=activity_type,
            checked_in_at=when,
            lecture_name=lecture_name,
            union_section=union_section,
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)
        return checkin

    return _add


@pytest.fixture
def freeze_settings(db):
    """صف الإعدادات بالوقت الافتراضي (السبت 3:30)."""
    settings = WheelSettings(id=wheel_service.SETTINGS_ROW_ID, freeze_at=FREEZE_DEFAULT)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def _eligible_student(
    student,
    add_checkin,
    *,
    lectures: int = 0,
    wednesday_span: bool = True,
):
    """
    طالب مؤهل: دخل في الثلاثة أيام + محاضرات + (اختياري) مدى ليوم الأربعاء.

    لازم يدخل السبت وإلا بيتشال من كل التابات ببوابة السبت.
    """
    add_checkin(student, _at(WED, 8, 0))
    add_checkin(student, _at(THU, 9, 0))
    add_checkin(student, _at(SAT, 10, 0))
    if wednesday_span:
        # سطر union بيطيل مدى الأربعاء (08:00 → 15:00) بدون ما يضيف نقاط.
        add_checkin(
            student,
            _at(WED, 15, 0),
            activity_type=ActivityType.union,
            union_section=UnionSection.central,
        )
    for i in range(lectures):
        add_checkin(
            student,
            _at(THU, 11, i),
            activity_type=ActivityType.lecture,
            lecture_name=Lecture(f"lecture_{i + 1}"),
        )
    return student


def _row(rows, unique_code):
    return next(row for row in rows if row["unique_code"] == unique_code)


def _codes(db, tab, freeze=FREEZE_DEFAULT):
    return [r["unique_code"] for r in wheel_service.pool_rows(db, tab, freeze)]


# ═══════════════════════════════════════════════════════════════════════════
# اختبارات انحدار الـSQL الأربعة (من مراجعة ما قبل التنفيذ)
# ═══════════════════════════════════════════════════════════════════════════


def test_nulls_do_not_sort_first_when_activity_is_after_freeze(
    db, student_factory, add_checkin
):
    """
    انحدار #1 (HIGH): طالب نشاطه كله بعد التجميد.

    بيعدّي من بوابة السبت (اللي مش مجمّدة)، بس أرقامه بتطلع NULL من
    المعادلات لو ما تجمّعت بـcoalesce. وPostgreSQL بيحطّ NULLs أولاً بـ
    ORDER BY ... DESC، فالطالب الفارغ كان بيطلع **بمقدمة** ترتيب الجائزة
    الثالثة والنهائية.
    """
    _eligible_student(student_factory("R-0001", full_name="محضر كامل"), add_checkin)
    late = student_factory("R-0002", full_name="دخل بعد التجميد")
    add_checkin(late, _at(SAT, 16, 0))

    rows = wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT)
    codes = [row["unique_code"] for row in rows]
    assert codes.index("R-0001") < codes.index("R-0002"), (
        "الطالب اللي نشاطه بعد التجميد رتّب قبل المحضر الكامل"
    )
    # وبقيت أرقامه صريحة مو NULL
    late_row = _row(rows, "R-0002")
    assert late_row["freeze_points"] == 0
    assert late_row["raw_lectures"] == 0
    assert late_row["max_span_minutes"] == 0


def test_span_respects_a_lowered_freeze(db, student_factory, add_checkin):
    """
    انحدار #2 (MEDIUM): استعلام المدى كان يتجاهل freeze_at.

    كان بفلتر بس على وقت اليوم ([08:00، 16:00))، فحضور الأربعاء 15:00 كان
    بينحسب حتى لو الـadmin نزّل التجميد للخميس 10:00 — أي قبل بداية
    الج Saturday أصلاً.
    """
    student = _eligible_student(student_factory("R-0003"), add_checkin)

    at_default = _row(
        wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT), "R-0003"
    )
    assert at_default["max_span_minutes"] == WED_SPAN_MINUTES

    # التجميدiannزل للخميس 10:00: سطر الأربعاء 15:00 بيستبعد، فبWednesday
    # يبقى سطر واحد (08:00) والمدى = 0.
    lowered = _row(
        wheel_service.pool_rows(db, WheelTab.third_prize, _at(THU, 10, 0)),
        "R-0003",
    )
    assert lowered["max_span_minutes"] == 0


def test_wheel_points_match_point_service_for_off_event_day_checkin(
    db, student_factory, add_checkin
):
    """
    انحدار #3 (MEDIUM): نقاط العجلة كانت تنحرف عن نقطة point_service.

    كان بفلتر `day IN (أيام الفعالية)` على الـCTE اللي بتحسب النقاط، بينما
    point_service بiscount campus_entry على **كل** الأيام. طالب دخل يوم مش
    فعالية كان نقاطه أعلى بالنظام وأقل بالعجلة — وده بيكسر ترتيب الجائزة
    الثالثة/النهائية لأن النقاط معيار كسر تعادل.
    """
    student = student_factory("R-0004")
    add_checkin(student, _at(TUE_BEFORE_EVENT, 10, 0))  # يوم خارج الفعالية
    _eligible_student(student, add_checkin, lectures=2)

    expected = point_service._calculate_points_for_student_id(db, student.id)
    # 4 أيام دخول (الثلاثة + الثلاثاء) = 20، + محاضرتين = 20
    assert expected == 40, "نقطة النظام تغيّرت — حدّث الاختبار مو الكود"

    row = _row(
        wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT), "R-0004"
    )
    assert row["freeze_points"] == expected


def test_span_is_measured_within_a_single_day(
    db, student_factory, add_checkin
):
    """
    انحدار #4 (LOW): طول المدى محسوب بأيام الفعالية وبوحدة زمنية واضحة.

    المدى = أطول فترة بين أول وآخر حضور **بنفس اليوم**، مش بين أول يوم
    وآخر يوم. وسطر الثلاثاء 08:00 برّا أيام الفعالية ما بيعدّي أبداً.
    """
    student = student_factory("R-0005")
    _eligible_student(student, add_checkin)
    add_checkin(student, _at(TUE_BEFORE_EVENT, 8, 0))

    row = _row(
        wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT), "R-0005"
    )
    assert row["max_span_minutes"] == WED_SPAN_MINUTES


def test_lecture_daily_cap_matches_point_service(
    db, student_factory, add_checkin
):
    """سقف 3 محاضرات باليوم واحد — نفس قاعدة point_service. 5 محاضرات = 3."""
    student = student_factory("R-0006")
    add_checkin(student, _at(WED, 8, 0))
    add_checkin(student, _at(THU, 9, 0))
    add_checkin(student, _at(SAT, 10, 0))
    for i in range(5):
        add_checkin(
            student,
            _at(WED, 10, i),
            activity_type=ActivityType.lecture,
            lecture_name=Lecture(f"lecture_{i + 1}"),
        )

    expected = point_service._calculate_points_for_student_id(db, student.id)
    # 3 أيام دخول = 15، + سقف 3 محاضرات = 30
    assert expected == 45

    row = _row(
        wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT), "R-0006"
    )
    # raw_lectures بتعدّ كل المحاضرات (5)، والنقاط بتقبل السقف.
    assert row["freeze_points"] == expected
    assert row["raw_lectures"] == 5


def test_saturday_gate_excludes_students_without_saturday_entry(
    db, student_factory, add_checkin
):
    """بوابة السبت مش مجمّدة — بس لازم موجودة. من ما دخل السبت برّا."""
    no_saturday = student_factory("R-0007")
    add_checkin(no_saturday, _at(WED, 8, 0))
    add_checkin(
        no_saturday,
        _at(WED, 15, 0),
        activity_type=ActivityType.union,
        union_section=UnionSection.central,
    )
    add_checkin(no_saturday, _at(THU, 9, 0))

    with_saturday = student_factory("R-0008")
    add_checkin(with_saturday, _at(SAT, 10, 0))
    add_checkin(
        with_saturday,
        _at(SAT, 15, 0),
        activity_type=ActivityType.union,
        union_section=UnionSection.central,
    )

    codes = _codes(db, WheelTab.third_prize)
    assert "R-0007" not in codes
    assert "R-0008" in codes


def test_final_prize_is_top_50_of_the_third_prize_ordering(
    db, student_factory, add_checkin
):
    """الجائزة النهائية = أول 50 من **نفس** ترتيب الجائزة الثالثة."""
    third = wheel_service.pool_rows(db, WheelTab.third_prize, FREEZE_DEFAULT)
    final = wheel_service.pool_rows(db, WheelTab.final_prize, FREEZE_DEFAULT)

    assert [r["unique_code"] for r in final] == [
        r["unique_code"] for r in third[:50]
    ]
    assert [r["rank"] for r in final] == list(range(1, len(final) + 1))


def test_top_n_caps_the_pool(db, student_factory, add_checkin):
    """سقف 100 للثالثة و50 للنهائية — مُطبّق بالاستعلام لا بالعرض."""
    assert wheel_service.count_pool(db, WheelTab.third_prize, FREEZE_DEFAULT) <= 100
    assert wheel_service.count_pool(db, WheelTab.final_prize, FREEZE_DEFAULT) <= 50


def test_first_and_second_prize_point_gates(
    db, student_factory, add_checkin
):
    """تابات النقاط: 15 و40 — والبوابة مشتركة مع شرط السبت."""
    _eligible_student(student_factory("R-0010"), add_checkin)  # 15 نقطة
    _eligible_student(student_factory("R-0011"), add_checkin, lectures=3)  # 45

    assert set(_codes(db, WheelTab.first_prize)) == {"R-0010", "R-0011"}
    assert set(_codes(db, WheelTab.second_prize)) == {"R-0011"}


def test_tiebreak_is_deterministic_by_unique_code(
    db, student_factory, add_checkin
):
    """كسر التعادل بـunique_code تصاعدي — نفس المدخلات = نفس الترتيب دائماً."""
    codes = ["R-0050", "R-0020", "R-0040", "R-0030"]
    for code in codes:
        _eligible_student(student_factory(code), add_checkin)

    first = _codes(db, WheelTab.third_prize)
    assert first == sorted(codes)
    assert _codes(db, WheelTab.third_prize) == first


# ═══════════════════════════════════════════════════════════════════════════
# الأدوار وخصوصية الجمهور
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "path",
    [
        "/admin/wheel/tabs",
        "/admin/wheel/settings",
        "/admin/wheel/archive",
        "/admin/wheel/ceremony-snapshot",
    ],
)
def test_admin_endpoints_reject_non_super_admin(
    client, students_admin_headers, path
):
    resp = client.get(path, headers=students_admin_headers)
    assert resp.status_code == 403, f"{path} مرر لـstudents_admin"


def test_admin_endpoints_reject_anonymous(client):
    assert client.get("/admin/wheel/tabs").status_code == 401


def test_ceremony_snapshot_rejects_non_super_admin(client, students_admin_headers):
    resp = client.get(
        "/admin/wheel/ceremony-snapshot", headers=students_admin_headers
    )
    assert resp.status_code == 403


def test_draw_endpoint_rejects_non_super_admin(
    client, students_admin_headers, freeze_settings, student_factory, add_checkin
):
    _eligible_student(student_factory("R-0020"), add_checkin, lectures=3)
    resp = client.post(
        "/admin/wheel/draws",
        json={"tab": "first_prize"},
        headers=students_admin_headers,
    )
    assert resp.status_code == 403


def test_live_endpoint_is_open_to_any_authenticated_account(
    client, college_staff_headers, gate_scanner_headers
):
    """
    شاشة الجمهور مش محمية بـsuper_admin — أي حساب مسجّل يقدر يشوفها.
    (قرار موثّق: دور الجمهور متجاوز عمداً.)
    """
    for headers in (college_staff_headers, gate_scanner_headers):
        assert client.get("/wheel/live", headers=headers).status_code == 200


def test_live_endpoint_rejects_anonymous(client):
    assert client.get("/wheel/live").status_code == 401


def test_live_response_exposes_only_six_fields(client, super_headers):
    """
    خصوصية الجمهور مفروضة بالـschema: ست حقول بس. لو حدا ضاف freeze_at
    أو counts أو أسماء مؤهلين، هاد الاختبار بينهار.
    """
    resp = client.get("/wheel/live", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {
        "draw_id",
        "tab",
        "tab_label",
        "winner_name",
        "winner_code",
        "revealed_at",
    }
    # كل القيم null لما ما في شي معروض
    assert all(value is None for value in body.values())


# ═══════════════════════════════════════════════════════════════════════════
# الإعدادات والتجميد
# ═══════════════════════════════════════════════════════════════════════════


def test_get_settings_does_not_create_a_row(client, super_headers, db):
    """القراءة ما بتكتب: ما ينشأ صف wheel_settings لمجرد فتح اللوحة."""
    resp = client.get("/admin/wheel/settings", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["freeze_at"] == FREEZE_DEFAULT.isoformat()
    assert body["is_default"] is True
    assert body["frozen"] is True  # الآن مثبّت بعد التجميد
    assert db.query(WheelSettings).count() == 0


def test_tabs_endpoint_reports_criteria_and_counts(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    _eligible_student(student_factory("R-0030"), add_checkin)
    _eligible_student(student_factory("R-0031"), add_checkin, lectures=3)

    resp = client.get("/admin/wheel/tabs", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    tabs = {tab["tab"]: tab for tab in body["tabs"]}
    assert list(tabs) == [
        "first_prize",
        "second_prize",
        "third_prize",
        "final_prize",
    ]
    assert tabs["first_prize"]["eligible_count"] == 2
    assert tabs["second_prize"]["eligible_count"] == 1
    assert "دخل من بوابة الجامعة يوم السبت" in tabs["first_prize"]["criteria"]
    # القاعدة كاملة بأربع مفاتيح: القبول يلزمه التحقق اليدوي، والرفض يلزمه
    # التأكيد. مفتاحي "الرفض ما بيحتاج تحقق" و"القبول ما بيحتاج تأكيد"
    # موجودين عمداً لأن الفرونت بيقرأ هالمتطلبات بدل ما يخمّنها.
    assert body["decision_requirements"] == {
        "accept_requires_presence_verified": True,
        "accept_requires_confirmation": False,
        "reject_requires_presence_verified": False,
        "reject_requires_confirmation": True,
    }


def test_update_freeze_persists_audit_row(
    client, super_headers, db, seeded_accounts, freeze_settings
):
    new_freeze = _at(SAT, 14, 0)
    resp = client.put(
        "/admin/wheel/settings",
        json={"freeze_at": new_freeze.isoformat(), "reason": "نقل السحب أبكر"},
        headers=super_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["freeze_at"] == new_freeze.isoformat()
    assert resp.json()["is_default"] is False

    # الطلب بيعدّي على جلسة ثانية (Depends(get_db))، فجلسة الاختبار كااشة
    # بتخبّئ الصف من قبل التعديل. expire_all بتجبرها تقرأ من القاعدة.
    db.expire_all()
    assert db.query(WheelSettings).one().freeze_at == new_freeze
    audit = db.query(WheelFreezeAudit).one()
    assert audit.freeze_at == new_freeze
    assert audit.previous_freeze_at == FREEZE_DEFAULT
    assert audit.reason == "نقل السحب أبكر"
    assert audit.changed_by == seeded_accounts["super_admin"].id


@pytest.mark.parametrize(
    "bad_freeze",
    [
        _at(WED - timedelta(days=1), 12, 0),  # قبل أول يوم فعالية
        _at(SAT, 17, 0),  # بعد وقت السحب
    ],
)
def test_out_of_range_freeze_is_rejected(
    client, super_headers, freeze_settings, bad_freeze
):
    resp = client.put(
        "/admin/wheel/settings",
        json={"freeze_at": bad_freeze.isoformat()},
        headers=super_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "wheel_freeze_out_of_range"


def test_prospective_preview_does_not_persist(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """المعاينة تحسب الأثر بدون حفظ — freeze_at ما بيتغيّر."""
    _eligible_student(student_factory("R-0040"), add_checkin, lectures=3)
    earlier = _at(THU, 10, 0)

    resp = client.get(
        "/admin/wheel/settings",
        params={"prospective_freeze_at": earlier.isoformat()},
        headers=super_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["freeze_at"] == FREEZE_DEFAULT.isoformat()
    assert body["preview"]["prospective_freeze_at"] == earlier.isoformat()
    # محاضرات 11:00 بالخميس بتستبعد بمعاينة 10:00، فالعدد ما بيزيد
    deltas = {item["tab"]: item["delta"] for item in body["preview"]["tabs"]}
    assert deltas["first_prize"] <= 0
    assert db.query(WheelSettings).one().freeze_at == FREEZE_DEFAULT


def test_malformed_prospective_is_400(client, super_headers, freeze_settings):
    resp = client.get(
        "/admin/wheel/settings",
        params={"prospective_freeze_at": "مش تاريخ"},
        headers=super_headers,
    )
    assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# السحب والقرار
# ═══════════════════════════════════════════════════════════════════════════


def test_empty_pool_is_409(client, super_headers, freeze_settings):
    resp = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "wheel_tab_empty"


def test_draw_then_decide_accepts(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    student = _eligible_student(
        student_factory("R-0055", full_name="مُقبل عليه"), add_checkin
    )
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    )
    assert draw.status_code == 200
    body = draw.json()
    assert body["status"] == "revealed"
    assert body["replayed"] is False
    assert body["unique_code"] == "R-0055"
    assert body["tab_label"] == "الجائزة الأولى"

    decision = client.post(
        f"/admin/wheel/draws/{body['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "accepted"
    assert decision.json()["presence_verified"] is True
    assert decision.json()["excluded_globally"] is True

    stored = db.query(WheelDraw).one()
    assert stored.status == WheelDrawStatus.accepted
    assert stored.student_id == student.id
    assert stored.presence_verified is True
    assert stored.decided_at is not None
    assert db.query(WheelExclusion).one().student_id == student.id


def test_accept_requires_presence_verification(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    _eligible_student(student_factory("R-0056"), add_checkin)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()

    resp = client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": False},
        headers=super_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "wheel_presence_verification_required"
    # والاسم ضل معروض والقرار ما انحفظ
    assert db.query(WheelDraw).one().status == WheelDrawStatus.revealed
    assert db.query(WheelExclusion).count() == 0


def test_reject_requires_explicit_confirmation(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    _eligible_student(student_factory("R-0057"), add_checkin)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()

    resp = client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "rejected", "confirmed": False},
        headers=super_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "wheel_reject_confirmation_required"
    assert db.query(WheelExclusion).count() == 0


def test_reject_does_not_require_presence_verification(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """الرفض ما بيحتاج تحقق حضور — بس بيحتاج تأكيد صريح."""
    _eligible_student(student_factory("R-0058"), add_checkin)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()

    resp = client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "rejected", "confirmed": True},
        headers=super_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    # وبيتسجل إنه مرّ بدون تحقق يدوي (للتدقيق)
    assert db.query(WheelDraw).one().presence_verified is False


def test_accept_does_not_require_confirmation(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    """القبول ما بيحتاج confirmed — التحقق اليدوي هو المطلوب الوحيد."""
    _eligible_student(student_factory("R-0059"), add_checkin)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()

    resp = client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True, "confirmed": False},
        headers=super_headers,
    )
    assert resp.status_code == 200


def test_decision_twice_is_409(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    _eligible_student(student_factory("R-0060"), add_checkin)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    payload = {"decision": "accepted", "presence_verified": True}

    assert client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json=payload,
        headers=super_headers,
    ).status_code == 200
    replay = client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json=payload,
        headers=super_headers,
    )
    assert replay.status_code == 409
    assert replay.json()["error_code"] == "wheel_draw_already_decided"


def test_decision_on_missing_draw_is_404(client, super_headers):
    resp = client.post(
        "/admin/wheel/draws/999999/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "wheel_draw_not_found"


def test_second_draw_blocked_while_a_name_is_pending(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """ضغطة مزدوجة على الزر: في اسم معروض بنفس التاب وبانتظار قرار."""
    _eligible_student(student_factory("R-0061"), add_checkin)
    _eligible_student(student_factory("R-0062"), add_checkin)

    assert client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).status_code == 200
    second = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    )
    assert second.status_code == 409
    assert second.json()["error_code"] == "wheel_pending_draw_exists"
    assert db.query(WheelDraw).count() == 1


def test_pending_guard_is_per_tab_not_global(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    """التابات مستقلة — اسم معروض بتاب ما بيمنع سحب بتاب تاني."""
    _eligible_student(student_factory("R-0063"), add_checkin, lectures=3)

    assert client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).status_code == 200
    assert client.post(
        "/admin/wheel/draws", json={"tab": "third_prize"}, headers=super_headers
    ).status_code == 200


def test_idempotency_key_replays_the_same_draw(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """نفس المفتاح = نفس السحبة (انقطاع شبكة بعد ما القاعدة حفظت)."""
    _eligible_student(student_factory("R-0064"), add_checkin)
    _eligible_student(student_factory("R-0065"), add_checkin)
    key = "draw-first-prize-1"

    first = client.post(
        "/admin/wheel/draws",
        json={"tab": "first_prize", "idempotency_key": key},
        headers=super_headers,
    )
    assert first.status_code == 200
    assert first.json()["replayed"] is False

    replay = client.post(
        "/admin/wheel/draws",
        json={"tab": "first_prize", "idempotency_key": key},
        headers=super_headers,
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["draw_id"] == first.json()["draw_id"]
    assert db.query(WheelDraw).count() == 1


def test_draw_without_idempotency_key_allows_multiple_rows(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """بدون مفتاح، كل طلب = سحبة جديدة (بعد كل قرار)."""
    _eligible_student(student_factory("R-0066"), add_checkin)
    _eligible_student(student_factory("R-0067"), add_checkin)

    first = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{first['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )
    assert client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).status_code == 200
    assert db.query(WheelDraw).count() == 2


# ═══════════════════════════════════════════════════════════════════════════
# الاستبعاد العالمي
# ═══════════════════════════════════════════════════════════════════════════


def test_accepted_student_is_excluded_from_all_tabs(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """الاستبعاد عالمي: فائز الجائزة الأولى بيطلع من التانية والثالثة."""
    student = _eligible_student(student_factory("R-0070"), add_checkin, lectures=3)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )

    for tab in wheel_service.TAB_ORDER:
        assert wheel_service.count_pool(db, tab, FREEZE_DEFAULT) == 0, tab

    tabs = client.get("/admin/wheel/tabs", headers=super_headers).json()["tabs"]
    assert all(tab["eligible_count"] == 0 for tab in tabs)

    exclusion = db.query(WheelExclusion).one()
    assert exclusion.student_id == student.id
    assert exclusion.tab == WheelTab.first_prize
    assert exclusion.decision == WheelDecision.accepted
    assert exclusion.draw_id == draw["draw_id"]


def test_rejected_student_is_also_excluded_globally(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """الاستبعاد بيصير بعد **أي** قرار — حتى الرفض."""
    student = _eligible_student(student_factory("R-0071"), add_checkin, lectures=3)
    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "rejected", "confirmed": True},
        headers=super_headers,
    )

    assert wheel_service.count_pool(db, WheelTab.second_prize, FREEZE_DEFAULT) == 0
    exclusion = db.query(WheelExclusion).one()
    assert exclusion.student_id == student.id
    assert exclusion.decision == WheelDecision.rejected


def test_redraw_after_rejection_is_a_plain_new_request(
    client, super_headers, db, freeze_settings, student_factory, add_checkin
):
    """"أعد السحب" بعد رفض = طلب جديد عادي بلا endpoint خاص."""
    _eligible_student(student_factory("R-0072"), add_checkin)
    _eligible_student(student_factory("R-0073"), add_checkin)

    first = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{first['draw_id']}/decision",
        json={"decision": "rejected", "confirmed": True},
        headers=super_headers,
    )
    # التاب فاضي صار (الاثنين اتستبعدوا) — نضيف طالب ونعيد
    _eligible_student(student_factory("R-0074"), add_checkin)

    second = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    )
    assert second.status_code == 200
    assert second.json()["draw_id"] != first["draw_id"]
    assert second.json()["status"] == "revealed"


def test_exclusion_is_unique_per_student(
    db, seeded_accounts, student_factory, add_checkin
):
    """القيد الفريد على wheel_exclusions.student_id هو اللي بيفرض القاعدة."""
    student = _eligible_student(student_factory("R-0075"), add_checkin)
    draw = WheelDraw(
        tab=WheelTab.first_prize,
        student_id=student.id,
        status=WheelDrawStatus.accepted,
        freeze_at_snapshot=FREEZE_DEFAULT,
        presence_verified=True,
        created_by=seeded_accounts["super_admin"].id,
    )
    db.add(draw)
    db.commit()
    db.refresh(draw)

    db.add(
        WheelExclusion(
            student_id=student.id,
            tab=WheelTab.first_prize,
            decision=WheelDecision.accepted,
            draw_id=draw.id,
            decided_by=seeded_accounts["super_admin"].id,
        )
    )
    db.commit()

    db.add(
        WheelExclusion(
            student_id=student.id,
            tab=WheelTab.third_prize,
            decision=WheelDecision.rejected,
            draw_id=draw.id,
            decided_by=seeded_accounts["super_admin"].id,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ═══════════════════════════════════════════════════════════════════════════
# الأرشيف واللقطة والشاشة المباشرة
# ═══════════════════════════════════════════════════════════════════════════


def test_archive_lists_only_accepted_draws(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    """سجل الفائزين = status='accepted' بس. المرفوض ما بيطلع."""
    for code in ("R-0080", "R-0081", "R-0082"):
        _eligible_student(student_factory(code), add_checkin)

    accepted = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{accepted['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )
    rejected = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    client.post(
        f"/admin/wheel/draws/{rejected['draw_id']}/decision",
        json={"decision": "rejected", "confirmed": True},
        headers=super_headers,
    )

    archive = client.get("/admin/wheel/archive", headers=super_headers)
    assert archive.status_code == 200
    winners = archive.json()["winners"]
    assert len(winners) == 1
    assert winners[0]["draw_id"] == accepted["draw_id"]
    assert winners[0]["presence_verified"] is True


def test_ceremony_snapshot_has_names_for_manual_verification(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    """لقطة الحفل فيها الأسماء — هذا سبب وجودها: التحقق اليدوي."""
    _eligible_student(
        student_factory("R-0090", full_name="طالب للتحقق"), add_checkin, lectures=3
    )
    resp = client.get("/admin/wheel/ceremony-snapshot", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["frozen"] is True  # الآن مثبّت بعد التجميد
    assert body["effective_freeze_at"] == FREEZE_DEFAULT.isoformat()

    names = [
        cand["full_name"] for tab in body["tabs"] for cand in tab["winners"]
    ]
    assert "طالب للتحقق" in names

    # والنهائية = أول 50 من ترتيب الثالثة
    third = next(t for t in body["tabs"] if t["tab"] == "third_prize")
    final = next(t for t in body["tabs"] if t["tab"] == "final_prize")
    assert [c["unique_code"] for c in final["winners"]] == [
        c["unique_code"] for c in third["winners"][:50]
    ]


def test_live_shows_then_clears_the_pending_winner(
    client, super_headers, freeze_settings, student_factory, add_checkin
):
    """الاسم على الشاشة يتحدّث فور السحب ويتمسح فور القرار."""
    _eligible_student(
        student_factory("R-0100", full_name="اسم على الشاشة"), add_checkin
    )
    empty = client.get("/wheel/live", headers=super_headers).json()
    assert empty["winner_name"] is None
    assert empty["draw_id"] is None

    draw = client.post(
        "/admin/wheel/draws", json={"tab": "first_prize"}, headers=super_headers
    ).json()
    live = client.get("/wheel/live", headers=super_headers).json()
    assert live["winner_name"] == "اسم على الشاشة"
    assert live["winner_code"] == "R-0100"
    assert live["tab"] == "first_prize"
    assert live["tab_label"] == "الجائزة الأولى"
    assert live["draw_id"] == draw["draw_id"]

    client.post(
        f"/admin/wheel/draws/{draw['draw_id']}/decision",
        json={"decision": "accepted", "presence_verified": True},
        headers=super_headers,
    )
    cleared = client.get("/wheel/live", headers=super_headers).json()
    assert cleared["draw_id"] is None
    assert cleared["winner_name"] is None
