"""
التسميات العربية للكليات — مصدر واحد مشترك لكل الرسائل ولوحة المدير.

النصوص مطابقة لـ src/api/faculties.js بالفرونت (FACULTY_OPTIONS / FACULTY_LABELS)
حرفياً، ولازم تنحاذى معه: نفس الـ id ونفس الاسم العربي. لوحة المدير بتعتمد
نسخة موازية (COLLEGE_VISIT_LABELS) بنفس النصوص.

قيمة enum Faculty رمز تقني (medicine, dentistry...) — الرسائل المعروضة للمستخدم
لازم تعرض الاسم الرسمي العربي مش الرمز.
"""

from app.models.enums import Faculty

FACULTY_LABELS: dict[Faculty, str] = {
    Faculty.medicine: "كلية الطب البشري",
    Faculty.dentistry: "المجمع الطبي",
    Faculty.pharmacy: "كلية الصيدلة",
    Faculty.health_sciences: "كلية العلوم الصحية",
    Faculty.informatics: "كلية الهندسة المعلوماتية",
    Faculty.civil_engineering: "كلية الهندسة المدنية",
    Faculty.architecture: "كلية الهندسة المعمارية",
    Faculty.agriculture: "كلية الهندسة الزراعية",
    Faculty.electrical_mechanical: "كلية الهندسة الكهربائية والميكانيكية",
    Faculty.chemical_food: "كلية الهندسة الكيميائية والغذائية",
    Faculty.economics: "كلية الاقتصاد",
    Faculty.tourism: "كلية السياحة",
    Faculty.music: "كلية الموسيقى",
    Faculty.arts: "كلية الآداب والعلوم الإنسانية",
    Faculty.education: "كلية التربية",
    Faculty.sciences: "كلية العلوم",
    Faculty.applied: "الكلية التطبيقية",
    Faculty.law: "كلية الحقوق",
    Faculty.institute_agriculture: "معهد تقاني زراعي",
    Faculty.institute_desert_affairs: "معهد تقاني لشؤون البادية والتصحر",
    Faculty.institute_engineering: "معهد تقاني هندسي",
    Faculty.institute_health: "معهد تقاني صحي",
    Faculty.institute_dentistry: "معهد تقاني طب اسنان",
    Faculty.institute_applied_industries: "معهد تقاني صناعات تطبيقية",
    Faculty.institute_computer: "معهد تقاني حاسوب",
}


def faculty_label(faculty: Faculty | None) -> str:
    """
    الاسم العربي للكلية — واجهة عامة يعيد استخدامها checkins/bookings/dashboard.
    كلية غير معروفة بترجع الرمز نفسه (مش crash) حتى ما تنكسر رسالة الخطأ.
    """
    if faculty is None:
        return ""
    return FACULTY_LABELS.get(faculty, faculty.value)
