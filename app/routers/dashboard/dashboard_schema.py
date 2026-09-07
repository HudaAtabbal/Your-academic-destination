"""
Pydantic schemas لروتر admin/dashboard — مطابقة لقسم 9 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Lecture


class DashboardStatsResponse(BaseModel):
    registered_online_count: int
    campus_entries_count: int
    activities_today_cumulative: int
    survey_completed_count: int


class RoomOccupancyItem(BaseModel):
    lecture_name: Lecture
    hall_label: str
    current_count: int
    last_updated: datetime


class RoomsOccupancyResponse(BaseModel):
    rooms: list[RoomOccupancyItem]