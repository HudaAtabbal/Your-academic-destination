BEGIN;

-- إضافة محاضرة الافتتاح (opening) إلى قيم lecture_enum —
-- تُنفذ يدوياً على قاعدة البيانات (Neon) قبل كشف الـ gate scanner الجديد.
-- ALTER TYPE لا يُنفذ داخل create_all؛ لازم migration يدوي.
ALTER TYPE lecture_enum ADD VALUE 'opening';

COMMIT;