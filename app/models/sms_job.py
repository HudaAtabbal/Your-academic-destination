"""
موديل SmsJob — صف مهمة إرسال SMS مؤجلة (async queue).

في وضع SMS_MODE=queue، تسجيل الطالب ينشئ OTP + صف SmsJob (pending) ويرجع
201 فوراً، والمُرسِل الداخلي (لابتوب في سوريا) يسحب الصف عبر /internal/sms
ويرسل الرمز عبر سيرياتيل من IP سوري (سيرياتيل ترفض الإرسال من IP أجنبي).

⚠️ otp_code مخزّن نصاً صريحاً هنا — ضروري لأن المُراسل يحتاج الرمز الفعلي
لإرساله، وotps تخزّن sha256 فقط (لا رجوع). الضمانات: عمر قصير (صلاحية OTP
10 دقائق)، حذف CASCADE عند حذف صف OTP، والتحقق بالرمز يبقى على الهاش.
"""

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import SmsJobStatus


class SmsJob(Base):
    __tablename__ = "sms_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    otp_id = Column(
        BigInteger, ForeignKey("otps.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # نسخة contact_id لحظة الإنشاء — عزل الصف عن أي تعديل لاحق على الطالب
    phone = Column(String(20), nullable=False)
    otp_code = Column(String(4), nullable=False)
    status = Column(
        Enum(SmsJobStatus, name="sms_job_status"),
        nullable=False,
        default=SmsJobStatus.pending,
    )
    attempts = Column(Integer, nullable=False, default=0)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    claimed_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    otp = relationship("OTP")
