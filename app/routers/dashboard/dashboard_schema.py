"""
Pydantic schemas لروتر admin/dashboard — مطابقة لقسم 9 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CertificateType, College, Faculty, Lecture, OpinionChange, UnionSection


class DashboardStatsResponse(BaseModel):
    registered_online_count: int
    students_inside_today: int
    students_inside_all_days: int
    survey_completed_count: int
    registered_no_show_count: int
    walkin_pending_count: int
    walkin_completed_count: int
    total_consultations: int
    game_scans_total: int
    union_scans_total: int


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


class SurveyCompletionItem(BaseModel):
    unique_code: str
    full_name: str | None = None
    contact_id: str | None = None
    first_campus_entry_at: datetime | None = None
    chosen_colleges: list[College] = []
    survey_college: College | None = None
    opinion_change: OpinionChange | None = None
    answered_at: datetime | None = None


class SurveyCompletionsResponse(BaseModel):
    items: list[SurveyCompletionItem]
    page: int
    limit: int
    total: int
    total_pages: int


class RegisteredNoShowItem(BaseModel):
    unique_code: str
    full_name: str | None = None
    contact_id: str | None = None
    created_at: datetime


class RegisteredNoShowListResponse(BaseModel):
    items: list[RegisteredNoShowItem]
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


class UnionSectionCountItem(BaseModel):
    section: UnionSection
    label: str
    count: int


class AnalyticsResponse(BaseModel):
    college_visits: list[CollegeVisitItem]
    lecture_attendance: list[LectureAttendanceItem]
    score_distribution: list[ScoreBucketItem]
    year_distribution: list[YearCountItem]
    certificate_distribution: list[CertificateCountItem]
    union_sections: list[UnionSectionCountItem]