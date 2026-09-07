import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/api';
import '../../style/UniversityGatePage.css';

const UniversityGatePage = () => {
  const navigate = useNavigate();
  const [studentId, setStudentId] = useState('');
  const [todayCount, setTodayCount] = useState(null);

  useEffect(() => {
    apiGet('/checkins/count/today?activity_type=campus_entry')
      .then((res) => setTodayCount(res.count))
      .catch(() => {
        // فشل تحميل العداد مش خطأ حرج، بيضل "—"
      });
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    // بننقل لصفحة إدارة بيانات الطالب، ومنمرر الرقم يلي دخلته لتعبئة خانة البحث هناك تلقائياً
    navigate('/gate-manage', { state: { presetId: studentId } });
  };

  const handleScan = () => {
    // ⚠️ موك لسا — محتاج مكتبة قراءة QR فعلية عبر الكاميرا (زي html5-qrcode)
    // قبل ما نقدر نستدعي POST /checkins/campus-entry برمز حقيقي
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
              <span className="stat-value">{todayCount ?? '—'}</span>
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
            <span className="status-count">{todayCount ?? '—'} دخول اليوم</span>
          </div>

        </main>
      </div>
    </div>
  );
};

export default UniversityGatePage;