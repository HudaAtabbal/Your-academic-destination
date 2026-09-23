"""
Pydantic schemas لروتر admin/dashboard — مطابقة لقسم 9 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CertificateType, Faculty, Lecture


class DashboardStatsResponse(BaseModel):
    registered_online_count: int
    students_inside_today: int
    students_inside_all_days: int
    survey_completed_count: int
    walkin_pending_count: int
    walkin_completed_count: int
    total_consultations: int


class RoomOccupancyItem(BaseModel):
    lecture_name: Lecture
    hall_label: str
    current_count: int
    last_updated: datetime


class RoomsOccupancyResponse(BaseModel):
    rooms: list[RoomOccupancyItem]


class HallStudentItem(BaseModel):
    checkin_id: int
    unique_code: str
    full_name: str | None = None
    checked_in_at: datetime


class HallStudentsResponse(BaseModel):
    lecture_name: Lecture
    hall_label: str
    current_count: int
    students: list[HallStudentItem]


class HallClearResponse(BaseModel):
    lecture_name: Lecture
    hall_label: str
    deleted_count: int


class CheckinDeleteResponse(BaseModel):
    checkin_id: int
    deleted: bool


class StudentsInsideItem(BaseModel):
    unique_code: str
    full_name: str | None = None
    contact_id: str | None = None
    total_points: int


class StudentsInsideListResponse(BaseModel):
    items: list[StudentsInsideItem]
    page: int
    limit: int
    total: int
    total_pages: int


class SmsCounts(BaseModel):
    pending: int
    sending: int
    sent: int
    failed: int


class SmsStatusResponse(BaseModel):
    counts: SmsCounts
    last_heartbeat: datetime | None
    worker_online: bool


class CollegeVisitItem(BaseModel):
    college: Faculty
    count: int


class LectureAttendanceItem(BaseModel):
    lecture_name: Lecture
    label: str
    count: int


class ScoreBucketItem(BaseModel):
    label: str
    count: int


class YearCountItem(BaseModel):
    year: int
    count: int


class CertificateCountItem(BaseModel):
    certificate_type: CertificateType
    count: int


class AnalyticsResponse(BaseModel):
    college_visits: list[CollegeVisitItem]
    lecture_attendance: list[LectureAttendanceItem]
    score_distribution: list[ScoreBucketItem]
    year_distribution: list[YearCountItem]
    certificate_distribution: list[CertificateCountItem]