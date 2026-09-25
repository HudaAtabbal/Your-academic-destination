-- إزالة وسيلة التواصل (contact_platform) — الإرسال دائماً عبر SMS
-- يُطبَّق مرة واحدة على القواعد القائمة (dev/test). القواعد الجديدة تُنشأ
-- مباشرةً من الموديلات عبر create_all فلا تحتاج هذا الملف.
--
-- تشغيل (من جذر المشروع، مع تفعيل الـ venv):
--   python scripts/run_sql_migration.py
-- أو عبر psql مع تحديد القاعدة الهدف.

BEGIN;

-- 1) حذف الفهرس القديم الذي يعتمد على العمود قبل حذف العمود نفسه
DROP INDEX IF EXISTS unique_contact_per_registration;

-- 2) حذف العمود
ALTER TABLE students DROP COLUMN IF EXISTS contact_platform;

-- 3) حذف نوع الـ enum بعد زوال مستخدمه الوحيد
DROP TYPE IF EXISTS contact_platform_enum;

-- 4) إعادة بناء الفهرس الفريد على رقم التواصل وحده (للمسجّلين إلكترونياً فقط)
CREATE UNIQUE INDEX unique_contact_per_registration
  ON students (contact_id)
  WHERE registration_type = 'registered';

COMMIT;