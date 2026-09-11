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
    medicine = "medicine"  # طب بشري
    dentistry = "dentistry"  # طب أسنان
    pharmacy = "pharmacy"  # صيدلة
    health_sciences = "health_sciences"  # علوم صحية
    informatics = "informatics"  # هندسة معلوماتية
    civil = "civil"  # هندسة مدنية
    architecture = "architecture"  # هندسة معمارية
    agriculture = "agriculture"  # هندسة زراعة
    electrical_mechanical_eng = "electrical_mechanical_eng"  # هندسة كهربائية وميكانيكية
    chemical_food_eng = "chemical_food_eng"  # هندسة كيميائية وغذائية
    economics = "economics"  # اقتصاد
    tourism = "tourism"  # سياحة
    music = "music"  # موسيقا
    literature = "literature"  # اداب
    education = "education"  # تربية
    science = "science"  # علوم
    applied_science = "applied_science"  # تطبيقية
    law = "law"  # حقوق
    institute_agriculture = "institute_agriculture"  # معهد تقاني زراعي
    institute_desert_affairs = "institute_desert_affairs"  # معهد تقاني لشؤون البادية والتصحر
    institute_engineering = "institute_engineering"  # معهد تقاني هندسي
    institute_health = "institute_health"  # معهد تقاني صحي
    institute_dentistry = "institute_dentistry"  # معهد تقاني طب اسنان
    institute_applied_industries = "institute_applied_industries"  # معهد تقاني صناعات تطبيقية
    institute_computer = "institute_computer"  # معهد تقاني حاسوب
    not_chosen_yet = "not_chosen_yet"  # لسّا ما قرّرت


# ⚠️ TODO: استبدال الـ placeholders بأسماء المحاضرات الفعلية قبل الإطلاق.
class Lecture(str, enum.Enum):
    lecture_1 = "lecture_1"
    lecture_2 = "lecture_2"
    lecture_3 = "lecture_3"
    lecture_4 = "lecture_4"
    lecture_5 = "lecture_5"
    lecture_6 = "lecture_6"
    lecture_7 = "lecture_7"
    lecture_8 = "lecture_8"
    lecture_9 = "lecture_9"
    lecture_10 = "lecture_10"
    lecture_11 = "lecture_11"
    lecture_12 = "lecture_12"
    lecture_13 = "lecture_13"
    lecture_14 = "lecture_14"
    lecture_15 = "lecture_15"
    lecture_16 = "lecture_16"

class AccountRole(str, enum.Enum):
    super_admin = "super_admin"
    students_admin = "students_admin"
    college_staff = "college_staff"
    gate_scanner = "gate_scanner"


class CertificateType(str, enum.Enum):
    """نوع الشهادة الثانوية — حقل مكتشف من كود الفرونت الفعلي، مش موجود بالسكيما الأصلية."""

    scientific = "scientific"  # علمي
    literary = "literary"  # أدبي

