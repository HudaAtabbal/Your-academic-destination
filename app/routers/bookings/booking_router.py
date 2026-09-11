"""
Router: bookings — راجع قسم 3 بملف wijhatak_api_contract.md
كل الـ endpoints هون محصورة بدور college_staff (شاشة "ركن التوجيه") — والكلية
بتنجلب من حساب الموظف نفسه، مش من جسم الطلب (نفس مبدأ checkins/tour بالضبط).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_account, require_role
from app.errors import AppError
from app.models import Account, AccountRole, BookingType, College
from app.routers.bookings import booking_service
from app.routers.bookings.booking_schema import (
    BookingCountResponse,
    BookingRequest,
    BookingResponse,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _get_account_college(current_account: Account) -> str:
    if current_account.college is None:
        raise AppError(
            status_code=400,
            error_code="validation_error",
            message="حساب مسؤول الكلية هاد مش مربوط بأي كلية — راجعي الأدمن",
        )
    return current_account.college


@router.post("/tour", response_model=BookingResponse, status_code=201)
def book_tour(
    payload: BookingRequest,
    db: Session = Depends(get_db),
    current_account: Account = Depends(require_role(AccountRole.college_staff)),
) -> BookingResponse:
    college = _get_account_college(current_account)
    booking, student_name = booking_service.create_tour_booking(db, payload.unique_code, college)
    return BookingResponse(
        booking_id=booking.id,
        student_name=student_name,
        booked_at=booking.booked_at,
        college=booking.college,
    )


@router.post(
    "/consultation",
    response_model=BookingResponse,
    status_code=201,
    dependencies=[Depends(require_role(AccountRole.college_staff))],
)
def book_consultation(payload: BookingRequest, db: Session = Depends(get_db)) -> BookingResponse:
    booking, student_name = booking_service.create_consultation_booking(db, payload.unique_code)
    return BookingResponse(
        booking_id=booking.id, student_name=student_name, booked_at=booking.booked_at
    )


@router.get("/count/today", response_model=BookingCountResponse)
def count_bookings_today(
    # نفس توحيد 422: قيمة college غير صالحة = خطأ فاليديشن بدل 500
    booking_type: BookingType,
    college: College | None = None,
    db: Session = Depends(get_db),
    current_account: Account = Depends(get_current_account),
) -> BookingCountResponse:
    count = booking_service.count_bookings_today(db, booking_type, college=college)
    return BookingCountResponse(count=count)