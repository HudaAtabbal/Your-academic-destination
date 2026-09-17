// قائمة "الكلية المرتبطة" لحسابات الفريق — نفس قيم (id) enum Faculty
// بالباك وبنفس ترتيبه المعتمد (قائمة منفصلة عن اختيارات الطلاب).
export const FACULTY_OPTIONS = [
  { value: 'medicine', label: 'كلية الطب البشري' },
  { value: 'dentistry', label: 'كلية طب الأسنان' },
  { value: 'pharmacy', label: 'كلية الصيدلة' },
  { value: 'health_sciences', label: 'كلية العلوم الصحية' },
  { value: 'informatics', label: 'كلية الهندسة المعلوماتية' },
  { value: 'civil_engineering', label: 'كلية الهندسة المدنية' },
  { value: 'architecture', label: 'كلية الهندسة المعمارية' },
  { value: 'agriculture', label: 'كلية الهندسة الزراعية' },
  { value: 'electrical_mechanical', label: 'كلية الهندسة الكهربائية والميكانيكية' },
  { value: 'chemical_food', label: 'كلية الهندسة الكيميائية والغذائية' },
  { value: 'economics', label: 'كلية الاقتصاد' },
  { value: 'tourism', label: 'كلية السياحة' },
  { value: 'music', label: 'كلية الموسيقى' },
  { value: 'arts', label: 'كلية الآداب والعلوم الإنسانية' },
  { value: 'education', label: 'كلية التربية' },
  { value: 'sciences', label: 'كلية العلوم' },
  { value: 'applied', label: 'الكلية التطبيقية' },
  { value: 'law', label: 'كلية الحقوق' },
  { value: 'institute_agriculture', label: 'معهد تقاني زراعي' },
  { value: 'institute_desert_affairs', label: 'معهد تقاني لشؤون البادية والتصحر' },
  { value: 'institute_engineering', label: 'معهد تقاني هندسي' },
  { value: 'institute_health', label: 'معهد تقاني صحي' },
  { value: 'institute_dentistry', label: 'معهد تقاني طب اسنان' },
  { value: 'institute_applied_industries', label: 'معهد تقاني صناعات تطبيقية' },
  { value: 'institute_computer', label: 'معهد تقاني حاسوب' },
];

// خريطة id → الاسم العربي، للعرض (مثل لوحة المدير)
export const FACULTY_LABELS = FACULTY_OPTIONS.reduce((acc, item) => {
  acc[item.value] = item.label;
  return acc;
}, {});
