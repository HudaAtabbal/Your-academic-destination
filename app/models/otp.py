"""
موديل OTP — رموز التحقق المؤقتة لمسار التسجيل الإلكتروني.
مطابق تماماً لجدول otps بـ wijhatak_schema_v2.sql.
جدول مؤقت بطبيعته — بينتظف يومياً بمهمة مجدولة (Scheduled Job) بمنطق الـ backend.
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String ,INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class OTP(Base):
    __tablename__ = "otps"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    code = Column(String(10), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False, index=True)

    verified = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="otps")