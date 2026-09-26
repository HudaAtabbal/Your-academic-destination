"""
تصدير أرقام الطلاب "اللي سجّلوا إلكترونياً ودخلوا الجامعة (مرة على الأقل)"
لملف Excel (.xlsx).

المصدر: GET /admin/dashboard/students-inside?reg_type=R — قائمة الطلاب المميزين
follow دخلوا الحرم عبر بوابة الجامعة (campus_entry) مرة وحدة على الأقل بكل
الأيام، و reg_type=R بيقلّيهم للمسجّلين إلكترونياً بس (بدون ووك إن).
الرقم = contact_id. الدور المطلوب: super_admin.

مكمّل لملف export_unverified_registered.py (اللي بيصدّر غير الموثّقين) —
بيستعمل نفس دوال الدخول وكتابة الـ Excel.

الاستخدام (من جذر المشروع):
    powershell -ExecutionPolicy Bypass -File scripts\\run_export_entered.ps1

أو مباشرة:
    python scripts/export_registered_entered.py --user U --password P
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

# نفس المجلد — التشغيل كـ `python scripts\export_registered_entered.py` بيخلي
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
LIST_PATH = "/admin/dashboard/students-inside"


def fetch_registered_entered(base_url: str, auth_header: str) -> tuple[list[str], int]:
    """
    ترجع (أرقام التواصل بلا تكرار ولا ترتيب، إجمالي السجلات بالمصدر).

    paginate كل الصفحات بحد الـ endpoint (limit≤100) و reg_type=R لمسجّلي
    الموقع بس. لو النسخة المنشورة أقدم وما بتقبل reg_type، بينزل تلقائياً
    لوضع "جيب الكل وافرّم عالعميل" — نفس النتيجة بلا ما نلمس السيرفر.
    """
    server_filtered = True

    def _page(page: int, with_filter: bool) -> dict | None:
        params: dict[str, str | int] = {"page": page, "limit": PAGE_LIMIT}
        if with_filter:
            params["reg_type"] = "R"
        try:
            resp = requests.get(
                f"{base_url}{LIST_PATH}",
                headers={"Authorization": auth_header},
                params=params,
                timeout=TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            _err(f"تعذّر جلب الصفحة {page} — {exc}")
            return None

        if resp.status_code == 401:
            _err("التوكن منتهي أو غير صالح (401) — سجّل دخول من جديد", 2)
        if resp.status_code == 403:
            _err("الحساب ما إلو صلاحية (403) — هاد الـ endpoint بدو super_admin", 2)
        if resp.status_code == 422 and with_filter:
            return None
        if resp.status_code >= 400:
            _err(f"فشل الجلب — {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    payload = _page(1, True)
    if payload is None:
        print("… النسخة المنشورة ما بتدعم reg_type — بنفلتر محلياً")
        server_filtered = False
        payload = _page(1, False)
    if payload is None:
        _err("ما قدرنا نجيب أي رد من الـ endpoint", 2)

    total = int(payload.get("total") or 0)
    total_pages = int(payload.get("total_pages") or 1)

    items = list(payload.get("items") or [])
    for page in range(2, total_pages + 1):
        page_body = _page(page, server_filtered) or {}
        items.extend(page_body.get("items") or [])

    numbers: list[str] = []
    skipped_null = 0
    for item in items:
        if not server_filtered and item.get("registration_type") not in (None, "registered"):
            continue
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
        description="تصدير أرقام المسجّلين إلكترونياً يلي دخلوا الجامعة لملف Excel"
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
        help="مسار ملف الـ xlsx (افتراضياً exports/ registered_entered_<وقت>.xlsx)",
    )
    args = parser.parse_args()

    if not args.user or not args.password:
        print("✗ ناقص بيانات الدخول. مرّرها بـ --user و --password،")
        print("  أو حدّد متغيّرات البيئة WJ_API_USER و WJ_API_PASS قبل التشغيل.")
        print("  أو استعمل: powershell -File scripts\\run_export_entered.ps1")
        return 2

    base_url = args.base.rstrip("/")
    print(f"→ تسجيل الدخول بـ {base_url} ...")
    auth_header = build_auth_header(base_url, args.user, args.password)
    print("✓ تم الدخول")

    print("→ سحب الطلاب ...")
    numbers, source_total = fetch_registered_entered(base_url, auth_header)
    print(f"✓ السجلات بالمصدر: {source_total} | أرقام بلا تكرار: {len(numbers)}")

    if args.out:
        out_path = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = EXPORT_DIR / f"registered_entered_{stamp}.xlsx"

    write_xlsx(numbers, out_path, sheet_title="دخل الجامعة")
    print(f"✓ حُفظ الملف: {out_path}")
    if numbers:
        print(f"  أول 3: {', '.join(numbers[:3])}")
        print(f"  آخر 3: {', '.join(numbers[-3:])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
