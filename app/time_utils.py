"""
مصدر الوقت الموحّد للتطبيق — بمنطقة سوريا (Asia/Damascus) بدل توقيت السيرفر.

لماذا؟ السيرفر عملياً خارج سوريا (فارق ساعة+)، والحدث بسوريا. العدادات وحدود
"اليوم" لازم تُعرَّف باليوم التقويمي السوري، وإلا مثلاً 00:30 بسوريا يمكن أن
يُصنّف كـ"يوم سابق" لو اعتمدنا توقيت السيرفر.

الاصطلاح: كل القيم الناتجة naive (بدون tzinfo) — مطابقة لبقية التطبيق.
الساعة قابلة للضبط عبر env APP_TIMEZONE (default Asia/Damascus).
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_DEFAULT_TIMEZONE = "Asia/Damascus"


def _local_zone() -> ZoneInfo:
    return ZoneInfo(os.getenv("APP_TIMEZONE", _DEFAULT_TIMEZONE))


def now_naive() -> datetime:
    """الوقت الحالي بمنطقة سوريا، naive (بدون tzinfo) بنفس اصطلاح التطبيق."""
    return datetime.now(_local_zone()).replace(tzinfo=None)


def today_start() -> datetime:
    """بداية اليوم التقويمي (00:00) بتوقيت سوريا."""
    return now_naive().replace(hour=0, minute=0, second=0, microsecond=0)


def today_end() -> datetime:
    """بداية اليوم التالي — للاستعلامات الفاصلة [start, end)."""
    return today_start() + timedelta(days=1)


def same_day(a: datetime, b: datetime) -> bool:
    """هل التاريخان يقعان بنفس اليوم التقويمي؟"""
    return a.date() == b.date()