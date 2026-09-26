"""
موديل Booking — الحجز المسبق (نية) لجولة كلية أو استشارة، قبل التأكيد الفعلي.
مطابق تماماً لجدول bookings بـ wijhatak_schema_v2.sql.
"""

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Index, cast
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import time_utils
from app.database import Base
from app.models.enums import BookingType, Faculty


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    booking_type = Column(SAEnum(BookingType, name="booking_type_enum"), nullable=False)
    college = Column(SAEnum(Faculty, name="faculty_enum"), nullable=True)

    booked_at = Column(
        DateTime,
        nullable=False,
        default=lambda: time_utils.now_naive(),
        server_default=func.now(),
    )

    student = relationship("Student", back_populates="bookings")

    __table_args__ = (
        # جولة: كل كلية مرة وحدة للطالب وبنفس اليوم — مسموح يرجع لنفس الكلية
        # بيوم تاني من أيام الفعالية (نفس نمط unique_campus_entry_checkin).
        Index(
            "unique_tour_booking",
            "student_id",
            "college",
            cast(booked_at, Date),
            unique=True,
            postgresql_where=(booking_type == BookingType.tour),
        ),
        # استشارة: حجز مرة وحدة بالكامل للطالب
        Index(
            "unique_consultation_booking",
            "student_id",
            unique=True,
            postgresql_where=(booking_type == BookingType.consultation),
        ),
    )