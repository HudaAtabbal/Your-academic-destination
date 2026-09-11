import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

// أسماء الأدوار بالعربي — نفس الماب المستخدم بصفحة اختيار المحطة
const ROLE_LABELS = {
  super_admin: 'المدير العام',
  students_admin: 'مدير بيانات الطلاب',
  gate_scanner: 'مسؤول المسح',
  college_staff: 'مسؤول الكلية',
};

const ConsultationPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظف يدوس الزر
  const [isProcessing, setIsProcessing] = useState(false); // guard: يمنع مسح/طلب جديد قبل ما يخلص السابق

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول بـ TeamLoginPage)
  const accountUsername = localStorage.getItem('accountUsername') || '';
  const accountRole = localStorage.getItem('accountRole') || '';
  const accountCollege = localStorage.getItem('accountCollege') || '';
  const roleLabel = ROLE_LABELS[accountRole] || accountRole || 'مسؤول الكلية';

  useEffect(() => {
    apiGet('/checkins/count/today?activity_type=consultation')
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, []);

  const handleScan = async (rawCode) => {
    if (isProcessing) return; // guard: طلب سابق لسا شغال، منتجاهل هاد المسح

    const code = rawCode.trim();
    if (!code) return;

    setIsProcessing(true);

    try {
      const response = await apiPost('/checkins/consultation', { unique_code: code });
      setResult({
        status: 'success',
        title: 'تفصّل — أول استشارة إلك',
        studentName: response.student_name,
        studentCode: code,
      });
      setScanCount((prev) => (prev != null ? prev + 1 : prev));
      setManualCode('');
      setIsCameraPaused(true);
    } catch (err) {
      setResult({
        status: 'error',
        title: err instanceof ApiError ? err.message : 'صار خطأ غير متوقع',
        studentName: '',
        studentCode: code,
      });
      setIsCameraPaused(true);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResumeCamera = () => {
    setIsCameraPaused(false);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="استشارة فردية"
          username={accountUsername}
          role={roleLabel}
          location={accountCollege || 'باب الاستشارة'}
        />

        <main className="card-body">
          {/* الكاميرا الفعلية — بتستدعي handleScan تلقائياً بمجرد ما تلتقط رمز */}
          <ScanBox onScan={handleScan} paused={isCameraPaused} onResume={handleResumeCamera} />

          <div className="manual-code-row">
            <input
              type="text"
              className="manual-code-input"
              placeholder="R-0248 (بديل يدوي لو تعطلت الكاميرا)"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              dir="ltr"
              disabled={isProcessing}
            />
            <button
              type="button"
              className="manual-code-btn"
              onClick={() => handleScan(manualCode)}
              disabled={isProcessing}
            >
              تحقق
            </button>
          </div>

          <ScanResultCard
            status={result?.status}
            title={result?.title}
            studentName={result?.studentName}
            studentCode={result?.studentCode}
          />

          <p className="scan-rule-text">
            يُسمح للطالب بحضور استشارة واحدة بس طول الفعالية كلها — بغض النظر عن الكلية.
          </p>
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="استشارة اليوم" />
      </div>
    </div>
  );
};

export default ConsultationPage;