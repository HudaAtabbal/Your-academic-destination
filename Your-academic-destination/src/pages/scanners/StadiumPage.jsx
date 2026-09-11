import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

// أسماء الأدوار بالعربي — لبناء نص المستخدم من بيانات الحساب المخزّنة فعلياً
const ROLE_LABELS = {
  super_admin: 'المدير العام',
  students_admin: 'مدير بيانات الطلاب',
  gate_scanner: 'مسؤول المسح',
  college_staff: 'مسؤول الكلية',
};

// مطابقة لـ enum Lecture بالباك (id = اسم القيمة بالـ enum، name = النص الفعلي).
// ⚠️ القاعة (hall) مش موجودة بالـ enum — لسا لازم نحددها مع الباك أو نضيفها لاحقاً.
const LECTURES = [
  { id: 'lecture_1', name: 'ندوة كليات العلوم الإنسانية', hall: '' },
  { id: 'lecture_2', name: 'ندوة مركزية: كيف تختار تخصصك الجامعي', hall: '' },
  { id: 'lecture_3', name: 'ندوة الكليات الطبية', hall: '' },
  { id: 'lecture_4', name: 'ندوة مركزية: اتجاهات سوق العمل والمهن الصاعدة', hall: '' },
  { id: 'lecture_5', name: 'ندوة أولياء الأمور', hall: '' },
  { id: 'lecture_6', name: 'ندوة كليات العلوم الأساسية والاقتصادية', hall: '' },
  { id: 'lecture_7', name: 'ندوة مركزية 2', hall: '' },
  { id: 'lecture_8', name: 'ندوة كلية الهندسة المعلوماتية مع نبذة عن الكلية التطبيقية', hall: '' },
  { id: 'lecture_9', name: 'ندوة الكليات: الهندسية المدنية · الهندسة المدنية · المعمارية · الزراعة', hall: '' },
  { id: 'lecture_10', name: 'ندوة مركزية: التخصصات المستجدة', hall: '' },
  { id: 'lecture_11', name: 'ندوة كلية الهندسة الميكانيكية', hall: '' },
  { id: 'lecture_12', name: 'ندوة كلية الهندسة الكيميائية والبترولية', hall: '' },
  { id: 'lecture_13', name: 'ندوة كلية الهندسة الكهربائية', hall: '' },
  { id: 'lecture_14', name: 'ندوة صناعة الحياة الجامعية', hall: '' },
  { id: 'lecture_15', name: 'ندوة المعاهد المتوسطة والعليا', hall: '' },
  { id: 'lecture_16', name: 'حفل الختام والتكريم وتوزيع جوائز النقاط', hall: '' },
];

const StadiumPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [selectedLectureId, setSelectedLectureId] = useState(LECTURES[0].id);
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظف يدوس الزر

  const selectedLecture = LECTURES.find((l) => l.id === selectedLectureId);

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول)
  const username = localStorage.getItem('accountUsername') || '';
  const roleType = localStorage.getItem('accountRole') || '';
  const roleLabel = ROLE_LABELS[roleType] || roleType;

  useEffect(() => {
    apiGet(`/checkins/count/today?activity_type=lecture&lecture_name=${selectedLectureId}`)
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, [selectedLectureId]);

  const handleScan = async (rawCode) => {
    const code = rawCode.trim();
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
      setIsCameraPaused(true);
    } catch (err) {
      setResult({
        status: 'error',
        title: err instanceof ApiError ? err.message : 'صار خطأ غير متوقع',
        studentName: '',
        studentCode: code,
      });
      setIsCameraPaused(true);
    }
  };

  const handleResumeCamera = () => {
    setIsCameraPaused(false);
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
          username={username}
          role={roleLabel}
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
                    {lecture.hall ? `${lecture.name} · ${lecture.hall}` : lecture.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

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

          
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default StadiumPage;