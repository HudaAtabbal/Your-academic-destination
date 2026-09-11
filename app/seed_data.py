"""
سكريبت زرع بيانات أولية (Seed Data) — يشتغل مرة وحدة يدوياً لإنشاء أول حساب
super_admin (وحسابات تجريبية لباقي الأدوار)، لأنه ما في تسجيل ذاتي لأي حساب
فريق عمل بالنظام — كلهم بينشأو من قبل super_admin عبر POST /admin/accounts.

كمان بيزرع طالب تجريبي واحد "نظامي" (registered، مش walk-in) مشان يصير فيك
تجرّبي عمليات المسح (checkins) والحجز (bookings) بدون ما تضطري تعدّي فعلياً
عبر فلو التسجيل الإلكتروني (تسجيل + OTP) يلي لسا ما بنيناه.

كلمات السر:
- للبيئة المحلية (تطوير): تظل كلمات السر الافتراضية التجريبية الواضحة بالأسفل.
- لأي بيئة غير محلية: عرّفي متغيّرات بيئة بالشكل SEED_PASSWORD_<USERNAME>
  (بأحرف كبيرة، مثلاً SEED_PASSWORD_TAHER_SUPER) — وبتطغى على الافتراضي.
  ما عاد في طباعة لكلمات السر بأي حالة.

طريقة التشغيل (من مجلد المشروع، بعد ما تفعّلي الـ venv):
    python -m app.seed_data
"""

import os
from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import (
    Account,
    AccountRole,
    College,
    ContactPlatform,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)
from app.security import hash_password

DEFAULT_DEV_PASSWORDS = {
    "taher_super": "super123",
    "sedra_admin": "admin123",
    "rima_staff": "staff123",
    "hadi_gate": "gate123",
}


def _resolve_password(username: str) -> str:
    env_password = os.getenv(f"SEED_PASSWORD_{username.upper()}")
    if env_password:
        return env_password
    if os.getenv("APP_ENV", "development") != "development":
        raise RuntimeError(
            f"كلمة سر الحساب {username} مش معرّفة — خارج بيئة التطوير لازم "
            f"تحدّدي SEED_PASSWORD_{username.upper()}"
        )
    return DEFAULT_DEV_PASSWORDS[username]


# (username, role, college)
SEED_ACCOUNTS = [
    ("taher_super", AccountRole.super_admin, None),
    ("sedra_admin", AccountRole.students_admin, None),
    ("rima_staff", AccountRole.college_staff, College.medicine),
    ("hadi_gate", AccountRole.gate_scanner, None),
]

# طالب تجريبي واحد "نظامي" (registered) — verified وbالكامل مكتمل البيانات،
# مشان يصير فيك تجرّبي عليه checkins/bookings مباشرة
SEED_STUDENT = {
    "unique_code": "R-9001",
    "full_name": "طالب تجريبي",
    "contact_platform": ContactPlatform.whatsapp,
    "contact_id": "0999999999",
    "birth_date": date(2008, 1, 1),
    "bacc_year": 2026,
    "bacc_average": 285.5,
    "initial_preferred_major": ["informatics"],
    "verification_status": VerificationStatus.verified,
    "registration_type": RegistrationType.registered,
    "status": StudentStatus.complete,
}


def seed():
    # بيتأكد إنه الجداول موجودة قبل ما يحاول يزرع فيها (ما بيضر لو موجودة أصلاً)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for username, role, college in SEED_ACCOUNTS:
            existing = db.query(Account).filter(Account.username == username).first()
            if existing:
                print(f"⏭  الحساب '{username}' موجود مسبقاً — تم تخطّيه")
                continue

            account = Account(
                username=username,
                password_hash=hash_password(_resolve_password(username)),
                role=role,
                college=college,
            )
            db.add(account)
            db.commit()
            print(f"✅ تم إنشاء الحساب: {username}  (دور: {role.value})")

        existing_student = (
            db.query(Student).filter(Student.unique_code == SEED_STUDENT["unique_code"]).first()
        )
        if existing_student:
            print(f"⏭  الطالب '{SEED_STUDENT['unique_code']}' موجود مسبقاً — تم تخطّيه")
        else:
            student = Student(**SEED_STUDENT)
            db.add(student)
            db.commit()
            print(
                f"✅ تم إنشاء طالب تجريبي: {SEED_STUDENT['unique_code']} "
                f"({SEED_STUDENT['full_name']}) — registered / verified / complete"
            )
    finally:
        db.close()


if __name__ == "__main__":
    seed()