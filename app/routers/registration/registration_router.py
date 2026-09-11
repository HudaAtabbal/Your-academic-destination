"""
Router: registration — تسجيل الطالب الإلكتروني + OTP + بطاقة QR + استرجاع بالرقم.
عام بالكامل (بدون Authorization) — الطالب نفسه هو يلي بيستخدمه من موبايله.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_public_lookup, rate_limit_student_otp
from app.routers.registration import registration_service
from app.routers.registration.registration_schema import (
    LookupByContactRequest,
    LookupByContactResponse,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    ResendOtpResponse,
    StudentCardResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

router = APIRouter(prefix="/students", tags=["registration"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    student, unique_code = registration_service.register_student(
        db,
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        certificate_year=payload.certificate_year,
        certificate_type=payload.certificate_type,
        average_score=payload.average_score,
        initial_preferred_major=payload.initial_preferred_major,
        contact_platform=payload.contact_platform,
        contact_id=payload.contact_id,
    )
    return RegisterResponse(unique_code=unique_code, full_name=student.full_name)


@router.post(
    "/otp/resend",
    response_model=ResendOtpResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def resend_otp(
    payload: ResendOtpRequest,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_public_lookup),
) -> ResendOtpResponse:
    rate_limit_student_otp(payload.unique_code, max_requests=2)  # مهلة resend: 2/دقيقة لكل طالب
    expires_at = registration_service.resend_otp(db, payload.unique_code)
    return ResendOtpResponse(expires_at=expires_at)


@router.post(
    "/otp/verify",
    response_model=VerifyOtpResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit_public_lookup),
) -> VerifyOtpResponse:
    rate_limit_student_otp(payload.unique_code)  # 5 محاولات لكل طالب (محدد في الـ limiter)
    student = registration_service.verify_otp(db, payload.unique_code, payload.otp)
    return VerifyOtpResponse(
        unique_code=student.unique_code,
        full_name=student.full_name,
        verification_status=student.verification_status,
    )


@router.get(
    "/card/{unique_code}",
    response_model=StudentCardResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def get_card(unique_code: str, db: Session = Depends(get_db)) -> StudentCardResponse:
    student = registration_service.get_student_card(db, unique_code)
    return StudentCardResponse(
        unique_code=student.unique_code,
        full_name=student.full_name,
        verification_status=student.verification_status,
        qr_payload=student.unique_code,
    )


@router.post(
    "/lookup-by-contact",
    response_model=LookupByContactResponse,
    dependencies=[Depends(rate_limit_public_lookup)],
)
def lookup_by_contact(
    payload: LookupByContactRequest, db: Session = Depends(get_db)
) -> LookupByContactResponse:
    student = registration_service.lookup_by_contact(
        db, payload.contact_platform, payload.contact_id
    )
    return LookupByContactResponse(unique_code=student.unique_code, full_name=student.full_name)