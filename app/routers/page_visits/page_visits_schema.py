"""
Pydantic schemas لروتر students/page-visit — تتبّع فتح الصفحات ومدّة البقاء.

المدّة ما بتنقبل من المتصفح أبداً: start يسجّل وقت الدخول على السيرفر
ويرجّع رقم الصف، و end يستقبل الرقم بس — والسيرفر هو اللي يحسب الفرق.
"""

from pydantic import BaseModel, Field


class PageVisitStartRequest(BaseModel):
    """بداية زيارة — المتصفح ما بيكسر إلّا معرّف الصفحة والمتصفح ورمز الطالب."""

    page: str = Field(..., min_length=1, max_length=64)
    visitor_id: str = Field(..., min_length=8, max_length=64)
    student_code: str | None = Field(default=None, max_length=32)


class PageVisitStartResponse(BaseModel):
    """رقم الصف المولّد على السيرفر — بيتبعه العميل بإشارة النهاية."""

    visit_id: int
    entered_at: str


class PageVisitEndRequest(BaseModel):
    """نهاية زيارة — رقم الصف بس. ما في حقل للمدّة (مقصود)."""

    visit_id: int = Field(..., ge=1)


class PageVisitEndResponse(BaseModel):
    visit_id: int
    duration_seconds: float
