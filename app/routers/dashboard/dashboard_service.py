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

from sqlalchemy import Date, Time, cast, func, or_
from sqlalchemy.orm import Session

from app import cache, time_utils
from app.errors import checkin_not_found, validation_error
from app.event_days import (
    EVENT_DAYS,
    EVENT_WINDOW_END,
    EVENT_WINDOW_START,
    day_range,
)
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

    # "مسجّلون سجّالوا عالموقع وما حضرولها" — طلاب مسجّلون موثّقون (verified)
    # بدون أي دخول من بوابة الجامعة على الإطلاق، وبدون أي زيارة لكلية (لا حجز
    # ولا شيك جولة/استشارة مسجّل على كلية). نفس منطق count/list بالنازل.
    registered_no_show_count = _registered_no_show_query(db).count()

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

    # إجمالي الاستشارات الفردية — عدّ سجلات bookings بنوع استشارة
    # (تراكمي لكل الأيام). استشارة إلزامية مرة وحدة لكل طالب، فيساوي تقريباً
    # عدد الطلاب اللي نفّذوا استشارتهم، لكن المصدر الرسمي هو الحجوزات مش المسحات.
    total_consultations = (
        db.query(Booking)
        .filter(Booking.booking_type == BookingType.consultation)
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
        "registered_no_show_count": registered_no_show_count,
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


def _registered_no_show_query(db: Session):
    """
    استعلام الـ"مسجّلون بلا حضور": طلاب مسجّلون أونلاين وموثّقون (verified)
    أولّ ما جاوُ للفعالية إطلاقاً — بدون أي دخول من بوابة الجامعة (لا يوجد
    checkin بنوع campus_entry)، وبدون أي زيارة لكلية (لا حجز ولا شيك جولة/
    استشارة مسجّل على كلية). يستخدمه count الخاص بالبطاقة وقائمة الصفحة.
    """
    has_campus_entry = (
        db.query(Checkin.student_id)
        .filter(
            Checkin.activity_type == ActivityType.campus_entry,
            Checkin.student_id == Student.id,
        )
        .exists()
    )
    has_college_visit = or_(
        db.query(Booking.student_id)
        .filter(Booking.college.isnot(None), Booking.student_id == Student.id)
        .exists(),
        db.query(Checkin.student_id)
        .filter(Checkin.college.isnot(None), Checkin.student_id == Student.id)
        .exists(),
    )
    return db.query(Student).filter(
        Student.registration_type == RegistrationType.registered,
        Student.verification_status == VerificationStatus.verified,
        ~has_campus_entry,
        ~has_college_visit,
    )


def list_registered_no_shows(
    db: Session, page: int, limit: int, code: str | None = None
) -> tuple[list[dict], int]:
    """
    قائمة "مسجّلون بلا حضور" — الطلاب اللي سجّالوا عالموقع وموثّقين بس أولّ
    ما دخلو من بوابة الجامعة ولا فاتو ع أي كلية. مرتبة من الأحدث تسجيلاً.
    البحث بـ code اختياري (بحث جزئي بالرمز/الاسم على التوالي).
    """
    query = _registered_no_show_query(db)

    if code:
        query = query.filter(
            or_(
                Student.unique_code.ilike(f"%{code}%"),
                Student.full_name.ilike(f"%{code}%"),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Student.created_at.desc(), Student.unique_code.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    items = [
        {
            "unique_code": student.unique_code,
            "full_name": student.full_name,
            "contact_id": student.contact_id,
            "created_at": student.created_at,
        }
        for student in rows
    ]
    return items, total


def list_survey_completions(
    db: Session, page: int, limit: int, code: str | None = None
) -> tuple[list[dict], int]:
    """
    قائمة "أكملوا الاستبيان" — كل شخص عبّى الاستبيان البعدي، مع:
    الاسم، الرمز، رقم التواصل، وقت أول دخول من بوابة الجامعة، الكليات اللي
    اختارها وقت التسجيل (initial_preferred_major)، وإجابات الاستبيان
    (opinion_change + preferred_major) + وقت الإجابة. مرتبة من الأحدث إجابةً.
    """
    first_campus_entry_at = (
        db.query(Checkin.checked_in_at)
        .filter(
            Checkin.student_id == Student.id,
            Checkin.activity_type == ActivityType.campus_entry,
        )
        .order_by(Checkin.checked_in_at.asc())
        .limit(1)
        .scalar_subquery()
    )

    query = (
        db.query(PostSurvey, Student, first_campus_entry_at.label("first_campus_entry_at"))
        .join(Student, PostSurvey.student_id == Student.id)
    )

    total_query = db.query(PostSurvey).join(
        Student, PostSurvey.student_id == Student.id
    )

    if code:
        filter_ = or_(
            Student.unique_code.ilike(f"%{code}%"),
            Student.full_name.ilike(f"%{code}%"),
        )
        query = query.filter(filter_)
        total_query = total_query.filter(filter_)

    total = total_query.count()
    rows = (
        query.order_by(PostSurvey.answered_at.desc(), Student.unique_code.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [
        {
            "unique_code": student.unique_code,
            "full_name": student.full_name,
            "contact_id": student.contact_id,
            "registration_type": student.registration_type,
            "first_campus_entry_at": first_entry,
            "chosen_colleges": [c for c in (student.initial_preferred_major or [])],
            "survey_college": survey.preferred_major,
            "opinion_change": survey.opinion_change,
            "answered_at": survey.answered_at,
        }
        for survey, student, first_entry in rows
    ]
    return items, total


# الكليات المدمجة/المستثناة من قائمة زيارات الكلية — تُحسب ولا تُعرض كصفوف
# مستقلة: الموسيقا دُمجت ضمن الركن المركزي بالاتحاد، والطب البشري والصيدلة
# دُمجتا بالمجمع الطبي (طب الأسنان).
_VISITS_EXCLUDED = {Faculty.music, Faculty.medicine, Faculty.pharmacy}


def _college_visit_counts(
    db: Session, start: datetime | None = None, end: datetime | None = None
) -> dict[Faculty, int]:
    """
    عدد الطلاب المميزين (distinct) اللي زاروا كل كلية — عبر حجوزات الجولة
    (Booking بكتغوري tour) فقط، والكلية مطلوبة (college is not null).
    المسحات (check-ins) وحجوزات الاستشارة ما بتدخل هون إطلاقاً.

    start/end اختياريان — لو انبعتا، الفلترة الزمنية تنسحب على booked_at
    بس. يارجع خريطة كاملة (بما فيها الكليات المستثناة من العرض) لأنها تستخدم
    بموضعين: قائمة زيارات الكلية ودمج الموسيقا ضمن دليل الاتحاد.
    """
    q = (
        db.query(Booking.college, func.count(func.distinct(Booking.student_id)))
        .filter(
            Booking.booking_type == BookingType.tour,
            Booking.college.is_not(None),
        )
    )
    if start is not None:
        q = q.filter(Booking.booked_at >= start, Booking.booked_at < end)

    rows = q.group_by(Booking.college).all()
    return {college: count for college, count in rows}


def _union_section_counts(
    db: Session,
    college_counts: dict[Faculty, int],
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict[UnionSection, int]:
    """
    مسحات ركن الاتحاد لكل قسم (الركن المركزي / دليل التخصص / نادي التركي).

    "كلية الموسيقا" ما عادت ركن مستقل بالفعالية، فأي زيارة/إضافة مسجّلة عليها
    تُحسب على «الركن المركزي» وتختفي الموسيقا من قائمة زيارات الكليات — نفس
    قرار dimfes في /analytics.
    """
    union_q = (
        db.query(Checkin.union_section, func.count(Checkin.id))
        .filter(Checkin.activity_type == ActivityType.union)
    )
    if start is not None:
        union_q = union_q.filter(Checkin.checked_in_at >= start, Checkin.checked_in_at < end)
    rows = union_q.group_by(Checkin.union_section).all()
    union_count_map = {section: count for section, count in rows}
    union_count_map[UnionSection.central] = (
        union_count_map.get(UnionSection.central, 0)
        + college_counts.get(Faculty.music, 0)
    )
    return union_count_map


def get_dashboard_analytics(db: Session) -> dict:
    """
    إحصائيات تفصيلية للوحة المدير العام — كلها إجمالية لكل الأيام (تراكمية).

    - college_visits: "زيارة الكلية (ركن التوجيه)" — عدد الطلاب المميزين اللي
      زاروا الكلية عبر أي مسح بيسجّل كلية (حجز/شيك جولة أو استشارة عند الكلية).
      تُعرض كل أعضاء Faculty عدا كلية الموسيقا (دُمجت ضمن «الركن المركزي»
      بالاتحاد). الطب البشري والصيدلة ما عادن ركنان مستقلان — دُمجتا ضمن
      مجموعة واحدة باسم «المجمع الطبي» (كلية طب الأسنان) بعملية دمج بيانات
      لمرة وحدة، ولذلك لا تكونان كصفين منفصلين هنا. مرتّبة تنازلياً.
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
    # الكلية، عبر أي مسح سجّل كلية: حجز/شيك جولة، أو حجز/شيك استشارة عند باب
    # الكلية. كل طالب يُحسب مرة واحدة لكل كلية حتى لو عمل الحجز والشيك معاً
    # (union + distinct) — فارح لأي مصدر تاني بس يثبت مرور الطالب.
    college_count_map = _college_visit_counts(db)
    college_visits = [
        {"college": college, "count": college_count_map.get(college, 0)}
        for college in Faculty
        if college not in _VISITS_EXCLUDED
    ]
    college_visits.sort(key=lambda item: item["count"], reverse=True)

    # حضور المحاضرات — كل الـ16 مضمنة بترتيب enum، إلّا العناصر اللي ضمن مجموعة
    # دمج (ندوات الهندسة الثلاث) بتنعرض وحدة: العنصر الأول بالمجموعة بياخد
    # الأرقام كلها، والباقي بينحذف من القائمة.
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
            "count": sum(
                lecture_count_map.get(member, 0)
                for member in checkin_service.lecture_merge_group(lecture)
            ),
        }
        for lecture in Lecture
        if checkin_service.lecture_canonical(lecture) == lecture
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
    year_distribution = [{"year": year, "count": count} for year, count in year_rows]

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
    union_count_map = _union_section_counts(db, college_count_map)

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


def _resolve_day_range(day: str) -> tuple[datetime, datetime] | None:
    """الفاصل الزمني ليوم فعالية — 'all' تصفّر الفلترة (None). يوم غير معروف → 422."""
    return day_range(day)


# ---------------------------------------------------------------------------
# نقاط نهاية v2 — عدادات مفلترة باليوم (قسم 3.1)
# ---------------------------------------------------------------------------


def count_students_inside_for_day(db: Session, day: str) -> int:
    """
    طلاب مميزون (distinct) دخلوا الحرم (campus_entry). مع day != all تكون
    الفلترة على تاريخ سوري (المسح السجّل داخل ذلك اليوم). مع day = all تعيد
    نفس قيمة students_inside_all_days (تراكمي، بدون فلترة).
    """
    rng = _resolve_day_range(day)
    q = (
        db.query(Checkin.student_id)
        .filter(Checkin.activity_type == ActivityType.campus_entry)
    )
    if rng is not None:
        start, end = rng
        q = q.filter(Checkin.checked_in_at >= start, Checkin.checked_in_at < end)
    return q.distinct().count()


def count_game_scans_for_day(db: Session, day: str) -> int:
    """عدد مسحات ركن الترفيه (activity_type = game) — اليوم المحدد أو كل الأيام."""
    rng = _resolve_day_range(day)
    q = db.query(Checkin).filter(Checkin.activity_type == ActivityType.game)
    if rng is not None:
        start, end = rng
        q = q.filter(Checkin.checked_in_at >= start, Checkin.checked_in_at < end)
    return q.count()


def college_visits_for_day(db: Session, day: str) -> dict:
    """
    زيارة الكلية (ركن التوجيه) مفلترة باليوم — نفس منطق /analytics بالضبط
    (union الحجوزات والمسحات، استثناء الموسيقا/الطب/الصيدلة، ترتيب تنازلي).
    الفلترة الزمنية على booked_at للحجوزات و checked_in_at للمسحات.
    """
    rng = _resolve_day_range(day)
    start, end = rng if rng is not None else (None, None)
    college_count_map = _college_visit_counts(db, start, end)
    items = [
        {"college": college, "count": college_count_map.get(college, 0)}
        for college in Faculty
        if college not in _VISITS_EXCLUDED
    ]
    items.sort(key=lambda item: item["count"], reverse=True)
    return {"items": items, "total": sum(item["count"] for item in items)}


def union_sections_for_day(db: Session, day: str) -> dict:
    """مسحات ركن الاتحاد لكل قسم مفلترة باليوم — الأقسام الثلاثة مدرجة دائماً."""
    rng = _resolve_day_range(day)
    start, end = rng if rng is not None else (None, None)
    college_count_map = _college_visit_counts(db, start, end)
    union_count_map = _union_section_counts(db, college_count_map, start, end)
    items = [
        {
            "section": section,
            "label": checkin_service.union_section_label(section),
            "count": union_count_map.get(section, 0),
        }
        for section in UnionSection
    ]
    return {"items": items, "total": sum(item["count"] for item in items)}


# ---------------------------------------------------------------------------
# حضور (قسم 3.2) — presence
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = 300


def _presence_rows(db: Session):
    """
    مدة التواجد لكل (student_id, يوم سوري): من أول لآخر نشاط لذلك اليوم.

    تُحسب فقط المسحات اللي وقتها (time-of-day) ضمن نافذة الفعالية
    [EVENT_WINDOW_START, EVENT_WINDOW_END) — المسحات برا النافذة (مثلاً
    إدخالات 18:00–23:59 التي تسجّل وقت الإدخال مش وقت الزيارة) متجاهلة
    كلياً. تُستبعد الأزواج التي فيها مسحة وحيدة (مدتها صفر) قبل أي متوسط.
    بما أن النافذة طولها 8 ساعات، أي مدة (student, day) مستحيل تتجاوز 8 ساعات.
    """
    event_dates = list(EVENT_DAYS.values())
    day_col = cast(Checkin.checked_in_at, Date)
    time_col = cast(Checkin.checked_in_at, Time)
    rows = (
        db.query(
            Checkin.student_id,
            day_col.label("day"),
            func.min(Checkin.checked_in_at).label("first_at"),
            func.max(Checkin.checked_in_at).label("last_at"),
            func.count(Checkin.id).label("n_checkins"),
        )
        .filter(
            day_col.in_(event_dates),
            time_col >= EVENT_WINDOW_START,
            time_col < EVENT_WINDOW_END,
        )
        .group_by(Checkin.student_id, day_col)
        .all()
    )
    # الأزواج ذات المسحة الواحدة مدتها صفر — تُستبعد من الحساب أصلاً.
    return [
        {
            "student_id": student_id,
            "day": day,
            "minutes": int((last_at - first_at).total_seconds() // 60),
        }
        for student_id, day, first_at, last_at, n_checkins in rows
        if n_checkins >= 2
    ]


def _presence_frequency(db: Session) -> dict:
    """
    تكرار الحضور: لكل طالب، عدد الأيام المميزة (ضمن أيام الفعالية الثلاثة) التي
    دخل منها الحرم (campus_entry). يُجمّع إلى: يوم واحد / يومين / كل الأيام الثلاثة.
    total لازم يساوي students_inside_all_days (داخلون من البوابة خلال أيام الفعالية).
    """
    event_dates = list(EVENT_DAYS.values())
    rows = (
        db.query(
            Checkin.student_id,
            func.count(func.distinct(cast(Checkin.checked_in_at, Date))),
        )
        .filter(
            Checkin.activity_type == ActivityType.campus_entry,
            cast(Checkin.checked_in_at, Date).in_(event_dates),
        )
        .group_by(Checkin.student_id)
        .all()
    )
    one_day = two_days = all_days = 0
    for _student_id, n_days in rows:
        if n_days == 1:
            one_day += 1
        elif n_days == 2:
            two_days += 1
        else:
            all_days += 1
    return {
        "one_day": one_day,
        "two_days": two_days,
        "all_days": all_days,
        "total": one_day + two_days + all_days,
    }


def get_presence_stats(db: Session) -> dict:
    """إحصاءات الحضور الكاملة (متوسط المدة + التكرار) — تُخزَّن بالذاكرة المؤقتة."""
    def _compute() -> dict:
        pairs = _presence_rows(db)
        per_day: dict[str, list[int]] = {key: [] for key in EVENT_DAYS}
        for pair in pairs:
            day_key = next(
                (k for k, v in EVENT_DAYS.items() if v == pair["day"]), None
            )
            if day_key is None:
                continue
            per_day[day_key].append(pair["minutes"])

        def _avg(values: list[int]) -> int:
            return round(sum(values) / len(values)) if values else 0

        avg_minutes_all = (
            round(sum(pair["minutes"] for pair in pairs) / len(pairs)) if pairs else 0
        )

        return {
            "avg_minutes_all": avg_minutes_all,
            "per_day": [
                {
                    "day": key,
                    "avg_minutes": _avg(per_day[key]),
                    "students_counted": len(per_day[key]),
                }
                for key in EVENT_DAYS
            ],
            "frequency": _presence_frequency(db),
        }

    return cache.cached_call(
        "dashboard:presence", _CACHE_TTL_SECONDS, _compute
    )


# ---------------------------------------------------------------------------
# ساعات الذروة (قسم 3.3) — peak-hours
# ---------------------------------------------------------------------------


def get_peak_hours(db: Session) -> dict:
    """
    عدد المسحات (كل الأنواع) لكل ساعة من نافذة الفعالية ولكل يوم فعالية.
    الساعات المعروضة 8..15 (من EVENT_WINDOW_START حتى قبل EVENT_WINDOW_END)؛
    أي مسحة وقتها خارج النافذة (مثلاً إدخالات 18:00–23:59) بتتجاهل تماماً بدل
    ما تثبت على أقرب حافة. peak = أعلى خلية (None لو كلها صفر).
    """
    def _compute() -> dict:
        event_dates = list(EVENT_DAYS.values())
        day_col = cast(Checkin.checked_in_at, Date)
        hour_col = func.extract("hour", Checkin.checked_in_at)
        rows = (
            db.query(
                day_col.label("day"),
                hour_col.label("hour"),
                func.count(Checkin.id).label("count"),
            )
            .filter(
                day_col.in_(event_dates),
                hour_col >= EVENT_WINDOW_START.hour,
                hour_col < EVENT_WINDOW_END.hour,
            )
            .group_by(day_col, hour_col)
            .all()
        )

        hours = list(range(EVENT_WINDOW_START.hour, EVENT_WINDOW_END.hour))
        first = min(hours)
        counts_by_day: dict[str, list[int]] = {
            key: [0] * len(hours) for key in EVENT_DAYS
        }
        for day, hour, count in rows:
            day_key = next((k for k, v in EVENT_DAYS.items() if v == day), None)
            if day_key is None:
                continue
            # الساعات داخل النافذة فقط — خارجها ما بنهتّم فيها هون أصلاً.
            idx = int(hour) - first
            if 0 <= idx < len(hours):
                counts_by_day[day_key][idx] += int(count)

        peak_day = None
        peak_hour = None
        peak_count = 0
        for day_key in EVENT_DAYS:
            for i, count in enumerate(counts_by_day[day_key]):
                if count > peak_count:
                    peak_count = count
                    peak_day = day_key
                    peak_hour = first + i

        return {
            "hours": hours,
            "days": [
                {"day": day_key, "counts": counts_by_day[day_key]}
                for day_key in EVENT_DAYS
            ],
            "peak": (
                {"day": peak_day, "hour": peak_hour, "count": peak_count}
                if peak_day is not None and peak_count > 0
                else None
            ),
        }

    return cache.cached_call("dashboard:peak-hours", _CACHE_TTL_SECONDS, _compute)


# ---------------------------------------------------------------------------
# الطلاب المتميزون (قسم 3.4) — top-students
# ---------------------------------------------------------------------------

_TOPS_AVAILABLE_METRICS = ("lectures", "tours", "presence", "union_all")


def _top_students_rows(db: Session, metric: str) -> list[dict]:
    """القائمة الكاملة (قبل الترقيم) للمقياس المطلوب — [student_id, value, order_key]."""
    if metric == "lectures":
        rows = (
            db.query(Checkin.student_id, func.count(Checkin.id))
            .filter(Checkin.activity_type == ActivityType.lecture)
            .group_by(Checkin.student_id)
            .all()
        )
        return [
            {"student_id": sid, "value": count}
            for sid, count in rows
        ]
    if metric == "tours":
        # عدد حجوزات الجولة لكل طالب (Booking بكتغوري tour) — المسحات ما
        # بتدخل هون. حجز الجولة إلزامية مرة وحدة لكل كلية، فالعدد يساوي عدد
        # الكليات اللي جالها الطالب.
        rows = (
            db.query(Booking.student_id, func.count(Booking.id))
            .filter(Booking.booking_type == BookingType.tour)
            .group_by(Booking.student_id)
            .all()
        )
        return [
            {"student_id": sid, "value": count}
            for sid, count in rows
        ]
    if metric == "presence":
        # مجموع دقائق التواجد لكل طالب عبر كل الأيام (نفس قاعدة استبعاد اليوم
        # ذي المسحة الواحدة من _presence_rows) + عدد الأيام المعدودة لكل طالب.
        totals: dict[int, int] = {}
        day_counts: dict[int, int] = {}
        for pair in _presence_rows(db):
            sid = pair["student_id"]
            totals[sid] = totals.get(sid, 0) + pair["minutes"]
            day_counts[sid] = day_counts.get(sid, 0) + 1
        return [
            {"student_id": sid, "value": value, "days": day_counts.get(sid, 0)}
            for sid, value in totals.items()
        ]
    if metric == "union_all":
        # الطلاب اللي ماسحين كل الأركان الثلاثة — value ثابت 3، الترتيب بآخر
        # مسحة اتحاد تصاعدياً (مين خلّص الأركان أولاً).
        event_dates = list(EVENT_DAYS.values())
        day_col = cast(Checkin.checked_in_at, Date)
        rows = (
            db.query(
                Checkin.student_id,
                func.count(func.distinct(Checkin.union_section)).label("sections"),
                func.max(Checkin.checked_in_at).label("last_at"),
            )
            .filter(
                Checkin.activity_type == ActivityType.union,
                Checkin.union_section.isnot(None),
                day_col.in_(event_dates),
            )
            .group_by(Checkin.student_id)
            .having(func.count(func.distinct(Checkin.union_section)) == 3)
            .all()
        )
        return [
            {"student_id": sid, "value": 3, "order_key": last_at}
            for sid, _sections, last_at in rows
        ]
    raise validation_error(f"مقياس غير معروف: {metric}")


def list_top_students(
    db: Session, metric: str, page: int, limit: int
) -> dict:
    """
    قائمة الطلاب المتميزين للمقياس المعطى، مرتبة تنازلياً حسب القيمة ثم الرمز
    تصاعدياً (استثناء union_all: آخر مسحة تصاعدياً). rank هو الرتبة المطلقة
    (ضمن القائمة الكاملة، قبل الترقيم). تُخزَّن بالذاكرة المؤقتة.
    """
    def _compute() -> dict:
        rows = _top_students_rows(db, metric)
        # الـ students المرتبطين — نجلب الأسماء/الرموز مرة واحدة.
        ids = {row["student_id"] for row in rows}
        students = {
            s.id: s
            for s in db.query(Student).filter(Student.id.in_(ids))
        }

        sort_key = (
            (lambda r: (r.get("order_key") or datetime.min, r["student_id"]))
            if metric == "union_all"
            else (lambda r: (-r["value"], r["student_id"]))
        )
        ranked = sorted(rows, key=sort_key)

        items = []
        for i, row in enumerate(ranked, start=1):
            student = students.get(row["student_id"])
            item = {
                "rank": i,
                "unique_code": student.unique_code if student else "—",
                "full_name": student.full_name if student else None,
                "value": row["value"],
            }
            if row.get("days") is not None:
                item["days"] = row["days"]
            items.append(item)
        return {"items": items, "total": len(items)}

    key = f"dashboard:top-students:{metric}"
    result = cache.cached_call(key, _CACHE_TTL_SECONDS, _compute)
    start = (page - 1) * limit
    return {
        "metric": metric,
        "items": result["items"][start : start + limit],
        "total": result["total"],
    }