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
from app.errors import checkin_not_found
from app.models import (
    ActivityType,
    Booking,
    BookingType,
    CertificateType,
    Checkin,
    Faculty,
    Lecture,
    PostSurvey,
    RegistrationType,
    Student,
    StudentStatus,
    UnionSection,
    VerificationStatus,
)
from app.routers.checkins import checkin_service
from app.routers.internal import internal_service
from app.routers.points import point_service

_HALL_LABEL = "المدرج الرئيسي"


def get_hall_label() -> str:
    """تسمية القاعة الوحيدة (مدرج رئيسي) — نفس القيمة المعروضة بإشغال القاعات."""
    return _HALL_LABEL


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

    # إجمالي الاستشارات الفردية المنفذة — عدّ سجلات checkin بنوع consultation
    # (تراكمي لكل الأيام). كل طالب بيسجّل استشارة مرة وحدة بالكامل عن طريق
    # فهرس unique_consultation_checkin، فالعدد يساوي عدد الطلاب المنجزين للاستشارة.
    total_consultations = (
        db.query(Checkin)
        .filter(Checkin.activity_type == ActivityType.consultation)
        .count()
    )

    # مسحات ركن الترفيه وركن الاتحاد — إجمالية (تراكمي لكل الأيام).
    # كل طالب بينمسح مرة وحدة بطول الفعالية (فهرس unique_game_checkin /
    # unique_union_checkin)، فالعدد يساوي عدد الطلاب الممسوحين.
    game_scans_total = (
        db.query(Checkin)
        .filter(Checkin.activity_type == ActivityType.game)
        .count()
    )

    union_scans_total = (
        db.query(Checkin)
        .filter(Checkin.activity_type == ActivityType.union)
        .count()
    )

    return {
        "registered_online_count": registered_online_count,
        "students_inside_today": students_inside_today,
        "students_inside_all_days": students_inside_all_days,
        "survey_completed_count": survey_completed_count,
        "walkin_pending_count": walkin_pending_count,
        "walkin_completed_count": walkin_completed_count,
        "total_consultations": total_consultations,
        "game_scans_total": game_scans_total,
        "union_scans_total": union_scans_total,
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


def list_hall_students(db: Session, lecture_name: Lecture) -> list[dict]:
    """الطلاب المسجّلون حالياً داخل قاعة محاضرة معيّنة (اليوم فقط، بتوقيت سوريا)."""
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    rows = (
        db.query(Checkin, Student)
        .join(Student, Checkin.student_id == Student.id)
        .filter(
            Checkin.activity_type == ActivityType.lecture,
            Checkin.lecture_name == lecture_name,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .order_by(Checkin.checked_in_at.asc())
        .all()
    )

    return [
        {
            "checkin_id": checkin.id,
            "unique_code": student.unique_code,
            "full_name": student.full_name,
            "checked_in_at": checkin.checked_in_at,
        }
        for checkin, student in rows
    ]


def clear_hall_occupancy(db: Session, lecture_name: Lecture) -> int:
    """إفراغ قاعة محاضرة ليوم — حذف كل سجلات دخول الطلاب القدام لها.

    ملاحظة مهمة: الحذف غير مقيّد بأي سعة — حتى لو نزّلنا السعة (room capacity)
    تحت عدد الموجودين، نضل قادرين نمسح دخول الطلاب. لا يوجد عمود capacity
    بالسكيما، لذا لا يوجد أي فحص يمنع حذف الدخول أبداً.
    """
    today_start = time_utils.today_start()
    today_end = today_start + timedelta(days=1)

    to_delete = (
        db.query(Checkin)
        .filter(
            Checkin.activity_type == ActivityType.lecture,
            Checkin.lecture_name == lecture_name,
            Checkin.checked_in_at >= today_start,
            Checkin.checked_in_at < today_end,
        )
        .all()
    )
    count = len(to_delete)
    for checkin in to_delete:
        db.delete(checkin)
    db.commit()
    return count


def delete_checkin_by_id(db: Session, checkin_id: int) -> None:
    """حذف سجل دخول واحد (لطالب محدد) — للحذف الفردي داخل قاعة الداشبورد."""
    checkin = db.query(Checkin).filter(Checkin.id == checkin_id).first()
    if checkin is None:
        raise checkin_not_found()
    student_id = checkin.student_id
    db.delete(checkin)
    db.commit()
    # إعادة حساب نقاط الطالب — حذف دخول (مثلاً محاضرة) لازم ينعكس على نقاطه/نقاطها
    point_service.recalculate_and_store_points(db, student_id)
    db.commit()


def get_sms_status(db: Session) -> dict:
    """حالة طابور إرسال SMS (أعداد حسب الحالة) + حالة المرسل المحلي."""
    return internal_service.get_sms_status(db)


def list_students_inside_all_days(
    db: Session,
    page: int,
    limit: int,
    code: str | None = None,
    reg_type: str | None = None,
    order: str = "desc",
) -> tuple[list[dict], int]:
    """
    قائمة الطلاب المميزين (distinct) يلي دخلوا الحرم على مدار كل الأيام — تراكمي
    بدون فلترة تاريخ (نفس أساس عدّاد students_inside_all_days). لكل طالب نرجع
    الرمز والاسم ورقم التواصل ومجموع نقاطه المخزّنة (total_points) — بدون أي
    حساب معقّد وقت الطلب، لأنه عمود مخزّن ومحدّث تلقائياً.

    الفلترة/الترتيب:
    - code: بحث جزئي بالرمز (ILIKE) — ما بفرّق بين walk_in و registered.
    - reg_type: "R" للمسجّلين أو "W" للووك إن (يُطهّر على RegistrationType).
    - order: "desc" (الأعلى نقاطاً أولاً) أو "asc" (الأقل أولاً).
    - الصفحات مرتبة دائماً بنفس الترتيب الثانوي (unique_code) لترقيم ثابت.
    """
    # طلاب ممن دخلوا الحرم مرة على الأقل (campus_entry) — بدون شرط اليوم.
    inside_student_ids = (
        db.query(Checkin.student_id)
        .filter(Checkin.activity_type == ActivityType.campus_entry)
        .distinct()
        .subquery()
    )

    query = db.query(Student).join(
        inside_student_ids, Student.id == inside_student_ids.c.student_id
    )

    if code:
        query = query.filter(Student.unique_code.ilike(f"%{code}%"))

    if reg_type:
        query = query.filter(
            Student.registration_type
            == (RegistrationType.registered if reg_type == "R" else RegistrationType.walk_in)
        )

    total = query.count()

    order_col = Student.total_points.desc() if order == "desc" else Student.total_points.asc()
    rows = (
        query.order_by(order_col, Student.unique_code.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [
        {
            "unique_code": student.unique_code,
            "full_name": student.full_name,
            "contact_id": student.contact_id,
            "total_points": student.total_points,
        }
        for student in rows
    ]
    return items, total


def get_dashboard_analytics(db: Session) -> dict:
    """
    إحصائيات تفصيلية للوحة المدير العام — كلها إجمالية لكل الأيام (تراكمية).

    - college_visits: "زيارة الكلية (ركن التوجيه)" — عدد الطلاب المميزين اللي
      زاروا الكلية إمّا عبر مسح ركن التوجيه (حجز جولة) أو عبر شيك جولة منفذ عند
      باب الكلية. تُعرض كل أعضاء Faculty الخمسة والعشرين (الكلية بلا زيارات =
      صفر)، مرتّبة تنازلياً بعدد الزيارات.
    - lecture_attendance: حضور المحاضرات — كل الـ16 مضمنة (صفر للفاضي)،
      بترتيب enum، مع الاسم العربي الرسمي لكل محاضرة.
    - score_distribution: توزيع معدل الطالب (bacc_average) على فترات عرض 10
      (0-10 … 90-100) — الحقل اختياري، والقيم الفارغة (NULL) متجاهلة.
    - year_distribution: توزيع سنة الشهادة (bacc_year) — كل سنة فئة، مرتبة
      تصاعدياً، والفارغة متجاهلة.
    - certificate_distribution: الفرع الثانوي — علمي/أدبي (certificate_type).
      الفئتان مدرجتان دائماً حتى لو كانت إحداهما صفراً.
    - union_sections: مسحات ركن الاتحاد لكل قسم (الركن المركزي / دليل التخصص /
      نادي التركي) — إجمالية لكل الأيام، الأقسام الثلاثة مدرجة دائماً (صفر للفاضي).
    """
    # "زيارة الكلية (ركن التوجيه)" — عدد الطلاب المميزين (distinct) اللي زاروا
    # الكلية، إمّا عبر مسح ركن التوجيه (حجز جولة) أو عبر شيك جولة منفذ عند باب
    # الكلية. كل طالب يُحسب مرة واحدة لكل كلية حتى لو عمل الحجز والشيك معاً
    # (union + distinct) — فارح لأي مصدر تاني بس يثبت مرور الطالب.
    college_visit_sources = (
        db.query(
            Booking.college.label("college"),
            Booking.student_id.label("student_id"),
        )
        .filter(Booking.booking_type == BookingType.tour)
        .union(
            db.query(
                Checkin.college.label("college"),
                Checkin.student_id.label("student_id"),
            ).filter(Checkin.activity_type == ActivityType.tour)
        )
        .subquery()
    )
    college_visits_rows = (
        db.query(
            college_visit_sources.c.college,
            func.count(func.distinct(college_visit_sources.c.student_id)),
        )
        .group_by(college_visit_sources.c.college)
        .all()
    )
    college_count_map = {college: count for college, count in college_visits_rows}
    college_visits = [
        {"college": college, "count": college_count_map.get(college, 0)}
        for college in Faculty
    ]
    college_visits.sort(key=lambda item: item["count"], reverse=True)

    # حضور المحاضرات — كل الـ16 مضمنة بترتيب enum.
    lecture_rows = (
        db.query(Checkin.lecture_name, func.count(Checkin.id))
        .filter(Checkin.activity_type == ActivityType.lecture)
        .group_by(Checkin.lecture_name)
        .all()
    )
    lecture_count_map = {lecture: count for lecture, count in lecture_rows}
    lecture_attendance = [
        {
            "lecture_name": lecture,
            "label": checkin_service.lecture_display_name(lecture),
            "count": lecture_count_map.get(lecture, 0),
        }
        for lecture in Lecture
    ]

    # توزيع المعدل (bacc_average) على فترات عرض 10 — 0-10 … 90-100.
    score_rows = db.query(Student.bacc_average).filter(Student.bacc_average.isnot(None)).all()
    score_counts = {i: 0 for i in range(0, 100, 10)}
    for (value,) in score_rows:
        bucket = min(int(float(value) // 10) * 10, 90)
        score_counts[bucket] += 1
    score_distribution = [
        {"label": f"{start}-{start + 10}", "count": score_counts[start]}
        for start in sorted(score_counts)
    ]

    # توزيع سنة الشهادة (bacc_year) — مرتبة تصاعدياً.
    year_rows = (
        db.query(Student.bacc_year, func.count(Student.id))
        .filter(Student.bacc_year.isnot(None))
        .group_by(Student.bacc_year)
        .order_by(Student.bacc_year.asc())
        .all()
    )
    year_distribution = [
        {"year": year, "count": count} for year, count in year_rows
    ]

    # الفرع الثانوي — علمي/أدبي (الفئتان مدرجتان دائماً حتى لو بصفر).
    cert_rows = (
        db.query(Student.certificate_type, func.count(Student.id))
        .filter(Student.certificate_type.isnot(None))
        .group_by(Student.certificate_type)
        .all()
    )
    cert_count_map = {cert: count for cert, count in cert_rows}
    certificate_distribution = [
        {"certificate_type": cert, "count": cert_count_map.get(cert, 0)}
        for cert in (CertificateType.scientific, CertificateType.literary)
    ]

    # مسحات ركن الاتحاد لكل قسم — الأقسام الثلاثة مدرجة دائماً (صفر للفاضي)،
    # بنفس نمط حضور المحاضرات، مع الاسم العربي الرسمي لكل قسم.
    union_rows = (
        db.query(Checkin.union_section, func.count(Checkin.id))
        .filter(Checkin.activity_type == ActivityType.union)
        .group_by(Checkin.union_section)
        .all()
    )
    union_count_map = {section: count for section, count in union_rows}
    union_sections = [
        {
            "section": section,
            "label": checkin_service.union_section_label(section),
            "count": union_count_map.get(section, 0),
        }
        for section in UnionSection
    ]

    return {
        "college_visits": college_visits,
        "lecture_attendance": lecture_attendance,
        "score_distribution": score_distribution,
        "year_distribution": year_distribution,
        "certificate_distribution": certificate_distribution,
        "union_sections": union_sections,
    }