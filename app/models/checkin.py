"""
موديل Checkin — تسجيل الحضور الفعلي لأي نشاط (محاضرة/جولة/استشارة/دخول الجامعة).
مطابق تماماً لجدول checkins بـ wijhatak_schema_v2.sql.
"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ActivityType, College, Lecture


class Checkin(Base):
    __tablename__ = "checkins"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    activity_type = Column(SAEnum(ActivityType, name="activity_type_enum"), nullable=False)
    lecture_name = Column(SAEnum(Lecture, name="lecture_enum"), nullable=True)
    college = Column(SAEnum(College, name="college_enum"), nullable=True)

    checked_in_at = Column(DateTime, nullable=False, server_default=func.now())

    student = relationship("Student", back_populates="checkins")

    __table_args__ = (
        # دخول الجامعة: مرة وحدة بالكامل للطالب
        Index(
            "unique_campus_entry_checkin",
            "student_id",
            unique=True,
            postgresql_where=(activity_type == ActivityType.campus_entry),
        ),
        # محاضرة: كل lecture_name مرة وحدة للطالب
        Index(
            "unique_lecture_checkin",
            "student_id",
            "lecture_name",
            unique=True,
            postgresql_where=(activity_type == ActivityType.lecture),
        ),
        # جولة: كل college مرة وحدة للطالب
        Index(
            "unique_tour_checkin",
            "student_id",
            "college",
            unique=True,
            postgresql_where=(activity_type == ActivityType.tour),
        ),
        # استشارة: مرة وحدة بالكامل للطالب
        Index(
            "unique_consultation_checkin",
            "student_id",
            unique=True,
            postgresql_where=(activity_type == ActivityType.consultation),
        ),
    )