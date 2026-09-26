"""
Pydantic schemas لروتر admin/dashboard — مطابقة لقسم 9 بملف wijhatak_api_contract.md
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.enums import (
    CertificateType,
    College,
    Faculty,
    Lecture,
    OpinionChange,
    RegistrationType,
    UnionSection,
)

EventDay = Literal["all", "wed", "thu", "sat"]

# وضع عدّ زيارات الكلية: "all" كل حجز عداد زيارة، و"unique" الطالب مرة وحدة.
CollegeVisitMode = Literal["all", "unique"]


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
    registration_type: RegistrationType
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


class DayCountResponse(BaseModel):
    day: EventDay
    count: int
    generated_at: datetime


class DayCollegeVisitsResponse(BaseModel):
    day: EventDay
    mode: CollegeVisitMode
    total: int
    items: list[CollegeVisitItem]
    generated_at: datetime


class AttendanceSplitItem(BaseModel):
    """شريحة وحدة من تقسيم الحضور — المفتاح بيتعرف عليه الواجهة."""

    key: Literal["registered_in", "walkin_in", "registered_out"]
    count: int


class AttendanceSplitResponse(BaseModel):
    """مين فات عالجامعة — مسجّلون فatroا، Walk-in فatroا، ومسجّلون ما فatroا."""

    day: EventDay
    # الشرائح الثلاث بالترتيب: registered_in, walkin_in, registered_out.
    items: list[AttendanceSplitItem]
    total: int
    generated_at: datetime


class DayUnionSectionsResponse(BaseModel):
    day: EventDay
    total: int
    items: list[UnionSectionCountItem]
    generated_at: datetime


class PresenceDayItem(BaseModel):
    day: EventDay
    avg_minutes: int
    students_counted: int


class PresenceFrequency(BaseModel):
    one_day: int
    two_days: int
    all_days: int
    total: int


class PresenceResponse(BaseModel):
    avg_minutes_all: int
    per_day: list[PresenceDayItem]
    frequency: PresenceFrequency
    generated_at: datetime


class PeakHourDayItem(BaseModel):
    day: EventDay
    counts: list[int]


class PeakItem(BaseModel):
    day: EventDay
    hour: int
    count: int


class PeakHoursResponse(BaseModel):
    hours: list[int]
    days: list[PeakHourDayItem]
    peak: PeakItem | None
    generated_at: datetime


class TopStudentItem(BaseModel):
    rank: int
    unique_code: str
    full_name: str | None = None
    value: int
    days: int | None = None


class TopStudentsResponse(BaseModel):
    metric: str
    items: list[TopStudentItem]
    page: int
    limit: int
    total: int
    total_pages: int
    generated_at: datetime


class CornerBucketItem(BaseModel):
    """عمود بتوزيع الطلاب حسب عدد الأركان اللي زاروها."""

    # 1..4 ركن بالضبط، 5 = "5 أركان فأكثر"، 0 = "ندوة فقط" (زاروا ولا ركن).
    bucket: int
    label: str
    count: int


class CornerPairItem(BaseModel):
    """صف بجدول: زوج أركان (مشترك) أو انتقال مباشر بينهما."""

    # مفتاح الركن: "c:<faculty>" أو "u:<section>" أو "g:game".
    source: str
    target: str
    # التسمية العربية الجاهزة للعرض ("... + ..." للأزواج، "من ... إلى ..." للانتقالات).
    label: str
    count: int


class CornerJourneyResponse(BaseModel):
    """حركة الطلاب بين أركان الفعالية — التوزيع، الأزواج المشتركة، الانتقالات."""

    day: EventDay
    # عدد الطلاب اللي عندهم ركن واحد على الأقل أو ندوة واحدة على الأقل.
    total_students: int
    # عدد الطلاب اللي زاروا ركنين فأكثر (مجموع الأعمدة 2..5).
    multi_corner_students: int
    distribution: list[CornerBucketItem]
    pairs: list[CornerPairItem]
    # مجموع أعداد صفوف الانتقالات (انتقال واحد محسوب لكل زوج متجاور).
    total_transitions: int
    transitions: list[CornerPairItem]
    generated_at: datetime