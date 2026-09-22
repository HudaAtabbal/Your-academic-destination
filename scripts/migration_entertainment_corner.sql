-- دور ركن الترفيه (Entertainment Corner) + نشاط "ركن الترفيه"
-- ---------------------------------------------------------------------------
-- حقق هاد الملف على قاعدة البيانات الحية (التطوير والإنتاج) منجز خارج
-- أي transaction — ALTER TYPE ... ADD VALUE لازم يشتغل standalone على
-- PostgreSQL < 12، وحتى على الإصدارات الأحدث من الأضمن تشغيلو لحالو.
--
-- الاستخدام (من جذر المشروع):
--     python scripts/run_sql_migration.py   ← بعد ضبط ملفات الـ SQL المطلوبة
-- أو عبر psql مباشرة على القاعدة المستهدفة.
-- ---------------------------------------------------------------------------

-- 1) دور الحساب الجديد: "مسؤول ركن الترفيه"
ALTER TYPE account_role_enum ADD VALUE IF NOT EXISTS 'game_corner_manager';

-- 2) نوع النشاط الجديد: زيارة ركن الترفيه (بدون نقاط)
ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'game';

-- 3) كتسجيل فريد: كل طالب مرة وحدة بطول الفعالية لركن الترفيه
--    (مثل الاستشارة الفردية) — مستنسخ من unique_consultation_checkin
CREATE UNIQUE INDEX IF NOT EXISTS unique_game_checkin
    ON checkins (student_id)
    WHERE activity_type = 'game';