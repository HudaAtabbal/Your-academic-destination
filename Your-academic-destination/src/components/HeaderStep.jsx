import React from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/whited-logo-1.png';
import '../style/HeaderStep.css';

// اللوغو بأعلى الصفحات أصبح زر "الرئيسية" (بدل زر الرجوع القديم):
// مسجّل دخول (عندو studentCode + studentName بالملاحة) → /my-card
// غير مسجّل → / (الصفحة الترحيبية/البداية)
const HeaderStep = ({ title, stepText }) => {
  const navigate = useNavigate();

  const goHome = () => {
    const studentCode = localStorage.getItem('studentCode');
    const studentName = localStorage.getItem('studentName');
    if (studentCode && studentName) {
      navigate('/my-card');
    } else {
      navigate('/');
    }
  };

  return (
    <header className="step-header">
      <button type="button" onClick={goHome} className="back-btn" aria-label="الرئيسية">
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