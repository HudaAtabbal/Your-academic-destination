"""
منطق العمل لحجز جولة كلية أو استشارة (نية/حجز فقط، بدون تأكيد حضور فعلي).
راجع قسم 3 بملف wijhatak_api_contract.md.

القواعد المطبّقة:
1) لازم يكون عند الطالب campus_entry مسبقاً قبل أي حجز.
2) ما بينسمح حجز نفس الكلية مرتين (جولة)، ولا حجز استشارة مرتين.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.errors import duplicate_booking, missing_campus_entry, student_not_found
from app.models import Booking, BookingType, Checkin, ActivityType, College, Student


def _get_student_or_raise(db: Session, unique_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student


def _has_campus_entry(db: Session, student_id: int) -> bool:
    return (
        db.query(Checkin)
        .filter(Checkin.student_id == student_id, Checkin.activity_type == ActivityType.campus_entry)
        .first()
        is not None
    )


def _find_existing_booking(
    db: Session, student_id: int, booking_type: BookingType, college: College | None = None
) -> Booking | None:
    query = db.query(Booking).filter(
        Booking.student_id == student_id, Booking.booking_type == booking_type
    )
    if booking_type == BookingType.tour:
        query = query.filter(Booking.college == college)
    return query.first()


def create_tour_booking(db: Session, unique_code: str, college: College) -> tuple[Booking, str | None]:
    student = _get_student_or_raise(db, unique_code)

    if not _has_campus_entry(db, student.id):
        raise missing_campus_entry()

    existing = _find_existing_booking(db, student.id, BookingType.tour, college=college)
    if existing is not None:
        raise duplicate_booking(
            student.full_name or unique_code, unique_code, f"جولة كلية ({college.value})"
        )

    booking = Booking(student_id=student.id, booking_type=BookingType.tour, college=college)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, student.full_name


def create_consultation_booking(db: Session, unique_code: str) -> tuple[Booking, str | None]:
    student = _get_student_or_raise(db, unique_code)

    if not _has_campus_entry(db, student.id):
        raise missing_campus_entry()

    existing = _find_existing_booking(db, student.id, BookingType.consultation)
    if existing is not None:
        raise duplicate_booking(student.full_name or unique_code, unique_code, "استشارة فردية")

    booking = Booking(student_id=student.id, booking_type=BookingType.consultation)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking, student.full_name


def count_bookings_today(
    db: Session, booking_type: BookingType, college: College | None = None
) -> int:
    """
    عدّاد "اليوم" لعدد الحجوزات (بغض النظر إذا تأكدت فعلياً بـ checkins أو لأ) —
    يستخدم توقيت السيرفر المحلي حالياً (قرار مؤجّل، راجع Business Rules #11).
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    query = db.query(Booking).filter(
        Booking.booking_type == booking_type,
        Booking.booked_at >= today_start,
        Booking.booked_at < today_end,
    )
    if college is not None:
        query = query.filter(Booking.college == college)

    return query.count()