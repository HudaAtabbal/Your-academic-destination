"""
أدوات الأمان: تشفير/التحقق من كلمات السر (bcrypt) + إنشاء/فك تشفير JWT.
كل هاد الملف مبني على متغيرات البيئة JWT_SECRET_KEY / JWT_ALGORITHM /
ACCESS_TOKEN_EXPIRE_MINUTES (راجع .env.example).
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "متغير البيئة JWT_SECRET_KEY مش معرّف. "
        "انسخي .env.example إلى .env وعبيها بالقيم الصحيحة."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """تشفير كلمة سر قبل تخزينها بعمود password_hash."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """مقارنة كلمة سر مُدخلة مع الهاش المخزّن — بدون فك تشفير الهاش أبداً."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    إنشاء JWT token يحمل بيانات الحساب (username كـ sub، role، college).
    مدة الصلاحية من ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    فك تشفير التوكن والتحقق من صلاحيته.
    بيرمي jwt.PyJWTError (من مكتبة PyJWT) لو التوكن غلط أو منتهي الصلاحية —
    المسؤول عن التقاطها هو dependencies.get_current_account.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])