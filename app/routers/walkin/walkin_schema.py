"""
Pydantic schemas لروتر walkin — مطابقة لقسم 8 بملف wijhatak_api_contract.md
(محدّث: count بس — الرمز التالي بيتحدد تلقائياً من آخر رمز موجود بالـ DB)
"""

from pydantic import BaseModel, Field


class WalkinCodesGenerateRequest(BaseModel):
    count: int = Field(gt=0, le=500, description="عدد الرموز المطلوب توليدها (1 لـ 500)")


class WalkinCodesGenerateResponse(BaseModel):
    codes: list[str]