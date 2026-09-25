"""
منطق العمل لتوليد دفعة رموز walk-in عشوائية.

الأكواد عشوائية (W-XXXXXX) مثل رموز التسجيل الإلكتروني (R-XXXXXX) — مش
متسلسلة، حتى ما يقدرف أحد يخمّن الكود التالي. الدفعة تُولَّد عشوائياً مع
فحص التعارض مع الأكواد الموجودة بالـ DB (تكرار داخل الدفعة أو مع الموجود).
"""

import secrets

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import code_range_taken
from app.models import RegistrationType, Student, VerificationStatus

_PREFIX = "W"
# 6 خانات مثل R-XXXXXX (1,000,000 مساحة) — 4 خانات كانت تسلسلية وضيّقة
# للدفعات الكبيرة (حتى 500)، والتوسعة تمنع نضوب الأكواد والارتباطات العالية.
_DIGITS = 6


def _generate_random_code() -> str:
    return f"{_PREFIX}-{secrets.randbelow(10 ** _DIGITS):0{_DIGITS}d}"


def generate_walkin_codes(db: Session, count: int) -> list[str]:
    candidate_codes: list[str] = []
    for attempt in range(5):
        candidate_codes = [_generate_random_code() for _ in range(count)]

        # تكرار جوا الدفعة نفسها — نعيد التوليد
        if len(set(candidate_codes)) != len(candidate_codes):
            continue

        # تكرار مع أكواد موجودة بالـ DB — نعيد التوليد
        existing_codes = {
            row[0]
            for row in db.query(Student.unique_code)
            .filter(Student.unique_code.in_(candidate_codes))
            .all()
        }
        if existing_codes:
            continue

        for code in candidate_codes:
            db.add(
                Student(
                    unique_code=code,
                    registration_type=RegistrationType.walk_in,
                    # طلاب walk-in ما بيمرّوا بمرحلة OTP إطلاقاً — verified تلقائياً
                    verification_status=VerificationStatus.verified,
                )
            )

        try:
            db.commit()
            return candidate_codes
        except IntegrityError:
            db.rollback()

    raise code_range_taken(candidate_codes)