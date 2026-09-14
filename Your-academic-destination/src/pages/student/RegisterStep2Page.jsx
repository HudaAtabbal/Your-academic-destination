import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import StepProgress from '../../components/StepProgress';
import { updateRegistrationData, getRegistrationData } from '../../api/RegistrationStorage';
import '../../style/RegisterStep2Page.css';

// --- Sub-Component: قائمة تخصصات قابلة للبحث (اختيار متعدد) ---
const MajorSearchList = ({
  categories,
  searchTerm,
  onSearchChange,
  selectedCategories,
  onToggleCategory,
}) => {
  const query = searchTerm.trim();
  const filtered = categories.filter((cat) => !query || cat.name.includes(query));

  return (
    <div className="interests-section">
      <input
        type="text"
        className="custom-input major-search-input"
        placeholder="دوّري عن تخصصك..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
      />

      <div className="majors-list-box">
        {filtered.length > 0 ? (
          filtered.map((cat) => (
            <button
              key={cat.id}
              type="button"
              className={`major-list-item ${
                selectedCategories.includes(cat.id) ? 'selected' : ''
              }`}
              onClick={() => onToggleCategory(cat.id)}
            >
              {cat.name}
            </button>
          ))
        ) : (
          <p className="major-no-results">ما لقينا تخصص مطابق</p>
        )}
      </div>
    </div>
  );
};

// --- Main Page Component ---
const RegisterStep2Page = () => {
  const navigate = useNavigate();

  // بنحمّل الاختيار المحفوظ من قبل (لو الطالب رجع لهالخطوة بعد ريفريش أو من خطوة تانية)
  const saved = getRegistrationData();
  const savedMajors = Array.isArray(saved.initialPreferredMajor) ? saved.initialPreferredMajor : [];
  const savedIsUndecided = savedMajors.length === 1 && savedMajors[0] === 'not_chosen_yet';

  const [selectedCategories, setSelectedCategories] = useState(
    savedIsUndecided ? [] : savedMajors
  );
  const [isUndecided, setIsUndecided] = useState(savedIsUndecided);
  const [searchTerm, setSearchTerm] = useState('');

  // القيم (id) هون مطابقة بالحرف لـ enum College بالباك — نفس الترتيب المعتمد.
  const categories = [
    { id: 'medicine', name: 'الطب البشري' },
    { id: 'pharmacy', name: 'الصيدلة' },
    { id: 'dentistry', name: 'طب الأسنان' },
    { id: 'health_labs', name: 'علوم صحيّة مخابر' },
    { id: 'health_nutrition', name: 'علوم صحيّة تغذية' },
    { id: 'health_physiotherapy', name: 'علوم صحية علاج فيزيائي' },
    { id: 'mech_power_eng', name: 'هندسة قوى ميكانيكية' },
    { id: 'control_computer_eng', name: 'هندسة تحكم آلي وحواسيب' },
    { id: 'energy_eng', name: 'هندسة طاقة' },
    { id: 'mechatronics', name: 'ميكاترونك' },
    { id: 'telecom_eng', name: 'هندسة اتصالات' },
    { id: 'metallurgy_eng', name: 'هندسة المعادن' },
    { id: 'design_production_eng', name: 'هندسة التصميم والإنتاج' },
    { id: 'petroleum_eng', name: 'هندسة بيتروليّة' },
    { id: 'food_eng', name: 'هندسة غذائية' },
    { id: 'chemical_eng', name: 'هندسة كيميائية' },
    { id: 'textile_eng', name: 'هندسة الغزل والنسيج' },
    { id: 'civil', name: 'هندسة مدنيّة' },
    { id: 'tourism', name: 'سياحة' },
    { id: 'architecture', name: 'هندسة معماريّة' },
    { id: 'music', name: 'موسيقا' },
    { id: 'physics', name: 'فيزياء' },
    { id: 'mathematics', name: 'رياضيات' },
    { id: 'statistics', name: 'إحصاء' },
    { id: 'biology', name: 'علم الحياة بيولوجيا' },
    { id: 'geology', name: 'علم الحياة جيولوجيا' },
    { id: 'chemistry', name: 'كيمياء' },
    { id: 'economics', name: 'اقتصاد' },
    { id: 'informatics', name: 'هندسة معلوماتية' },
    { id: 'applied_science', name: 'كلية تطبيقية' },
    { id: 'arabic', name: 'لغة عربية' },
    { id: 'english', name: 'لغة انكليزية' },
    { id: 'french', name: 'لغة فرنسية' },
    { id: 'persian', name: 'لغة فارسية' },
    { id: 'history', name: 'تاريخ' },
    { id: 'philosophy', name: 'فلسفة' },
    { id: 'agriculture', name: 'هندسة زراعية' },
    { id: 'law', name: 'حقوق' },
    { id: 'curricula', name: 'مناهج وطرق تدريس' },
    { id: 'psychology', name: 'علم نفس' },
    { id: 'kindergarten', name: 'رياض أطفال' },
    { id: 'psychological_counseling', name: 'إرشاد نفسي' },
    { id: 'class_teacher', name: 'معلم صف' },
    { id: 'sharia', name: 'شريعة' },
    { id: 'institute_agriculture', name: 'معهد تقاني زراعي' },
    { id: 'institute_desert_affairs', name: 'معهد تقاني لشؤون البادية والتصحر' },
    { id: 'institute_engineering', name: 'معهد تقاني هندسي' },
    { id: 'institute_health', name: 'معهد تقاني صحي' },
    { id: 'institute_dentistry', name: 'معهد تقاني طب اسنان' },
    { id: 'institute_applied_industries', name: 'معهد تقاني صناعات تطبيقية' },
    { id: 'institute_computer', name: 'معهد تقاني حاسوب' },
  ];

  // حفظ تلقائي بكل تغيير بالاختيار — بلا ما ننتظر ضغطة "تابع".
  // ⚠️ initialPreferredMajor صارت array (بانتظار الباك يعدّل الحقل لـ List[InterestCluster])
  useEffect(() => {
    updateRegistrationData({
      initialPreferredMajor:
        isUndecided || selectedCategories.length === 0 ? ['not_chosen_yet'] : selectedCategories,
    });
  }, [selectedCategories, isUndecided]);

  const handleToggleCategory = (id) => {
    setIsUndecided(false);
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  const handleToggleUndecided = () => {
    setIsUndecided(true);
    setSelectedCategories([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // البيانات أصلاً محفوظة أول بأول عبر الحفظ التلقائي (useEffect فوق)
    navigate('/register-step3');
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="شو بيهمّك تعرف؟"
          stepText="خطوة 2 من 3"
          onBack={() => window.history.back()}
        />

        <StepProgress totalSteps={3} currentStep={2} />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container">

            <MajorSearchList
              categories={categories}
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              selectedCategories={selectedCategories}
              onToggleCategory={handleToggleCategory}
            />

            <div
              className={`undecided-box ${isUndecided ? 'active' : ''}`}
              onClick={handleToggleUndecided}
            >
              <span className="undecided-title">لسّا ما قرّرت</span>
              <span className="undecided-subtitle">منرتّبلك جولة عامة على كل التجمّعات</span>
            </div>

            <div className="actions">
              <button type="submit" className="btn btn-primary">
                تابع
              </button>
            </div>

          </form>
        </main>

      </div>
    </div>
  );
};

export default RegisterStep2Page;