-- جولة الكلية: من "مرة وحدة لكل كلية بطول الفعالية" إلى "مرة وحدة لكل كلية باليوم"
-- ---------------------------------------------------------------------------
-- فهرسان بيتغيّروا مع بعض: فهرس الحجز (bookings) وفهرس المسحة (checkins). القديم
-- في كل واحد منهم كان (student_id, college) — فبنفس الكلية مرتين بأي يوم من أيام
-- الفعالية. الجديد بيضيف CAST(... AS DATE) كعمود ثالث، فصار المسح/الحجز مسموح
-- مرة وحدة لكل كلية ولكل يوم — بنفس نمط unique_campus_entry_checkin و
-- unique_lecture_checkin و unique_union_checkin.
--
-- القيد الجديد أوسع من القديم (أضيق ← أوسع)، فكل السجلات الموجودة بتلتزم فيه
-- بلا استثناء: ما في أي تعديل على البيانات ولا إعادة زرع ولا حذف.
--
-- الاستشارة ما بتتغير: unique_consultation_booking و unique_consultation_checkin
--ضلوا "مرة وحدة بالكامل" (بدون عمود تاريخ). ونفس الشي ركن الترفيه.
--
-- الفهارس القديمة تُحذف أولاً لأن PostgreSQL ما بيسمح بإعادة تعريف فهرس بنفس
-- الاسم بـ IF NOT EXISTS.
--
-- يُطبَّق على قواعد التطوير والإنتاج (حيث انطبّقت الترحيلات السابقة). ملاحظة:
-- صيغة القواعد الجديدة (create_all): الموديل يبني الفهارس بأعمدتها الثلاثة تلقائياً.
--
-- الاستخدام (من جذر المشروع):
--     python scripts/run_sql_migration.py   ← بعد ضبط ملف الـ SQL المطلوب
-- أو عبر psql مباشرة على القاعدة المستهدفة.
-- ---------------------------------------------------------------------------

BEGIN;

DROP INDEX IF EXISTS unique_tour_booking;

CREATE UNIQUE INDEX unique_tour_booking
    ON bookings (student_id, college, CAST(booked_at AS DATE))
    WHERE booking_type = 'tour';

DROP INDEX IF EXISTS unique_tour_checkin;

CREATE UNIQUE INDEX unique_tour_checkin
    ON checkins (student_id, college, CAST(checked_in_at AS DATE))
    WHERE activity_type = 'tour';

COMMIT;
