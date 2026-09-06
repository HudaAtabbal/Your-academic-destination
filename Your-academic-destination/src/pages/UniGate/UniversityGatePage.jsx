import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../style/UniversityGatePage.css';

const UniversityGatePage = () => {
  const navigate = useNavigate();
  const [studentId, setStudentId] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    // بننقل لصفحة إدارة بيانات الطالب، ومنمرر الرقم يلي دخلته لتعبئة خانة البحث هناك تلقائياً
    navigate('/gate-manage', { state: { presetId: studentId } });
  };

  const handleScan = () => {
    // موك: محاكاة مسح ناجح لرمز QR (لاحقاً بيتبدل بطلب فعلي للـ backend)
    navigate('/gate-entry-success');
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Top Header */}
        <header className="gate-header">
          <div className="user-info">
            <h1 className="header-title">بوابة الجامعة</h1>
            <p className="header-subtitle">
              sedra_admin <span className="dot">•</span> مدير بيانات الطلاب
            </p>
          </div>
        </header>

        {/* Scrollable Content Area */}
        <main className="gate-body">
          
          {/* Stats Cards Row */}
          <div className="stats-row">
           
            <div className="stat-card">
              <span className="stat-label">دخلوا اليوم</span>
              <span className="stat-value">5,117</span>
            </div>
          </div>

          {/* QR Scanner Area */}
          <button type="button" className="qr-card" onClick={handleScan}>
            <div className="qr-viewfinder">
              <div className="qr-frame"></div>
            </div>
            <p className="qr-hint">امسح رمز QR لتسجيل دخول الطالب</p>
          </button>

          {/* Divider */}
          <div className="divider">— أو —</div>

          {/* Search Section */}
          <form onSubmit={handleSearch} className="search-form">
            <div className="input-group">
              <label htmlFor="studentId">ابحث برقم الطالب الفريد</label>
              <input
                type="text"
                id="studentId"
                placeholder="R-0248"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                dir="ltr"
              />
            </div>

            <button type="submit" className="btn btn-secondary">
              بحث وتعديل بيانات
            </button>
          </form>

          {/* Bottom Status Bar */}
          <div className="status-bar">
            <span className="status-text">متصل</span>
            <span className="status-count">٦١٢ دخول اليوم</span>
          </div>

        </main>
      </div>
    </div>
  );
};

export default UniversityGatePage;