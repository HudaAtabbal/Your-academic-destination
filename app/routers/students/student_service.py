"""
منطق العمل للوحة مدير بيانات الطلاب — راجع قسم 6 بملف wijhatak_api_contract.md.

قاعدة تصنيف السجلات (walk-in):
- تبويب "غير مكتملة" (status=incomplete): سجلات status=pending.
  - "no_data" (بلا بيانات): بلا أي نشاط حضور إطلاقاً.
  - "partial" (جزئي): عليه نشاط واحد على الأقل، بس بياناته الشخصية لسا ناقصة.
- تبويب "مكتملة" (status=complete): سجلات status=complete.
"""

import math

from sqlalchemy.orm import Session

from app.errors import duplicate_contact, student_not_found
from app.models import Checkin, RegistrationType, Student, StudentStatus, VerificationStatus

# حقول ما بينسمح تعديلها من هاد الروتر — registration_type ثابت بعد الإنشاء
_IMMUTABLE_FIELDS = {"registration_type", "id", "unique_code", "created_at", "verification_status"}

_WALKIN_REQUIRED_FIELDS = (
    "full_name",
    "contact_id",
    "birth_date",
    "bacc_year",
    "bacc_average",
    "certificate_type",
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

    # فحص تكرار رقم التواصل عند تعديله — نفس قاعدة التسجيل: رقم مسجّل مسبقاً
    # لطالب تاني ممنوع. الرقم نفسه للطالب الحالي مسموح.
    new_contact = updates.get("contact_id")
    if new_contact is not None:
        existing = (
            db.query(Student)
            .filter(
                Student.contact_id == new_contact,
                Student.id != student_id,
                Student.registration_type == RegistrationType.registered,
            )
            .first()
        )
        if existing is not None and existing.verification_status == VerificationStatus.verified:
            raise duplicate_contact()

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


def get_student_stats(db: Session) -> tuple[int, int, int]:
    # "إجمالي الطلاب المسجّلين" = اللي سجّلوا إلكترونياً + تحققوا (بعد OTP وظهور
    # البطاقة) — مش كل الطلاب بما فيهم walk-in والمنتظرين، راجع نفس المنطق
    # بـ dashboard_service (registered_online_count).
    total_registered = (
        db.query(Student)
        .filter(
            Student.registration_type == RegistrationType.registered,
            Student.verification_status == VerificationStatus.verified,
        )
        .count()
    )
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
    return total_registered, walkin_pending_count, walkin_completed_count


def list_walkin_incomplete(
    db: Session, page: int, limit: int, status: str = "incomplete"
) -> tuple[list[dict], int]:
    is_complete_tab = status == "complete"
    target_status = StudentStatus.complete if is_complete_tab else StudentStatus.pending

    base_query = db.query(Student).filter(
        Student.registration_type == RegistrationType.walk_in,
        Student.status == target_status,
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

    if is_complete_tab:
        items = [
            {
                "unique_code": s.unique_code,
                "full_name": s.full_name,
                "contact_id": s.contact_id,
                "status": "complete",
            }
            for s in students
        ]
        return items, total

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


def list_registered(
    db: Session, page: int, limit: int
) -> tuple[list[dict], int]:
    """قائمة المسجّلين إلكترونياً (registration_type=registered) — بترقيم صفحات.
    تُستعمل لصفحة "مسجّلون إلكترونياً" بالفرونت (RegisteredStudentsListPage)."""
    base_query = db.query(Student).filter(
        Student.registration_type == RegistrationType.registered
    )
    total = base_query.count()

    students = (
        base_query.order_by(Student.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = [
        {
            "unique_code": s.unique_code,
            "full_name": s.full_name,
            "contact_id": s.contact_id,
            "bacc_year": s.bacc_year,
            "bacc_average": s.bacc_average,
            "certificate_type": (
                s.certificate_type.value if s.certificate_type is not None else None
            ),
            "verification_status": (
                s.verification_status.value
                if s.verification_status is not None
                else None
            ),
        }
        for s in students
    ]

    return items, total
