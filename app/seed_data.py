"""
سكريبت زرع بيانات أولية (Seed Data) — يشتغل مرة وحدة يدوياً لإنشاء أول حساب
super_admin (وحسابات تجريبية لباقي الأدوار)، لأنه ما في تسجيل ذاتي لأي حساب
فريق عمل بالنظام — كلهم بينشأو من قبل super_admin عبر POST /admin/accounts.

⚠️ كلمات السر هون كلها تجريبية وواضحة (dev-only) — لازم تتغيّر يدوياً قبل أي
استخدام فعلي بيوم الفعالية.

طريقة التشغيل (من مجلد المشروع، بعد ما تفعّلي الـ venv):
    python -m app.seed_data
"""

from app.database import Base, SessionLocal, engine
from app.models import Account, AccountRole, College
from app.security import hash_password

# (username, password, role, college)
SEED_ACCOUNTS = [
    ("taher_super", "super123", AccountRole.super_admin, None),
    ("sedra_admin", "admin123", AccountRole.students_admin, None),
    ("rima_staff", "staff123", AccountRole.college_staff, College.college_placeholder_1),
    ("hadi_gate", "gate123", AccountRole.gate_scanner, None),
]


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
    finally:
        db.close()


if __name__ == "__main__":
    seed()