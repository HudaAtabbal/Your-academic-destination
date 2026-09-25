"""اختبارات نهايات v2 للوحة المدير العام — عدادات الأيام، حضور، ساعات الذروة، المتميزون."""

from datetime import datetime, timedelta

from app import time_utils
from app.event_days import EVENT_DAYS
from app.models import (
    ActivityType,
    Booking,
    BookingType,
    Checkin,
    Faculty,
    RegistrationType,
    Student,
    StudentStatus,
    UnionSection,
    VerificationStatus,
)


def _phone(suffix: int) -> str:
    return f"09{suffix:08d}"


def _day_start(day_key: str) -> datetime:
    return datetime.combine(EVENT_DAYS[day_key], datetime.min.time())


def _checkin_for_day(
    db,
    student,
    activity_type: ActivityType,
    day_key: str,
    *,
    hour: int = 10,
    minute: int = 0,
    college: Faculty | None = None,
    lecture_name=None,
    union_section: UnionSection | None = None,
):
    """ينشئ Checkin بتاريخ ضمن يوم فعالية محدد (بتوقيت سوريا)."""
    at = _day_start(day_key) + timedelta(hours=hour, minutes=minute)
    checkin = Checkin(
        student_id=student.id,
        activity_type=activity_type,
        college=college,
        lecture_name=lecture_name,
        union_section=union_section,
        checked_in_at=at,
    )
    db.add(checkin)
    return checkin


def _tour_booking(
    db,
    student,
    day_key: str,
    college: Faculty,
    *,
    hour: int = 9,
    minute: int = 0,
):
    """ينشئ Booking جولة بتاريخ ضمن يوم فعالية محدد (بتوقيت سوريا)."""
    booking = Booking(
        student_id=student.id,
        booking_type=BookingType.tour,
        college=college,
        booked_at=_day_start(day_key) + timedelta(hours=hour, minutes=minute),
    )
    db.add(booking)
    return booking


