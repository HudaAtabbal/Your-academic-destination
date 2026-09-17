"""
منطق العمل لإحصائيات لوحة المدير العام — راجع قسم 9 بملف wijhatak_api_contract.md.

ملاحظات القرارات المحسومة:
- registered_online_count: بس registration_type=registered (الاسم "إلكترونياً"
  بيقصد المسجّلين أونلاين تحديداً، مش كل الطلاب — تصحيح عن النسخة الأولى
  بالعقد يلي كانت COUNT(students) بدون فلترة).
- students_inside_today: طلاب مميزون (distinct) دخلوا الحرم اليوم — يصفّر كل
  يوم، بدون مفهوم دخول/خروج لحظي (راجع Business Rules #6).
- students_inside_all_days: طلاب مميزون (distinct) دخلوا الحرم على مدار كل
  الأيام — تراكمي بدون فلترة تاريخ.
- hall_label: قيمة ثابتة — مدرج واحد بس رح يستضيف كل المحاضرات، فما في داعي
  mapping أو عمود جديد بالـ DB (راجع Business Rules #12). لسبب مشابه، ما في
  عمود يربط أي كلية بأي محاضرة بالسكيما الحالية، فحقل "college" اتشال من
  الاستجابة بالكامل بدل ما يترك فاضي بدون تفسير.
"""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import time_utils
from app.models import ActivityType, Checkin, PostSurvey, RegistrationType, Student, StudentStatus, VerificationStatus
from app.routers.internal import internal_service

_HALL_LABEL = "المدرج الرئيسي"


def get_dashboard_stats(db: Session) -> dict:
    registered_online_count = (
        db.query(Student).filter(
            Student.registration_type == RegistrationType.registered,
            Student.verification_status == VerificationStatus.verified,
        ).count()
    )

    # "داخل الحرم اليوم": طلاب مميزون (distinct) سجّلوا دخول حرم اليوم
    # — يصفّر كل يوم، ولا يُعدّ نفس الطالب أكثر من مرة باليوم الواحد.
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)
    students_inside_today = (
        db.query(Checkin.student_id)
        .filter(
            Checkin.activity_type == ActivityType.campus_entry,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .distinct()
        .count()
    )

    # "إجمالي الطلاب داخل الجامعة": طلاب مميزون دخلوا الحرم على مدار كل
    # الأيام — تراكمي بدون فلترة تاريخ.
    students_inside_all_days = (
        db.query(Checkin.student_id)
        .filter(Checkin.activity_type == ActivityType.campus_entry)
        .distinct()
        .count()
    )

    survey_completed_count = db.query(PostSurvey).count()

    walkin_pending_count = (
        db.query(Student)
        .filter(
            Student.registration_type == RegistrationType.walk_in,
            Student.status == StudentStatus.pending,
        )
        .count()
    )

    walkin_completed_count = (
        db.query(Student)
        .filter(
            Student.registration_type == RegistrationType.walk_in,
            Student.status == StudentStatus.complete,
        )
        .count()
    )

    return {
        "registered_online_count": registered_online_count,
        "students_inside_today": students_inside_today,
        "students_inside_all_days": students_inside_all_days,
        "survey_completed_count": survey_completed_count,
        "walkin_pending_count": walkin_pending_count,
        "walkin_completed_count": walkin_completed_count,
    }


def get_rooms_occupancy(db: Session) -> list[dict]:
    """
    إشغال المدرج — محاضرات اليوم فقط (بتوقيت سوريا عبر time_utils).
    محدّث: سابقاً كان يعدّ أياماً كلها بلا فلترة تاريخ تحت تسمية current_count؛
    الآن العداد يقتصر على اليوم، لأن عنوان الحقل الحالي يدل على إشغال لحظي.
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    rows = (
        db.query(
            Checkin.lecture_name,
            func.count(Checkin.id),
            func.max(Checkin.checked_in_at),
        )
        .filter(
            Checkin.activity_type == ActivityType.lecture,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .group_by(Checkin.lecture_name)
        .all()
    )

    return [
        {
            "lecture_name": lecture_name,
            "hall_label": _HALL_LABEL,
            "current_count": count,
            "last_updated": last_updated,
        }
        for lecture_name, count, last_updated in rows
    ]


def get_sms_status(db: Session) -> dict:
    """حالة طابور إرسال SMS (أعداد حسب الحالة) + حالة المرسل المحلي."""
    return internal_service.get_sms_status(db)