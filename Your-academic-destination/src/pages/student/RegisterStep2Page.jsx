import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import StepProgress from '../../components/StepProgress';
import { updateRegistrationData, getRegistrationData } from '../../api/RegistrationStorage';
import '../../style/RegisterStep2Page.css';

// --- Sub-Component: قائمة تخصصات قابلة للبحث ---
const MajorSearchList = ({
  categories,
  searchTerm,
  onSearchChange,
  selectedCategory,
  onSelectCategory,
  isUndecided,
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
                selectedCategory === cat.id && !isUndecided ? 'selected' : ''
              }`}
              onClick={() => onSelectCategory(cat.id)}
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
  const savedIsUndecided = saved.initialPreferredMajor === 'not_chosen_yet';

  const [selectedCategory, setSelectedCategory] = useState(
    savedIsUndecided || !saved.initialPreferredMajor ? null : saved.initialPreferredMajor
  );
  const [isUndecided, setIsUndecided] = useState(savedIsUndecided);
  const [searchTerm, setSearchTerm] = useState('');

  const categories = [
    { id: 'medicine', name: 'الطب البشري' },
    { id: 'informatics', name: 'المعلوماتية' },
    { id: 'architecture', name: 'الهندسة المعمارية' },
    { id: 'law', name: 'الحقوق' },
    { id: 'pharmacy', name: 'الصيدلة' },
    { id: 'agriculture', name: 'الهندسة الزراعية' },
    { id: 'education', name: 'التربية' },
    { id: 'civil', name: 'الهندسة المدنية' },
  ];

  // حفظ تلقائي بكل تغيير بالاختيار — بلا ما ننتظر ضغطة "تابع"
  useEffect(() => {
    updateRegistrationData({
      initialPreferredMajor: isUndecided || !selectedCategory ? 'not_chosen_yet' : selectedCategory,
    });
  }, [selectedCategory, isUndecided]);

  const handleSelectCategory = (id) => {
    setSelectedCategory(id);
    setIsUndecided(false);
  };

  const handleToggleUndecided = () => {
    setIsUndecided(true);
    setSelectedCategory(null);
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
              selectedCategory={selectedCategory}
              onSelectCategory={handleSelectCategory}
              isUndecided={isUndecided}
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