def _make_student(db, code: str, full_name: str = "طالب تجريبي"):
    student = Student(
        unique_code=code,
        full_name=full_name,
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# ---------------------------------------------------------------------------
# عدادات مفلترة باليوم (قسم 3.1)
# ---------------------------------------------------------------------------


def test_stats_consultations_count_from_bookings(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    s3 = _make_student(db, "R-0003")
    # s1: حجز استشارة + شيك استشارة (الاثنين موجودان — يُحسب مرة من الحجز)
    # s2: شيك استشارة بلا حجز → لا يُحسب
    # s3: لا شيء
    db.add_all(
        [
            Booking(
                student_id=s1.id,
                booking_type=BookingType.consultation,
                college=Faculty.medicine,
                booked_at=_day_start("wed") + timedelta(hours=10),
            ),
            _checkin_for_day(db, s1, ActivityType.consultation, "thu", hour=11),
            _checkin_for_day(db, s2, ActivityType.consultation, "thu", hour=12),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/stats", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    # حجز استشارة واحد فقط — شيك بلا حجز لا يُعدّ
    assert body["total_consultations"] == 1


def test_students_inside_count_all_days(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    # s1 دخل يومين (أربعاء + خميس) — distinct على مستوى الطالب
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed"),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "thu"),
            _checkin_for_day(db, s2, ActivityType.campus_entry, "wed"),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/students-inside-count?day=all", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["day"] == "all"
    assert body["count"] == 2  # نفس students_inside_all_days (تراكمي)
    assert "generated_at" in body

    # كل يوم على حدة — s1 بكل يوم، s2 بأربعاء فقط
    wed = client.get("/admin/dashboard/students-inside-count?day=wed", headers=super_headers).json()
    assert wed["count"] == 2
    thu = client.get("/admin/dashboard/students-inside-count?day=thu", headers=super_headers).json()
    assert thu["count"] == 1
    sat = client.get("/admin/dashboard/students-inside-count?day=sat", headers=super_headers).json()
    assert sat["count"] == 0


def test_students_inside_count_unknown_day_422(client, super_headers):
    resp = client.get("/admin/dashboard/students-inside-count?day=mon", headers=super_headers)
    assert resp.status_code == 422


def test_game_scans_day_filtered(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    s3 = _make_student(db, "R-0003")
    # فهرس unique_game_checkin يسمح بمسحة غرفة واحدة لكل طالب — لذلك نستخدم
    # ثلاث طلاب، طالب واحد فقط بيومين غير ممكن.
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.game, "wed"),
            _checkin_for_day(db, s2, ActivityType.game, "thu"),
            _checkin_for_day(db, s3, ActivityType.game, "wed"),
        ]
    )
    db.commit()

    all_resp = client.get("/admin/dashboard/game-scans?day=all", headers=super_headers).json()
    assert all_resp["count"] == 3
    wed = client.get("/admin/dashboard/game-scans?day=wed", headers=super_headers).json()
    assert wed["count"] == 2
    thu = client.get("/admin/dashboard/game-scans?day=thu", headers=super_headers).json()
    assert thu["count"] == 1
    sat = client.get("/admin/dashboard/game-scans?day=sat", headers=super_headers).json()
    assert sat["count"] == 0


def test_college_visits_day_filtered(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    s3 = _make_student(db, "R-0003")
    # s1: حجز جولة civil_engineering يوم أربعاء + شيك جولة civil_engineering يوم خميس (بلا حجز → لا يُحتسب)
    # s2: حجز جولة civil_engineering يوم خميس (مفترق حساب)
    # s3: حجز استشارة civil_engineering يوم خميس (نوع خاطئ → لا يُحتسب)
    db.add_all(
        [
            _tour_booking(db, s1, "wed", Faculty.civil_engineering, hour=9),
            _checkin_for_day(
                db, s1, ActivityType.tour, "thu", college=Faculty.civil_engineering
            ),
            _tour_booking(db, s2, "thu", Faculty.civil_engineering, hour=11),
            Booking(
                student_id=s3.id,
                booking_type=BookingType.consultation,
                college=Faculty.civil_engineering,
                booked_at=_day_start("thu") + timedelta(hours=12),
            ),
        ]
    )
    db.commit()

    wed = client.get("/admin/dashboard/college-visits?day=wed", headers=super_headers).json()
    eng = next(i for i in wed["items"] if i["college"] == "civil_engineering")
    assert eng["count"] == 1
    assert wed["total"] >= 1

    thu = client.get("/admin/dashboard/college-visits?day=thu", headers=super_headers).json()
    eng_thu = next(i for i in thu["items"] if i["college"] == "civil_engineering")
    # فقط حجز s2 — شيك s1 بلا حجز واستشارة s3 لا يُحتسبان
    assert eng_thu["count"] == 1

    all_resp = client.get("/admin/dashboard/college-visits?day=all", headers=super_headers).json()
    eng_all = next(i for i in all_resp["items"] if i["college"] == "civil_engineering")
    assert eng_all["count"] == 2


def test_union_sections_day_filtered(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    db.add_all(
        [
            _checkin_for_day(
                db, s1, ActivityType.union, "wed", union_section=UnionSection.central
            ),
            _checkin_for_day(
                db, s1, ActivityType.union, "thu", union_section=UnionSection.major_guide
            ),
            _checkin_for_day(
                db, s2, ActivityType.union, "wed", union_section=UnionSection.central
            ),
        ]
    )
    db.commit()

    wed = client.get("/admin/dashboard/union-sections?day=wed", headers=super_headers).json()
    assert wed["total"] == 2
    by_section = {i["section"]: i["count"] for i in wed["items"]}
    assert by_section["central"] == 2
    assert by_section["major_guide"] == 0
    assert by_section["turkish_club"] == 0
    # الأقسام الثلاثة مدرجة دائماً
    assert [i["section"] for i in wed["items"]] == [
        "central",
        "major_guide",
        "turkish_club",
    ]

    thu = client.get("/admin/dashboard/union-sections?day=thu", headers=super_headers).json()
    assert thu["total"] == 1
    assert {i["section"] for i in thu["items"]} == {
        "central",
        "major_guide",
        "turkish_club",
    }


# ---------------------------------------------------------------------------
# حضور (قسم 3.2)
# ---------------------------------------------------------------------------


def test_presence_excludes_single_checkin_days(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    # s1: يوم أربعاء فيه مسحتان (09:00 و 11:00) → مدة 120 دقيقة
    #     يوم خميس فيه مسحة وحيدة → مستثناة
    # s2: يوم أربعاء فيه مسحتان (10:00 و 10:30) → مدة 30 دقيقة
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=9),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=11),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "thu", hour=9),
            _checkin_for_day(
                db, s2, ActivityType.campus_entry, "wed", hour=10
            ),
            _checkin_for_day(db, s2, ActivityType.consultation, "wed", hour=10, minute=30),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/presence", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["avg_minutes_all"] == 75  # (120 + 30) / 2
    per_day = {d["day"]: d for d in body["per_day"]}
    assert per_day["wed"]["students_counted"] == 2
    assert per_day["wed"]["avg_minutes"] == 75
    assert per_day["thu"]["students_counted"] == 0
    assert per_day["thu"]["avg_minutes"] == 0
    assert per_day["sat"]["students_counted"] == 0
    assert "generated_at" in body


def test_presence_frequency_buckets_sum_to_inside_all_days(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    s3 = _make_student(db, "R-0003")
    # s1: دخل الأيام الثلاثة
    # s2: دخل يومين (أربعاء + خميس)
    # s3: دخل يوم واحد (سبت)
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed"),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "thu"),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "sat"),
            _checkin_for_day(db, s2, ActivityType.campus_entry, "wed"),
            _checkin_for_day(db, s2, ActivityType.campus_entry, "thu"),
            _checkin_for_day(db, s3, ActivityType.campus_entry, "sat"),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/presence", headers=super_headers).json()
    freq = resp["frequency"]
    assert freq["one_day"] == 1
    assert freq["two_days"] == 1
    assert freq["all_days"] == 1
    assert freq["total"] == 3

    # مطابقة مع students_inside_all_days (داخلون من البوابة — هنا داخل الأيام الثلاثة)
    stats = client.get("/admin/dashboard/stats", headers=super_headers).json()
    assert freq["total"] == stats["students_inside_all_days"]


# ---------------------------------------------------------------------------
# ساعات الذروة (قسم 3.3)
# ---------------------------------------------------------------------------


def test_peak_hours_counts_and_peak(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    s2 = _make_student(db, "R-0002")
    # يوم خميس: ساعة 11 فيها 3 مسحات (الأعلى) — يوم أربعاء ساعة 10 فيها 2
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=10),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=10),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "thu", hour=11),
            _checkin_for_day(db, s2, ActivityType.campus_entry, "thu", hour=11),
            _checkin_for_day(db, s2, ActivityType.lecture, "thu", hour=11),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/peak-hours", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    # الساعات 8..15 — نافذة الفعالية، خارجها لا يُحتسب
    assert body["hours"] == list(range(8, 16))
    days = {d["day"]: d["counts"] for d in body["days"]}
    assert len(days["wed"]) == 8
    # index للساعة = hour - 8
    assert days["wed"][10 - 8] == 2
    assert days["thu"][11 - 8] == 3
    assert days["sat"][11 - 8] == 0
    assert body["peak"] == {"day": "thu", "hour": 11, "count": 3}


def test_peak_hours_peak_null_when_empty(client, super_headers):
    resp = client.get("/admin/dashboard/peak-hours", headers=super_headers).json()
    assert resp["peak"] is None


# ---------------------------------------------------------------------------
# الطلاب المتميزون (قسم 3.4)
# ---------------------------------------------------------------------------


def _seed_top_students(db):
    s1 = _make_student(db, "R-0001", full_name="أحمد الأول")
    s2 = _make_student(db, "R-0002", full_name="سمير الثاني")
    s3 = _make_student(db, "R-0003", full_name="ريم الثالثة")
    # s1: محاضرتان · جولتان (كليتان مختلفتان — فهرس unique_tour_booking يسمح
    #     بحجز جولة واحد لكل (طالب، كلية)).
    # s2: محاضرة واحدة · جولة واحدة
    # s3: ثلاث محاضرات · صفر جولات (الأعلى محاضرات، الأدنى جولات)
    tour_colleges = [Faculty.civil_engineering, Faculty.architecture]
    for student, lectures, tours in ((s1, 2, 2), (s2, 1, 1), (s3, 3, 0)):
        for i in range(lectures):
            _checkin_for_day(db, student, ActivityType.lecture, "wed", hour=10)
        for i in range(tours):
            _tour_booking(db, student, "thu", tour_colleges[i], hour=11)
    return s1, s2, s3


def test_top_students_lectures(db, client, super_headers):
    _seed_top_students(db)
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=lectures&limit=3", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["metric"] == "lectures"
    assert body["total"] == 3
    assert body["items"][0]["rank"] == 1
    assert body["items"][0]["unique_code"] == "R-0003"
    assert body["items"][0]["value"] == 3
    # sort تنازلي ثم رمز تصاعدي — للـ ties (القيمة 2 لـ s1 لا تنطبق هنا)
    codes = [i["unique_code"] for i in body["items"]]
    assert codes == ["R-0003", "R-0001", "R-0002"]
    assert "generated_at" in body


def test_top_students_tours(db, client, super_headers):
    _seed_top_students(db)
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=tours&limit=3", headers=super_headers).json()
    assert resp["items"][0]["unique_code"] == "R-0001"
    assert resp["items"][0]["value"] == 2
    assert resp["total"] == 2  # s3 بدون جولات لا يظهر


def test_top_students_presence(db, client, super_headers):
    s1 = _make_student(db, "R-0001", full_name="أحمد")
    s2 = _make_student(db, "R-0002", full_name="سمير")
    # s1: يوم أربعاء مدته 180 دقيقة (09:00 و 12:00) + يوم خميس مدته 60 دقيقة (10:00 و 11:00)
    #     → الإجمالي 240 دقيقة على يومين
    # s2: يوم أربعاء مدته 60 دقيقة (10:00 و 11:00) → 60 دقيقة على يوم واحد
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=9),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=12),
            _checkin_for_day(db, s1, ActivityType.campus_entry, "thu", hour=10),
            _checkin_for_day(db, s1, ActivityType.lecture, "thu", hour=11),
            _checkin_for_day(db, s2, ActivityType.campus_entry, "wed", hour=10),
            _checkin_for_day(db, s2, ActivityType.lecture, "wed", hour=11),
        ]
    )
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=presence&limit=3", headers=super_headers).json()
    assert resp["items"][0]["unique_code"] == "R-0001"
    assert resp["items"][0]["value"] == 240
    assert resp["items"][0]["days"] == 2
    assert resp["items"][1]["unique_code"] == "R-0002"
    assert resp["items"][1]["value"] == 60
    assert resp["items"][1]["days"] == 1


