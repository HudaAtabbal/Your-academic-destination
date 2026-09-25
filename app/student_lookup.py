"""
دوال مشتركة للبحث عن الطلاب — وحدة مساعدة تتجنب تكرار المنطق عبر الخدمات.

أُعيد استخدامها من checkin_service / booking_service / survey_service (نقطة 6 —
نفس السلوك السابق بالضبط: 404 مع error_code=student_not_found).
"""

from sqlalchemy.orm import Session

from app.errors import student_not_found
from app.models import Student


def get_student_or_raise(db: Session, unique_code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == unique_code).first()
    if student is None:
        raise student_not_found()
    return student