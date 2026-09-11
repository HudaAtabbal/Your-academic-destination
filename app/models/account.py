"""
موديل Account — حسابات فريق العمل (الأدوار الأربعة).
مطابق تماماً لجدول accounts بـ wijhatak_schema_v2.sql.
ملاحظة: ما في قيد "حساب واحد لكل كلية" — مسموح أكتر من حساب college_staff
لنفس الكلية (كل واحد بيغطي محطة مختلفة: توجيه/جولة/استشارة).
"""

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import AccountRole, College


class Account(Base):
    __tablename__ = "accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    role = Column(SAEnum(AccountRole, name="account_role_enum"), nullable=False)
    college = Column(SAEnum(College, name="college_enum"), nullable=True)

    # يرتفع عند تغيير كلمة السر — التوكنات القديمة (عندها token_version قديم)
    # بتصير مرفوضة فوراً من get_current_account (إبطال الجلسات)
    token_version = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, server_default=func.now())