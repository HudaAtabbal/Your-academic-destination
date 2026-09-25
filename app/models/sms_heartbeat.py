"""
موديل SmsHeartbeat — جدول أحادي الصف يحفظ آخر نبضة حياة من المُرسِل الداخلي.

المُرسِل (لابتوب في سوريا) يحدّث last_seen_at كل بضع ثوانٍ عبر
POST /internal/sms/heartbeat؛ لوحة الإدارة تعتبر المُرسِل "متصل" إذا كانت
النبضة خلال آخر 180 ثانية.
"""

from sqlalchemy import BigInteger, Column, DateTime
from sqlalchemy.sql import func

from app.database import Base


class SmsHeartbeat(Base):
    __tablename__ = "sms_heartbeats"

    # صف وحيد ثابت بمعرّف 1 عمداً — no-pk single-row upsert
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    last_seen_at = Column(DateTime, nullable=False, server_default=func.now())
