"""
بنية الاختبارات — قاعدة اختبارات PostgreSQL حقيقية (wijhatak_test).
كل اختبار بيبلّش بقاعدة فاضية + الحسابات الأربعة الأساسية.

ملاحظة: DATABASE_URL و JWT_SECRET_KEY بيتم ضبطهم هون قبل استيراد التطبيق
عشان الـ engine يتريبط بقاعدة الاختبارات وليس قاعدة التطوير.
"""

import os

from dotenv import load_dotenv

load_dotenv()

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:5432/wijhatak_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-tests")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import main as main_module
from app import cache as cache_module
from app.database import Base, SessionLocal, engine
from app.dependencies import _otp_student_log, _request_log, _visit_log
from app.models import Account, AccountRole, College, Faculty, RegistrationType, Student, StudentStatus, VerificationStatus
from app.security import hash_password

BASE_ACCOUNTS = [
    ("taher_super", "super123", AccountRole.super_admin, None),
    ("sedra_admin", "admin123", AccountRole.students_admin, None),
    ("rima_staff", "staff123", AccountRole.college_staff, Faculty.medicine),
    ("hadi_gate", "gate123", AccountRole.gate_scanner, None),
    ("nour_game", "game123", AccountRole.game_corner_manager, None),
    ("sara_union", "union123", AccountRole.union, None),
]

DEFAULT_STUDENT_CODE = "R-9001"


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    Base.metadata.create_all(bind=engine)
    # القيم الجديدة للأونكس ما بتتضاف تلقائياً عبر create_all للأونكس الموجودة —
    # بزوّدها هون (IF NOT EXISTS) حتى تكون قاعدة الاختبار محدّثة دائماً.
    # ALTER TYPE ADD VALUE لازم يكون كل واحد بمعاملة لحال + إنشاء الـ index بعدين
    # بمعاملة تانية (PostgreSQL ما بيسمح باستخدام قيمة enum جديد بنفس المعاملة).
    with engine.begin() as conn:
        conn.execute(text("ALTER TYPE account_role_enum ADD VALUE IF NOT EXISTS 'union'"))
        conn.execute(text("ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'union'"))
        conn.execute(text("ALTER TYPE lecture_enum ADD VALUE IF NOT EXISTS 'opening'"))
    # أقسام ركن الاتحاد: نوع + عمود — يُضافان على قاعدة الاختبار الحية لأن
    # الجدول موجود مسبقاً و الـ create_all ما بيعدّل جدولاً قائماً.
    with engine.begin() as conn:
        conn.execute(
            text(
                "DO $$ BEGIN "
                "CREATE TYPE union_section_enum AS ENUM "
                "('central', 'major_guide', 'turkish_club'); "
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE checkins ADD COLUMN IF NOT EXISTS union_section union_section_enum"
            )
        )
    # كتسجيل فريد لكل قسم (بدل "مرة وحدة بالكامل" القديمة) — يُحذف الفهرس
    # القديم أولاً لأن إعادة تعريف بنفس الاسم تحتاج DROP على قاعدة موجودة.
    # محدّث: القيد صار لكل قسم وبنفس اليوم (CAST(checked_in_at AS DATE))،
    # بنفس نمط unique_campus_entry_checkin — فالقاعدة وسعة مش أضيق،
    # و السجلات الموجودة بتلتزم فيها كلها.
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS unique_union_checkin"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX unique_union_checkin "
                "ON checkins (student_id, union_section, CAST(checked_in_at AS DATE)) "
                "WHERE activity_type = 'union'"
            )
        )
    # جولة الكلية: صارت "مرة لكل كلية وبنفس اليوم" (CAST(... AS DATE)) بعد ما كانت
    # "مرة لكل كلية بطول الفعالية" — الفهرس القديم يُحذف لأن إعادة تعريف نفس الاسم
    # تحتاج DROP على قاعدة موجودة. القيد أوسع، فالسجلات الموجودة بتلتزم فيه كلها.
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS unique_tour_booking"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX unique_tour_booking "
                "ON bookings (student_id, college, CAST(booked_at AS DATE)) "
                "WHERE booking_type = 'tour'"
            )
        )
        conn.execute(text("DROP INDEX IF EXISTS unique_tour_checkin"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX unique_tour_checkin "
                "ON checkins (student_id, college, CAST(checked_in_at AS DATE)) "
                "WHERE activity_type = 'tour'"
            )
        )
    yield


@pytest.fixture(autouse=True)
def _clean_tables(_init_test_db):
    _request_log.clear()
    _otp_student_log.clear()
    _visit_log.clear()
    cache_module.clear_cache()
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE students, checkins, bookings, post_survey, otps, accounts, "
                "sms_jobs, sms_heartbeats, page_visits RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded_accounts(db):
    accounts = {}
    for username, password, role, college in BASE_ACCOUNTS:
        account = Account(
            username=username,
            password_hash=hash_password(password),
            role=role,
            college=college,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        accounts[role.value] = account
    return accounts


@pytest.fixture
def client(seeded_accounts):
    with TestClient(main_module.app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    def _headers(username: str, password: str) -> dict:
        resp = client.post("/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _headers


@pytest.fixture
def super_headers(auth_headers):
    return auth_headers("taher_super", "super123")


@pytest.fixture
def students_admin_headers(auth_headers):
    return auth_headers("sedra_admin", "admin123")


@pytest.fixture
def college_staff_headers(auth_headers):
    return auth_headers("rima_staff", "staff123")


@pytest.fixture
def gate_scanner_headers(auth_headers):
    return auth_headers("hadi_gate", "gate123")


@pytest.fixture
def game_corner_headers(auth_headers):
    return auth_headers("nour_game", "game123")


@pytest.fixture
def union_headers(auth_headers):
    return auth_headers("sara_union", "union123")


@pytest.fixture
def student_factory(db):
    def _make(
        unique_code: str,
        *,
        full_name: str = "طالب تجريبي",
        registration_type: RegistrationType = RegistrationType.registered,
        verification_status: VerificationStatus = VerificationStatus.verified,
        status: StudentStatus = StudentStatus.complete,
        contact_id: str | None = None,
        initial_preferred_major=None,
    ) -> Student:
        student = Student(
            unique_code=unique_code,
            full_name=full_name,
            registration_type=registration_type,
            verification_status=verification_status,
            status=status,
            contact_id=contact_id,
        )
        if initial_preferred_major is not None:
            student.initial_preferred_major = initial_preferred_major
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    return _make


@pytest.fixture
def create_custom_staff(db):
    def _create(username: str, password: str, college: Faculty | None) -> Account:
        account = Account(
            username=username,
            password_hash=hash_password(password),
            role=AccountRole.college_staff,
            college=college,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    return _create