"""
منطق العمل لتسجيل الطالب الإلكتروني + OTP + بطاقة QR.
راجع قسم 2 بملف wijhatak_api_contract.md (محدّث بحقول جديدة اكتُشفت من كود
الفرونت الفعلي: certificate_type, certificate_year, average_score,
initial_preferred_major بمستوى تجمّع لا كلية محددة).

إرسال OTP فعلياً عبر SMS (سيرياتيل Bulk Messaging) — راجع app/sms_service.py.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from requests.exceptions import RequestException
from sqlalchemy.orm import Session

from app import sms_service
from app.errors import (
    AppError,
    duplicate_contact,
    otp_invalid,
    otp_too_many_attempts,
    sms_send_failed,
    student_not_found,
)
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
_OTP_EXPIRY_MINUTES = 10
_MAX_OTP_ATTEMPTS = 5
_MAX_RETRIES = 10  # الرموز العشوائية: التصادم نادر، بس مساحة أمان كافية

def _generate_unique_code() -> str:
    """
    رمز عشوائي 6 خانات (R-XXXXXX) بدل المتسلسل (R-0001, R-0002...).
    الرمز المتسلسل كان يسمح بتعداد كل الطلاب عبر محاولة رموز متتالية على
    الـ endpoints العامة (card/points/survey/otp) — وكذلك تزوير QR.
    الشكل نفسه أمام الفرونت (R-6 خانات) — ما في تغيير بالعقد.
    """
    return f"{_PREFIX}-{secrets.randbelow(1_000_000):06d}"


def _generate_otp_code() -> str:
    return f"{secrets.randbelow(10_000):04d}"


def register_student(
    db: Session,
    full_name: str,
    birth_date,
    certificate_year: int,
    certificate_type: CertificateType,
    average_score: float,
    initial_preferred_major: list[College],
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
        if existing_contact.verification_status == VerificationStatus.verified:
            raise duplicate_contact()
        # الطالب مسجّل بس لسا ما تحقق من OTP — بنحذفه ونبلّش من جديد
        # (الرقم ما بينحجز إلا بعد التحقق الكامل + الباركود)
        db.delete(existing_contact)
        db.flush()

    student = None
    for attempt in range(_MAX_RETRIES):
        unique_code = _generate_unique_code()
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
        except IntegrityError as exc:
            constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if constraint_name == "unique_contact_per_registration":
                db.rollback()
                # سباق: طلب تاني سجّل نفس الرقم قبلنا — نشوف: pending نحذفه ونعيده، verified نرفض
                conflicting = (
                    db.query(Student)
                    .filter(
                        Student.contact_platform == contact_platform,
                        Student.contact_id == contact_id,
                        Student.registration_type == RegistrationType.registered,
                    )
                    .first()
                )
                if (
                    conflicting is not None
                    and conflicting.verification_status == VerificationStatus.verified
                ):
                    raise duplicate_contact()
                if conflicting is not None:
                    db.delete(conflicting)
                    db.flush()
                continue
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

def _create_otp(db: Session, student_id: int, unique_code: str, phone: str) -> datetime:
    code = _generate_otp_code()
    expires_at = datetime.now() + timedelta(minutes=_OTP_EXPIRY_MINUTES)

    # الرمز الصريح ما بينخزن — هاش بس (أي قراءة DB ما بتكشف الرموز الصالحة)
    otp = OTP(
        student_id=student_id,
        code=hashlib.sha256(code.encode()).hexdigest(),
        expires_at=expires_at,
    )
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

    return expires_at


def resend_otp(db: Session, unique_code: str) -> datetime:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()

    # إبطال كل الـ OTPs السابقة غير المحققة قبل إصدار الجديد — الرمز القديم
    # ما عاد صالح، وبالتالي حد المحاولات (5) صار حقيقياً مش قابل للتفافي بالـ resend
    db.query(OTP).filter(
        OTP.student_id == student.id,
        OTP.verified == False,  # noqa: E712
    ).delete()
    db.commit()

    try:
        expires_at = _create_otp(db, student.id, student.unique_code, student.contact_id)
    except AppError:
        # فشل إرسال الـ SMS — منمسح آخر OTP انخلق (يتيم، محدش استلم رمزه فعلياً)
        orphaned_otp = (
            db.query(OTP)
            .filter(OTP.student_id == student.id, OTP.verified == False)  # noqa: E712
            .order_by(OTP.id.desc())
            .first()
        )
        if orphaned_otp is not None:
            db.delete(orphaned_otp)
            db.commit()
        raise

    return expires_at
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

    # تجاوز الحد الأقصى للمحاولات على نفس الرمز — لازم تطلب رمز جديد (resend)
    if otp.attempts >= _MAX_OTP_ATTEMPTS:
        raise otp_too_many_attempts()

    # انتهت صلاحية الرمز
    if otp.expires_at < datetime.now():
        raise otp_invalid()

    # الرمز غير صحيح — منزيد العداد ومنرفض، بدون ما نستهلك محاولة لو كان منتهي الصلاحية أصلاً
    # المقارنة على الهاش بهاشتا (compare_digest) — بدون oracle زمني
    if not hmac.compare_digest(otp.code, hashlib.sha256(otp_code.encode()).hexdigest()):
        otp.attempts += 1
        db.commit()
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