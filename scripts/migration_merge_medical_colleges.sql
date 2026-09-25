-- دمج لمرة وحدة: زيارة كليات الطب البشري والصيدلة تُنقَل إلى كلية الأسنان
-- (التي صارت تُعرف بالواجهة باسم «المجمع الطبي»).
--
-- شرط الدمج: يُنقل سجل (حجز أو شيك جولة/استشارة) مسجل بـ college=medicine
-- أو college=pharmacy إلى college=dentistry فقط إذا لم يكن للطالب أصلن أي زيارة
-- لطب الأسنان (لا حجز ولا شيك مسجل على كلية الأسنان). أما الطالب اللي فعنده
-- أصلن زيارة أسنان فلا يُضاف عليه أي زيارة إضافية (ما يتضاعف عدده).
--
-- هذا الترحيل يُطبَّق مرة واحدة على قاعدة البيانات القائمة (dev/prod)، فالحسابات
-- (موظفو ركن الطب البشري والصيدلة) حُذفت ولا يُسجَّل عليها أي زيارة جديدة بعدها.
-- التشغيل (من جذر المشروع، مع قاعدة هادفة):
--   psql "[REDACTED]" -f scripts/migration_merge_medical_colleges.sql
-- أو عبر أداته، أو بالنقر على run_sql_migration.py بعد تعيين
-- MIGRATION_FILE = "migration_merge_medical_colleges.sql".

BEGIN;

-- 1) الطلاب اللي عندهم أصلن زيارة طب أسنان (من أي مصدر: حجز أو شيك)
CREATE TEMP TABLE tmpl_students_with_dentistry ON COMMIT DROP AS
SELECT student_id
FROM (
    SELECT student_id FROM bookings WHERE college = 'dentistry'
    UNION
    SELECT student_id FROM checkins WHERE college = 'dentistry'
) AS dent_sources;

-- 2) نقل سجلات الطب البشري والصيدلة إلى طب الأسنان — فقط للطلاب اللي ما
--    عندهم أصلن زيارة أسنان (الشرط بالأسفل: student_id NOT IN).
--    الأحجز أولاً ثم الشيكات (تسلسل منطقي مستقل عن بعضه بالمصدرين).
UPDATE bookings
SET college = 'dentistry'
WHERE college IN ('medicine', 'pharmacy')
  AND student_id NOT IN (SELECT student_id FROM tmpl_students_with_dentistry);

UPDATE checkins
SET college = 'dentistry'
WHERE college IN ('medicine', 'pharmacy')
  AND student_id NOT IN (SELECT student_id FROM tmpl_students_with_dentistry);

-- 3) ملاحظة: الطلاب اللي عندهم زيارة أسنان أصلن، تبقى سجلاتهم الطبية/الصيدلية
--    كما هي (لا تُنقل) حتى لا يتضاعف عدد زياراتهم؛ وواجهة الزيارات لن تعرض
--    medicine/pharmacy كصفين مستقلين بعد هذا الترحيل.

COMMIT;