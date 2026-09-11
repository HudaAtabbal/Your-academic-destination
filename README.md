# وجهتك الأكاديمية — Backend API

Backend لمنصة فعالية الاتحاد الطالبي "وجهتك الأكاديمية" — مبني بـ FastAPI + SQLAlchemy + PostgreSQL.

يوفر النظام: تسجيل الطلاب (مع OTP عبر SMS)، رموز دخول عشوائية، حضور (check-ins)، حجوزات، نقاط ولوحة ترتيب، استبيانات، إدارة حسابات فريق العمل، وتوليد رموز walk-in.

---

## التشغيل المحلي (تطوير)

```bash
# 1. درثة بايثون 3.12
python -m venv venv
# Windows: venv\Scripts\activate    |  macOS/Linux: source venv/bin/activate

# 2. التبعيات
pip install -r requirements-dev.txt

# 3. الإعدادات
cp .env.example .env        # ثم عبي القيم الصحيحة (انظري القسم بالأسفل)

# 4. زرع (اختياري) — حسابات فريق العمل + طالب تجريبي
python -m app.seed_data

# 5. تشغيل
uvicorn main:app --reload
```

- التوثيق التلقائي: `http://localhost:8000/docs`
- فحص الصحة: `http://localhost:8000/health`
- الاختبارات: `pytest -q` (تستخدم قاعدة `wijhatak_test`)

### متغيرات البيئة المطلوبة

| المتغير | مطلوب؟ | الاستخدام |
|---|---|---|
| `DATABASE_URL` | ✅ نعم | عنوان قاعدة PostgreSQL (صيغة SQLAlchemy) |
| `JWT_SECRET_KEY` | ✅ نعم | سر توقيع التوكنات — قيمة عشوائية طويلة |
| `APP_ENV` | لا | `development` (افتراضي) أو `production` |
| `ALLOWED_ORIGINS` | في production | دومينات الفرونت المسموحة، بفواصل |
| `SYRIATEL_*` | للـ SMS | بيانات حساب سيرياتيل لإرسال الرموز |
| `SEED_PASSWORD_*` | خارج dev | كلمات سر حسابات الـ seed (مثال: `SEED_PASSWORD_TAHER_SUPER`) |
| `TRUST_PROXY_HEADERS` | لا | `1` إذا كان السيرفر خلف وكيل موثوق (nginx/cloudflare tunnel) |
| `JWT_ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` | لا | قيم افتراضية: `HS256` / `480` |

> ⚠️ كلمات سر حسابات الـ seed الافتراضية (`super123/admin123/staff123/gate123`) مقبولة **في بيئة التطوير فقط**. خارجها يرفض السكريبت العمل بدون `SEED_PASSWORD_<USERNAME>`.

---

## النشر

### الخيارات المتاحة

**1. Docker (يصلح على أي VPS أو منصة PaaS تدعم الحاويات)**

```bash
docker build -t wijhatak-backend .
docker run -p 8000:8000 --env-file .env wijhatak-backend
```

**2. PaaS (Render / Railway / Fly.io وغيرها)**

- الأمر عند الإقلاع: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- (ملف `Procfile` جاهز للأنظمة التي تقرأه)
- عند الإقلاع يُنشئ التطبيق الجداول تلقائياً (`create_all` idempotent) — مناسبة لقاعدة نظيفة.

### ملاحظة حول Cloudflare

- **الفرونت** (المبني بـ Vite) يعمل بشكل ممتاز على **Cloudflare Pages**.
- **الـ Backend (FastAPI + PostgreSQL) لا يعمل على Workers/Pages Functions السيرفرلس** — لأنه يحتاج اتصال PostgreSQL مستمراً ومكتبات غير متوافقة مع بيئة الـ serverless.
- المسار المدعوم: تشغيل الـ backend على **سيرفر / VPS / PaaS** خلف **Cloudflare Tunnel أو Proxy** — هكذا تحصل على مزايا كلاودفاير (HTTPS، حماية، Caching) عبر `cloudflared tunnel --url http://localhost:8000` أو إعداد DNS + ثقل.
- عندها اضبط `TRUST_PROXY_HEADERS=1` ليكتشف الـ rate limiter عناوين IP الحقيقية.

### بيئة الإنتاج

- `APP_ENV=production` يخفي `/docs` و `/redoc` ويقيّد CORS لـ `ALLOWED_ORIGINS`.
- `JWT_SECRET_KEY` يجب أن تكون سراً عشوائياً قوياً: `openssl rand -hex 32`
- عرّفي `SEED_PASSWORD_*` أو شغّلي seed محلياً قبل النشر.

---

## معمارية مختصرة

```
main.py                     ← FastAPI app + معالجات الأخطاء الموحدة + create_all عند الإقلاع
app/database.py             ← اتصال SQLAlchemy + get_db
app/security.py             ← bcrypt + JWT
app/dependencies.py         ← مصادقة + أدوار + rate limiting (IP و per-student)
app/sms_service.py          ← إرسال OTP عبر سيرياتيل
app/seed_data.py            ← زرع حسابات فريق العمل + طالب تجريبي
app/models/                 ← SQLAlchemy models (Account, Student, Checkin, Booking, OTP, PostSurvey)
app/routers/                ← الوحدات: registration, checkins, bookings, points, survey,
                              students, accounts, auth, dashboard, walkin
tests/                      ← اختبارات pytest (92+ — تغطي المنطق والأمان)
```

---

## الأمان المطبّق

- رموز طلاب **عشوائية** (R-XXXXXX) — لا تعداد ولا تزوير QR
- Rate limiting على كل النقاط العامة + حد لكل طالب على OTP
- OTP مخزون كهاش SHA-256 (لا يُخزن النص الصريح)
- `token_version` يُبطل التوكنات بعد تغيير كلمة السر
- قيمة enum غير صالحة في query → 422 موحد (بدل 500)
- كلمات سر seed مقيدة ببيئة التطوير

> ⚠️ ملاحظة تاريخ: إصدار سابق من `.env` (بسر `mysecretkey123`) كان متتبَّعاً في git ثم أُزيل. هذا السر **قديم وغير مستخدَم**، لكنه موجود في سجل الريبو — عند الحاجة يُنصح بمسحه نهائياً عبر `git filter-repo` وتدوير أي قيمة شاركت به.