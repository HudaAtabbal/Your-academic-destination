"""
منطق عجلة الحظ — الأهلية المجمّدة، السحب، والقرار.

⚠️ أسلوب الاستعلامات هون مختلف عن باقي المشروع: بيستخدم select() + db.execute()
بدل db.query(). السبب إن هاد الملف كله CTEs ونافذة row_number()، وكتابة
CTEs بالأسلوب القديم بتطلع معقّدة وغير مقروءة. باقي المشروع ما تأثّر.

الأعمدة الأربعة المحسوبة (freeze_points, raw_lectures, max_span_seconds,
rank_no) بتطلع كلها من استعلام واحد اسمه _ranked_query، و**كل** التابات
بتبني عليه — فالفرق بين تاب والتاني هو الفلترة بعده بس. هيك مستحيل يخلي تاب
يتسلّح قاعدة تاني بالخطأ.

ثلاث قواعد بتتنفّذ هنا ومكتوبة صراحة بالاستعلام، مش بالكود:

  1) التجميد: كل الأرقام بتُحسب بـ effective_freeze = min(now, freeze_at)
     المُقروء من wheel_settings. قبل وقت التجميد النتيجة مطابقة للوقت الحقيقي،
     وبعده ما بتتأثر بأي checkin جديد.
  2) الاستبعاد العالمي: NOT IN (wheel_exclusions) — فلتر بالقيد الفريد على
     student_id، فالطالب المستبعد ما بيطلع بأي تاب بعد ما ينستبعد.
  3) شرط السبت: campus_entry بتاريخ يوم السبت — **غير** مجمّد عمداً، لأنه شرط
     حضور موثّق مش مصدر نقاط. لوudent دخل السبت بعد التجميد بنقص نقاطه
     (النقاط مجمّدة) بس بيبقى مؤهل (شرط الحضور لا).

الترتيب (الجائزة الثالثة/النهائية) مثبّت بالكامل: أطول مدى يومي، ثم أكبر
عدد محاضرات خام، ثم النقاط، ثم كسر التعادل بـ unique_code تصاعدي — عشان نفس
المدخلات ترجّع نفس الترتيب دائماً.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Mapping

from sqlalchemy import Date, Time, case, cast, func, select
from sqlalchemy.orm import Session

from app import time_utils
from app.errors import (
    wheel_draw_already_decided,
    wheel_draw_not_found,
    wheel_freeze_out_of_range,
    wheel_pending_draw_exists,
    wheel_presence_verification_required,
    wheel_reject_confirmation_required,
    wheel_tab_empty,
)
from app.event_days import EVENT_DAYS, EVENT_WINDOW_END, EVENT_WINDOW_START
from app.models import (
    ActivityType,
    Checkin,
    PostSurvey,
    Student,
    WheelDecision,
    WheelDraw,
    WheelDrawStatus,
    WheelExclusion,
    WheelFreezeAudit,
    WheelSettings,
    WheelTab,
)
from app.models.wheel import (
    DRAW_HOUR,
    DRAW_MINUTE,
    default_freeze_at,
)
from app.routers.points.point_service import (
    _CAMPUS_ENTRY_POINTS,
    _CONSULTATION_POINTS,
    _LECTURE_POINTS,
    _MAX_LECTURES_PER_DAY,
    _MAX_TOURS_PER_DAY,
    _SURVEY_POINTS,
    _TOUR_POINTS,
)

# القيم الحرفية لنقاط point_service مستوردة عمداً (بالأسماء اللي فيها _) —
# العكس (نسخها هنا) كان بيخلق مصدرين للحقيقة ينحرفوا عن بعض. لو بدّك نقاط
# مختلفة بالعجلة، غيّرها بمكان واحد: point_service.

SETTINGS_ROW_ID = 1

TAB_ORDER: tuple[WheelTab, ...] = (
    WheelTab.first_prize,
    WheelTab.second_prize,
    WheelTab.third_prize,
    WheelTab.final_prize,
)

_SATURDAY_CRITERION = "دخل من بوابة الجامعة يوم السبت"

# وصف كل تاب للواجهة. criteria نصوص فقط — الواجهة بتعرضها، والباك ما بيقرّر
# شي منها. min_points/top_n هما نفس الأرقام اللي بتفلتر الاستعلام.
_TAB_META: dict[WheelTab, dict[str, Any]] = {
    WheelTab.first_prize: {
        "label": "الجائزة الأولى",
        "min_points": 15,
        "top_n": None,
        "criteria": ["15 نقطة أو أكثر", _SATURDAY_CRITERION],
    },
    WheelTab.second_prize: {
        "label": "الجائزة الثانية",
        "min_points": 40,
        "top_n": None,
        "criteria": ["40 نقطة أو أكثر", _SATURDAY_CRITERION],
    },
    WheelTab.third_prize: {
        "label": "الجائزة الثالثة",
        "min_points": None,
        "top_n": 100,
        "criteria": [
            "أعلى 100 طالب",
            "أطول مدة حضور بيوم واحد",
            "أكبر عدد محاضرات",
            "الأعلى بالنقاط",
            _SATURDAY_CRITERION,
        ],
    },
    WheelTab.final_prize: {
        "label": "الجائزة النهائية",
        "min_points": None,
        "top_n": 50,
        "criteria": [
            "أعلى 50 طالب من ترتيب الجائزة الثالثة",
            "أطول مدة حضور بيوم واحد",
            "أكبر عدد محاضرات",
            "الأعلى بالنقاط",
            _SATURDAY_CRITERION,
        ],
    },
}

TAB_LABELS: dict[WheelTab, str] = {
    tab: str(meta["label"]) for tab, meta in _TAB_META.items()
}


# ── وقت التجميد ──────────────────────────────────────────────────────────────


def get_settings(db: Session) -> WheelSettings | None:
    """صف الإعدادات إن وُجد، بدون ما ينشئه — قراءة ما بتكتب بالقاعدة."""
    return db.query(WheelSettings).filter(WheelSettings.id == SETTINGS_ROW_ID).first()


def get_configured_freeze(db: Session) -> datetime:
    """freeze_at المحفوظ، أو الافتراضي (سبت 3:30) إذا ما في صف بعد."""
    row = get_settings(db)
    return row.freeze_at if row is not None else default_freeze_at()


def get_effective_freeze(db: Session, prospective: datetime | None = None) -> datetime:
    """
    LEAST(now, freeze_at) — بتحسبها بـPython مش بـSQL عمداً.

    checked_in_at و freeze_at كلهم naive بتوقيت سوريا (time_utils)، فأقوى شي
    نعملو إن نقارن بإطار واحد معروف بدل ما نخلط func.now() بتوقيت القاعدة
    (timestamptz) مع قيمنا الـnaive. النتيجة نفس الشي، والمقارنة أأمن.
    """
    if prospective is not None:
        return prospective
    return min(time_utils.now_naive(), get_configured_freeze(db))


def is_frozen(db: Session) -> bool:
    """هل مرّ وقت التجميد؟ (لعرض "مجمّد" بشاشة الأدمن)"""
    return time_utils.now_naive() >= get_configured_freeze(db)


def validate_freeze_value(value: datetime) -> datetime:
    """
    وقت التجميد لازم يكون جوه نافذة الفعالية: من أول يوم فعالية 8:00ص لآخر
    يوم (السبت) الساعة وقت السحب. أي قيمة برّا = طلب غلط 400.
    """
    earliest = datetime.combine(min(EVENT_DAYS.values()), EVENT_WINDOW_START)
    latest = datetime.combine(EVENT_DAYS["sat"], time(DRAW_HOUR, DRAW_MINUTE))
    if value < earliest:
        raise wheel_freeze_out_of_range(
            f"وقت التجميد لازم يكون {earliest.strftime('%Y-%m-%d %H:%M')} أو بعده "
            "(بداية أول يوم فعالية)"
        )
    if value > latest:
        raise wheel_freeze_out_of_range(
            f"وقت التجميد لازم يكون {latest.strftime('%Y-%m-%d %H:%M')} أو قبله "
            "(بداية أول يوم فعالية)"
        )
    return value


# ── الاستعلام الأساسي ────────────────────────────────────────────────────────


def _ranked_query(effective_freeze: datetime):
    """
    الاستعلام الأساسي: كل طالب مستوفٍ لشرط السبت وغير مستبعد، مع كل أرقامه
    المجمّدة و ترتيبه. يرجع Subquery بأعمدة:
      student_id, unique_code, full_name, freeze_points, raw_lectures,
      max_span_seconds, rank_no

    ملاحظات تنفيذ:
    * كل الأرقام بتجمّع بـcoalesce(..., 0) قبل أي ORDER BY. بدونها، طالب
      نشاطه كله بعد التجميد بيبقى NULL بالمعادلات، وPostgreSQL بيحطّ
      NULLs أولاً بالـDESC — يعني بيرتّب بالمقدمة بلا أي أساس.
    * النقاط محسوبة بنفس قواعد point_service بالحرف (نفس الثوابت، نفس السقوف
      اليومية، نفس "مرة وحدة للاستشارة والاستبيان")، بس مع cutoff التجميد.
    * المدى بالثواني عبر extract(epoch from max - min) — مش max(interval)،
      لأن ناتج الأرقام هنا numeric مدعوم ومفهوم، وما في أي غموض بنوعه.
    """
    day_col = cast(Checkin.checked_in_at, Date)
    time_col = cast(Checkin.checked_in_at, Time)

    # سقف النافذة: أقل من 16:00 أو وقت التجميد — أيّهماEarlier.
    # نقارن وقت-يوم بوقت-يوم (time vs time)، مش datetime — بخلاف أول
    # مسوّدة لهالملف اللي كانت بتقارن time بـdatetime وبيطلع TypeError.
    cutoff_time = (
        EVENT_WINDOW_END
        if effective_freeze.time() >= EVENT_WINDOW_END
        else effective_freeze.time()
    )

    saturday_ok = (
        select(Checkin.student_id.label("sid"))
        .where(
            Checkin.activity_type == ActivityType.campus_entry,
            day_col == EVENT_DAYS["sat"],
        )
        .distinct()
        .cte("saturday_ok")
    )
    consultation_ok = (
        select(Checkin.student_id.label("sid"), func.count().label("flag"))
        .where(
            Checkin.activity_type == ActivityType.consultation,
            Checkin.checked_in_at <= effective_freeze,
        )
        .group_by(Checkin.student_id)
        .cte("consultation_ok")
    )
    # answered_at بيتكتب من now() بتوقيت القاعدة (server_default)، وبقية
    # timestamps بالمشروع من وقت سوريا. المقارنة هون direct بين
    # answered_at والـfreeze — صالحة طالما APP_TIMEZONE وتوقيت جلسة القاعدة
    # واحد، وهاد نفس الافتراض القائم بكل استعلامات التطبيق.
    survey_ok = (
        select(PostSurvey.student_id.label("sid"), func.count().label("flag"))
        .where(PostSurvey.answered_at <= effective_freeze)
        .group_by(PostSurvey.student_id)
        .cte("survey_ok")
    )

    # العدّ اليومي. بلا فلترة على أيام الفعالية هنا — عمداً: point_service
    # بيحسب فوق أي تاريخ، فلو حطّينا الفلترة كان عدد النقاط بالعجلة بيختلف
    # عن total_points لنفس الطالب. النافذة الزمنية بتنطبق على المدى فقط
    # (لأن المواصفة بتحكي "يوم واحد من أيام الفعالية" للمدى).
    #
    # ⚠️ لازم sum مش count: count(CASE WHEN cond THEN 1 ELSE 0 END) بيعدّ الـ0
    # كمان (count بيتجاهل NULL بس مو الصفر)، فكل الأعمدة كان بتبيرجع "عدد
    # السجلات بهاليوم" بدل "عدد محاضرات هاليوم". sum بتتجاهل الصفر صح.
    per_day = (
        select(
            Checkin.student_id.label("sid"),
            day_col.label("day"),
            func.sum(
                case((Checkin.activity_type == ActivityType.campus_entry, 1), else_=0)
            ).label("entries"),
            func.sum(
                case((Checkin.activity_type == ActivityType.lecture, 1), else_=0)
            ).label("lectures"),
            func.sum(
                case((Checkin.activity_type == ActivityType.tour, 1), else_=0)
            ).label("tours"),
        )
        .where(Checkin.checked_in_at <= effective_freeze)
        .group_by(Checkin.student_id, day_col)
        .cte("per_day")
    )

    activity_points = (
        select(
            per_day.c.sid.label("sid"),
            (
                func.sum(case((per_day.c.entries > 0, 1), else_=0))
                * _CAMPUS_ENTRY_POINTS
                + func.sum(
                    case(
                        (per_day.c.lectures > _MAX_LECTURES_PER_DAY, _MAX_LECTURES_PER_DAY),
                        else_=per_day.c.lectures,
                    )
                )
                * _LECTURE_POINTS
                + func.sum(
                    case(
                        (per_day.c.tours > _MAX_TOURS_PER_DAY, _MAX_TOURS_PER_DAY),
                        else_=per_day.c.tours,
                    )
                )
                * _TOUR_POINTS
            ).label("activity_points"),
            # عدد المحاضرات الخام: count لا يحترم السقف اليومي إطلاقاً،
            # لأن المواصفة Wants "أكبر عدد محاضرات" مش "أكبر عدد نقاط محاضرات".
            func.sum(per_day.c.lectures).label("raw_lectures"),
        )
        .group_by(per_day.c.sid)
        .cte("activity_points")
    )

    # المدى اليومي. شرط <= effective_freeze أساسي ومش زايد: لو حدا خفّض
    # التجميد ليوم خميس 10:00، مسحات الأربعاء 12:00 جوة النافذة [08:00,16:00)
    # بس **بعد** التجميد — فلو ما فلترناها كانت بتضل محسوبة وبتخرّب الترقيم.
    span_per_day = (
        select(
            Checkin.student_id.label("sid"),
            func.extract(
                "epoch",
                func.max(Checkin.checked_in_at) - func.min(Checkin.checked_in_at),
            ).label("span_seconds"),
        )
        .where(
            day_col.in_(list(EVENT_DAYS.values())),
            Checkin.checked_in_at <= effective_freeze,
            time_col >= EVENT_WINDOW_START,
            time_col < cutoff_time,
        )
        .group_by(Checkin.student_id, day_col)
        .cte("span_per_day")
    )

    span_max = (
        select(
            span_per_day.c.sid.label("sid"),
            func.max(span_per_day.c.span_seconds).label("max_span_seconds"),
        )
        .group_by(span_per_day.c.sid)
        .cte("span_max")
    )

    scored = (
        select(
            Student.id.label("student_id"),
            Student.unique_code.label("unique_code"),
            Student.full_name.label("full_name"),
            (
                func.coalesce(activity_points.c.activity_points, 0)
                + func.coalesce(consultation_ok.c.flag, 0) * _CONSULTATION_POINTS
                + func.coalesce(survey_ok.c.flag, 0) * _SURVEY_POINTS
            ).label("freeze_points"),
            func.coalesce(activity_points.c.raw_lectures, 0).label("raw_lectures"),
            func.coalesce(span_max.c.max_span_seconds, 0).label("max_span_seconds"),
        )
        .select_from(Student)
        .outerjoin(activity_points, activity_points.c.sid == Student.id)
        .outerjoin(consultation_ok, consultation_ok.c.sid == Student.id)
        .outerjoin(survey_ok, survey_ok.c.sid == Student.id)
        .outerjoin(span_max, span_max.c.sid == Student.id)
        .where(Student.id.in_(select(saturday_ok.c.sid)))
        .cte("scored")
    )

    # ترتيب واحد مثبّت، بتستعمله لوحة الأدمن والسحب والقرار، فكلهم متفقين.
    order_by = (
        scored.c.max_span_seconds.desc(),
        scored.c.raw_lectures.desc(),
        scored.c.freeze_points.desc(),
        scored.c.unique_code.asc(),
    )

    return (
        select(
            scored.c.student_id,
            scored.c.unique_code,
            scored.c.full_name,
            scored.c.freeze_points,
            scored.c.raw_lectures,
            scored.c.max_span_seconds,
            func.row_number().over(order_by=order_by).label("rank_no"),
        )
        .where(scored.c.student_id.notin_(select(WheelExclusion.student_id)))
        .order_by(*order_by)
        .cte("ranked")
    )


def _tab_pool(tab: WheelTab, effective_freeze: datetime):
    """
    pool تاب واحد = ranked + فلتر التاب. الفرق بين الأربعة تابات هو هالفلتر
    وخلاص — نفس الحساب ونفس الترتيب.
    """
    ranked = _ranked_query(effective_freeze)
    meta = _TAB_META[tab]
    conditions = []
    if meta["min_points"] is not None:
        conditions.append(ranked.c.freeze_points >= meta["min_points"])
    if meta["top_n"] is not None:
        conditions.append(ranked.c.rank_no <= meta["top_n"])
    return select(ranked).where(*conditions).cte(f"pool_{tab.value}")


# ── قراءة الأرقام للواجهة ────────────────────────────────────────────────────


def count_pool(db: Session, tab: WheelTab, effective_freeze: datetime) -> int:
    pool = _tab_pool(tab, effective_freeze)
    return int(db.execute(select(func.count()).select_from(pool)).scalar_one())


def tab_counts(db: Session, effective_freeze: datetime) -> dict[WheelTab, int]:
    """عدد المؤهلين بالأربعة تابات — لحظي، كل تاب باستعلام مستقل."""
    return {tab: count_pool(db, tab, effective_freeze) for tab in TAB_ORDER}


def pool_rows(
    db: Session,
    tab: WheelTab,
    effective_freeze: datetime,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """صفوف التاب مرتّبة. limit=None معناها كل المؤهلين (للحفل snapshot)."""
    pool = _tab_pool(tab, effective_freeze)
    stmt = select(
        pool.c.student_id,
        pool.c.unique_code,
        pool.c.full_name,
        pool.c.freeze_points,
        pool.c.raw_lectures,
        pool.c.max_span_seconds,
        pool.c.rank_no,
    ).order_by(
        pool.c.max_span_seconds.desc(),
        pool.c.raw_lectures.desc(),
        pool.c.freeze_points.desc(),
        pool.c.unique_code.asc(),
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return [_student_row(mapping) for mapping in db.execute(stmt).mappings().all()]


def _student_row(mapping: Mapping[str, Any]) -> dict[str, Any]:
    span_seconds = int(mapping["max_span_seconds"] or 0)
    return {
        "student_id": mapping["student_id"],
        "unique_code": mapping["unique_code"],
        "full_name": mapping["full_name"],
        "freeze_points": int(mapping["freeze_points"] or 0),
        "raw_lectures": int(mapping["raw_lectures"] or 0),
        "max_span_minutes": span_seconds // 60,
        "rank": int(mapping["rank_no"]) if mapping.get("rank_no") is not None else None,
    }


# ── السحب ────────────────────────────────────────────────────────────────────


def find_pending_draw(db: Session, tab: WheelTab) -> WheelDraw | None:
    """سحب انكشف اسمه وبانتظار قرار — يمنع تكرار الاسم على الشاشة لحاله."""
    return (
        db.query(WheelDraw)
        .filter(WheelDraw.tab == tab, WheelDraw.status == WheelDrawStatus.revealed)
        .order_by(WheelDraw.created_at.desc(), WheelDraw.id.desc())
        .first()
    )


def draw_winner(
    db: Session,
    tab: WheelTab,
    account_id: int,
    idempotency_key: str | None = None,
) -> tuple[WheelDraw, bool]:
    """
    سحب فائز واحد بالتاب. يرجع (السحب, هل تكرر Idempotency).

    التوزيع منتظم: ORDER BY random() على نفس الـpool يلي بيشوفه الأدمن،
    فكل مؤهل بنفس الاحتمال و"الأعلى بالنقاط" ما بيضمن أحد — التاب الثالث
    بيقصّ الـpool عند 100، مش بيرجّعها بالترتيب.
    """
    if idempotency_key:
        existing = (
            db.query(WheelDraw)
            .filter(WheelDraw.idempotency_key == idempotency_key)
            .first()
        )
        if existing is not None:
            return existing, True

    # باسم معروض وبانتظار قرار بنفس التاب = ضغط مزدوج على الزر. بدون هالحراسة
    # بتنكشف اسمين وبضل الأول معلّق بلا صاحب. حارس على التاب مش على الـpool،
    # فرياضيات الأهلية ما بتتغيّر أبداً.
    if find_pending_draw(db, tab) is not None:
        raise wheel_pending_draw_exists(TAB_LABELS[tab])

    effective_freeze = get_effective_freeze(db)
    pool = _tab_pool(tab, effective_freeze)
    picked = db.execute(
        select(pool.c.student_id)
        .order_by(func.random())
        .limit(1)
    ).scalar_one_or_none()
    if picked is None:
        raise wheel_tab_empty(TAB_LABELS[tab], _TAB_META[tab]["min_points"])

    draw = WheelDraw(
        tab=tab,
        student_id=picked,
        status=WheelDrawStatus.revealed,
        freeze_at_snapshot=effective_freeze,
        idempotency_key=idempotency_key,
        created_by=account_id,
    )
    db.add(draw)
    db.commit()
    db.refresh(draw)
    return draw, False


def draw_payload(db: Session, draw: WheelDraw) -> dict[str, Any]:
    """شكل بطاقة السحب المأرجعة للأدمن."""
    student = db.query(Student).filter(Student.id == draw.student_id).first()
    return {
        "draw_id": draw.id,
        "tab": draw.tab.value,
        "tab_label": TAB_LABELS[draw.tab],
        "student_id": draw.student_id,
        "unique_code": student.unique_code if student else None,
        "full_name": student.full_name if student else None,
        "status": draw.status.value,
        "created_at": draw.created_at.isoformat() if draw.created_at else None,
    }


# ── القرار ───────────────────────────────────────────────────────────────────


def submit_decision(
    db: Session,
    draw_id: int,
    decision: WheelDecision,
    presence_verified: bool,
    confirmed: bool,
    account_id: int,
) -> WheelDraw:
    """
    قرار الأدمن على سحبة revealed. يقفل الصف (with_for_update) عشان ضغطتين
    متزامنتين ما يحطوا استبعادين ولا يبدّلوا الحالة مرتين.

    الحقول المطلوبة تختلف purposefully بين القبول والرفض:
      - القبول: presence_verified=True إلزامي (تحقق يدوي منفصل).
      - الرفض : confirmed=True إلزامي، و presence_verified مش مطلوب.
    الحقل التاني بينحفظ دائماً حتى لو False، عشان الأرشيف يبيّن условиطين.
    """
    draw = (
        db.query(WheelDraw)
        .filter(WheelDraw.id == draw_id)
        .with_for_update()
        .first()
    )
    if draw is None:
        raise wheel_draw_not_found()
    if draw.status != WheelDrawStatus.revealed:
        raise wheel_draw_already_decided()

    if decision == WheelDecision.accepted and not presence_verified:
        raise wheel_presence_verification_required()
    if decision == WheelDecision.rejected and not confirmed:
        raise wheel_reject_confirmation_required()

    now = time_utils.now_naive()
    draw.status = decision
    draw.presence_verified = presence_verified
    draw.decided_at = now
    draw.decided_by = account_id
    db.add(
        WheelExclusion(
            student_id=draw.student_id,
            tab=draw.tab,
            decision=decision,
            draw_id=draw.id,
            decided_at=now,
            decided_by=account_id,
        )
    )
    db.commit()
    db.refresh(draw)
    return draw


# ── الإعدادات والتدقيق ───────────────────────────────────────────────────────


def update_freeze(
    db: Session,
    freeze_at: datetime,
    account_id: int,
    reason: str | None = None,
) -> WheelSettings:
    """حفظ وقت تجميد جديد + سطر تدقيق بالقيمة القديمة. الأثر رح ينحسب مباشرة."""
    validate_freeze_value(freeze_at)
    row = get_settings(db)
    now = time_utils.now_naive()
    if row is None:
        row = WheelSettings(id=SETTINGS_ROW_ID, freeze_at=freeze_at)
        db.add(row)
        previous = None
    else:
        previous = row.freeze_at
        row.freeze_at = freeze_at
        row.updated_at = now
        row.updated_by = account_id
    db.add(
        WheelFreezeAudit(
            freeze_at=freeze_at,
            previous_freeze_at=previous,
            changed_by=account_id,
            changed_at=now,
            reason=reason,
        )
    )
    db.commit()
    db.refresh(row)
    return row


def _tab_info(tab: WheelTab, eligible_count: int) -> dict[str, Any]:
    """
    بنية تاب واحدة للواجهة — بالمكان الوحيد.

    كان في نسختين (tabs_payload و settings_payload) وحدة منهم ناقصها
    criteria، فكانت /admin/wheel/settings ترجع 500. أي حقل جديد لازم
    ينضاف هون وبس.
    """
    return {
        "tab": tab.value,
        "tab_label": TAB_LABELS[tab],
        "criteria": list(_TAB_META[tab]["criteria"]),
        "eligible_count": eligible_count,
    }


def settings_payload(
    db: Session, prospective_freeze_at: datetime | None = None
) -> dict[str, Any]:
    """
    إعدادات التجميد + معاينة الأثر. prospective_freeze_at = "شوفني شو بصير لو
    حفظت هالوقت" — ما بيحفظ شي، وبيحسب عدادات التابات بالوقت الجديد.
    """
    configured = get_configured_freeze(db)
    current = get_effective_freeze(db)
    payload: dict[str, Any] = {
        "freeze_at": configured.isoformat(),
        "frozen": time_utils.now_naive() >= configured,
        "is_default": get_settings(db) is None,
        "effective_freeze_at": current.isoformat(),
        "min_allowed": datetime.combine(
            min(EVENT_DAYS.values()), EVENT_WINDOW_START
        ).isoformat(),
        "max_allowed": datetime.combine(
            EVENT_DAYS["sat"], time(DRAW_HOUR, DRAW_MINUTE)
        ).isoformat(),
    }
    current_counts = tab_counts(db, current)
    payload["tabs"] = [_tab_info(tab, current_counts[tab]) for tab in TAB_ORDER]
    if prospective_freeze_at is not None:
        validate_freeze_value(prospective_freeze_at)
        prospective_counts = tab_counts(db, prospective_freeze_at)
        payload["preview"] = {
            "prospective_freeze_at": prospective_freeze_at.isoformat(),
            "tabs": [
                {**_tab_info(tab, prospective_counts[tab]),
                 "delta": prospective_counts[tab] - current_counts[tab]}
                for tab in TAB_ORDER
            ],
        }
    return payload


# ── الأرشيف وشاشة الجمهور ────────────────────────────────────────────────────


def archive_rows(db: Session) -> list[dict[str, Any]]:
    """
    سجل الفائزين = كل السحوبات المقبولة. مرتّبة بترتيب التابات ثم وقت القبول.
    الرفض ما بيطلع — بس موجود بwheel_draws لحسابه.
    """
    draws = (
        db.query(WheelDraw)
        .filter(WheelDraw.status == WheelDrawStatus.accepted)
        .order_by(WheelDraw.decided_at.asc(), WheelDraw.id.asc())
        .all()
    )
    rows = []
    for draw in draws:
        student = db.query(Student).filter(Student.id == draw.student_id).first()
        rows.append(
            {
                "draw_id": draw.id,
                "tab": draw.tab.value,
                "tab_label": TAB_LABELS[draw.tab],
                "student_id": draw.student_id,
                "unique_code": student.unique_code if student else None,
                "full_name": student.full_name if student else None,
                "presence_verified": draw.presence_verified,
                "decided_at": draw.decided_at.isoformat() if draw.decided_at else None,
            }
        )
    rows.sort(key=lambda r: (TAB_ORDER.index(WheelTab(r["tab"])),))
    return rows


def ceremony_snapshot(db: Session) -> dict[str, Any]:
    """
    لقطة الحفل — كل المؤهلين بالتابات الأربعة، بأسمائهم. للعرض على جهاز
    التشغيل أثناء الحفل حين ينقطع الإنترنت، وariability ما بتصل بفرونت
    جمهور — هاد endpoint super_admin بس.
    """
    effective_freeze = get_effective_freeze(db)
    counts = tab_counts(db, effective_freeze)
    return {
        "generated_at": time_utils.now_naive().isoformat(),
        "effective_freeze_at": effective_freeze.isoformat(),
        "frozen": is_frozen(db),
        "tabs": [
            {
                "tab": tab.value,
                "tab_label": TAB_LABELS[tab],
                "criteria": list(_TAB_META[tab]["criteria"]),
                "eligible_count": counts[tab],
                "winners": pool_rows(db, tab, effective_freeze),
            }
            for tab in TAB_ORDER
        ],
    }


def live_draw_payload(db: Session) -> dict[str, Any]:
    """
    اللي على شاشة الجمهور هلق. ست حقول فقط — وFIXED: ما في freeze_at ولا
    counts ولا حالة تجميد، لأن المواصفة بتمنع كشفها للجمهور. لو ما في
    سحبة معروضة، كل الحقول null و 200 (مش 404) لأن الواجهة بتسأل كل ثانيتين
    وما بدها أخطاء بكل دورة.
    """
    draw = (
        db.query(WheelDraw)
        .filter(WheelDraw.status == WheelDrawStatus.revealed)
        .order_by(WheelDraw.created_at.desc(), WheelDraw.id.desc())
        .first()
    )
    if draw is None:
        return {
            "draw_id": None,
            "tab": None,
            "tab_label": None,
            "winner_name": None,
            "winner_code": None,
            "revealed_at": None,
        }
    student = db.query(Student).filter(Student.id == draw.student_id).first()
    return {
        "draw_id": draw.id,
        "tab": draw.tab.value,
        "tab_label": TAB_LABELS[draw.tab],
        "winner_name": student.full_name if student else None,
        "winner_code": student.unique_code if student else None,
        "revealed_at": draw.created_at.isoformat() if draw.created_at else None,
    }


def tabs_payload(db: Session) -> list[dict[str, Any]]:
    """قائمة التابات للواجهة: الوصف + عدد المؤهلين الحالي."""
    counts = tab_counts(db, get_effective_freeze(db))
    return [_tab_info(tab, counts[tab]) for tab in TAB_ORDER]


def decision_requirements() -> dict[str, bool]:
    """
    أي حقول مطلوبة لكل قرار — منشور كـmetadata مع تابات الواجهة بدل ما
    تتكرّر القاعدة بالفرونت وبالباك.
    """
    return {
        "accept_requires_presence_verified": True,
        "accept_requires_confirmation": False,
        "reject_requires_presence_verified": False,
        "reject_requires_confirmation": True,
    }
