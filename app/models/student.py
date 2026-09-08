"""
موديل Student — الجدول المركزي (هوية الطالب فقط).
مطابق تماماً لجدول students بـ wijhatak_schema_v2.sql.
"""

from sqlalchemy import BigInteger, Column, Date, DateTime, Index, Numeric, SmallInteger, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import (
    CertificateType,
    ContactPlatform,
    InterestCluster,
    RegistrationType,
    StudentStatus,
    VerificationStatus,
)


class Student(Base):
    __tablename__ = "students"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    unique_code = Column(String(20), unique=True, nullable=False, index=True)

    full_name = Column(String(255), nullable=True)
    contact_platform = Column(SAEnum(ContactPlatform, name="contact_platform_enum"), nullable=True)
    contact_id = Column(String(255), nullable=True)
    birth_date = Column(Date, nullable=True)

    bacc_average = Column(Numeric(5, 2), nullable=True)  # اختياري — نطاق 0-100 (نسبة مئوية، مش مجموع)
    # سنة البكالوريا — nullable بالـ DB (لسجلات walk-in الفارغة)، إلزامي بمستوى
    # الـ API فقط لمسار registered
    bacc_year = Column(SmallInteger, nullable=True)

    # الفرع الثانوي (علمي/أدبي) — حقل مكتشف من كود الفرونت الفعلي، nullable
    # بالـ DB لنفس سبب bacc_year (لسجلات walk-in)
    certificate_type = Column(SAEnum(CertificateType, name="certificate_type_enum"), nullable=True)

    # التجمّع (المجال) يلي بيميل إله الطالب — enum بـ 8 قيم + not_chosen_yet،
    # مختلف عن college_enum (راجع تعليق InterestCluster بـ enums.py)
    initial_preferred_major = Column(
        SAEnum(InterestCluster, name="interest_cluster_enum"), nullable=True
    )

    verification_status = Column(
        SAEnum(VerificationStatus, name="verification_status_enum"),
        nullable=False,
        default=VerificationStatus.pending,
    )
    registration_type = Column(SAEnum(RegistrationType, name="registration_type_enum"), nullable=False)
    status = Column(
        SAEnum(StudentStatus, name="student_status_enum"),
        nullable=False,
        default=StudentStatus.pending,
    )

    # صافي النقاط المتراكمة (نقاطي) — محسوبة ومخزّنة، بتتحدّث تلقائياً بعد كل
    # نشاط جديد (checkin أو استبيان) عبر points_service.recalculate_and_store_points
    total_points = Column(SmallInteger, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # لا حاجة لأي cascade هون — سلوك ON DELETE RESTRICT مطبّق أصلاً على مستوى
    # العمود الأجنبي (foreign key) نفسه بجدول checkins، مش بمستوى الـ ORM.
    checkins = relationship("Checkin", back_populates="student")
    bookings = relationship("Booking", back_populates="student", cascade="all, delete-orphan")
    post_survey = relationship(
        "PostSurvey", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    otps = relationship("OTP", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_students_registration_status", "registration_type", "status"),
        # يمنع تسجيل نفس رقم التواصل مرتين لطلاب التسجيل المسبق فقط
        Index(
            "unique_contact_per_registration",
            "contact_platform",
            "contact_id",
            unique=True,
            postgresql_where=(registration_type == RegistrationType.registered),
        ),
    )