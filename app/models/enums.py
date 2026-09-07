"""
كل أنواع الـ Enum المستخدمة بموديلات المشروع — بنفس أسماء enums بالسكيما بالحرف.
مجمّعين هون بملف واحد لأنهن مشتركين بين أكتر من موديل (مثلاً college_enum
مستخدم بـ Student, Checkin, Booking, PostSurvey, Account كلهن).
"""

import enum


class ContactPlatform(str, enum.Enum):
    whatsapp = "whatsapp"
    telegram = "telegram"


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"


class RegistrationType(str, enum.Enum):
    registered = "registered"
    walk_in = "walk_in"


class StudentStatus(str, enum.Enum):
    pending = "pending"
    complete = "complete"


class ActivityType(str, enum.Enum):
    campus_entry = "campus_entry"
    lecture = "lecture"
    tour = "tour"
    consultation = "consultation"


class BookingType(str, enum.Enum):
    tour = "tour"
    consultation = "consultation"


class OpinionChange(str, enum.Enum):
    decided = "decided"                        # صار عندي قرار
    changed_completely = "changed_completely"   # تغيّر تماماً
    confirmed_choice = "confirmed_choice"       # تأكّد اللي كنت ناويه
    still_confused = "still_confused"           # لسا محتار


# ⚠️ TODO: استبدال الـ placeholders بأسماء الـ 42 كلية الفعلية قبل الإطلاق.
class College(str, enum.Enum):
    college_placeholder_1 = "college_placeholder_1"
    college_placeholder_2 = "college_placeholder_2"
    not_chosen_yet = "not_chosen_yet"  # قيمة خاصة بالاستبيانات فقط


# ⚠️ TODO: استبدال الـ placeholders بأسماء المحاضرات الفعلية قبل الإطلاق.
class Lecture(str, enum.Enum):
    lecture_placeholder_1 = "lecture_placeholder_1"
    lecture_placeholder_2 = "lecture_placeholder_2"


class AccountRole(str, enum.Enum):
    super_admin = "super_admin"
    students_admin = "students_admin"
    college_staff = "college_staff"
    gate_scanner = "gate_scanner"


class CertificateType(str, enum.Enum):
    """نوع الشهادة الثانوية — حقل مكتشف من كود الفرونت الفعلي، مش موجود بالسكيما الأصلية."""

    scientific = "scientific"  # علمي
    literary = "literary"  # أدبي


class InterestCluster(str, enum.Enum):
    """
    التجمّع (المجال) يلي بيميل إله الطالب قبل الفعالية — مطابق تماماً لقيم الـ 8
    "chips" الفعلية بشاشة RegisterStep2 بالفرونت (مش الـ 42 كلية المحددة).
    منفصل تماماً عن college_enum لأنه ده مستوى تجمّع/تخمين مبدئي، مش اختيار كلية
    محددة — الكليات المحددة (college_enum) بتُستخدم بس بـ bookings/checkins/accounts
    يلي فعلاً محتاجة تحديد كلية بعينها.
    """

    medicine = "medicine"  # الطب البشري
    informatics = "informatics"  # المعلوماتية
    architecture = "architecture"  # الهندسة المعمارية
    law = "law"  # الحقوق
    pharmacy = "pharmacy"  # الصيدلة
    agriculture = "agriculture"  # الهندسة الزراعية
    education = "education"  # التربية
    civil = "civil"  # الهندسة المدنية
    not_chosen_yet = "not_chosen_yet"  # لسّا ما قرّرت


class CertificateType(str, enum.Enum):
    """نوع الشهادة الثانوية — حقل مكتشف من كود الفرونت الفعلي، مش موجود بالسكيما الأصلية."""

    scientific = "scientific"  # علمي
    literary = "literary"  # أدبي


class InterestCluster(str, enum.Enum):
    """
    التجمّع (المجال) يلي بيميل إله الطالب قبل الفعالية — مطابق تماماً لقيم الـ 8
    "chips" الفعلية بشاشة RegisterStep2 بالفرونت (مش الـ 42 كلية المحددة).
    منفصل تماماً عن college_enum لأنه ده مستوى تجمّع/تخمين مبدئي، مش اختيار كلية
    محددة — الكليات المحددة (college_enum) بتُستخدم بس بـ bookings/checkins/accounts
    يلي فعلاً محتاجة تحديد كلية بعينها.
    """

    medicine = "medicine"  # الطب البشري
    informatics = "informatics"  # المعلوماتية
    architecture = "architecture"  # الهندسة المعمارية
    law = "law"  # الحقوق
    pharmacy = "pharmacy"  # الصيدلة
    agriculture = "agriculture"  # الهندسة الزراعية
    education = "education"  # التربية
    civil = "civil"  # الهندسة المدنية
    not_chosen_yet = "not_chosen_yet"  # لسّا ما قرّرت