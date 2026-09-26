"""
تصدير أرقام هواتف الطلاب "المسجّلين إلكترونياً وغير الموثّقين" لملف Excel (.xlsx).

المصدر هو endpoint موجود أصلاً بالمشروع:
    GET /admin/students/registered?verification_status=pending
والفيلتر بينهار مع: registration_type=registered (مسجّل إلكترونياً) +
verification_status=pending (ما أكّد كود OTP = غير موثّق). رقم الهاتف = contact_id.
الدور المطلوب للحساب: students_admin أو super_admin.

التصدير بيتم عبر الـ API المنشور (مش اتصال مباشر بالقاعدة) — القاعدة على
استضافة مشتركة و Postgres مربوط على localhost داخل السيرفر، فمافي اتصال خارجي.

الاستخدام (من جذر المشروع، PowerShell):
    حدّد متغيّرات البيئة WJ_API_BASE و WJ_API_USER و WJ_API_PASS قبل التشغيل،
    أو مرّر --user و --password كـ arguments (الطريقة الأنظف — ما بتخزّن كلمة السر).

    python scripts/export_unverified_registered.py --user U --password P
    python scripts/export_unverified_registered.py --user U --password P -o out.xlsx

الملف الناتج بينكتب بمجلد exports/ (مستثنى من git) إلا إذا مرّرت --out.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import NoReturn

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

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
except ImportError:
    print("✗ openpyxl غير مثبّت — شغّل: pip install openpyxl==3.1.5")
    raise SystemExit(3)

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://sunion-homs-uni.sy/api"
EXPORT_DIR = _REPO_ROOT / "exports"
PAGE_LIMIT = 100  # الحد الأقصى للـ endpoint (limit: le=100)
TIMEOUT_SECONDS = 30


def _err(message: str, code: int = 1) -> NoReturn:
    print(f"✗ {message}")
    raise SystemExit(code)


def build_auth_header(base_url: str, username: str, password: str) -> str:
    """
    تسجيل دخول بـ POST /auth/login وإرجاع هيدر Authorization جاهز للتعليق.
    كلمة السر ما بتتخزّن بأي مكان وبتما ببساطة ما بتطبع شي منها.
    """
    try:
        resp = requests.post(
            f"{base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        _err(f"تعذّر الوصول لـ {base_url} — {exc}")

    if resp.status_code == 401:
        _err("اسم المستخدم أو كلمة السر غلط (401)", 2)
    if resp.status_code == 429:
        _err("تجاوزت حدّ محاولات الدخول — استنى دقيقة وحاول تاني (429)", 2)
    if resp.status_code >= 400:
        _err(f"فشل تسجيل الدخول — {resp.status_code}: {resp.text[:200]}", 2)

    body = resp.json()
    value = body.get("access_token")
    if not value:
        _err("الرد ما فيه access_token — تأكد إن الرابط صحيح وينتهي بـ /api", 2)
    return f"Bearer {value}"


def _get_page(base_url: str, auth_header: str, page: int, with_filter: bool) -> dict | None:
    """
    جلب صفحة وحدة من قائمة المسجّلين. ترجع None لو النسخة المنشورة ما بتقبل
    فلتر verification_status (422) — إشارة للسقوط للفلترة المحلية.
    """
    params: dict[str, str | int] = {"page": page, "limit": PAGE_LIMIT}
    if with_filter:
        params["verification_status"] = "pending"

    try:
        resp = requests.get(
            f"{base_url}/admin/students/registered",
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
        _err("الحساب ما إلو صلاحية (403) — لازم students_admin أو super_admin", 2)
    if resp.status_code == 422 and with_filter:
        return None
    if resp.status_code >= 400:
        _err(f"فشل الجلب — {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def fetch_unverified_numbers(base_url: str, auth_header: str) -> tuple[list[str], int]:
    """
    ترجع (أرقام التواصل بلا تكرار ولا ترتيب، إجمالي السجلات بالمصدر).

    بتمرّر verification_status=pending للـ endpoint؛ لو النسخة المنشورة أقدم
    بتقبل 422 بينزل تلقائياً لوضع "جيب الكل وافرّم عالعميل" — نفس النتيجة
    بلا ما نلمس السيرفر.
    """
    server_filtered = True
    payload = _get_page(base_url, auth_header, 1, True)
    if payload is None:
        print("… النسخة المنشورة ما بتدعم verification_status — بنفلتر محلياً")
        server_filtered = False
        payload = _get_page(base_url, auth_header, 1, False)
    if payload is None:
        _err("ما قدرنا نجيب أي رد من الـ endpoint", 2)

    total = int(payload.get("total") or 0)
    total_pages = int(payload.get("total_pages") or 1)

    items = list(payload.get("items") or [])
    for page in range(2, total_pages + 1):
        page_body = _get_page(base_url, auth_header, page, server_filtered) or {}
        items.extend(page_body.get("items") or [])

    numbers: list[str] = []
    skipped_null = 0
    for item in items:
        if not server_filtered and item.get("verification_status") != "pending":
            continue
        contact = str(item.get("contact_id") or "").strip()
        if contact:
            numbers.append(contact)
        else:
            skipped_null += 1

    if skipped_null:
        print(f"… تخطّينا {skipped_null} سجل بدون رقم تواصل")

    return sorted(set(numbers)), total


def write_xlsx(numbers: list[str], out_path: Path, sheet_title: str = "غير موثقين") -> None:
    """كتابة الأرقام بملف .xlsx — عمود واحد، كل رقم نص عشان ما يضيع الصفر الأول."""
    wb = Workbook()
    ws = wb.active
    if ws is None:
        _err("openpyxl ما رجّع ورقة عمل — نادر، بعطّل إنشاء الـ file")
    ws.title = sheet_title
    ws.sheet_view.rightToLeft = True  # الأرقام يمين-لشمال مثل الجدول بالفرونت

    header = ws.cell(row=1, column=1, value="رقم الهاتف")
    header.font = Font(bold=True)
    header.alignment = Alignment(horizontal="center")

    for offset, number in enumerate(numbers, start=2):
        cell = ws.cell(row=offset, column=1, value=number)
        cell.number_format = "@"  # نص: 09xxxxxxxx ما يصير رقم ويفقد الصفر

    ws.column_dimensions["A"].width = 20
    ws.freeze_panes = "A2"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="تصدير أرقام المسجّلين إلكترونياً وغير الموثّقين لملف Excel"
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
        help="مسار ملف الـ xlsx (افتراضياً exports/ unverified_registered_<وقت>.xlsx)",
    )
    args = parser.parse_args()

    if not args.user or not args.password:
        print("✗ ناقص بيانات الدخول. مرّرها بـ --user و --password،")
        print("  أو حدّد متغيّرات البيئة WJ_API_USER و WJ_API_PASS قبل التشغيل.")
        print("  (ما بيكتبوا كلمة السر بالملف ولا بيطبعوها بالـ output)")
        return 2

    base_url = args.base.rstrip("/")
    print(f"→ تسجيل الدخول بـ {base_url} ...")
    auth_header = build_auth_header(base_url, args.user, args.password)
    print("✓ تم الدخول")

    print("→ سحب الطلاب ...")
    numbers, source_total = fetch_unverified_numbers(base_url, auth_header)
    print(f"✓ السجلات بالمصدر: {source_total} | أرقام بلا تكرار: {len(numbers)}")

    if args.out:
        out_path = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_path = EXPORT_DIR / f"unverified_registered_{stamp}.xlsx"

    write_xlsx(numbers, out_path)
    print(f"✓ حُفظ الملف: {out_path}")
    if numbers:
        print(f"  أول 3: {', '.join(numbers[:3])}")
        print(f"  آخر 3: {', '.join(numbers[-3:])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
