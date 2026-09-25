"""
كل أنواع الـ Enum المستخدمة بموديلات المشروع — بنفس أسماء enums بالسكيما بالحرف.
مجمّعين هون بملف واحد لأنهن مشتركين بين أكتر من موديل (مثلاً college_enum
مستخدم بـ Student, Checkin, Booking, PostSurvey, Account كلهن).
"""

import enum


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
    game = "game"
    union = "union"


class BookingType(str, enum.Enum):
    tour = "tour"
    consultation = "consultation"


class OpinionChange(str, enum.Enum):
    decided = "decided"                        # صار عندي قرار
    changed_completely = "changed_completely"   # تغيّر تماماً
    confirmed_choice = "confirmed_choice"       # تأكّد اللي كنت ناويه
    still_confused = "still_confused"           # لسا محتار


# قائمة الكليات الرسمية — الترتيب هنا هو ترتيب العرض المعتمد (id إنجليزي ثابت،
# والاسم العربي معروض بالواجهة). القيمة `not_chosen_yet` مميزة: تعني "لسّا ما قرّرت".
class College(str, enum.Enum):
    medicine = "medicine"  # الطب البشري
    pharmacy = "pharmacy"  # الصيدلة
    dentistry = "dentistry"  # طب الأسنان
    health_labs = "health_labs"  # علوم صحيّة مخابر
    health_nutrition = "health_nutrition"  # علوم صحيّة تغذية
    health_physiotherapy = "health_physiotherapy"  # علوم صحية علاج فيزيائي
    mech_power_eng = "mech_power_eng"  # هندسة قوى ميكانيكية
    control_computer_eng = "control_computer_eng"  # هندسة تحكم آلي وحواسيب
    energy_eng = "energy_eng"  # هندسة طاقة
    mechatronics = "mechatronics"  # ميكاترونك
    telecom_eng = "telecom_eng"  # هندسة اتصالات
    metallurgy_eng = "metallurgy_eng"  # هندسة المعادن
    design_production_eng = "design_production_eng"  # هندسة التصميم والإنتاج
    petroleum_eng = "petroleum_eng"  # هندسة بيتروليّة
    food_eng = "food_eng"  # هندسة غذائية
    chemical_eng = "chemical_eng"  # هندسة كيميائية
    textile_eng = "textile_eng"  # هندسة الغزل والنسيج
    civil = "civil"  # هندسة مدنيّة
    tourism = "tourism"  # سياحة
    architecture = "architecture"  # هندسة معماريّة
    music = "music"  # موسيقا
    physics = "physics"  # فيزياء
    mathematics = "mathematics"  # رياضيات
    statistics = "statistics"  # إحصاء
    biology = "biology"  # علم الحياة بيولوجيا
    geology = "geology"  # علم الحياة جيولوجيا
    chemistry = "chemistry"  # كيمياء
    economics = "economics"  # اقتصاد
    informatics = "informatics"  # هندسة معلوماتية
    applied_science = "applied_science"  # كلية تطبيقية
    arabic = "arabic"  # لغة عربية
    english = "english"  # لغة انكليزية
    french = "french"  # لغة فرنسية
    persian = "persian"  # لغة فارسية
    history = "history"  # تاريخ
    philosophy = "philosophy"  # فلسفة
    agriculture = "agriculture"  # هندسة زراعية
    law = "law"  # حقوق
    curricula = "curricula"  # مناهج وطرق تدريس
    psychology = "psychology"  # علم نفس
    kindergarten = "kindergarten"  # رياض أطفال
    psychological_counseling = "psychological_counseling"  # إرشاد نفسي
    class_teacher = "class_teacher"  # معلم صف
    sharia = "sharia"  # شريعة
    institute_agriculture = "institute_agriculture"  # معهد تقاني زراعي
    institute_desert_affairs = "institute_desert_affairs"  # معهد تقاني لشؤون البادية والتصحر
    institute_engineering = "institute_engineering"  # معهد تقاني هندسي
    institute_health = "institute_health"  # معهد تقاني صحي
    institute_dentistry = "institute_dentistry"  # معهد تقاني طب اسنان
    institute_applied_industries = "institute_applied_industries"  # معهد تقاني صناعات تطبيقية
    institute_computer = "institute_computer"  # معهد تقاني حاسوب
    not_chosen_yet = "not_chosen_yet"  # لسّا ما قرّرت


