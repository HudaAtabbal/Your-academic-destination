"""
Pydantic schemas لروتر checkins — مطابقة لقسم 4 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Faculty, Lecture, UnionSection


class UniqueCodeRequest(BaseModel):
    """جسم الطلب المشترك لكل عمليات المسح يلي بس بتحتاج الرمز الفريد."""

    unique_code: str


class LectureCheckinRequest(BaseModel):
    unique_code: str
    lecture_name: Lecture


class UnionCheckinRequest(BaseModel):
    unique_code: str
    union_section: UnionSection


class CheckinResponse(BaseModel):
    checkin_id: int
    student_name: str | None = None
    checked_in_at: datetime
    lecture_name: Lecture | None = None
    college: Faculty | None = None
    union_section: UnionSection | None = None


class CheckinCountResponse(BaseModel):
    count: int