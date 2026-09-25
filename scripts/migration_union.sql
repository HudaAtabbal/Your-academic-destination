-- دور الاتحاد (Union) + نشاط "الاتحاد"
-- ---------------------------------------------------------------------------
-- حقق هاد الملف على قاعدة البيانات الحية (التطوير والإنتاج) منجز خارج
-- أي transaction — ALTER TYPE ... ADD VALUE لازم يشتغل standalone على
-- PostgreSQL < 12، وحتى على الإصدارات الأحدث من الأضمن تشغيلو لحالو.
--
-- الاستخدام (من جذر المشروع):
--     python scripts/run_sql_migration.py   ← بعد ضبط ملفات الـ SQL المطلوبة
-- أو عبر psql مباشرة على القاعدة المستهدفة.
-- ---------------------------------------------------------------------------

-- 1) دور الحساب الجديد: "مسؤول الاتحاد"
ALTER TYPE account_role_enum ADD VALUE IF NOT EXISTS 'union';

-- 2) نوع النشاط الجديد: زيارة ركن الاتحاد (بدون نقاط)
ALTER TYPE activity_type_enum ADD VALUE IF NOT EXISTS 'union';

-- 3) كتسجيل فريد: كل طالب مرة وحدة بطول الفعالية لركن الاتحاد
--    (مثل الاستشارة الفردية و ركن الترفيه) — مستنسخ من unique_game_checkin
CREATE UNIQUE INDEX IF NOT EXISTS unique_union_checkin
    ON checkins (student_id)
    WHERE activity_type = 'union';