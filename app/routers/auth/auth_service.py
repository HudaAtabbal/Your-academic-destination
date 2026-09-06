"""
منطق العمل (business logic) لتسجيل الدخول — بعيداً عن طبقة الـ HTTP.
هيك لو احتجنا نفس منطق التحقق بمكان تاني بالمستقبل (مثلاً سكريبت إداري)،
منقدر نستدعيه مباشرة بدون ما نعدي عبر الـ router.
"""

from sqlalchemy.orm import Session

from app.errors import invalid_credentials
from app.models import Account
from app.security import verify_password


def authenticate_account(db: Session, username: str, password: str) -> Account:
    """
    يتحقق من اسم المستخدم وكلمة السر، وبيرجع الحساب لو صح.
    بيرمي AppError (invalid_credentials) لو اسم المستخدم مش موجود أو كلمة
    السر غلط — بنفس الرسالة بالحالتين مشان ما نعطي معلومة إضافية لمحاولات
    التخمين.
    """
    account = db.query(Account).filter(Account.username == username).first()

    if account is None or not verify_password(password, account.password_hash):
        raise invalid_credentials()

    return account