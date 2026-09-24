"""
منطق العمل لكل عمليات تسجيل الحضور الفعلي (check-in) — راجع قسم 4 وقسم 14
(Business Rules Summary) بملف wijhatak_api_contract.md.

القواعد المطبّقة هون بمنطق الكود (مش قيود DB فقط):
1) ما في check-in لأي نشاط (محاضرة/جولة/استشارة) إلا إذا كان عند الطالب
   campus_entry مسبقاً.
2) ما في check-in فعلي لجولة/استشارة إلا بوجود booking مطابق.
3) أي محاولة check-in مكرر بترجع رسالة فيها اسم الطالب ووقت أول تسجيل —
   مش رفض صامت.
"""

from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import time_utils
from app.errors import (
    duplicate_checkin,
    game_requirements_not_met,
    missing_booking,
    missing_campus_entry,
)
from app.models import ActivityType, Booking, BookingType, Checkin, Faculty, Lecture, Student, UnionSection
from app.routers.points import point_service
from app.student_lookup import get_student_or_raise

_ACTIVITY_LABELS = {
    ActivityType.campus_entry: "الدخول من بوابة الجامعة اليوم",
    ActivityType.consultation: "الاستشارة الفردية",
    ActivityType.game: "ركن الترفيه",
    ActivityType.union: "الاتحاد",
}

# أسماء أقسام ركن الاتحاد بالعربي — معروضة للمستخدم في رسائل التكرار والواجهات.
_UNION_SECTION_LABELS = {
    UnionSection.central: "الركن المركزي",
    UnionSection.major_guide: "دليل التخصص",
    UnionSection.turkish_club: "نادي التركي",
}

# الأسماء العربية للمحاضرات — مطابقة لقائمة LECTURES بالواجهة (StadiumPage).
# قيمة enum Lecture (lecture_1..lecture_16) رمز تقني؛ الرسائل للمستخدم لازم
# تعرض الاسم الرسمي العربي مش الرمز.
_LECTURE_DISPLAY_NAMES = {
    Lecture.opening: "حفل الافتتاح",
    Lecture.lecture_1: "ندوة كليات العلوم الإنسانية",
    Lecture.lecture_2: "ندوة مركزية: كيف تختار تخصصك الجامعي",
    Lecture.lecture_3: "ندوة الكليات الطبية",
    Lecture.lecture_4: "ندوة مركزية: اتجاهات سوق العمل والمهن الصاعدة",
    Lecture.lecture_5: "ندوة أولياء الأمور",
    Lecture.lecture_6: "ندوة كليات العلوم الأساسية والاقتصادية",
    Lecture.lecture_7: "ندوة مركزية 2",
    Lecture.lecture_8: "ندوة كلية الهندسة المعلوماتية مع نبذة عن الكلية التطبيقية",
    Lecture.lecture_9: "ندوة الكليات: الهندسية المدنية · الهندسة المدنية · المعمارية · الزراعة",
    Lecture.lecture_10: "ندوة مركزية: التخصصات المستجدة",
    Lecture.lecture_11: "ندوة كلية الهندسة الميكانيكية",
    Lecture.lecture_12: "ندوة كلية الهندسة الكيميائية والبترولية",
    Lecture.lecture_13: "ندوة كلية الهندسة الكهربائية",
    Lecture.lecture_14: "ندوة صناعة الحياة الجامعية",
    Lecture.lecture_15: "ندوة المعاهد المتوسطة والعليا",
    Lecture.lecture_16: "حفل الختام والتكريم وتوزيع جوائز النقاط",
}


def _lecture_label(lecture: Lecture) -> str:
    return _LECTURE_DISPLAY_NAMES.get(lecture, lecture.value)


def lecture_display_name(lecture: Lecture) -> str:
    """الاسم الرسمي العربي للمحاضرة — واجهة عامة يعيد استخدامها dashboard."""
    return _lecture_label(lecture)


def union_section_label(section: UnionSection) -> str:
    """الاسم العربي لقسم ركن الاتحاد — واجهة عامة يعيد استخدامها dashboard."""
    return _UNION_SECTION_LABELS.get(section, section.value)


def _today_range() -> tuple[datetime, datetime]:
    """حدود "اليوم" — بتوقيت سوريا عبر time_utils."""
    start = time_utils.today_start()
    return start, start + timedelta(days=1)