def test_presence_window_ignores_outside_checkins(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    # s1: أربعاء — مسحتان داخل النافذة؟ لا، الأولى 22:00 خارج النافذة (بعد 16:00)
    #     والثانية 07:30 خارج النافذة (قبل 08:00) → كلاهما خارج [08:00, 16:00)
    #     فلا يتشكل زوج → لا يُحتسب بالمرة
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=22),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=7, minute=30),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/presence", headers=super_headers)
    assert resp.status_code == 200
    body = resp.json()
    per_day = {d["day"]: d for d in body["per_day"]}
    assert per_day["wed"]["students_counted"] == 0
    assert per_day["wed"]["avg_minutes"] == 0
    assert body["avg_minutes_all"] == 0


def test_presence_window_0830_counts(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    # مسحة 08:30 داخل النافذة + مسحة 15:30 داخل النافذة → زوج صالح
    # مدة (student, day) = 7 ساعات (لا تتجاوز 8)
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=8, minute=30),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=15, minute=30),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/presence", headers=super_headers).json()
    per_day = {d["day"]: d for d in resp["per_day"]}
    assert per_day["wed"]["students_counted"] == 1
    assert per_day["wed"]["avg_minutes"] == 420  # 7 ساعات
    assert resp["avg_minutes_all"] == 420
    assert per_day["wed"]["avg_minutes"] <= 8 * 60


