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
    Lecture,
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


def test_top_students_union_all_with_repeat_visit(db, client, super_headers):
    """
    مقياس union_all بيعدّ الأقسام المميّزة (count distinct) مش المسحات: طالب زار
    الركن المركزي مرتين (يومين) + دليل التخصص + نادي التركي = 3 أقسام، فبينحسب
    بقيمة 3 — الزيارة المكررة ما بتخبط العدّاد.
    """
    s1 = _make_student(db, "R-0001", full_name="أحمد")
    s2 = _make_student(db, "R-0002", full_name="سمير")
    db.add_all(
        [
            # s1: المركزي يومين + قسمين مرة وحدة لكل منهما
            _checkin_for_day(db, s1, ActivityType.union, "wed", union_section=UnionSection.central),
            _checkin_for_day(db, s1, ActivityType.union, "thu", union_section=UnionSection.central),
            _checkin_for_day(
                db, s1, ActivityType.union, "sat", union_section=UnionSection.major_guide
            ),
            _checkin_for_day(
                db, s1, ActivityType.union, "wed", hour=14, union_section=UnionSection.turkish_club
            ),
            # s2: قسمين فقط (مع تكرار أحدهما بيوم تاني) — ما بينحسب
            _checkin_for_day(db, s2, ActivityType.union, "wed", union_section=UnionSection.central),
            _checkin_for_day(db, s2, ActivityType.union, "thu", union_section=UnionSection.central),
            _checkin_for_day(
                db, s2, ActivityType.union, "sat", union_section=UnionSection.major_guide
            ),
        ]
    )
    db.commit()
    resp = client.get("/admin/dashboard/top-students?metric=union_all", headers=super_headers).json()
    assert resp["total"] == 1
    assert resp["items"][0]["unique_code"] == "R-0001"
    assert resp["items"][0]["value"] == 3


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
# حركة الطلاب بين الأركان (قسم 3.1b) — corner-journey
# ---------------------------------------------------------------------------

# الركن = كلية (حجز جولة أو مسحة) + قسم اتحاد + قسم ترفيه.
# الانتقالات بتتبني على المسحات فقط وبنفس اليوم.
_JOURNEY_PATH = "/admin/dashboard/corner-journey"


