"""
Pydantic schemas لروتر bookings — مطابقة لقسم 3 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import College


class BookingRequest(BaseModel):
    """جسم الطلب المشترك لحجز جولة أو استشارة — بس الرمز الفريد، الكلية تُجلب من حساب الموظف."""

    unique_code: str


class BookingResponse(BaseModel):
    booking_id: int
    student_name: str | None = None
    booked_at: datetime
    college: College | None = None


class BookingCountResponse(BaseModel):
    count: int