"""
نقطة الدخول الرئيسية للتطبيق — FastAPI app + تسجيل الروترات + معالج الأخطاء الموحّد.
تشغيل محلي: uvicorn main:app --reload
"""

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.routers.accounts import account_router
from app.routers.auth import auth_router
from app.routers.bookings import booking_router
from app.routers.checkins import checkin_router
from app.routers.dashboard import dashboard_router
from app.routers.points import point_router
from app.routers.registration import registration_router
from app.routers.students import student_router
from app.routers.survey import survey_router
from app.routers.walkin import walkin_router

_APP_ENV = os.getenv("APP_ENV", "development")
_IS_PRODUCTION = _APP_ENV == "production"

app = FastAPI(
    title="Wijhatak Al-Akademia API",
    description="Backend لمنصة وجهتك الأكاديمية — فعالية الاتحاد الطالبي",
    version="0.1.0",
    # توثيق الـ API (Swagger) مكشوف بالتطوير بس — بعيداً عن الإنتاج
    docs_url=None if _IS_PRODUCTION else "/docs",
    redoc_url=None if _IS_PRODUCTION else "/redoc",
)

# CORS: بالتطوير أي origin مسموح (تجربة فرونت محلية من vite)، بالإنتاج
# دومين الفرونت الحقيقي محدد بالبيئة ALLOWED_ORIGINS (مفصول بفواصل)
if _IS_PRODUCTION:
    _allowed = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
else:
    _allowed = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    معالج موحّد لكل AppError — بيحوّلها لنفس شكل الخطأ الموثّق بقسم 12
    بملف wijhatak_api_contract.md، بغض النظر عن أي روتر رماها.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(FastAPIHTTPException)
def http_exception_handler(request: Request, exc: FastAPIHTTPException) -> JSONResponse:
    """
    معالج للأخطاء يلي FastAPI نفسها بترميها قبل ما توصل لأي كود منا
    (مثلاً HTTPBearer لما الهيدر Authorization مفقود بالكامل) — بنوحّد شكلها
    كمان مع باقي أخطاء المشروع بدل رسالة FastAPI الافتراضية.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "invalid_credentials" if exc.status_code == 401 else "http_error",
            "message": "لازم تسجّلي دخول أولاً" if exc.status_code == 401 else str(exc.detail),
            "details": {},
        },
    )


# ترجمة تقريبية لأسماء الحقول الشائعة — بس لتحسين وضوح رسالة الخطأ، مش شرط
# تغطي كل حقل بالمشروع (لو حقل مش موجود هون، بيظهر اسمه الإنجليزي وخلص)
_FIELD_NAMES_AR = {
    "full_name": "الاسم الثلاثي",
    "birth_date": "تاريخ الميلاد",
    "certificate_year": "سنة الشهادة",
    "certificate_type": "نوع الشهادة",
    "average_score": "المعدل",
    "initial_preferred_major": "التخصص المفضل",
    "contact_platform": "وسيلة التواصل",
    "contact_id": "رقم التواصل",
    "unique_code": "الرمز الفريد",
    "username": "اسم المستخدم",
    "password": "كلمة السر",
    "role": "الدور",
    "college": "الكلية",
    "otp": "رمز التحقق",
}


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    معالج لأخطاء الفاليديشن التلقائية من FastAPI/Pydantic (422) — لولا هاد
    المعالج، هاي الأخطاء كانت بترجع بشكل مختلف تماماً {"detail": [...]}
    بدل شكلنا الموحّد، فالفرونت كان بيعرض رسالة عامة "صار خطأ غير متوقع"
    بدل الرسالة الحقيقية المفيدة (مثلاً "المعدل لازم يكون ≤100").
    """
    errors = exc.errors()
    first = errors[0] if errors else {}
    # loc بيكون مثلاً ["body", "average_score"] — بنشيل "body" ومنعرّب الباقي
    field_path = [str(part) for part in first.get("loc", []) if part != "body"]
    field = ".".join(field_path) if field_path else ""
    field_ar = _FIELD_NAMES_AR.get(field, field)

    message = f"خطأ بحقل '{field_ar}': {first.get('msg', 'قيمة غير صالحة')}" if field else "البيانات المُرسَلة غير صالحة"

    return JSONResponse(
        status_code=422,
        content={
            "error_code": "validation_error",
            "message": message,
            "details": {"errors": errors},
        },
    )


# تسجيل الروترات — كل روتر جديد بيتضاف هون بس
app.include_router(auth_router.router)
app.include_router(walkin_router.router)
app.include_router(checkin_router.router)
app.include_router(booking_router.router)
app.include_router(survey_router.router)
app.include_router(account_router.router)
app.include_router(student_router.router)
app.include_router(dashboard_router.router)
app.include_router(registration_router.router)
app.include_router(point_router.router)


@app.get("/health", tags=["health"])
def health_check():
    """endpoint بسيط للتأكد إنه السيرفر شغال — مش موثّق بالعقد، بس مفيد للتطوير."""
    return {"status": "ok"}