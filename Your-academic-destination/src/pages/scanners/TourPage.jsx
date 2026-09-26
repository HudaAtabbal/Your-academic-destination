import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import { COLLEGE_LABELS } from '../../api/colleges';
import '../../style/StaffScan.css';

const TourPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظف يدوس الزر
  const [isProcessing, setIsProcessing] = useState(false); // guard: يمنع مسح/طلب جديد قبل ما يخلص السابق

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول بـ TeamLoginPage)
  const accountUsername = localStorage.getItem('accountUsername') || '';
  const accountRole = localStorage.getItem('accountRole') || '';
  const accountCollege = localStorage.getItem('accountCollege') || '';
  const roleLabel = ROLE_LABELS[accountRole] || accountRole || 'مسؤول الجولة';

  useEffect(() => {
    apiGet('/checkins/count/today?activity_type=tour')
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, []);

  const handleScan = async (rawCode) => {
    if (isProcessing) return; // guard: طلب سابق لسا شغال، منتجاهل هاد المسح

    const code = rawCode.trim();
    if (!code) return;
    if (!/^[RW]-\d{6}$/.test(code)) {
      setResult({ status: 'error', title: 'صيغة الرمز غير صحيحة — تأكد من الشكل R-XXXXXX أو W-XXXXXX', studentName: '', studentCode: code });
      return;
    }

    setIsProcessing(true);

    try {
      const response = await apiPost('/checkins/tour', { unique_code: code });
      setResult({
        status: 'success',
        title: COLLEGE_LABELS[response.college]
          ? `جولة — كلية ${COLLEGE_LABELS[response.college]}`
          : 'جولة — كلية',
        studentName: response.student_name,
        studentCode: code,
      });
      setScanCount((prev) => (prev != null ? prev + 1 : prev));
      setManualCode('');
      // بعد أي مسح ناجح، الكاميرا بتوقف — لازم دوسة زر يدوية لمسح الطالب التالي
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
          title="جولة تعريفية"
          username={accountUsername}
          role={roleLabel}
          location={COLLEGE_LABELS[accountCollege] || 'باب الكلية'}
        />

        <main className="card-body">
          {/* الكاميرا الفعلية — بتستدعي handleScan تلقائياً بمجرد ما تلتقط رمز */}
          <ScanBox
            onScan={handleScan}
            paused={isCameraPaused}
            onResume={handleResumeCamera}
          />

          <div className="manual-code-row">
            <input
              type="text"
              className="manual-code-input"
              placeholder="R-024865 (بديل يدوي لو تعطلت الكاميرا)"
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
            يمكن للطالب زيارة عدة كليات مختلفة، لكن لا يمكنه تسجيل حضور جولة نفس الكلية مرتين بنفس اليوم.
          </p>
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default TourPage;