# قائمة "الكلية المرتبطة" لحسابات مسؤولي الكليات (Account.college) — قائمة
# منفصلة ومبسّطة عن College اللي بتخصّ اختيارات الطلاب. الباك يحفظ id الإنكليزي،
# والاسم العربي معروض بالمقابل بالواجهة. نفس فكرة "المعاهد" مدمجة بنفس القائمة.
class Faculty(str, enum.Enum):
    medicine = "medicine"  # الطب البشري
    dentistry = "dentistry"  # طب الأسنان
    pharmacy = "pharmacy"  # الصيدلة
    health_sciences = "health_sciences"  # كلية العلوم الصحية
    informatics = "informatics"  # كلية المعلوماتية
    civil_engineering = "civil_engineering"  # كلية الهندسة المدنية
    architecture = "architecture"  # كلية العمارة
    agriculture = "agriculture"  # كلية الهندسة الزراعية
    electrical_mechanical = "electrical_mechanical"  # كلية الهندسة الكهربائية والميكانيكية
    chemical_food = "chemical_food"  # كلية الهندسة الكيميائية والغذائية
    economics = "economics"  # كلية الاقتصاد
    tourism = "tourism"  # كلية السياحة
    music = "music"  # كلية الموسيقا
    arts = "arts"  # كلية الآداب والعلوم الإنسانية
    education = "education"  # كلية التربية
    sciences = "sciences"  # كلية العلوم
    applied = "applied"  # الكلية التطبيقية
    law = "law"  # كلية الحقوق
    institute_agriculture = "institute_agriculture"  # معهد تقاني زراعي
    institute_desert_affairs = "institute_desert_affairs"  # معهد تقاني لشؤون البادية والتصحر
    institute_engineering = "institute_engineering"  # معهد تقاني هندسي
    institute_health = "institute_health"  # معهد تقاني صحي
    institute_dentistry = "institute_dentistry"  # معهد تقاني طب أسنان
    institute_applied_industries = "institute_applied_industries"  # معهد تقاني صناعات تطبيقية
    institute_computer = "institute_computer"  # معهد تقاني حاسوب


# ⚠️ TODO: استبدال الـ placeholders بأسماء المحاضرات الفعلية قبل الإطلاق.
class Lecture(str, enum.Enum):
    opening = "opening"  # حفل الافتتاح
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

class UnionSection(str, enum.Enum):
    central = "central"           # الركن المركزي
    major_guide = "major_guide"   # دليل التخصص
    turkish_club = "turkish_club" # نادي التركي


class AccountRole(str, enum.Enum):
    super_admin = "super_admin"
    students_admin = "students_admin"
    college_staff = "college_staff"
    gate_scanner = "gate_scanner"
    game_corner_manager = "game_corner_manager"
    union = "union"


class CertificateType(str, enum.Enum):
    """نوع الشهادة الثانوية — حقل مكتشف من كود الفرونت الفعلي، مش موجود بالسكيما الأصلية."""

    scientific = "scientific"  # علمي
    literary = "literary"  # أدبي


class SmsJobStatus(str, enum.Enum):
    pending = "pending"    # انخلق وبناطر المُرسِل
    sending = "sending"    # مُسحوب من المُرسِل (بمرحلة الإرسال)
    sent = "sent"          # تأكّد وصوله للمُرسِل وسيرياتيل
    failed = "failed"      # استُنفدت المحاولات أو فشل دائم

