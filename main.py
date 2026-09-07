"""
نقطة الدخول الرئيسية للتطبيق — FastAPI app + تسجيل الروترات + معالج الأخطاء الموحّد.
تشغيل محلي: uvicorn main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.routers.accounts import account_router
from app.routers.auth import auth_router
from app.routers.bookings import booking_router
from app.routers.checkins import checkin_router
#from app.routers.dashboard import dashboard_router
from app.routers.registration import registration_router
from app.routers.students import student_router
from app.routers.survey import survey_router
from app.routers.walkin import walkin_router

app = FastAPI(
    title="Wijhatak Al-Akademia API",
    description="Backend لمنصة وجهتك الأكاديمية — فعالية الاتحاد الطالبي",
    version="0.1.0",
)

# ⚠️ مؤقت للتطوير — بيسمح لأي origin يوصل للـ API (مشان تجربة الفرونت محلياً
# من vite:5173 وأمثاله بدون ما يرفض المتصفح الطلب). لازم يتقيّد بدومين
# الفرونت الحقيقي بس قبل أي نشر فعلي.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# تسجيل الروترات — كل روتر جديد بيتضاف هون بس
app.include_router(auth_router.router)
app.include_router(walkin_router.router)
app.include_router(checkin_router.router)
app.include_router(booking_router.router)
app.include_router(survey_router.router)
app.include_router(account_router.router)
app.include_router(student_router.router)
#app.include_router(dashboard_router.router)
app.include_router(registration_router.router)


@app.get("/health", tags=["health"])
def health_check():
    """endpoint بسيط للتأكد إنه السيرفر شغال — مش موثّق بالعقد، بس مفيد للتطوير."""
    return {"status": "ok"}