"""اختبار ترحيل "المجمع الطبي" — migration_merge_medical_colleges.sql.

يتحقّق أن الدمج لمرة وحدة ينقل سجلات كليات الطب البشري والصيدلة إلى طب الأسنان
فقط للطلاب اللي ما عندهم أصلن زيارة طب أسنان؛ أمّا اللي فعندهم زيارة أسنان
فلا يُضاف عليهم أيُّ زيارة (ما يتضاعف عددهم).
"""

from pathlib import Path

from sqlalchemy import text

from app.models import (
    ActivityType,
    Booking,
    BookingType,
    Checkin,
    Faculty,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)

_MIGRATION = Path(__file__).resolve().parent.parent / "scripts" / "migration_merge_medical_colleges.sql"


def _add_student(db, code: str) -> Student:
    student = Student(
        unique_code=code,
        full_name="طالب تجريبي",
        registration_type=RegistrationType.registered,
        verification_status=VerificationStatus.verified,
        status=StudentStatus.complete,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def _add_booking(db, student_id: int, college: Faculty) -> None:
    db.add(
        Booking(
            student_id=student_id,
            booking_type=BookingType.tour,
            college=college,
        )
    )
    db.commit()


def _add_tour_checkin(db, student_id: int, college: Faculty) -> None:
    db.add(
        Checkin(
            student_id=student_id,
            activity_type=ActivityType.tour,
            college=college,
        )
    )
    db.commit()


def _colleges_of(db, code: str) -> set[str]:
    from app.database import engine

    row = db.execute(text("SELECT id FROM students WHERE unique_code = :c"), {"c": code}).one()
    sid = row.id
    cols = db.execute(
        text("SELECT college FROM checkins WHERE student_id = :s"), {"s": sid}
    ).scalars().all()
    cols += db.execute(
        text("SELECT college FROM bookings WHERE student_id = :s"), {"s": sid}
    ).scalars().all()
    return {c for c in cols if c}


def test_merge_medical_colleges_migration(client, db):
    """الطلاب بلا زيارة أسنان تُنقل سجلاتهم؛ اللي معه أسنان ما يتضاعف."""
    # بدون أي زيارة أسنان — الترحيل لازم ينقل كل الكليات لـ dentistry
    s_med = _add_student(db, "R-1001")
    _add_booking(db, s_med.id, Faculty.medicine)
    _add_tour_checkin(db, s_med.id, Faculty.medicine)

    s_pharm = _add_student(db, "R-1002")
    _add_booking(db, s_pharm.id, Faculty.pharmacy)

    s_both_no_dent = _add_student(db, "R-1003")
    _add_booking(db, s_both_no_dent.id, Faculty.medicine)
    _add_tour_checkin(db, s_both_no_dent.id, Faculty.pharmacy)

    # فعنده زيارة أسنان أصلن — سجلاته الطبية ما تُنقل (عشان ما يتضاعف)
    s_already_dent = _add_student(db, "R-1004")
    _add_booking(db, s_already_dent.id, Faculty.dentistry)
    _add_booking(db, s_already_dent.id, Faculty.medicine)
    _add_tour_checkin(db, s_already_dent.id, Faculty.pharmacy)

    # تنفيذ ملف الترحيل كما هو (على قاعدة الاختبار)
    from app.database import engine

    with engine.begin() as conn:
        conn.execute(text(_MIGRATION.read_text(encoding="utf-8")))

    assert _colleges_of(db, "R-1001") == {"dentistry"}
    assert _colleges_of(db, "R-1002") == {"dentistry"}
    assert _colleges_of(db, "R-1003") == {"dentistry"}
    # اللي فعنده زيارة أسنان: "ما ينضاف" — سجلاته الطبية/الصيدلية تبقى كما هي
    # (ولو ظهرت بالجدول لاحقاً ما تُعرض بروابط زيارات الكليات)
    assert _colleges_of(db, "R-1004") == {"dentistry", "medicine", "pharmacy"}

    # على مستوى الإحصائية: كل الزيارات تظهر تحت «المجمع الطبي» (dentistry)
    resp = client.post(
        "/auth/login", json={"username": "taher_super", "password": "super123"}
    )
    super_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    analytics = client.get("/admin/dashboard/analytics", headers=super_headers)
    by_college = {v["college"]: v["count"] for v in analytics.json()["college_visits"]}
    assert by_college["dentistry"] == 4
    assert "medicine" not in by_college
    assert "pharmacy" not in by_college