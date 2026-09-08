import React from 'react';

const SurveyQuestionOne = ({ selectedOption, onSelect }) => {
  const options = [
    { id: 'confirmed_choice', label: 'تأكّد اللي كنت ناويه' },
    { id: 'changed_completely', label: 'تغيّر تماماً' },
    { id: 'decided', label: 'صار عندي قرار' },
    { id: 'still_confused', label: 'لسا محتار' },
  ];

  return (
    <div className="survey-card">
      <h3 className="question-title">١ • تغيّر رأيك بالتخصص؟</h3>
      <div className="options-chips">
        {options.map((opt) => (
          <button
            key={opt.id}
            type="button"
            className={`chip-btn ${selectedOption === opt.id ? 'active' : ''}`}
            onClick={() => onSelect(opt.id)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SurveyQuestionOne;