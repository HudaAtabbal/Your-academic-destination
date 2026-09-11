"""
منطق العمل للوحة مدير بيانات الطلاب — راجع قسم 6 بملف wijhatak_api_contract.md.

قاعدة تصنيف السجلات الناقصة (walk-in):
- "no_data" (بلا بيانات): بلا أي نشاط حضور إطلاقاً.
- "partial" (جزئي): عليه نشاط واحد على الأقل، بس بياناته الشخصية لسا ناقصة
  (status = pending).
السجلات status=complete ما بتظهر بهاد الجدول إطلاقاً.
"""

import math

from sqlalchemy.orm import Session

from app.errors import student_not_found
from app.models import Checkin, RegistrationType, Student, StudentStatus

# حقول ما بينسمح تعديلها من هاد الروتر — registration_type ثابت بعد الإنشاء
_IMMUTABLE_FIELDS = {"registration_type", "id", "unique_code", "created_at"}

_WALKIN_REQUIRED_FIELDS = (
    "full_name",
    "contact_platform",
    "contact_id",
    "birth_date",
    "bacc_year",
    "bacc_average",
    "certificate_type",
    "initial_preferred_major",
)


def find_student_by_code(db: Session, code: str) -> Student:
    student = db.query(Student).filter(Student.unique_code == code).first()
    if student is None:
        raise student_not_found()
    return student


def update_student(db: Session, student_id: int, updates: dict) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise student_not_found()

    for field, value in updates.items():
        if field in _IMMUTABLE_FIELDS:
            continue  # حماية إضافية — حتى لو انبعت الحقل، بيتجاهل بصمت
        if value is not None:
            setattr(student, field, value)

    if student.registration_type == RegistrationType.walk_in and student.status == StudentStatus.pending:
        if all(
            getattr(student, field) is not None
            for field in _WALKIN_REQUIRED_FIELDS
        ):
            student.status = StudentStatus.complete

    db.commit()
    db.refresh(student)
    return student


def get_student_stats(db: Session) -> tuple[int, int]:
    total_registered = db.query(Student).count()
    walkin_pending_count = (
        db.query(Student)
        .filter(
            Student.registration_type == RegistrationType.walk_in,
            Student.status == StudentStatus.pending,
        )
        .count()
    )
    return total_registered, walkin_pending_count


def list_walkin_incomplete(db: Session, page: int, limit: int) -> tuple[list[dict], int]:
    base_query = db.query(Student).filter(
        Student.registration_type == RegistrationType.walk_in,
        Student.status == StudentStatus.pending,
    )
    total = base_query.count()

    students = (
        base_query.order_by(Student.unique_code)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    if not students:
        return [], total

    # استعلام واحد لكل الصفحة بدل N+1 (استعلام لكل طالب على حدة)
    active_ids = {
        row[0]
        for row in db.query(Checkin.student_id)
        .filter(Checkin.student_id.in_([s.id for s in students]))
        .all()
    }

    items = [
        {
            "unique_code": s.unique_code,
            "full_name": s.full_name,
            "contact_id": s.contact_id,
            "status": "partial" if s.id in active_ids else "no_data",
        }
        for s in students
    ]

    return items, total