def _has_campus_entry_today(db: Session, student_id: int) -> bool:
    """
    محدّث: campus_entry صار مسموح مرة كل يوم (مش مرة وحدة طول الفعالية) —
    فالشرط المسبق لحضور محاضرة/جولة/استشارة صار "فات من البوابة بنفس اليوم"،
    مش "فات ولو مرة بأي يوم سابق".
    """
    today_start, today_end = _today_range()
    return (
        db.query(Checkin)
        .filter(
            Checkin.student_id == student_id,
            Checkin.activity_type == ActivityType.campus_entry,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .first()
        is not None
    )


def _find_existing_campus_entry_today(db: Session, student_id: int) -> Checkin | None:
    today_start, today_end = _today_range()
    return (
        db.query(Checkin)
        .filter(
            Checkin.student_id == student_id,
            Checkin.activity_type == ActivityType.campus_entry,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .first()
    )


def _find_existing_checkin(
    db: Session,
    student_id: int,
    activity_type: ActivityType,
    lecture_name: Lecture | None = None,
    college: Faculty | None = None,
    union_section: UnionSection | None = None,
) -> Checkin | None:
    query = db.query(Checkin).filter(
        Checkin.student_id == student_id, Checkin.activity_type == activity_type
    )
    if activity_type == ActivityType.lecture:
        query = query.filter(Checkin.lecture_name == lecture_name)
    elif activity_type == ActivityType.tour:
        query = query.filter(Checkin.college == college)
    elif activity_type == ActivityType.union:
        query = query.filter(Checkin.union_section == union_section)
    return query.first()


def _has_matching_booking(
    db: Session, student_id: int, booking_type: BookingType, college: Faculty | None = None
) -> bool:
    query = db.query(Booking).filter(
        Booking.student_id == student_id, Booking.booking_type == booking_type
    )
    if booking_type == BookingType.tour:
        query = query.filter(Booking.college == college)
    return query.first() is not None


def _raise_if_duplicate(
    existing: Checkin | None,
    student_name: str,
    unique_code: str,
    activity_type: ActivityType,
    activity_label: str,
) -> None:
    if existing is not None:
        raise duplicate_checkin(
            student_name=student_name or unique_code,
            unique_code=unique_code,
            activity_type=activity_type.value,
            activity_label=activity_label,
            first_occurred_at=existing.checked_in_at,
        )


def _flush_commit_checkin(
    db: Session,
    existing_lookup,
    student: Student,
    unique_code: str,
    activity_type: ActivityType,
    activity_label: str,
) -> None:
    """
    بيCommit إضافة checkin الحالية، وبيمسك سباق التزامن (IntegrityError من
    الـ index الفريد) نحوّله لـ 409 duplicate_checkin لطيفة بدل 500 خام.
    """
    try:
        db.flush()
        point_service.recalculate_and_store_points(db, student.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = existing_lookup()
        if existing is not None:
            raise duplicate_checkin(
                student_name=student.full_name or unique_code,
                unique_code=unique_code,
                activity_type=activity_type.value,
                activity_label=activity_label,
                first_occurred_at=existing.checked_in_at,
            )
        raise


def create_campus_entry_checkin(db: Session, unique_code: str) -> tuple[Checkin, str | None]:
    student = get_student_or_raise(db, unique_code)

    existing = _find_existing_campus_entry_today(db, student.id)
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.campus_entry,
        _ACTIVITY_LABELS[ActivityType.campus_entry],
    )

    checkin = Checkin(student_id=student.id, activity_type=ActivityType.campus_entry)
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_campus_entry_today(db, student.id),
        student,
        unique_code,
        ActivityType.campus_entry,
        _ACTIVITY_LABELS[ActivityType.campus_entry],
    )
    db.refresh(checkin)
    return checkin, student.full_name


def create_lecture_checkin(
    db: Session, unique_code: str, lecture_name: Lecture
) -> tuple[Checkin, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry_today(db, student.id):
        raise missing_campus_entry()

    existing = _find_existing_checkin(
        db, student.id, ActivityType.lecture, lecture_name=lecture_name
    )
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.lecture,
        f"محاضرة ({_lecture_label(lecture_name)})",
    )

    checkin = Checkin(
        student_id=student.id, activity_type=ActivityType.lecture, lecture_name=lecture_name
    )
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_checkin(db, student.id, ActivityType.lecture, lecture_name=lecture_name),
        student,
        unique_code,
        ActivityType.lecture,
        f"محاضرة ({_lecture_label(lecture_name)})",
    )
    db.refresh(checkin)
    return checkin, student.full_name


