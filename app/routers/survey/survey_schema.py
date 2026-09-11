"""
Pydantic schemas لروتر survey — مطابقة لقسم 5 بملف wijhatak_api_contract.md
"""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import College, OpinionChange


class SurveyStatusResponse(BaseModel):
    answered: bool


class SurveySubmitRequest(BaseModel):
    opinion_change: OpinionChange
    preferred_major: College


class SurveySubmitResponse(BaseModel):
    answered_at: datetime