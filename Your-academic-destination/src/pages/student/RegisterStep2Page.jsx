import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import StepProgress from '../../components/StepProgress';
import { updateRegistrationData, getRegistrationData } from '../../api/RegistrationStorage';
import { COLLEGE_OPTIONS } from '../../api/colleges';
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
        placeholder="ابحث عن اختصاص..."
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

  // القيم (id) مطابقة بالحرف لـ enum College بالباك — من المصدر الموحّد (src/api/colleges.js)
  const categories = COLLEGE_OPTIONS;

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
              <span className="undecided-title">لم اتخذ قراري بعد </span>
              <span className="undecided-subtitle">نرتب لك جولة عامة على كل التجمّعات</span>
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