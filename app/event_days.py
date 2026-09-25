"""
إعداد أيام الفعالية والساعات المعروضة — يغذّي كل تحليلات لوحة المدير v2.

أيام الفعالية (ثلاثة أيام غير متتالية):
  wed = 2026-09-23 (أربعاء)
  thu = 2026-09-24 (خميس)
  sat = 2026-09-26 (سبت)

قابلة للضبط عبر env EVENT_DAYS (تواريخ ISO مفصولة بفواصل) — الترتيب
wed,thu,sat ثابت، المواعيد فقط قابلة للتعديل.
"""

import os
from datetime import date, datetime, time, timedelta

from app.errors import AppError

_DEFAULT_EVENT_DATES = [
    date(2026, 9, 23),  # wed
    date(2026, 9, 24),  # thu
    date(2026, 9, 26),  # sat
]

_DAY_KEYS = ["wed", "thu", "sat"]

# الساعات المعروضة في مخططات الساعة: من 08:00 حتى 17:00 ضمناً.
# الساعات خارج هذا النطاق ما زالت تُحسب لكنها تُسيَّر (تُثبَّت) لأقرب حافة.
EVENT_HOURS = range(8, 18)

# نافذة "وقت الفعالية" الفعلية — المسحات اللي براها (مثلاً 18:00 وما بعد، أو
# قبل 08:00) ما بتدخل حسبات الحضور ولا ساعات الذروة، لأن توقيتها هو وقت
# الإدخال اليدوي مش وقت الزيارة الفعلية (مثال: إدخال متأخر من فريق الكلية
# بين 18:00 و 23:59 يوم 2026-09-24). النهاية مفتوحة ([08:00, 16:00)).
EVENT_WINDOW_START = time(8, 0)
EVENT_WINDOW_END = time(16, 0)


def _load_event_days() -> dict[str, date]:
    raw = os.getenv("EVENT_DAYS", "").strip()
    if not raw:
        return dict(zip(_DAY_KEYS, _DEFAULT_EVENT_DATES))
    parsed = [date.fromisoformat(part.strip()) for part in raw.split(",") if part.strip()]
    return dict(zip(_DAY_KEYS, parsed))


EVENT_DAYS: dict[str, date] = _load_event_days()


def day_range(day_key: str) -> tuple[datetime, datetime] | None:
    """
    الفاصل الزمني [بداية اليوم, بداية اليوم التالي) ليوم فعالية معيّن بتوقيت سوريا.

    "all" تعيد None (بدون فلترة). أي مفتاح غير معروف يرمي خطأ 422-style.
    """
    if day_key == "all":
        return None
    if day_key not in EVENT_DAYS:
        raise AppError(
            status_code=422,
            error_code="invalid_day",
            message=f"اليوم '{day_key}' غير معروف — القيم المقبولة: all, wed, thu, sat",
        )
    day = EVENT_DAYS[day_key]
    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)