def create_tour_checkin(
    db: Session, unique_code: str, college: Faculty
) -> tuple[Checkin, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry_today(db, student.id):
        raise missing_campus_entry()

    if not _has_matching_booking(db, student.id, BookingType.tour, college=college):
        raise missing_booking()

    existing = _find_existing_checkin(db, student.id, ActivityType.tour, college=college)
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.tour,
        f"جولة كلية ({college.value})",
    )

    checkin = Checkin(student_id=student.id, activity_type=ActivityType.tour, college=college)
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_checkin(db, student.id, ActivityType.tour, college=college),
        student,
        unique_code,
        ActivityType.tour,
        f"جولة كلية ({college.value})",
    )
    db.refresh(checkin)
    return checkin, student.full_name


def create_consultation_checkin(
    db: Session, unique_code: str, college: Faculty
) -> tuple[Checkin, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry_today(db, student.id):
        raise missing_campus_entry()

    if not _has_matching_booking(db, student.id, BookingType.consultation):
        raise missing_booking()

    existing = _find_existing_checkin(db, student.id, ActivityType.consultation)
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.consultation,
        _ACTIVITY_LABELS[ActivityType.consultation],
    )

    checkin = Checkin(
        student_id=student.id, activity_type=ActivityType.consultation, college=college
    )
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_checkin(db, student.id, ActivityType.consultation),
        student,
        unique_code,
        ActivityType.consultation,
        _ACTIVITY_LABELS[ActivityType.consultation],
    )
    db.refresh(checkin)
    return checkin, student.full_name


def _count_activity(db: Session, student_id: int, activity_type: ActivityType) -> int:
    return (
        db.query(Checkin)
        .filter(Checkin.student_id == student_id, Checkin.activity_type == activity_type)
        .count()
    )


def create_game_checkin(db: Session, unique_code: str) -> tuple[Checkin, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry_today(db, student.id):
        raise missing_campus_entry()

    tour_count = _count_activity(db, student.id, ActivityType.tour)
    lecture_count = _count_activity(db, student.id, ActivityType.lecture)
    if tour_count < 2 or lecture_count < 1:
        raise game_requirements_not_met(tour_count, lecture_count)

    existing = _find_existing_checkin(db, student.id, ActivityType.game)
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.game,
        _ACTIVITY_LABELS[ActivityType.game],
    )

    checkin = Checkin(student_id=student.id, activity_type=ActivityType.game)
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_checkin(db, student.id, ActivityType.game),
        student,
        unique_code,
        ActivityType.game,
        _ACTIVITY_LABELS[ActivityType.game],
    )
    db.refresh(checkin)
    return checkin, student.full_name


def create_union_checkin(
    db: Session, unique_code: str, union_section: UnionSection
) -> tuple[Checkin, str | None]:
    """
    مسح ركن الاتحاد — مثل الاستشارة من ناحية الشروط المسبقة: يكفي أن يكون
    الطالب دخل الحرم بنفس اليوم (بدون حجز أو جولات). بدون نقاط.

    قاعدة التكرار: مرة وحدة لكل قسم (union_section) — الطالب فيه يزور الأقسام
    الثلاثة (3 سجلات منفصلة)، بس مش نفس القسم مرتين.
    """
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry_today(db, student.id):
        raise missing_campus_entry()

    section_label = _UNION_SECTION_LABELS.get(union_section, union_section.value)
    activity_label = f"{_ACTIVITY_LABELS[ActivityType.union]} ({section_label})"

    existing = _find_existing_checkin(
        db, student.id, ActivityType.union, union_section=union_section
    )
    _raise_if_duplicate(
        existing,
        student.full_name,
        unique_code,
        ActivityType.union,
        activity_label,
    )

    checkin = Checkin(
        student_id=student.id,
        activity_type=ActivityType.union,
        union_section=union_section,
    )
    db.add(checkin)
    _flush_commit_checkin(
        db,
        lambda: _find_existing_checkin(
            db, student.id, ActivityType.union, union_section=union_section
        ),
        student,
        unique_code,
        ActivityType.union,
        activity_label,
    )
    db.refresh(checkin)
    return checkin, student.full_name


def count_checkins_today(
    db: Session,
    activity_type: ActivityType,
    college: Faculty | None = None,
    lecture_name: Lecture | None = None,
    union_section: UnionSection | None = None,
) -> int:
    """
    عدّاد "اليوم" — بتوقيت سوريا عبر time_utils.
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    query = db.query(Checkin).filter(
        Checkin.activity_type == activity_type,
        Checkin.checked_in_at >= today_start,
        Checkin.checked_in_at < today_end,
    )
    if college is not None:
        query = query.filter(Checkin.college == college)
    if lecture_name is not None:
        query = query.filter(Checkin.lecture_name == lecture_name)
    if union_section is not None:
        query = query.filter(Checkin.union_section == union_section)

    return query.count()