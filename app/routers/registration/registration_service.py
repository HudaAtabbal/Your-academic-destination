"""
منطق العمل لتسجيل الطالب الإلكتروني + OTP + بطاقة QR.
راجع قسم 2 بملف wijhatak_api_contract.md (محدّث بحقول جديدة اكتُشفت من كود
الفرونت الفعلي: certificate_type, certificate_year, average_score,
initial_preferred_major بمستوى تجمّع لا كلية محددة).

إرسال OTP فعلياً عبر SMS (سيرياتيل Bulk Messaging) — راجع app/sms_service.py.
"""

import secrets
import re
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from requests.exceptions import RequestException
from sqlalchemy.orm import Session

from app import sms_service
from app.errors import AppError, duplicate_contact, otp_invalid, sms_send_failed, student_not_found
from app.models import (
    CertificateType,
    ContactPlatform,
    College,
    OTP,
    RegistrationType,
    Student,
    VerificationStatus,
)

_PREFIX = "R"
_DIGITS = 4
_CODE_PATTERN = re.compile(rf"^{_PREFIX}-(\d+)$")
_OTP_EXPIRY_MINUTES = 10
_MAX_OTP_ATTEMPTS = 5
_MAX_RETRIES = 5

def _get_next_unique_code(db: Session) -> str:
    """
    نفس نمط walkin_service._get_next_number بالضبط — بس بادئة R بدل W.
    بيدوّر على أعلى رقم R-XXXX موجود ويرجع اللي بعده (أو 1 لو ما في ولا رمز).
    """
    existing_codes = (
        db.query(Student.unique_code).filter(Student.unique_code.like(f"{_PREFIX}-%")).all()
    )
    max_number = 0
    for (code,) in existing_codes:
        match = _CODE_PATTERN.match(code)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"{_PREFIX}-{str(max_number + 1).zfill(_DIGITS)}"


def _generate_otp_code() -> str:
    return f"{secrets.randbelow(10_000):04d}"

_MAX_RETRIES = 5

def register_student(
    db: Session,
    full_name: str,
    birth_date,
    certificate_year: int,
    certificate_type: CertificateType,
    average_score: float,
    initial_preferred_major: College,
    contact_platform: ContactPlatform,
    contact_id: str,
) -> tuple[Student, str]:
    existing_contact = (
        db.query(Student)
        .filter(
            Student.contact_platform == contact_platform,
            Student.contact_id == contact_id,
            Student.registration_type == RegistrationType.registered,
        )
        .first()
    )
    if existing_contact is not None:
        raise duplicate_contact()

    student = None
    for attempt in range(_MAX_RETRIES):
        unique_code = _get_next_unique_code(db)
        student = Student(
            unique_code=unique_code,
            full_name=full_name,
            birth_date=birth_date,
            bacc_year=certificate_year,
            certificate_type=certificate_type,
            bacc_average=average_score,
            initial_preferred_major=initial_preferred_major,
            contact_platform=contact_platform,
            contact_id=contact_id,
            registration_type=RegistrationType.registered,
            verification_status=VerificationStatus.pending,
        )
        db.add(student)
        try:
            db.commit()
            db.refresh(student)
            break
        except IntegrityError:
            db.rollback()
            if attempt == _MAX_RETRIES - 1:
                raise AppError(
                    status_code=500,
                    error_code="registration_failed",
                    message="تعذّر إتمام التسجيل حالياً، حاولي مرة تانية",
                )

    try:
        _create_otp(db, student.id, student.unique_code, student.contact_id)
    except AppError:
        db.query(OTP).filter(OTP.student_id == student.id).delete()
        db.delete(student)
        db.commit()
        raise

    return student, unique_code

def _create_otp(db: Session, student_id: int, unique_code: str, phone: str) -> str:
    code = _generate_otp_code()
    expires_at = datetime.now() + timedelta(minutes=_OTP_EXPIRY_MINUTES)

    otp = OTP(student_id=student_id, code=code, expires_at=expires_at)
    db.add(otp)
    db.commit()

    try:
        sms_service.send_otp_sms(phone, code)
    except sms_service.SmsSendError as e:
        # سيرياتيل نفسها ردّت برسالة خطأ (حساب موقوف، بارامترات غلط، إلخ)
        raise sms_send_failed(str(e))
    except RequestException as e:
        # فشل الاتصال نفسه (سيرفر سيرياتيل واقف، مشكلة شبكة، إلخ)
        raise sms_send_failed(f"connection_error: {e}")

    return code


def resend_otp(db: Session, unique_code: str) -> datetime:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()

    code = _create_otp(db, student.id, student.unique_code, student.contact_id)
    otp = (
        db.query(OTP)
        .filter(OTP.student_id == student.id, OTP.code == code)
        .order_by(OTP.id.desc())
        .first()
    )
    return otp.expires_at
def verify_otp(db: Session, unique_code: str, otp_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()

    if student is None:
        raise student_not_found()

    otp = (
        db.query(OTP)
        .filter(
            OTP.student_id == student.id,
            OTP.verified == False,  # noqa: E712
        )
        .order_by(OTP.id.desc())
        .first()
    )

    if otp is None:
        raise otp_invalid()

    # انتهت صلاحية الرمز
    if otp.expires_at < datetime.now():
        raise otp_invalid()

    # الرمز غير صحيح
    if otp.code != otp_code:
        raise otp_invalid()

    # الرمز صحيح
    otp.verified = True
    otp.verified_at = datetime.now()

    student.verification_status = VerificationStatus.verified

    db.commit()
    db.refresh(student)

    return student

def get_student_card(db: Session, unique_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student


def lookup_by_contact(db: Session, contact_platform: ContactPlatform, contact_id: str) -> Student:
    student = (
        db.query(Student)
        .filter(Student.contact_platform == contact_platform, Student.contact_id == contact_id)
        .first()
    )
    if student is None:
        raise student_not_found()
    return student