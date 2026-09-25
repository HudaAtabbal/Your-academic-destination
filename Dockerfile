# صورة تشغيل جاهزة للـ backend — تصلح على أي VPS أو منصة PaaS تدعم Docker
# (وراء cloudflare tunnel/proxy أو مباشرة). بيئة إنتاجية: تثبيت نظيف + مستخدم غير root.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# أدوات أنظمة قليلة الحجم — psycopg2-binary جاهز (لا حاجة لمترجم C)
WORKDIR /app

# تثبيت التبعيات أولاً (يستفيد من caching في كل build)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# الكود بعد التبعيات
COPY . .

# تشغيل كمستخدم غير root — ممارسة أمان قياسية
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# $PORT يستخدمها منصات PaaS مثل Render — لتناسب خارج nich
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]