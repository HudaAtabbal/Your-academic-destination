"""
خدمة تتبّع الصفحات — قياس مدّة البقاء على السيرفر.

مسار البداية ينشئ الصف ويخزّن وقت الدخول من time_utils.now_naive() (وحدة
الزمن الوحيدة بالتطبيق). مسار النهاية ما بيستقبل أي مدّة من العميل — بيحسب
الفرق بين "الآن" ووقت الدخول المخزّن، يعني المستحيل يخمّن رقم أكبر من الحقيقة.

`id` هو مُعرّف الربط بين المسارين (مش سر): مفتاح أساسي عادي، و end ما بيقبل
إلا صف مدّته لسا فارغة.
"""

from app import time_utils
from app.models.page_visit import PageVisit

# أقصى مدّة بنسجّلها (بالثواني). طالب بيسيب التابلت مفتوح بالبيت overnight
# ما لازم يسمّم متوسط البقاء. 12 ساعة سقف مريح لأي استخدام حقيقي.
MAX_TRACKED_DURATION_SECONDS = 12 * 60 * 60


def start_visit(db, page: str, visitor_id: str, student_code: str | None) -> PageVisit:
    """يسجّل بداية زيارة ويرجّع الصف — وقت الدخول من السيرفر مش من العميل."""
    visit = PageVisit(
        page=page,
        visitor_id=visitor_id,
        student_code=student_code or None,
        entered_at=time_utils.now_naive(),
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


def end_visit(db, visit_id: int) -> tuple[PageVisit, float]:
    """يحسب مدّة الزيارة على السيرفر ويرجّع (الصف، المدّة بالثواني).

    الزيارة اللي مدّتها محسوبة أصلاً بترجّع قيمتها المخزّنة كما هي (تكرار
    آمن لإشارة النهاية). الصف غير موجود بيطلع LookupError.
    """
    visit = db.get(PageVisit, visit_id)
    if visit is None:
        raise LookupError("page visit not found")

    if visit.duration_seconds is not None:
        return visit, visit.duration_seconds

    elapsed = (time_utils.now_naive() - visit.entered_at).total_seconds()
    # حماية من القفزات الغريبة (تعديل ساعة النظام مثلاً).
    duration = max(0.0, min(elapsed, float(MAX_TRACKED_DURATION_SECONDS)))
    visit.duration_seconds = duration
    db.commit()
    db.refresh(visit)
    return visit, duration
