import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScanBox from '../../components/ScanBox';
import { apiGet, apiPost, ApiError, clearAuthToken } from '../../api/api';
import '../../style/UniversityGatePage.css';
import '../../style/StaffScan.css'; // فيها ستايل ScanBox (الكاميرا) المشترك

const UniversityGatePage = () => {
  const navigate = useNavigate();
  const [studentId, setStudentId] = useState('');
  const [todayCount, setTodayCount] = useState(null);
  const [scanError, setScanError] = useState('');

  const handleLogout = () => {
    clearAuthToken();
    localStorage.removeItem('accountUsername');
    localStorage.removeItem('accountRole');
    localStorage.removeItem('accountCollege');
    navigate('/team-log');
  };

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

  const handleScan = async (rawCode) => {
    const code = rawCode.trim();
    if (!code) return;

    setScanError('');

    try {
      const response = await apiPost('/checkins/campus-entry', { unique_code: code });

      const entryTime = new Date(response.checked_in_at).toLocaleTimeString('ar', {
        hour: '2-digit',
        minute: '2-digit',
      });

      setTodayCount((prev) => (prev != null ? prev + 1 : prev));

      navigate('/gate-entry-success', {
        state: {
          studentName: response.student_name,
          studentId: code,
          entryTime,
        },
      });
    } catch (err) {
      setScanError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    }
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
          <button type="button" className="gate-logout-btn" onClick={handleLogout}>
            تسجيل خروج
          </button>
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

          {/* QR Scanner Area — كاميرا حقيقية */}
          <ScanBox caption="امسح رمز QR لتسجيل دخول الطالب" onScan={handleScan} />
          {scanError && <p className="gate-scan-error">{scanError}</p>}

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