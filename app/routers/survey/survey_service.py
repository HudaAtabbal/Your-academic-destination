"""
منطق العمل للاستبيان البعدي — راجع قسم 5 بملف wijhatak_api_contract.md.

ملاحظة مهمة: زر "لاحقاً" بالفرونت ما بينادي هاد الـ endpoint إطلاقاً — الطالب
يلي بضغط "لاحقاً" بيضل بلا سجل استبيان (مش سجل بقيم فارغة)، مشان يقدر يرجع
يعبّيه بأي وقت لاحق. يعني ما في "حالة لاحقاً" هون بالباك اند أصلاً.
"""

from sqlalchemy.orm import Session

from app.errors import duplicate_survey, student_not_found
from app.models import College, OpinionChange, PostSurvey, Student


def _get_student_or_raise(db: Session, unique_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student


def get_survey_status(db: Session, unique_code: str) -> bool:
    student = _get_student_or_raise(db, unique_code)
    existing = db.query(PostSurvey).filter(PostSurvey.student_id == student.id).first()
    return existing is not None


def submit_survey(
    db: Session, unique_code: str, opinion_change: OpinionChange, preferred_major: College
) -> PostSurvey:
    student = _get_student_or_raise(db, unique_code)

    existing = db.query(PostSurvey).filter(PostSurvey.student_id == student.id).first()
    if existing is not None:
        raise duplicate_survey()

    survey = PostSurvey(
        student_id=student.id, opinion_change=opinion_change, preferred_major=preferred_major
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return survey