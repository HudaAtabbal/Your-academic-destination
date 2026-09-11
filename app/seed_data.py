"""
سكريبت زرع بيانات أولية (Seed Data) — يشتغل مرة وحدة يدوياً لإنشاء أول حساب
super_admin (وحسابات تجريبية لباقي الأدوار)، لأنه ما في تسجيل ذاتي لأي حساب
فريق عمل بالنظام — كلهم بينشأو من قبل super_admin عبر POST /admin/accounts.

كمان بيزرع طالب تجريبي واحد "نظامي" (registered، مش walk-in) مشان يصير فيك
تجرّبي عمليات المسح (checkins) والحجز (bookings) بدون ما تضطري تعدّي فعلياً
عبر فلو التسجيل الإلكتروني (تسجيل + OTP) يلي لسا ما بنيناه.

⚠️ كلمات السر هون كلها تجريبية وواضحة (dev-only) — لازم تتغيّر يدوياً قبل أي
استخدام فعلي بيوم الفعالية.

طريقة التشغيل (من مجلد المشروع، بعد ما تفعّلي الـ venv):
    python -m app.seed_data
"""

from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import (
    Account,
    AccountRole,
    College,
    ContactPlatform,
    InterestCluster,
    RegistrationType,
    Student,
    StudentStatus,
    VerificationStatus,
)
from app.security import hash_password

# (username, password, role, college)
SEED_ACCOUNTS = [
    ("taher_super", "super123", AccountRole.super_admin, None),
    ("sedra_admin", "admin123", AccountRole.students_admin, None),
    ("rima_staff", "staff123", AccountRole.college_staff, College.college_placeholder_1),
    ("hadi_gate", "gate123", AccountRole.gate_scanner, None),
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
    "initial_preferred_major": [InterestCluster.informatics],
    "verification_status": VerificationStatus.verified,
    "registration_type": RegistrationType.registered,
    "status": StudentStatus.complete,
}


def seed():
    # بيتأكد إنه الجداول موجودة قبل ما يحاول يزرع فيها (ما بيضر لو موجودة أصلاً)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for username, password, role, college in SEED_ACCOUNTS:
            existing = db.query(Account).filter(Account.username == username).first()
            if existing:
                print(f"⏭  الحساب '{username}' موجود مسبقاً — تم تخطّيه")
                continue

            account = Account(
                username=username,
                password_hash=hash_password(password),
                role=role,
                college=college,
            )
            db.add(account)
            db.commit()
            print(f"✅ تم إنشاء الحساب: {username} / {password}  (دور: {role.value})")

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