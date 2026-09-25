"""
موديل PageVisit — جدول زيارات الصفحات مع مدّة البقاء المقاسة على السيرفر.

صفحة الدليل الأكاديمي (`/academic-guide`) صفحة iframe مدمجة، فبدنا نعرف:
كم مرة انفتحت، كم شخص (متصفح فريد) فتحها، وكم دقيقة بقي فيها.

المدّة يقيسها السيرفر بالكامل:
- POST /students/page-visit/start ينشئ الصف ب entered_at من time_utils.now_naive()
  ويرجّع رقم الصف (id) للمتصفح.
- POST /students/page-visit/end يستقبل رقم الصف ويحسب
  duration_seconds من now_naive() ناقص entered_at.

⚠️ لا يوجد أي حقل يقبل مدّة يرسلها المتصفح — مستحيل يتلاعب بالأرقام.
الزيارات اللي ما وصلت إشارة النهاية (إغلاق مفاجئ) بتضل مدّتها فارغة،
وتُستبعد من المتوسط مع إحصائها ضمن عدد الزيارات.

visitor_id معرّف ثابت للمتصفح بيتولّد مرة وحدة على جهاز الزائر، مش الـ IP
— لأن كل طلبة الجامعة بيتصلوا على نفس شبكة الواي-فاي أو مشغّل الشبكة،
فالـ IP ما بيفيدنا بعدد الأشخاص الحقيقي.

`id` هو نفسه مُعرّف الربط بين start و end (مش سر ولا بيانات حسّاسة): هو
مفتاح أساسي عادي، و end ما بيقبل إلا صف مدّته لسا فارغة.
"""

from sqlalchemy import BigInteger, Column, DateTime, Float, Index, String
from sqlalchemy.sql import func

from app.database import Base

# الحد الأدنى للزيارة المحسوبة (بالثواني) — أقل من هيك يعتبر ارتداد سريع
# (فتح الصفحة وطلعها فوراً) وما بندخلو بالمتوسط.
MIN_COUNTED_DURATION_SECONDS = 3

# طول أعمدة النصوص.
NAME_LEN = 64
CODE_LEN = 32


class PageVisit(Base):
    __tablename__ = "page_visits"

    # المفتاح الأساسي هو نفسه مُعرّف الربط بين start و end.
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # معرّف الصفحة — حالياً academic-guide فقط، قابل للتوسّع لاحقاً.
    page = Column(String(NAME_LEN), nullable=False)

    # معرّف المتصفح الثابت (مش الـ IP) لِعدّ الأشخاص المختلفين.
    visitor_id = Column(String(NAME_LEN), nullable=False)

    # رمز الطالب (R-XXXXXX) إذا كان مسجّل دخول — اختياري: كتير من الزوار
    # بيدخلوا الدليل قبل ما يسجّلوا أو بعد ما يسجّلوا بلا جلسة مفتوحة.
    student_code = Column(String(CODE_LEN), nullable=True)

    entered_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # مدّة البقاء بالثواني — فارغة إذا ما وصلت إشارة النهاية بعد.
    duration_seconds = Column(Float, nullable=True)

    __table_args__ = (
        # الفلاتر الأساسية: صفحة + نطاق اليوم.
        Index("idx_page_visits_page_entered_at", "page", "entered_at"),
        # إحصاء الأشخاص المختلفين لكل صفحة.
        Index("idx_page_visits_page_visitor", "page", "visitor_id"),
    )
