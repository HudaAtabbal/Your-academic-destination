import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../components/HeaderStep';
import StepProgress from '../components/Stepprogress';
import '../style/RegisterStep2Page.css';

// --- Sub-Component: InterestChips ---
const InterestChips = ({ categories, selectedCategory, onSelectCategory, isUndecided, onToggleUndecided }) => (
  <div className="interests-section">
    <div className="chips-grid">
      {categories.map((cat) => (
        <button
          key={cat.id}
          type="button"
          className={`chip-item ${selectedCategory === cat.id && !isUndecided ? 'selected' : ''}`}
          onClick={() => onSelectCategory(cat.id)}
        >
          {cat.name}
        </button>
      ))}
    </div>

    <div
      className={`undecided-box ${isUndecided ? 'active' : ''}`}
      onClick={onToggleUndecided}
    >
      <span className="undecided-title">لسّا ما قرّرت</span>
      <span className="undecided-subtitle">منرتّبلك جولة عامة على كل التجمّعات</span>
    </div>
  </div>
);

// --- Main Page Component ---
const RegisterStep2Page = () => {
  const navigate = useNavigate();

  const [selectedCategory, setSelectedCategory] = useState('informatics');
  const [isUndecided, setIsUndecided] = useState(false);

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
    console.log('Selected:', { selectedCategory, isUndecided });
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

            <InterestChips
              categories={categories}
              selectedCategory={selectedCategory}
              onSelectCategory={handleSelectCategory}
              isUndecided={isUndecided}
              onToggleUndecided={handleToggleUndecided}
            />

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