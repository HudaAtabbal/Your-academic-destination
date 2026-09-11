import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScanBox from '../../components/ScanBox';
import { apiGet, apiPost, ApiError, clearAuthToken } from '../../api/api';
import { showToast } from '../../api/toast';
import '../../style/UniversityGatePage.css';
import '../../style/StaffScan.css'; // فيها ستايل ScanBox (الكاميرا) المشترك

const UniversityGatePage = () => {
  const navigate = useNavigate();
  const [studentId, setStudentId] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [todayCount, setTodayCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظفة تدوس الزر

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

    try {
      const response = await apiPost('/checkins/campus-entry', { unique_code: code });

      const entryTime = new Date(response.checked_in_at).toLocaleTimeString('ar', {
        hour: '2-digit',
        minute: '2-digit',
      });

      setTodayCount((prev) => (prev != null ? prev + 1 : prev));

      // بعد أي مسح ناجح، الكاميرا بتوقف — لازم دوسة زر يدوية لمسح الطالب التالي
      setIsCameraPaused(true);

      navigate('/gate-entry-success', {
        state: {
          studentName: response.student_name,
          studentId: code,
          entryTime,
        },
      });
    } catch (err) {
      showToast(
        err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية',
        'error'
      );
      // منوقف الكاميرا فعلياً — بدل ما تضل تحاول تمسح نفس الكرت كل 3 ثواني
      // وترجع نفس الخطأ (409) بلا نهاية. الموظفة بتستأنف يدوياً لما تبعد الكرت
      setIsCameraPaused(true);
    } finally {
      setManualCode('');
    }
  };

  const handleResumeCamera = () => {
    setIsCameraPaused(false);
  };

  return (
    <div className="uniGate-wrapper">
      <div className="uniGate-container">

        {/* Top Header */}
        <header className="uniGate-header">
          <div className="uniGate-userInfo">
            <h1 className="uniGate-headerTitle">بوابة الجامعة</h1>
            <p className="uniGate-headerSubtitle">
              sedra_admin <span className="uniGate-dot">•</span> مدير بيانات الطلاب
            </p>
          </div>
          <button type="button" className="uniGate-logoutBtn" onClick={handleLogout}>
            تسجيل خروج
          </button>
        </header>

        {/* Scrollable Content Area */}
        <main className="uniGate-body">

          {/* Stats Cards Row */}
          <div className="uniGate-statsRow">

            <div className="uniGate-statCard">
              <span className="uniGate-statLabel">دخلوا اليوم</span>
              <span className="uniGate-statValue">{todayCount ?? '—'}</span>
            </div>
          </div>

          {/* QR Scanner Area — كاميرا حقيقية */}
          <ScanBox
            caption="امسح رمز QR لتسجيل دخول الطالب"
            onScan={handleScan}
            paused={isCameraPaused}
            onResume={handleResumeCamera}
          />

          {/* بديل يدوي بحال تعلّقت الكاميرا أو ما قدرت تقرا رمز الطالب */}
          <div className="manual-code-row">
            <input
              type="text"
              className="manual-code-input"
              placeholder="R-0248 (بديل يدوي لو تعطلت الكاميرا)"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              dir="ltr"
            />
            <button type="button" className="manual-code-btn" onClick={() => handleScan(manualCode)}>
              تسجيل
            </button>
          </div>

          {/* Divider */}
          <div className="uniGate-divider">— أو —</div>

          {/* Search Section */}
          <form onSubmit={handleSearch} className="uniGate-searchForm">
            <div className="uniGate-inputGroup">
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

            <button type="submit" className="uniGate-btn uniGate-btnSecondary">
              بحث وتعديل بيانات
            </button>
          </form>

          {/* Bottom Status Bar */}
          <div className="uniGate-statusBar">
            <span className="uniGate-statusText">متصل</span>
            <span className="uniGate-statusCount">{todayCount ?? '—'} دخول اليوم</span>
          </div>

        </main>
      </div>
    </div>
  );
};

export default UniversityGatePage;