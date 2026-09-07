import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../../style/GateEntrySuccessPage.css';

const GateEntrySuccessPage = ({ onNextScan }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // البيانات الحقيقية بتوصل عبر location.state من UniversityGatePage بعد نجاح المسح.
  // القيم الافتراضية هون بس fallback بحال حدا فتح الصفحة مباشرة بدون مسح فعلي.
  const {
    studentName = 'الطالب',
    studentId = '—',
    entryTime = '—',
  } = location.state || {};

  const handleNextScan = () => {
    if (onNextScan) {
      onNextScan();
    } else {
      // ما في handler ممرَّر من بره، فبنرجع افتراضياً لصفحة المسح
      navigate('/gate');
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Top Header */}
        <header className="gate-header">
          <div className="user-info">
            <h1 className="header-title">تسجيل الدخول</h1>
            <p className="header-subtitle">
              sedra_admin <span className="dot">•</span> مدير بيانات الطلاب
            </p>
          </div>
        </header>

        {/* Scrollable Content Area */}
        <main className="gate-body flex-center">
          
          {/* Success Check Icon */}
          <div className="success-icon-wrapper">
            <svg viewBox="0 0 24 24" className="check-icon" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>

          {/* Main Title & Student Info */}
          <div className="success-details">
            <h2 className="success-title">تم تسجيل الدخول</h2>
            <h3 className="student-name">{studentName}</h3>
            
            <div className="meta-row">
              <span className="meta-time">{entryTime}</span>
              <span className="dot-separator">•</span>
              <span className="meta-id">{studentId}</span>
            </div>
          </div>

          {/* Entry Info Banner — شيلناها لأنو الباك ما بيرجّع entry_count/last_entry_time أصلاً بالـ response */}

          {/* Bottom Action Button */}
          <div className="action-container">
            <button type="button" onClick={handleNextScan} className="btn btn-primary">
              التالي — مسح رمز جديد
            </button>
            <button
              type="button"
              onClick={() => navigate('/gate-manage', { state: { presetId: studentId } })}
              className="edit-link"
            >
              تعديل بيانات الطالب
            </button>
          </div>

        </main>
      </div>
    </div>
  );
};

export default GateEntrySuccessPage;