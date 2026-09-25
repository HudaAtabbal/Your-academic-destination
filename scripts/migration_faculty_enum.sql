BEGIN;

-- قائمة "الكلية المرتبطة" الجديدة (Faculty) — منفصلة عن college_enum اللي بخص
-- اختيارات الطلاب (students.initial_preferred_major / post_surveys.preferred_major).
-- تنطبق على أعمدة college في: accounts (حسابات الفريق)، bookings، checkins.
-- القيم الموجودة بسجلّات الحالية (مثل 'medicine') تُحتفظ عبر تحويل النص،
-- والأعمدة بتضل nullable. الـ indexes المعتمدة على العمود تتحدث تلقائياً.
CREATE TYPE faculty_enum AS ENUM (
    'medicine',
    'dentistry',
    'pharmacy',
    'health_sciences',
    'informatics',
    'civil_engineering',
    'architecture',
    'agriculture',
    'electrical_mechanical',
    'chemical_food',
    'economics',
    'tourism',
    'music',
    'arts',
    'education',
    'sciences',
    'applied',
    'law',
    'institute_agriculture',
    'institute_desert_affairs',
    'institute_engineering',
    'institute_health',
    'institute_dentistry',
    'institute_applied_industries',
    'institute_computer'
);

ALTER TABLE accounts ALTER COLUMN college TYPE faculty_enum USING (college::text)::faculty_enum;
ALTER TABLE bookings ALTER COLUMN college TYPE faculty_enum USING (college::text)::faculty_enum;
ALTER TABLE checkins ALTER COLUMN college TYPE faculty_enum USING (college::text)::faculty_enum;

COMMIT;