def _journey(client, headers, day="all"):
    resp = client.get(f"{_JOURNEY_PATH}?day={day}", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def _buckets(body):
    return {item["bucket"]: item["count"] for item in body["distribution"]}


def _bucket_labels(body):
    return [item["label"] for item in body["distribution"]]


def _pair_labels(body, key):
    return [(item["label"], item["count"]) for item in body[key]]


def _seed_corner_journey(db):
    """
    سيناريو مشترك للاختبارات:
      s1 — زار الآداب (حجز + مسحة 10:00) ثم الركن المركزي (11:00) يوم الأربعاء
      s2 — زار الهندسة المعلوماتية (10:00) ثم قسم الترفيه (12:00) يوم الخميس
      s3 — ندوة فقط يوم الأربعاء
      s4 — ما سجّل شي (ما بينحسب)
      s5 — حجز آداب + مسحة مركزي (حجز بلا مسحة: زاوية بدون انتقال)
      s6 — مسحة آداب الأربعاء 10:00 + مسحة مركزي الخميس 10:00 (ركنان، بلا انتقال)
      s7 — مسحة موسيقا + مسحة مركزي (توحيد: زاوية وحدة)
      s8 — مسحة طب + مسحة صيدلة (توحيد: زاوية وحدة)
    """
    students = {code: _make_student(db, code) for code in
                ("R-0101", "R-0102", "R-0103", "R-0104", "R-0105", "R-0106", "R-0107", "R-0108")}
    s1, s2, s3, s4, s5, s6, s7, s8 = (students[code] for code in
                                       ("R-0101", "R-0102", "R-0103", "R-0104",
                                        "R-0105", "R-0106", "R-0107", "R-0108"))

    db.add_all([
        # s1: زاويتان مرتبتان بالزمن (انتقال مباشر آداب ← مركزي)
        _tour_booking(db, s1, "wed", Faculty.arts, hour=9),
        _checkin_for_day(db, s1, ActivityType.tour, "wed", hour=10, college=Faculty.arts),
        _checkin_for_day(db, s1, ActivityType.union, "wed", hour=11,
                         union_section=UnionSection.central),
        # s2: زاويتان يوم الخميس (انتقال معلوماتية ← ترفيه)
        _checkin_for_day(db, s2, ActivityType.tour, "thu", hour=10,
                         college=Faculty.informatics),
        _checkin_for_day(db, s2, ActivityType.game, "thu", hour=12),
        # s3: ندوة فقط — عمود "ندوة فقط"
        _checkin_for_day(db, s3, ActivityType.lecture, "wed", hour=9,
                         lecture_name=Lecture.lecture_1),
        # s5: حجز بلا مسحة — زاوية بدون انتقال (والحجز وحده ما بيعمل انتقال)
        _tour_booking(db, s5, "wed", Faculty.arts, hour=8),
        _checkin_for_day(db, s5, ActivityType.union, "wed", hour=13,
                         union_section=UnionSection.central),
        # s6: ركنان بيومين مختلفين — ما في انتقال بينهم
        _checkin_for_day(db, s6, ActivityType.tour, "wed", hour=10, college=Faculty.arts),
        _checkin_for_day(db, s6, ActivityType.union, "thu", hour=10,
                         union_section=UnionSection.central),
        # s7: الموسيقا دُمجت بالركن المركزي — زاوية وحدة لا زاويتين
        _checkin_for_day(db, s7, ActivityType.tour, "sat", hour=10, college=Faculty.music),
        _checkin_for_day(db, s7, ActivityType.union, "sat", hour=11,
                         union_section=UnionSection.central),
        # s8: الطب والصيدلة دُمجوا بالمجمع الطبي — زاوية وحدة
        _checkin_for_day(db, s8, ActivityType.tour, "sat", hour=10, college=Faculty.medicine),
        _checkin_for_day(db, s8, ActivityType.tour, "sat", hour=11, college=Faculty.pharmacy),
    ])
    db.commit()
    return {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6": s6, "s7": s7, "s8": s8}


def test_corner_journey_distribution_buckets(db, client, super_headers):
    _seed_corner_journey(db)
    body = _journey(client, super_headers)

    # ترتيب الأعمدة: ركن واحد، ركنان، 3، 4، 5 فأكثر، ندوة فقط
    assert _bucket_labels(body) == [
        "ركن واحد", "ركنان", "3 أركان", "4 أركان", "5 أركان فأكثر", "ندوة فقط",
    ]
    buckets = _buckets(body)
    # s7 و s8 كل واحد زاوية وحدة بعد التوحيد؛ s4 ما سجّل شي
    assert buckets[1] == 2
    # s1, s2, s5, s6 — كلهم ركنان
    assert buckets[2] == 4
    assert buckets[3] == buckets[4] == buckets[5] == 0
    # s3: ندوة بلا ركن
    assert buckets[0] == 1
    # s4 ما بينحسب — مجموع الأعمدة 7 بدونه
    assert body["total_students"] == 7
    assert body["multi_corner_students"] == 4


def test_corner_journey_lecture_only_excludes_corner_visitors(db, client, super_headers):
    """من عنده ندوة وركن ما بينحسب بعمود «ندوة فقط»."""
    both = _make_student(db, "R-0109")
    db.add_all([
        _checkin_for_day(db, both, ActivityType.lecture, "wed", hour=9,
                         lecture_name=Lecture.lecture_1),
        _checkin_for_day(db, both, ActivityType.tour, "wed", hour=10,
                         college=Faculty.arts),
    ])
    db.commit()

    body = _journey(client, super_headers)
    assert _buckets(body)[0] == 0
    assert _buckets(body)[1] == 1


def test_corner_journey_merges_music_and_medical_colleges(db, client, super_headers):
    _seed_corner_journey(db)
    body = _journey(client, super_headers, day="sat")

    assert _buckets(body)[1] == 2  # s7 (موسيقا+مركزي) و s8 (طب+صيدلة) زاوية وحدة كل واحد
    # ما في زوج "الموسيقا + central" ولا "الطب + الصيدلة" — التوحی قبل التجميع
    labels = [label for label, _count in _pair_labels(body, "pairs")]
    assert all("الموسيقى" not in label for label in labels)
    assert all("الصيدلة" not in label for label in labels)


def test_corner_journey_pairs_use_distinct_corners(db, client, super_headers):
    _seed_corner_journey(db)
    body = _journey(client, super_headers)

    # s1 و s5 زاروا الآداب + المركزي (s1 بمسحة، s5 بحجز بلا مسحة) ⇒ زوج بعدّ 3
    # مع s6 (ركن من يوم وزاوية من يوم ثاني — تراكمي بـ all)
    assert _pair_labels(body, "pairs")[0] == (
        "كلية الآداب والعلوم الإنسانية + الركن المركزي",
        3,
    )
    # s2: هندسة المعلوماتية + قسم الترفيه
    assert ("كلية الهندسة المعلوماتية + قسم الترفيه", 1) in _pair_labels(body, "pairs")
    # s5 عنده زاوية واحدة بالمسحة (المركزي) والحجز ما بيعمل انتقال
    assert body["pairs"][0]["source"] == "c:arts"
    assert body["pairs"][0]["target"] == "u:central"


def test_corner_journey_transitions_are_direct_and_same_day(db, client, super_headers):
    _seed_corner_journey(db)
    body = _journey(client, super_headers)

    assert _pair_labels(body, "transitions") == [
        ("من كلية الآداب والعلوم الإنسانية إلى الركن المركزي", 1),  # s1
        ("من كلية الهندسة المعلوماتية إلى قسم الترفيه", 1),  # s2
    ]
    assert body["total_transitions"] == 2


def test_corner_journey_no_transition_across_days(db, client, super_headers):
    """سنة: زار الآداب الأربعاء والمركزي الخميس — انتقال عبر يومين مستحيل."""
    student = _make_student(db, "R-0112")
    db.add_all([
        _checkin_for_day(db, student, ActivityType.tour, "wed", hour=10, college=Faculty.arts),
        _checkin_for_day(db, student, ActivityType.union, "thu", hour=10,
                         union_section=UnionSection.central),
    ])
    db.commit()

    body = _journey(client, super_headers)
    # الركنين موجودين (تراكمي) والزوج موجود…
    assert _buckets(body)[2] == 1
    assert _pair_labels(body, "pairs") == [
        ("كلية الآداب والعلوم الإنسانية + الركن المركزي", 1)
    ]
    # …بس ما في انتقال، لأن مسحتين بيومين مختلفين
    assert body["transitions"] == []
    assert body["total_transitions"] == 0


def test_corner_journey_booking_alone_creates_no_transition(db, client, super_headers):
    """حجز الجولة ما عندو وقت زيارة — ما بيولّد انتقال."""
    student = _make_student(db, "R-0110")
    db.add_all([
        _tour_booking(db, student, "wed", Faculty.arts, hour=9),
        _checkin_for_day(db, student, ActivityType.union, "wed", hour=10,
                         union_section=UnionSection.major_guide),
    ])
    db.commit()

    body = _journey(client, super_headers)
    assert body["total_transitions"] == 0
    # بس بالزاويتين counted
    assert _buckets(body)[2] == 1
    assert _pair_labels(body, "pairs") == [
        ("كلية الآداب والعلوم الإنسانية + دليل التخصص", 1)
    ]


def test_corner_journey_day_filter(db, client, super_headers):
    _seed_corner_journey(db)

    wed = _journey(client, super_headers, day="wed")
    thu = _journey(client, super_headers, day="thu")
    sat = _journey(client, super_headers, day="sat")

    # s6 عنده ركن بالأربعاء (الآداب) وركن بالخميس (المركزي)
    assert _buckets(wed)[2] == 2  # s1, s5
    assert _buckets(wed)[1] == 1  # s6
    assert _buckets(wed)[0] == 1  # s3 ندوة فقط
    assert _buckets(thu)[2] == 1  # s2
    assert _buckets(thu)[1] == 1  # s6 الركن الثاني
    assert _buckets(sat)[1] == 2  # s7, s8 بعد التوحيد

    # الانتقالات تخص اليوم: s1 (أربعاء) و s2 (خميس)
    assert wed["total_transitions"] == 1
    assert thu["total_transitions"] == 1
    assert sat["total_transitions"] == 0
    assert _pair_labels(wed, "transitions")[0][0].startswith("من كلية الآداب")
    assert _pair_labels(thu, "transitions")[0][0].startswith("من كلية الهندسة المعلوماتية")


def test_corner_journey_all_equals_sum_of_days(db, client, super_headers):
    """'all' محصور بأيام الفعالية — الانتقالات بتتجميع بنفسها لكل يوم."""
    _seed_corner_journey(db)

    everything = _journey(client, super_headers, day="all")
    per_day = [_journey(client, super_headers, day=key) for key in ("wed", "thu", "sat")]

    assert everything["total_transitions"] == sum(d["total_transitions"] for d in per_day)
    assert _pair_labels(everything, "transitions") == [
        ("من كلية الآداب والعلوم الإنسانية إلى الركن المركزي", 1),
        ("من كلية الهندسة المعلوماتية إلى قسم الترفيه", 1),
    ]


def test_corner_journey_all_merges_corners_across_days(db, client, super_headers):
    """
    'all' تراكمي على الزوايا: s6 زار الآداب الأربعاء والمركزي الخميس، فبيصير
    عنده ركنين محسوبين بوحدة (على عكس جمع عدّاد الأيام، لأن s6 بينحسب مرتين
    هناك — مرة لكل يوم). فالتوزيع بيُبنى على البُعد الشخصي مش اليوم.
    """
    _seed_corner_journey(db)

    everything = _journey(client, super_headers, day="all")
    wed = _journey(client, super_headers, day="wed")
    thu = _journey(client, super_headers, day="thu")

    assert everything["total_students"] == 7
    assert _buckets(everything)[2] == 4
    # s6 ضمن ركنين بـ all، بس بركن واحد بكل يوم
    assert _buckets(wed)[1] + _buckets(thu)[1] >= 2


def test_corner_journey_ignores_scans_outside_event_window(db, client, super_headers):
    """مسحة إدخال يدوي الساعة 18:00 برا نافذة الفعالية [08:00, 16:00) بتتجاهل."""
    student = _make_student(db, "R-0111")
    db.add_all([
        _checkin_for_day(db, student, ActivityType.tour, "wed", hour=18,
                         college=Faculty.arts),
        _checkin_for_day(db, student, ActivityType.union, "wed", hour=19,
                         union_section=UnionSection.central),
    ])
    db.commit()

    body = _journey(client, super_headers)
    assert body["total_students"] == 0
    assert body["total_transitions"] == 0
    assert all(item["count"] == 0 for item in body["distribution"])
    assert body["pairs"] == []
    assert body["transitions"] == []


def test_corner_journey_empty_when_no_data(db, client, super_headers):
    body = _journey(client, super_headers)

    assert body["day"] == "all"
    assert body["total_students"] == 0
    assert body["multi_corner_students"] == 0
    assert body["total_transitions"] == 0
    assert [item["count"] for item in body["distribution"]] == [0] * 6
    assert body["pairs"] == []
    assert body["transitions"] == []
    assert body["generated_at"]


def test_corner_journey_invalid_day_422(client, super_headers):
    resp = client.get(f"{_JOURNEY_PATH}?day=bogus", headers=super_headers)
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
    "/admin/dashboard/corner-journey?day=wed",
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