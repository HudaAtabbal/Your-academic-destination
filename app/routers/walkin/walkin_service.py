"""
منطق العمل لتوليد دفعة رموز walk-in فارغة.
محدّث: ما عاد نطلب من المستخدم يحدد "من وين يبلش" — النظام نفسه بيلاقي
آخر رمز W-XXXX موجود بالـ DB ويكمّل تلقائياً من بعده (أو يبلّش من W-0001
لو ما في ولا رمز أصلاً). هيك منمنع أخطاء الكتابة اليدوية والتعارض.
"""

import re

from sqlalchemy.orm import Session

from app.errors import code_range_taken
from app.models import RegistrationType, Student, VerificationStatus
from sqlalchemy.exc import IntegrityError
_PREFIX = "W"
_DIGITS = 4  # عرض الرقم الافتراضي (W-0001) — بيتوسّع تلقائياً لو تجاوزنا 9999
_CODE_PATTERN = re.compile(rf"^{_PREFIX}-(\d+)$")


def _get_next_number(db: Session) -> int:
    """
    بيدوّر على أعلى رقم موجود حالياً بين كل رموز walk-in (W-XXXX)، ويرجع
    الرقم يلي بعده مباشرة. لو ما في ولا رمز walk-in لسا، بيرجع 1 (يعني
    بيبلّش من W-0001).
    """
    existing_codes = (
        db.query(Student.unique_code)
        .filter(Student.unique_code.like(f"{_PREFIX}-%"))
        .all()
    )

    max_number = 0
    for (code,) in existing_codes:
        match = _CODE_PATTERN.match(code)
        if match:
            max_number = max(max_number, int(match.group(1)))

    return max_number + 1


def generate_walkin_codes(db: Session, count: int) -> list[str]:
    for attempt in range(5):
        next_number = _get_next_number(db)
        candidate_codes = [
            f"{_PREFIX}-{str(next_number + i).zfill(_DIGITS)}" for i in range(count)
        ]

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
            if attempt == 4:
                raise