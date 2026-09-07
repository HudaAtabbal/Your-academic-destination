import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

// ⚠️ الباك لسا عنده بس قيمتين placeholder لـ Lecture enum (مش المحاضرات الحقيقية).
// لما تتوفر القائمة الفعلية، بنستبدل هالمصفوفة بالقيم الحقيقية القادمة من الباك.
const LECTURES = [
  { id: 'lecture_placeholder_1', name: 'محاضرة تجريبية 1 (placeholder)', hall: 'مدرج رئيسي' },
  { id: 'lecture_placeholder_2', name: 'محاضرة تجريبية 2 (placeholder)', hall: 'مدرج ب' },
];

const StadiumPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [selectedLectureId, setSelectedLectureId] = useState(LECTURES[0].id);
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);

  const selectedLecture = LECTURES.find((l) => l.id === selectedLectureId);

  useEffect(() => {
    apiGet(`/checkins/count/today?activity_type=lecture&lecture_name=${selectedLectureId}`)
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, [selectedLectureId]);

  const handleScan = async () => {
    const code = manualCode.trim();
    if (!code) return;

    try {
      const response = await apiPost('/checkins/lecture', {
        unique_code: code,
        lecture_name: selectedLectureId,
      });
      setResult({
        status: 'success',
        title: `حضور — ${selectedLecture.name}`,
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

  const handleQuickRegister = () => {
    // ⚠️ ما في endpoint مخصص لهاد الزر لسا — لازم نحدد مع الباك شو المفروض يصير هون بالضبط
    console.log('فتح تسجيل سريع بدون بطاقة للمحاضرة:', selectedLecture.name);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="مسح عند المدرج"
          username="hadi_gate"
          role="مسؤول المسح"
          location={selectedLecture.hall}
        />

        <main className="card-body">
          <div>
            <p className="input-label" style={{ marginBottom: 8, color: '#71122B', fontWeight: 700 }}>
              المحاضرة الجارية الآن
            </p>
            <div className="lecture-select-wrapper">
              <select
                className="lecture-select"
                value={selectedLectureId}
                onChange={(e) => {
                  setSelectedLectureId(e.target.value);
                  setResult(null);
                }}
              >
                {LECTURES.map((lecture) => (
                  <option key={lecture.id} value={lecture.id}>
                    {lecture.name} · {lecture.hall}
                  </option>
                ))}
              </select>
            </div>
          </div>

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

          
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default StadiumPage;