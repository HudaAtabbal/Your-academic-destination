"""
منطق حساب نقاط "نقاطي" — القيم والقواعد مأخوذة حرفياً من تصميم شاشة نقاطي:

| المحطة                | النقاط | ملاحظة                                  |
|------------------------|--------|-------------------------------------------|
| دخول البوابة           | 5      | مرة وحدة كل يوم (يعتمد على unique_campus_entry_checkin الجديد اليومي) |
| حضور ندوة (محاضرة)     | 10     | لكل محاضرة مختلفة، بحد أقصى 3 محاضرات باليوم الواحد |
| جولة كلية              | 10     | لكل كلية مختلفة يزورها، بحد أقصى 3 جولات باليوم الواحد |
| استشارة فردية          | 15     | مرة وحدة بالكامل                          |
| الاستبيان البعدي       | 20     | مرة وحدة بالكامل                          |

⚠️ جدول القيم نفسه (النصوص وأسماء المحطات) ثابت ومعروض بالفرونت مباشرة
("القيم معلنة ولا تتغير") — الباك اند بس بيرجّع total_points النهائي.
ما في مفهوم "ترتيب" (rank) بهالإصدار — تم إلغاؤه بالكامل بقرار صريح.
"""

from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import time_utils
from app.errors import student_not_found
from app.models import ActivityType, Checkin, PostSurvey, Student

_CAMPUS_ENTRY_POINTS = 5
_LECTURE_POINTS = 10
_MAX_LECTURES_PER_DAY = 3  # باليوم الواحد
_TOUR_POINTS = 10
_MAX_TOURS_PER_DAY = 3
_CONSULTATION_POINTS = 15
_SURVEY_POINTS = 20


def get_points(db: Session, unique_code: str) -> int:
    """قراءة النقاط المخزّنة مباشرة (مش حساب لحظي) — أسرع، وهاد مصدر الحقيقة هلق."""
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student.total_points

def get_points_detail(db: Session, unique_code: str) -> dict:
    """نقاط + معلومات السقوف لصفحة "نقاطي" في استدعاء واحد."""
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    breaks = get_lecture_and_tour_breaks(db, student.id)
    return {"total_points": student.total_points, **breaks}

def recalculate_and_store_points(db: Session, student_id: int) -> int:
    total = _calculate_points_for_student_id(db, student_id)
    db.query(Student).filter(Student.id == student_id).update({"total_points": total})
    db.flush()  # بس flush، مش commit — الـ commit صار مسؤولية اللي نادى الدالة
    return total

def _calculate_points_for_student_id(db: Session, student_id: int) -> int:
    day_expr = func.date(Checkin.checked_in_at)

    campus_entry_days = (
        db.query(day_expr)
        .filter(Checkin.student_id == student_id, Checkin.activity_type == ActivityType.campus_entry)
        .distinct()
        .count()
    )
    campus_entry_points = campus_entry_days * _CAMPUS_ENTRY_POINTS

    # المحاضرات: سقف يومي — كل يوم بتُحسب كحد أقصى 3 محاضرات
    lecture_counts_per_day = (
        db.query(day_expr.label("day"), func.count(Checkin.id).label("cnt"))
        .filter(Checkin.student_id == student_id, Checkin.activity_type == ActivityType.lecture)
        .group_by(day_expr)
        .all()
    )
    lecture_points = (
        sum(min(cnt, _MAX_LECTURES_PER_DAY) for _, cnt in lecture_counts_per_day) * _LECTURE_POINTS
    )

    # الجولات: سقف يومي — كل يوم بتُحسب كحد أقصى 3 جولات
    tour_counts_per_day = (
        db.query(day_expr.label("day"), func.count(Checkin.id).label("cnt"))
        .filter(Checkin.student_id == student_id, Checkin.activity_type == ActivityType.tour)
        .group_by(day_expr)
        .all()
    )
    tour_points = (
        sum(min(cnt, _MAX_TOURS_PER_DAY) for _, cnt in tour_counts_per_day) * _TOUR_POINTS
    )

    has_consultation = (
        db.query(Checkin)
        .filter(Checkin.student_id == student_id, Checkin.activity_type == ActivityType.consultation)
        .first()
        is not None
    )
    consultation_points = _CONSULTATION_POINTS if has_consultation else 0

    has_survey = (
        db.query(PostSurvey).filter(PostSurvey.student_id == student_id).first() is not None
    )
    survey_points = _SURVEY_POINTS if has_survey else 0

    return campus_entry_points + lecture_points + tour_points + consultation_points + survey_points


def get_lecture_and_tour_breaks(
    db: Session, student_id: int
) -> dict[str, int | bool]:
    """
    معلومات السقوف لصفحة "نقاطي" — عدد المحاضرات والجولات اليوم
    هل وصل كلٌّ سقفه (المحاضرات والجولات: 3 باليوم الواحد لكل منهما).
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    today_lecture_count = (
        db.query(Checkin)
        .filter(
            Checkin.student_id == student_id,
            Checkin.activity_type == ActivityType.lecture,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .count()
    )
    today_tour_count = (
        db.query(Checkin)
        .filter(
            Checkin.student_id == student_id,
            Checkin.activity_type == ActivityType.tour,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .count()
    )

    return {
        "today_lecture_count": today_lecture_count,
        "lectures_capped_today": today_lecture_count >= _MAX_LECTURES_PER_DAY,
        "today_tour_count": today_tour_count,
        "tours_capped_today": today_tour_count >= _MAX_TOURS_PER_DAY,
    }


def get_leaderboard(db: Session) -> list[dict]:
    """
    لوحة ترتيب شاملة لكل الطلاب — لمسابقة نهاية اليوم (super_admin فقط).
    بما إنه total_points صار عمود مخزّن ومحدّث تلقائياً، هون بس قراءة وترتيب
    بسيطين — بدون أي حساب معقّد وقت الطلب.
    """
    rows = (
        db.query(Student.unique_code, Student.full_name, Student.total_points)
        .order_by(Student.total_points.desc())
        .all()
    )
    return [
        {"unique_code": unique_code, "full_name": full_name, "total_points": total_points}
        for unique_code, full_name, total_points in rows
    ]