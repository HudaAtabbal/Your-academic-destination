"""
تصدير أرقام الطلاب "اللي سجّلوا إلكترونياً، موثّقين، وما دخلوا بوابة الجامعة
ولا مرة" لملف Excel (.xlsx).

المصدر: GET /admin/dashboard/registered-no-shows — نفس قائمة "مسجّلون بلا حضور"
اللي بالداشبورد. تعريفها بالمشروع (dashboard_service._registered_no_show_query):
    registration_type = registered
    verification_status = verified          ← موثّق (أكّد كود OTP)
    ولا يوجد checkin بنوع campus_entry      ← ما دخل البوابة ولا مرة
    ولا زيارة كلية (حجز أو checkin بكلية)
الرقم = contact_id. الدور المطلوب: super_admin.

مكمّل لـ export_unverified_registered.py (غير الموثّقين) و
export_registered_entered.py (اللي دخلوا) — بيستعمل نفس دوال الدخول
وكتابة الـ Excel.

⚠️ الفرق عن "كل المسجّلين يلي ما دخلوا": الشرط الرابع (ما زاروا كلية) موجود
بالاستعلام الأصلي. فلو بدك تشيله أو تضيف ترشيحات، عدّل الاستعلام بالمصدر.

الاستخدام (من جذر المشروع):
    powershell -ExecutionPolicy Bypass -File scripts\\run_export_no_shows.ps1

أو مباشرة:
    python scripts/export_registered_no_shows.py --user U --password P
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

try:
    import requests
except ImportError:
    print("✗ requests غير مثبّت — شغّل: pip install -r requirements.txt")
    raise SystemExit(3)

# نفس المجلد — التشغيل كـ `python scripts\export_registered_no_shows.py` بيخلي
# مجلد السكربت ضمن sys.path تلقائياً
from export_unverified_registered import (  # noqa: E402
    DEFAULT_BASE,
    PAGE_LIMIT,
    TIMEOUT_SECONDS,
    _err,
    build_auth_header,
    write_xlsx,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = _REPO_ROOT / "exports"
LIST_PATH = "/admin/dashboard/registered-no-shows"


def _get_page(base_url: str, auth_header: str, page: int) -> dict | None:
    """جلب صفحة وحدة من قائمة "مسجّلون بلا حضور"."""
    try:
        resp = requests.get(
            f"{base_url}{LIST_PATH}",
            headers={"Authorization": auth_header},
            params={"page": page, "limit": PAGE_LIMIT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        _err(f"تعذّر جلب الصفحة {page} — {exc}")
        return None

    if resp.status_code == 401:
        _err("التوكن منتهي أو غير صالح (401) — سجّل دخول من جديد", 2)
    if resp.status_code == 403:
        _err("الحساب ما إلو صلاحية (403) — هاد الـ endpoint بدو super_admin", 2)
    if resp.status_code >= 400:
        _err(f"فشل الجلب — {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def fetch_no_shows(base_url: str, auth_header: str) -> tuple[list[str], int]:
    """ترجع (أرقام التواصل بلا تكرار ولا ترتيب، إجمالي السجلات بالمصدر)."""
    payload = _get_page(base_url, auth_header, 1)
    if payload is None:
        _err("ما قدرنا نجيب أي رد من الـ endpoint", 2)

    total = int(payload.get("total") or 0)
    total_pages = int(payload.get("total_pages") or 1)

    items = list(payload.get("items") or [])
    for page in range(2, total_pages + 1):
        page_body = _get_page(base_url, auth_header, page) or {}
        items.extend(page_body.get("items") or [])

    numbers: list[str] = []
    skipped_null = 0
    for item in items:
        contact = str(item.get("contact_id") or "").strip()
        if contact:
            numbers.append(contact)
        else:
            skipped_null += 1

    if skipped_null:
        print(f"… تخطّينا {skipped_null} سجل بدون رقم تواصل")

    return sorted(set(numbers)), total


def main() -> int:
    parser = argparse.ArgumentParser(
        description="تصدير أرقام المسجّلين الموثّقين يلي ما دخلوا البوابة لملف Excel"
    )
    parser.add_argument(
        "--base", default=os.getenv("WJ_API_BASE", DEFAULT_BASE),
        help=f"رابط الـ API (افتراضياً {DEFAULT_BASE})",
    )
    parser.add_argument(
        "--user", default=os.getenv("WJ_API_USER"),
        help="اسم مستخدم أدمن (أو المتغيّر WJ_API_USER)",
    )
    parser.add_argument(
        "--password", default=os.getenv("WJ_API_PASS"),
        help="كلمة سر الأدمن (أو المتغيّر WJ_API_PASS)",
    )
    parser.add_argument(
        "--out", default=None,
        help="مسار ملف الـ xlsx (افتراضياً exports/ registered_no_shows_<وقت>.xlsx)",
    )
    args = parser.parse_args()

    if not args.user or not args.password:
        print("✗ ناقص بيانات الدخول. مرّرها بـ --user و --password،")
        print("  أو حدّد متغيّرات البيئة WJ_API_USER و WJ_API_PASS قبل التشغيل.")
        print("  أو استعمل: powershell -File scripts\\run_export_no_shows.ps1")
        return 2

    base_url = args.base.rstrip("/")
    print(f"→ تسجيل الدخول بـ {base_url} ...")
    auth_header = build_auth_header(base_url, args.user, args.password)
    print("✓ تم الدخول")

    print("→ سحب الطلاب ...")
    numbers, source_total = fetch_no_shows(base_url, auth_header)
    print(f"✓ السجلات بالمصدر: {source_total} | أرقام بلا تكرار: {len(numbers)}")

    if args.out:
        out_path = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = EXPORT_DIR / f"registered_no_shows_{stamp}.xlsx"

    write_xlsx(numbers, out_path, sheet_title="ما دخلوا البوابة")
    print(f"✓ حُفظ الملف: {out_path}")
    if numbers:
        print(f"  أول 3: {', '.join(numbers[:3])}")
        print(f"  آخر 3: {', '.join(numbers[-3:])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
