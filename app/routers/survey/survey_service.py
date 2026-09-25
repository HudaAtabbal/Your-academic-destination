"""
منطق العمل للاستبيان البعدي — راجع قسم 5 بملف wijhatak_api_contract.md.

ملاحظة مهمة: زر "لاحقاً" بالفرونت ما بينادي هاد الـ endpoint إطلاقاً — الطالب
يلي بضغط "لاحقاً" بيضل بلا سجل استبيان (مش سجل بقيم فارغة)، مشان يقدر يرجع
يعبّيه بأي وقت لاحق. يعني ما في "حالة لاحقاً" هون بالباك اند أصلاً.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import duplicate_survey, missing_campus_entry, survey_not_eligible
from app.models import ActivityType, Checkin, College, OpinionChange, PostSurvey
from app.routers.points import point_service
from app.student_lookup import get_student_or_raise


def get_survey_status(db: Session, unique_code: str) -> bool:
    student = get_student_or_raise(db, unique_code)
    existing = db.query(PostSurvey).filter(PostSurvey.student_id == student.id).first()
    return existing is not None


def _checkin_exists(db: Session, student_id: int, *activity_types: ActivityType) -> bool:
    return (
        db.query(Checkin)
        .filter(Checkin.student_id == student_id, Checkin.activity_type.in_(activity_types))
        .first()
        is not None
    )


def get_survey_eligibility(db: Session, unique_code: str) -> dict:
    student = get_student_or_raise(db, unique_code)
    answered = get_survey_status(db, unique_code)
    campus_entry = _checkin_exists(db, student.id, ActivityType.campus_entry)
    activity = _checkin_exists(
        db, student.id, ActivityType.lecture, ActivityType.tour, ActivityType.consultation
    )
    return {
        "answered": answered,
        "eligible": campus_entry and activity,
        "campus_entry": campus_entry,
        "activity": activity,
    }


def submit_survey(
    db: Session, unique_code: str, opinion_change: OpinionChange, preferred_major: College
) -> PostSurvey:
    student = get_student_or_raise(db, unique_code)

    if not _checkin_exists(db, student.id, ActivityType.campus_entry):
        raise missing_campus_entry()

    if not _checkin_exists(
        db, student.id, ActivityType.lecture, ActivityType.tour, ActivityType.consultation
    ):
        raise survey_not_eligible()

    existing = db.query(PostSurvey).filter(PostSurvey.student_id == student.id).first()
    if existing is not None:
        raise duplicate_survey()

    survey = PostSurvey(
        student_id=student.id, opinion_change=opinion_change, preferred_major=preferred_major
    )
    try:
        db.add(survey)
        db.flush()
        point_service.recalculate_and_store_points(db, student.id)
        db.commit()
    except IntegrityError:
        # سباق تزامن: طلب تاني أرسل نفس الاستبيان قبل ما نكتشف نحنا التكرار —
        # نفس نمط checkin_service._flush_commit_checkin: 409 لطيفة بدل 500 خام
        db.rollback()
        existing = db.query(PostSurvey).filter(PostSurvey.student_id == student.id).first()
        if existing is not None:
            raise duplicate_survey()
        raise
    db.refresh(survey)
    return survey
