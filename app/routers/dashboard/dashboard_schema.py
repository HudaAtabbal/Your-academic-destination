"""
Pydantic schemas لروتر admin/dashboard — مطابقة لقسم 9 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Lecture


class DashboardStatsResponse(BaseModel):
    registered_online_count: int
    students_inside_today: int
    students_inside_all_days: int
    survey_completed_count: int
    walkin_pending_count: int
    walkin_completed_count: int


class RoomOccupancyItem(BaseModel):
    lecture_name: Lecture
    hall_label: str
    current_count: int
    last_updated: datetime


class RoomsOccupancyResponse(BaseModel):
    rooms: list[RoomOccupancyItem]


class SmsCounts(BaseModel):
    pending: int
    sending: int
    sent: int
    failed: int


class SmsStatusResponse(BaseModel):
    counts: SmsCounts
    last_heartbeat: datetime | None
    worker_online: bool