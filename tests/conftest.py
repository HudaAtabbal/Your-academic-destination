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
from app.database import Base, SessionLocal, engine
from app.dependencies import _request_log
from app.models import Account, AccountRole, College, RegistrationType, Student, StudentStatus, VerificationStatus
from app.security import hash_password

BASE_ACCOUNTS = [
    ("taher_super", "super123", AccountRole.super_admin, None),
    ("sedra_admin", "admin123", AccountRole.students_admin, None),
    ("rima_staff", "staff123", AccountRole.college_staff, College.medicine),
    ("hadi_gate", "gate123", AccountRole.gate_scanner, None),
]

DEFAULT_STUDENT_CODE = "R-9001"


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables(_init_test_db):
    _request_log.clear()
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE students, checkins, bookings, post_survey, otps, accounts "
                "RESTART IDENTITY CASCADE"
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
def student_factory(db):
    def _make(
        unique_code: str,
        *,
        full_name: str = "طالب تجريبي",
        registration_type: RegistrationType = RegistrationType.registered,
        verification_status: VerificationStatus = VerificationStatus.verified,
        status: StudentStatus = StudentStatus.complete,
        contact_platform=None,
        contact_id: str | None = None,
        initial_preferred_major=None,
    ) -> Student:
        student = Student(
            unique_code=unique_code,
            full_name=full_name,
            registration_type=registration_type,
            verification_status=verification_status,
            status=status,
        )
        if contact_platform is not None:
            student.contact_platform = contact_platform
            student.contact_id = contact_id
        if initial_preferred_major is not None:
            student.initial_preferred_major = initial_preferred_major
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    return _make


@pytest.fixture
def create_custom_staff(db):
    def _create(username: str, password: str, college: College | None) -> Account:
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