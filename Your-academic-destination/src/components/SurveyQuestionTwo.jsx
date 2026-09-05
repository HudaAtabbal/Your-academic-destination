import React from 'react';

const SurveyQuestionTwo = ({ selectedMajor, onChange, majorsList }) => {
  return (
    <div className="survey-card">
      <h3 className="question-title">٢ • أي تخصص تميل إليه الآن؟</h3>
      <div className="select-wrapper">
        <select
          value={selectedMajor}
          onChange={(e) => onChange(e.target.value)}
          className="custom-select"
        >
          {majorsList.map((major) => (
            <option key={major.id} value={major.name}>
              {major.name}
            </option>
          ))}
        </select>
        <span className="select-arrow">&#9660;</span>
      </div>
    </div>
  );
};

export default SurveyQuestionTwo;