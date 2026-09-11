"""
الاتصال بقاعدة بيانات PostgreSQL عبر SQLAlchemy.
كل الروترات بتستورد `get_db` من هون للحصول على جلسة (session) بقاعدة البيانات.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "متغير البيئة DATABASE_URL مش معرّف. "
        "انسخي .env.example إلى .env وعبيها بالقيم الصحيحة."
    )

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# كل الموديلات بـ models.py بترث من هاد الـ Base
Base = declarative_base()


def get_db():
    """
    Dependency لـ FastAPI — بتفتح جلسة جديدة لكل request وبتسكرها بعد ما يخلص،
    حتى لو صار استثناء (exception) بنص المعالجة.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()