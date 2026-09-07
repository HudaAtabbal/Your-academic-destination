import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

const ConsultationPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);

  useEffect(() => {
    apiGet('/checkins/count/today?activity_type=consultation')
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, []);

  const handleScan = async (rawCode) => {
    const code = rawCode.trim();
    if (!code) return;

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
          title="استشارة فردية"
          username="nour_staff"
          role="مسؤول الكلية"
          location="باب الاستشارة"
        />

        <main className="card-body">
          {/* الكاميرا الفعلية — بتستدعي handleScan تلقائياً بمجرد ما تلتقط رمز */}
          <ScanBox onScan={handleScan} />

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