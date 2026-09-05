import React from 'react';
import logo from '../assets/English logo white-01.png';
import '../style/HeaderStep.css';

const HeaderStep = ({ title, stepText, onBack }) => {
  return (
    <header className="step-header">
      <button type="button" onClick={onBack} className="back-btn" aria-label="رجوع">
        <img src={logo} alt="شعار" className="back-btn-logo" />
      </button>
      <div className="step-title-group">
        <h2 className="step-title">{title}</h2>
        <span className="step-subtitle">{stepText}</span>
      </div>
    </header>
  );
};

export default HeaderStep;