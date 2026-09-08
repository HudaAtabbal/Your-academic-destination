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

from sqlalchemy.orm import Session

from app.errors import duplicate_checkin, missing_booking, missing_campus_entry, student_not_found
from app.models import ActivityType, Booking, BookingType, Checkin, College, Lecture, Student
from app.routers.points import point_service

_ACTIVITY_LABELS = {
    ActivityType.campus_entry: "الدخول من بوابة الجامعة اليوم",
    ActivityType.consultation: "الاستشارة الفردية",
}


def _today_range() -> tuple[datetime, datetime]:
    """
    حدود "اليوم" — بتستخدم توقيت السيرفر المحلي حالياً (قرار مؤجّل، راجع
    Business Rules #11 بالعقد: بنحدد الـ timezone بدقة قبل يوم الفعالية).
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today_start, today_start + timedelta(days=1)


def _get_student_or_raise(db: Session, unique_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student


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
    college: College | None = None,
) -> Checkin | None:
    query = db.query(Checkin).filter(
        Checkin.student_id == student_id, Checkin.activity_type == activity_type
    )
    if activity_type == ActivityType.lecture:
        query = query.filter(Checkin.lecture_name == lecture_name)
    elif activity_type == ActivityType.tour:
        query = query.filter(Checkin.college == college)
    return query.first()


def _has_matching_booking(
    db: Session, student_id: int, booking_type: BookingType, college: College | None = None
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


def create_campus_entry_checkin(db: Session, unique_code: str) -> tuple[Checkin, str | None]:
    student = _get_student_or_raise(db, unique_code)

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
    db.commit()
    db.refresh(checkin)
    point_service.recalculate_and_store_points(db, student.id)
    return checkin, student.full_name


def create_lecture_checkin(
    db: Session, unique_code: str, lecture_name: Lecture
) -> tuple[Checkin, str | None]:
    student = _get_student_or_raise(db, unique_code)

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
        f"محاضرة ({lecture_name.value})",
    )

    checkin = Checkin(
        student_id=student.id, activity_type=ActivityType.lecture, lecture_name=lecture_name
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    point_service.recalculate_and_store_points(db, student.id)
    return checkin, student.full_name


def create_tour_checkin(
    db: Session, unique_code: str, college: College
) -> tuple[Checkin, str | None]:
    student = _get_student_or_raise(db, unique_code)

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
    db.commit()
    db.refresh(checkin)
    point_service.recalculate_and_store_points(db, student.id)
    return checkin, student.full_name


def create_consultation_checkin(db: Session, unique_code: str) -> tuple[Checkin, str | None]:
    student = _get_student_or_raise(db, unique_code)

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

    checkin = Checkin(student_id=student.id, activity_type=ActivityType.consultation)
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    point_service.recalculate_and_store_points(db, student.id)
    return checkin, student.full_name


def count_checkins_today(
    db: Session,
    activity_type: ActivityType,
    college: College | None = None,
    lecture_name: Lecture | None = None,
) -> int:
    """
    عدّاد "اليوم" — بيستخدم توقيت السيرفر المحلي حالياً (قرار مؤجّل، راجع
    Business Rules #11 بالعقد: بنحدد الـ timezone بدقة قبل يوم الفعالية).
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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

    return query.count()