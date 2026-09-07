import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

const TourPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);

  useEffect(() => {
    apiGet('/checkins/count/today?activity_type=tour')
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, []);

  const handleScan = async () => {
    const code = manualCode.trim();
    if (!code) return;

    try {
      const response = await apiPost('/checkins/tour', { unique_code: code });
      setResult({
        status: 'success',
        title: `جولة — كلية ${response.college || ''}`,
        studentName: response.student_name,
        studentCode: code,
      });
      setScanCount((prev) => (prev != null ? prev + 1 : prev));
      setManualCode('');
    } catch (err) {
      setResult({
        status: 'error',
        title: err instanceof ApiError ? err.message : 'صار خطأ غير متوقع',
        studentName: '',
        studentCode: code,
      });
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="جولة تعريفية"
          username="yousef_tour"
          role="مسؤول الجولة"
          location="باب الكلية"
        />

        <main className="card-body">
          {/* ⚠️ الكاميرا الفعلية لسا مش مربوطة — إدخال يدوي مؤقت للاختبار */}
          <ScanBox caption="اكتبي رمز الطالب تحت واضغطي مسح (مؤقتاً لحد ما تجهز الكاميرا)" onScan={handleScan} />

          <div className="manual-code-row">
            <input
              type="text"
              className="manual-code-input"
              placeholder="R-0248"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              dir="ltr"
            />
            <button type="button" className="manual-code-btn" onClick={handleScan}>
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
            يمكن للطالب زيارة عدة كليات مختلفة، لكن لا يمكنه تسجيل حضور جولة نفس الكلية مرتين.
          </p>
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default TourPage;