def test_peak_hours_window_ignores_outside_checkins(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    # مسحات خارج [08:00, 16:00) (22:00 و 07:30) → لا تظهر في ساعات الذروة
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=22),
            _checkin_for_day(db, s1, ActivityType.lecture, "thu", hour=7, minute=30),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/peak-hours", headers=super_headers).json()
    assert resp["peak"] is None
    days = {d["day"]: d["counts"] for d in resp["days"]}
    assert sum(days["wed"]) == 0
    assert sum(days["thu"]) == 0


def test_presence_day_duration_max_eight_hours(db, client, super_headers):
    s1 = _make_student(db, "R-0001")
    # أقصى مدة ممكنة لزوج داخل النافذة [08:00, 16:00) = 8 ساعات بالضبط
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.campus_entry, "wed", hour=8),
            _checkin_for_day(db, s1, ActivityType.lecture, "wed", hour=15, minute=59),
        ]
    )
    db.commit()

    resp = client.get("/admin/dashboard/presence", headers=super_headers).json()
    per_day = {d["day"]: d for d in resp["per_day"]}
    assert per_day["wed"]["avg_minutes"] == 7 * 60 + 59  # 479 < 480
    assert per_day["wed"]["avg_minutes"] <= 8 * 60


def test_top_students_union_all(db, client, super_headers):
    s1 = _make_student(db, "R-0001", full_name="أحمد")
    s2 = _make_student(db, "R-0002", full_name="سمير")
    # s1: الثلاثة أركان كاملة
    # s2: ركنان فقط
    db.add_all(
        [
            _checkin_for_day(db, s1, ActivityType.union, "wed", union_section=UnionSection.central),
            _checkin_for_day(
                db, s1, ActivityType.union, "thu", union_section=UnionSection.major_guide
            ),
            _checkin_for_day(
                db, s1, ActivityType.union, "sat", union_section=UnionSection.turkish_club
            ),
            _checkin_for_day(db, s2, ActivityType.union, "wed", union_section=UnionSection.central),
            _checkin_for_day(
                db, s2, ActivityType.union, "thu", union_section=UnionSection.major_guide
            ),
        ]
    )
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=union_all", headers=super_headers).json()
    assert resp["total"] == 1
    assert resp["items"][0]["unique_code"] == "R-0001"
    assert resp["items"][0]["value"] == 3
    assert len(resp["items"]) == 1


