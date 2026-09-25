-- أقسام ركن الاتحاد (Union Sections): عمود union_section + فهرس فريد لكل قسم
-- ---------------------------------------------------------------------------
-- يحوّل قاعدة الاتحاد من "مرة وحدة بالكامل" إلى "مرة وحدة لكل قسم":
-- الركن المركزي / دليل التخصص / نادي التركي — 3 سجلات checkins منفصلة كحد أقصى.
--
-- يُطبَّق يدوياً على قواعد التطوير والإنتاج (حيث انطبّق migration_union.sql سابقاً).
-- ملاحظة: فهرس unique_union_checkin القديم (عمود واحد) يُحذف ويُعاد إنشاؤه بنفس
-- الاسم مع عمودين (student_id, union_section) — مطلوب حذفه أولاً لأن PostgreSQL
-- لا يسمح بإعادة تعريف فهرس بنفس الاسم بـ IF NOT EXISTS.
--
-- صيحة للقواعد الجديدة (create_all): الموديل يبني العمود والفهرس تلقائياً.
-- ---------------------------------------------------------------------------

BEGIN;

CREATE TYPE union_section_enum AS ENUM ('central', 'major_guide', 'turkish_club');

ALTER TABLE checkins ADD COLUMN union_section union_section_enum;

DROP INDEX IF EXISTS unique_union_checkin;

CREATE UNIQUE INDEX unique_union_checkin
    ON checkins (student_id, union_section)
    WHERE activity_type = 'union';

COMMIT;