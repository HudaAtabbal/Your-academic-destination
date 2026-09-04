import React from 'react';

const HeaderStep = ({ title, stepText, onBack }) => {
  return (
    <header className="step-header">
      <button type="button" onClick={onBack} className="back-btn" aria-label="رجوع">
        &rarr;
      </button>
      <div className="step-title-group">
        <h2 className="step-title">{title}</h2>
        <span className="step-subtitle">{stepText}</span>
      </div>
    </header>
  );
};

export default HeaderStep;