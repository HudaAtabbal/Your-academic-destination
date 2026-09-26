"""
منطق العمل لحجز جولة كلية أو استشارة (نية/حجز فقط، بدون تأكيد حضور فعلي).
راجع قسم 3 بملف wijhatak_api_contract.md.

القواعد المطبّقة:
1) لازم يكون عند الطالب campus_entry مسبقاً قبل أي حجز.
2) ما بينسمح حجز نفس الكلية مرتين بنفس اليوم (جولة) — وبإمكانه يرجع لها
   بيوم تاني من أيام الفعالية. حجز الاستشارة مر وحدة وحدة طول الفعالية.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import time_utils
from app.errors import duplicate_booking, missing_campus_entry, student_not_found
from app.faculty_labels import faculty_label
from app.models import Booking, BookingType, Checkin, ActivityType, Faculty, Student
from app.student_lookup import get_student_or_raise


def _has_campus_entry(db: Session, student_id: int) -> bool:
    """
    محدّث: campus_entry صار مسموح مرة كل يوم — فالشرط المسبق للحجز (جولة/استشارة)
    صار "فات من البوابة بنفس اليوم" مثل checkin_service._has_campus_entry_today.
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)
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


def _find_existing_booking(
    db: Session, student_id: int, booking_type: BookingType, college: Faculty | None = None
) -> Booking | None:
    """
    التكرار محسوب بنفس قاعدة الفهرس الفريد: جولة = (الطالب + الكلية + اليوم)،
    فحجز نفس الكلية بيوم تاني مسموح. الاستشارة = مرة وحدة بالكامل (بدون تاريخ).
    """
    query = db.query(Booking).filter(
        Booking.student_id == student_id, Booking.booking_type == booking_type
    )
    if booking_type == BookingType.tour:
        today_start = time_utils.today_start()
        query = query.filter(
            Booking.college == college,
            Booking.booked_at >= today_start,
            Booking.booked_at < today_start + timedelta(days=1),
        )
    return query.first()


def create_tour_booking(db: Session, unique_code: str, college: Faculty) -> tuple[Booking, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry(db, student.id):
        raise missing_campus_entry()

    existing = _find_existing_booking(db, student.id, BookingType.tour, college=college)
    if existing is not None:
        raise duplicate_booking(
            student.full_name or unique_code,
            unique_code,
            f"جولة كلية ({faculty_label(college)})",
        )

    booking = Booking(student_id=student.id, booking_type=BookingType.tour, college=college)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, student.full_name


def create_consultation_booking(
    db: Session, unique_code: str, college: Faculty
) -> tuple[Booking, str | None]:
    student = get_student_or_raise(db, unique_code)

    if not _has_campus_entry(db, student.id):
        raise missing_campus_entry()

    existing = _find_existing_booking(db, student.id, BookingType.consultation)
    if existing is not None:
        raise duplicate_booking(student.full_name or unique_code, unique_code, "استشارة فردية")

    booking = Booking(
        student_id=student.id, booking_type=BookingType.consultation, college=college
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, student.full_name


def count_bookings_today(
    db: Session, booking_type: BookingType, college: Faculty | None = None
) -> int:
    """
    عدّاد "اليوم" لعدد الحجوزات (بغض النظر إذا تأكدت فعلياً بـ checkins أو لأ) —
    بتوقيت سوريا عبر time_utils.
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    query = db.query(Booking).filter(
        Booking.booking_type == booking_type,
        Booking.booked_at >= today_start,
        Booking.booked_at < today_end,
    )
    if college is not None:
        query = query.filter(Booking.college == college)

    return query.count()