def test_top_students_pagination(db, client, super_headers):
    _seed_top_students(db)
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=lectures&limit=2&page=2", headers=super_headers).json()
    assert resp["total"] == 3
    assert resp["page"] == 2
    assert resp["limit"] == 2
    assert resp["total_pages"] == 2
    # الرتبة مطلقة — الصفحة الثانية تبدأ من الرتبة 3
    assert resp["items"][0]["rank"] == 3
    assert resp["items"][0]["unique_code"] == "R-0002"


def test_top_students_invalid_metric_422(client, super_headers):
    resp = client.get("/admin/dashboard/top-students?metric=bogus", headers=super_headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# صلاحيات — 403 لكل الأدوار غير super_admin
# ---------------------------------------------------------------------------

_ADMIN_V2_ENDPOINTS = [
    "/admin/dashboard/students-inside-count?day=wed",
    "/admin/dashboard/game-scans?day=thu",
    "/admin/dashboard/college-visits?day=sat",
    "/admin/dashboard/union-sections?day=wed",
    "/admin/dashboard/presence",
    "/admin/dashboard/peak-hours",
    "/admin/dashboard/top-students?metric=lectures",
]


def test_non_super_admin_forbidden_on_new_endpoints(
    client, students_admin_headers, college_staff_headers, gate_scanner_headers, super_headers
):
    for endpoint in _ADMIN_V2_ENDPOINTS:
        resp = client.get(endpoint, headers=students_admin_headers)
        assert resp.status_code == 403, f"{endpoint}: {resp.status_code}"
        resp = client.get(endpoint, headers=college_staff_headers)
        assert resp.status_code == 403, f"{endpoint}: {resp.status_code}"
    # سوبر أدمن مقبول
    resp = client.get("/admin/dashboard/presence", headers=super_headers)
    assert resp.status_code == 200