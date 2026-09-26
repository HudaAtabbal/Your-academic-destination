"""
تشغيل ملفات الترحيل SQL على قواعد التطوير والاختبار المحلية (Wijhatak_db /
wijhatak_test). القواعد الجديدة تُنشأ من الموديلات مباشرةً فلا تحتاج هذا السكريبت.

الاستخدام (من جذر المشروع، مع تفعيل الـ venv):
    python scripts/run_sql_migration.py
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

MIGRATION_FILE = Path(__file__).resolve().parent / "migration_tour_per_day.sql"
TARGET_DBS = [
    ("dev", "postgresql://postgres:1234@localhost:5432/Wijhatak_db"),
    ("test", "postgresql://postgres:1234@localhost:5432/wijhatak_test"),
]


def main() -> int:
    if not MIGRATION_FILE.exists():
        print(f"✗ الملف غير موجود: {MIGRATION_FILE}")
        return 2

    try:
        import psycopg2  # noqa: F401
    except ImportError:
        print("✗ psycopg2 غير مثبّت — شغّل: pip install -r requirements.txt")
        return 3

    sql = MIGRATION_FILE.read_text(encoding="utf-8")

    for label, url in TARGET_DBS:
        print(f"→ تطبيق على {label} ...")
        conn = psycopg2.connect(url)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"✓ {label} تم")
        except Exception as exc:
            conn.rollback()
            print(f"✗ {label} فشل: {exc}")
        finally:
            conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())