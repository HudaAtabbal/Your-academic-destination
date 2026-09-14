"""
منطق طابور إرسال SMS — سحب المهام، استرداد المهام العالقة، الإبلاغ بالنتيجة، والنبضة.

القرارات المحسومة (تناقشنا بها قبل التنفيذ):
- يسير الخادم على Cloudflare والمُراسِل على لابتوب داخل سوريا (سيرياتيل ترفض
  السيرفرات الأجنبية). الصف يحمل `otp_code` نصاً صريحاً — ضروري للإرسال، مع
  أن otps تخزّن sha256 فقط؛ الإزاحة: عمر قصير (10 دقائق) + CASCADE عند حذف OTP.
- at-least-once: قد يتكرر الإرسال لو ضاع إبلاغ النتيجة بين السحب والإبلاغ —
  الاسترداد أدناه يضمن عدم بقاء أي مهمة عالقة أبداً.
- كل المقارنات الزمنية naive-local datetime.now() — نفس اصطلاح بقية التطبيق
  (هنا otps.expires_at و dashboard) لتفادي انحراف متقابل بين المقارنات.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import OTP, SmsHeartbeat, SmsJob, SmsJobStatus
from app.sms_service import to_international_format

# ---- ثوابت السلوك ----
_MAX_ATTEMPTS = 5                       # كحد أقصى 5 محاولات إرسال حقيقية
_CLAIM_TIMEOUT_SECONDS = 120            # صف sending بلا إبلاغ أطول من هذا = عالق يُستردّ
_WORKER_ONLINE_SECONDS = 180            # مرسِل متصل إذا نبضته أحدث من هذا بالوحة الإدارة
_ERROR_MAX_LENGTH = 500


def _now() -> datetime:
    """وقت مرجعي موحّد — naive local، متطابق مع بقية التطبيق (otps/dashboard)."""
    return datetime.now()


def _is_online(last_seen_at: datetime | None, now: datetime) -> bool:
    """معيار "المُرسِل متصل" — نبضة خلال آخر 180 ثانية (مصدر واحد للقاعدة)."""
    return last_seen_at is not None and last_seen_at >= now - timedelta(
        seconds=_WORKER_ONLINE_SECONDS
    )


def is_worker_online(db: Session, now: datetime | None = None) -> bool:
    """حالة المُرسِل للوحة الإدارة — نبضة حديثة خلال نافذة الاتصال."""
    now = now or _now()
    heartbeat = db.query(SmsHeartbeat).first()
    return _is_online(heartbeat.last_seen_at if heartbeat is not None else None, now)


def _reclaim_stale_jobs(db: Session, now: datetime) -> None:
    """
    إعادة صف عالق (sending بلا إبلاغ) إلى pending بعد انتهاء مهلة السحب.

    لا نشترط موت المُرسِل: إبلاغ النتيجة قد يضيع لو انقطعت الشبكة بين اللابتوب
    والخادم بينما المُرسِل حيّ يرسل نبضات — ولو اشترطنا موته لبقيت المهمة
    محتجزة إلى الأبد بلا إرسال ولا ظهور كفشل. مهلة 120 ثانية أكبر بكثير من
    مهلة الإرسال نفسها (15s)، فاعتبار الصف عالقاً آمن. المقايضة at-least-once:
    إبلاغ ضائع بعد إرسال ناجح قد يسبب رسالة مكررة واحدة — أفضل من رمز لا يصل.
    """
    cutoff = now - timedelta(seconds=_CLAIM_TIMEOUT_SECONDS)
    stale_jobs = (
        db.query(SmsJob)
        .filter(
            SmsJob.status == SmsJobStatus.sending,
            or_(SmsJob.claimed_at.is_(None), SmsJob.claimed_at < cutoff),
        )
        .all()
    )
    for job in stale_jobs:
        if job.attempts >= _MAX_ATTEMPTS:
            # استُنفدت كل المحاولات بدون نجاح — المهمة فشلت نهائياً
            job.status = SmsJobStatus.failed
        else:
            job.status = SmsJobStatus.pending
            job.claimed_at = None

    # SessionLocal بيعمل autoflush=False — عمليات التحديث بالذاكرة لازم تِفلاش
    # صراحة قبل الاستعلام اللاحق (لكي يرى استعلام السحب الحالة الجديدة)
    db.flush()


def dequeue_jobs(db: Session, batch: int) -> list[dict]:
    """
    يسحب batch مهام pending (SKIP LOCKED) ويرجعن ببيانات الإرسال.

    يستبعد: المهام التي بلغ صاحبها رمز OTP منتهي الصلاحية (الطلاب ما عاد
    يحتاجونها)، والمهام التي بلغت حد المحاولات. الصف الواحد يُسحب من مرسل
    واحد فقط في أي لحظة (FOR UPDATE SKIP LOCKED).
    """
    now = _now()
    _reclaim_stale_jobs(db, now)

    jobs = (
        db.query(SmsJob)
        .join(OTP, SmsJob.otp_id == OTP.id)
        .filter(
            SmsJob.status == SmsJobStatus.pending,
            SmsJob.attempts < _MAX_ATTEMPTS,
            OTP.expires_at > now,
        )
        .order_by(SmsJob.created_at.asc(), SmsJob.id.asc())
        .with_for_update(skip_locked=True)
        .limit(batch)
        .all()
    )

    result = []
    for job in jobs:
        job.status = SmsJobStatus.sending
        job.claimed_at = now
        job.attempts += 1
        result.append(
            {
                "job_id": job.id,
                "phone": to_international_format(job.phone),
                "otp_code": job.otp_code,
                "expires_at": job.otp.expires_at,
            }
        )

    db.commit()
    return result


def report_job(
    db: Session, job_id: int, success: bool, transient: bool, error: str | None
) -> SmsJob:
    """
    يطبّق نتيجة محاولة إرسال من المرسل على المهمة.

    idempotent: إذا لم تعد المهمة في حالة sending (سحبها مرسل آخر، أو أُنهي
    سابقاً) يعيدها كما هي بلا أي تغيير، بدل تطبيق نتيجة مرسل متأخر/مكرر.
    """
    job = db.query(SmsJob).filter(SmsJob.id == job_id).with_for_update().first()
    if job is None:
        raise LookupError(f"job {job_id} not found")

    if job.status != SmsJobStatus.sending:
        db.rollback()
        return job

    if success:
        job.status = SmsJobStatus.sent
        job.sent_at = _now()
        job.error = None
    elif transient and job.attempts < _MAX_ATTEMPTS:
        # فشل مؤقت مع محاولات متبقية — يعود للطابور من جديد
        job.status = SmsJobStatus.pending
        job.claimed_at = None
        job.error = (error or "")[:_ERROR_MAX_LENGTH]
    else:
        # فشل دائم (رسالة خطأ سيرياتيل) أو بلغ الفشل المؤقت حد المحاولات
        job.status = SmsJobStatus.failed
        job.error = (error or "send failed")[:_ERROR_MAX_LENGTH]

    db.commit()
    return job


def record_heartbeat(db: Session) -> None:
    """جدول أحادي الصف — النبضة الأخيرة للمرسل (upsert على id=1)."""
    now = _now()
    heartbeat = db.query(SmsHeartbeat).first()
    if heartbeat is None:
        db.add(SmsHeartbeat(id=1, last_seen_at=now))
    else:
        heartbeat.last_seen_at = now
    db.commit()


def get_sms_status(db: Session) -> dict:
    """إحصائيات المهام حسب الحالة + حالة المرسل — للوحة الإدارة."""
    counts = {status.value: 0 for status in SmsJobStatus}
    rows = db.query(SmsJob.status, func.count(SmsJob.id)).group_by(SmsJob.status).all()
    for status, count in rows:
        counts[status.value] = count

    heartbeat = db.query(SmsHeartbeat).first()
    last_seen_at = heartbeat.last_seen_at if heartbeat is not None else None
    return {
        "counts": counts,
        "last_heartbeat": last_seen_at,
        "worker_online": _is_online(last_seen_at, _now()),
    }
