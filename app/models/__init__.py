"""
تجميع كل الموديلات والـ enums بمكان واحد، مشان بقية الكود (الروترات مثلاً)
يقدر يعمل: from app.models import Student, Checkin, ActivityType, ...
بدل ما يفتش بأي ملف فرعي كل موديل موجود فيه.

⚠️ مهم: الاستيراد هون لازم يصير قبل أي استدعاء لـ Base.metadata.create_all()
مشان SQLAlchemy تعرف بكل الجداول قبل ما تنشئهن.
"""

from app.models.enums import (
    AccountRole,
    ActivityType,
    BookingType,
    College,
    ContactPlatform,
    Lecture,
    OpinionChange,
    RegistrationType,
    StudentStatus,
    VerificationStatus,
)
from app.models.student import Student
from app.models.checkin import Checkin
from app.models.booking import Booking
from app.models.post_survey import PostSurvey
from app.models.account import Account
from app.models.otp import OTP

__all__ = [
    "Student",
    "Checkin",
    "Booking",
    "PostSurvey",
    "Account",
    "OTP",
    "ContactPlatform",
    "VerificationStatus",
    "RegistrationType",
    "StudentStatus",
    "ActivityType",
    "BookingType",
    "OpinionChange",
    "College",
    "Lecture",
    "AccountRole",
]
