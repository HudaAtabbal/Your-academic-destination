"""
المُرسِل الداخلي SMS — يعمل على لابتوب داخل سوريا (سيرياتيل ترفض الإرسال من IP أجنبي).

الملف الوحيد الذي يُنسخ إلى اللابتوب، بجانبه app/sms_service.py (بنفس البنية
المجلدية) وملف .env صغير. لا يحتاج قاعدة بيانات ولا FastAPI ولا حسابات فريق — فقط:
- Python + requests
- HTTPS خارجي (منفذ 443) للوصول إلى الخادم و bms.syriatel.sy

الدورة: السحب من /internal/sms/dequeue ← إرسال عبر سيرياتيل ← إبلاغ بالنتيجة،
ونبضة /internal/sms/heartbeat كل ثوانٍ معدودة ليعرف الخادم أننا على قيد الحياة.

التشغيل: يحمّل التطبيق بشكل منطقي من نفس مجلد العمل. امنحه الإقلاع التلقائي
عبر Task Scheduler (عند بدء التشغيل) — لا يعيد تشغيل نفسه بنفسه.

⚠️ لا تُسجّل رمز OTP الخامي أبداً — اللوغات تحمل job_id فقط.
"""

import os
import sys
import time
import traceback
import logging
from logging.handlers import RotatingFileHandler

import requests

# السماح باستيراد app.sms_service من مجلد المشروع (على اللابتوب أعد تسمية
# المجلد كما تشاء — الشرط أن يحتوي على app/sms_service.py)
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app.sms_service import SmsSendError, send_otp_sms  # noqa: E402

_BASE_URL = os.getenv("API_BASE_URL", "https://api.example.com").rstrip("/")
_WORKER_TOKEN = os.getenv("WORKER_TOKEN", "")
_POLL_INTERVAL = float(os.getenv("SMS_POLL_INTERVAL", "1"))
_HEARTBEAT_INTERVAL = float(os.getenv("SMS_HEARTBEAT_INTERVAL", "30"))
_BATCH_SIZE = max(1, min(10, int(os.getenv("SMS_BATCH_SIZE", "3"))))

_HEADERS = {"Authorization": f"Bearer {_WORKER_TOKEN}"}


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("sms_worker")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "sms_worker.log"),
        maxBytes=1_000_000,
        backupCount=3,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger


def _dequeue(logger: logging.Logger, count: int) -> list[dict]:
    """يسحب حتى count مهمة pending من الخادم — او [] عند عدم وجود مهام."""
    resp = requests.post(
        f"{_BASE_URL}/internal/sms/dequeue",
        params={"batch": count},
        headers=_HEADERS,
        timeout=15,
    )
    if resp.status_code == 401:
        logger.error("dequeue: 401 — توكن المُرسِل مرفوض، تحقق من WORKER_TOKEN")
        return []
    resp.raise_for_status()
    return resp.json()


def _report(logger: logging.Logger, *, job_id: int, success: bool, transient: bool, error: str | None) -> None:
    """يبلّغ الخادم بالنتيجة؛ لو فشل الإبلاغ يسجّل الخطأ — الخادم ستستردّ المهمة تلقائياً."""
    try:
        response = requests.post(
            f"{_BASE_URL}/internal/sms/report",
            headers=_HEADERS,
            json={
                "job_id": job_id,
                "success": success,
                "transient": transient,
                "error": error,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error(
            "job %s: فشل إبلاغ النتيجة للخادم: %s — ستُستردّ المهمة تلقائياً",
            job_id,
            exc,
        )


def _heartbeat(logger: logging.Logger) -> None:
    try:
        requests.post(f"{_BASE_URL}/internal/sms/heartbeat", headers=_HEADERS, timeout=15)
    except requests.RequestException as exc:
        logger.warning("heartbeat: فشل الاتصال بالخادم: %s", exc)


def _process_job(logger: logging.Logger, job: dict) -> None:
    job_id = job["job_id"]
    try:
        send_otp_sms(job["phone"], job["otp_code"])
    except SmsSendError as exc:
        # فشل دائم: سيرياتيل أعادت رسالة خطأ معروفة — لا جدوى من إعادة المحاولة
        logger.error("job %s: فشل دائم من سيرياتيل: %s", job_id, exc)
        _report(logger, job_id=job_id, success=False, transient=False, error=str(exc)[:500])
    except requests.RequestException as exc:
        # فشل مؤقت (اتصال/شبكة) — الخادم سيعيد المهمة للطابور حتى حد المحاولات
        logger.warning("job %s: فشل اتصال مؤقت: %s", job_id, exc)
        _report(logger, job_id=job_id, success=False, transient=True, error=str(exc)[:500])
    except Exception:
        # خطأ برمجي غير متوقع — نعامله كمؤقت (يُعاد للمحاولة) مع تسجيل الأثر كاملاً
        logger.error("job %s: خطأ غير متوقع:\n%s", job_id, traceback.format_exc())
        _report(logger, job_id=job_id, success=False, transient=True, error="unexpected worker error")
    else:
        logger.info("job %s: تم إرسال الرمز إلى %s", job_id, job["phone"])
        _report(logger, job_id=job_id, success=True, transient=False, error=None)


def _validate_env(logger: logging.Logger) -> bool:
    """فحص مبكر قبل بدء الدورة — يعرض المشكلة بوضوح عند الإقلاع بدل الفوضى لاحقاً."""
    ok = True
    if not _WORKER_TOKEN:
        logger.error("WORKER_TOKEN غير مضبوط في البيئة")
        ok = False
    for variable in (
        "SYRIATEL_USERNAME",
        "SYRIATEL_PASSWORD",
        "SYRIATEL_SENDER",
        "SYRIATEL_TEMPLATE_CODE",
    ):
        if not os.getenv(variable):
            logger.error("%s غير مضبوط في البيئة", variable)
            ok = False
    if "example.com" in _BASE_URL:
        logger.error("API_BASE_URL غير مضبوط (افتراضي تجريبي)")
        ok = False
    return ok


def main() -> None:
    logger = _setup_logger()
    logger.info("بدء المُرسِل الداخلي — %s | batch=%d | poll=%.1fs | heartbeat=%.1fs",
                _BASE_URL, _BATCH_SIZE, _POLL_INTERVAL, _HEARTBEAT_INTERVAL)

    if not _validate_env(logger):
        logger.error("إقلاع مرفوض بسبب متغيرات بيئة ناقصة")
        raise SystemExit(1)

    last_heartbeat = 0.0
    while True:
        cycle_start = time.monotonic()

        try:
            jobs = _dequeue(logger, _BATCH_SIZE)
            for job in jobs:
                if not isinstance(job, dict) or "job_id" not in job:
                    logger.error("استجابة dequeue غير متوقعة: %r", job)
                    continue
                _process_job(logger, job)
        except requests.RequestException as exc:
            logger.warning("فشل الاتصال بالخادم: %s", exc)
        except Exception:
            logger.error("خطأ غير متوقع بالدورة الرئيسية:\n%s", traceback.format_exc())

        if time.monotonic() - last_heartbeat >= _HEARTBEAT_INTERVAL:
            _heartbeat(logger)
            last_heartbeat = time.monotonic()

        elapsed = time.monotonic() - cycle_start
        time.sleep(max(0.0, _POLL_INTERVAL - elapsed))


if __name__ == "__main__":
    main()
