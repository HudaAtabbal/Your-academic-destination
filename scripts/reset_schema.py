"""
إعادة بناء مخطط قاعدة البيانات (schema public) — يُشغَّل مرة واحدة عند تغيير
أنواع enum (PostgreSQL ما بيسمح بحذف/تعديل قيم enum قائمة، وcreate_all ما بيعدّل
نوعاً موجوداً).

⚠️  هذا السكريبت يمسح كل الجداول والبيانات في schema public بشكل نهائي.
    لا تشغّليه إلا على قاعدة بلا بيانات حقيقية (الإنتاج قبل الإطلاق).

الاستخدام (من جذر المشروع، مع تفعيل الـ venv):

    # 1) بالاعتماد على متغيّر البيئة DATABASE_URL
    python scripts/reset_schema.py --yes

    # 2) بتحديد رابط القاعدة صراحةً (يُستخدم هو أيضاً لأمر seed)
    python scripts/reset_schema.py --url "postgresql://USER:PASS@HOST/DB?sslmode=require" --yes

    # 3) إعادة البناء + زرع الحسابات الأولية بعده
    python scripts/reset_schema.py --url "..." --yes --seed

ملاحظات:
- لأمر DDL استخدمي رابط القاعدة المباشر (direct) مش الـ pooler إن أمكن.
- مع --seed خارج بيئة development لازم SEED_PASSWORD_* و JWT_SECRET_KEY بالبيئة.
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# طبعات عربية على كونسول ويندوز ممكن ترمي UnicodeEncodeError — نثبّت UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

RESET_STATEMENTS = [
    "DROP SCHEMA IF EXISTS public CASCADE",
    "CREATE SCHEMA public",
    "GRANT ALL ON SCHEMA public TO public",
]


def _to_psycopg2_url(url: str) -> str:
    """يحوّل صيغة SQLAlchemy (postgresql+psycopg2://) لصيغة psycopg2 مباشرة."""
    if url.startswith("postgresql+") or url.startswith("postgres+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


def _mask(url: str) -> str:
    """يخفي كلمة السر عند الطباعة."""
    try:
        parts = urlsplit(url)
        if parts.password:
            netloc = f"{parts.username}:***@{parts.hostname}"
            if parts.port:
                netloc = f"{netloc}:{parts.port}"
            return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except ValueError:
        pass
    return "<database-url>"


def _count_tables(pg_url: str) -> int:
    import psycopg2

    conn = psycopg2.connect(pg_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="إعادة بناء schema public + إنشاء الجداول (واختياريًا زرع البيانات الأولية)."
    )
    parser.add_argument(
        "--url",
        help="رابط القاعدة الهدف (افتراضيًا من متغيّر البيئة DATABASE_URL).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="تأكيد مباشر بدون سؤال تفاعلي (لازم في البيئات غير التفاعلية).",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="تشغيل app.seed_data بعد إعادة البناء لزرع الحسابات الأولية.",
    )
    args = parser.parse_args()

    url = args.url or os.getenv("DATABASE_URL")
    if not url:
        print("✗ ما في DATABASE_URL بالبيئة ولا --url بالوسائط.")
        return 2

    os.environ["DATABASE_URL"] = url
    pg_url = _to_psycopg2_url(url)

    print(f"قاعدة الهدف: {_mask(pg_url)}")
    print("⚠️  هذا سيمسح كل الجداول والبيانات في schema public بشكل نهائي.")

    if not args.yes:
        answer = input("اكتب RESET للتأكيد: ").strip()
        if answer != "RESET":
            print("تم الإلغاء — ما صار أي تغيير.")
            return 1

    try:
        import psycopg2  # noqa: F401
    except ImportError:
        print("✗ psycopg2 غير مثبّت — شغّل: pip install -r requirements.txt")
        return 3

    print("→ إعادة بناء المخطط ...")
    import psycopg2

    conn = psycopg2.connect(pg_url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            for statement in RESET_STATEMENTS:
                cur.execute(statement)
    finally:
        conn.close()
    print("✓ تم مسح وإعادة إنشاء schema public.")

    from app.database import Base, engine
    import app.models  # noqa: F401 — تسجيل كل الموديلات على Base.metadata قبل create_all

    Base.metadata.create_all(bind=engine)
    print("✓ تم إنشاء الجداول حسب التعريف الجديد (بما فيه قيم enum الجديدة).")

    if args.seed:
        from app.seed_data import seed

        seed()

    print(f"✓ عدد الجداول الآن: {_count_tables(pg_url)}")
    print("خلص. أعيدي تشغيل/نشر التطبيق (هو نفسه بيعمل create_all عند الإقلاع).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
