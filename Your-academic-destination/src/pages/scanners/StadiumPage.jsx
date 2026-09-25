import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import '../../style/StaffScan.css';

// مطابقة لـ enum Lecture بالباك (id = اسم القيمة بالـ enum، name = النص الفعلي).
// hall = القاعة و time = ساعة البداية — بيتبعتوا تحت اسم الندوة بالـ dropdown
// وبالـ header. القيم الفارغة معناها: ما في وقت/قاعة محددة بعد.
// ⚠️ ندوات الهندسة الثلاث (ميكانيكي · كهربائي · كيميائي وبترولي) بلّشت بندوة
// وحدة بالبرنامج "الهمك والبتروكيميا" الساعة 11:00، فمسحها بينكتب على
// lecture_11 والبـ backend بيجمع أرقام الثلاثة بالإحصائيات.
const MAIN_HALL = 'المدرج الرئيسي الكبير';
const ENGINEERING_TIME = '11:00';

const LECTURES = [
  { id: 'opening', name: 'حفل الافتتاح', hall: '', time: '' },
  { id: 'lecture_1', name: 'ندوة كليات العلوم الإنسانية', hall: '', time: '' },
  { id: 'lecture_2', name: 'ندوة مركزية: كيف تختار تخصصك الجامعي', hall: '', time: '' },
  { id: 'lecture_3', name: 'ندوة الكليات الطبية', hall: '', time: '' },
  { id: 'lecture_4', name: 'ندوة مركزية: اتجاهات سوق العمل والمهن الصاعدة', hall: '', time: '' },
  { id: 'lecture_5', name: 'ندوة أولياء الأمور', hall: '', time: '' },
  { id: 'lecture_6', name: 'ندوة كليات العلوم الأساسية والاقتصادية', hall: '', time: '' },
  { id: 'lecture_7', name: 'ندوة شريعة', hall: '', time: '' },
  { id: 'lecture_8', name: 'ندوة كلية الهندسة المعلوماتية مع نبذة عن الكلية التطبيقية', hall: '', time: '' },
  { id: 'lecture_9', name: 'ندوة الكليات: الهندسية المدنية · الهندسة المدنية · المعمارية · الزراعة', hall: '', time: '' },
  { id: 'lecture_10', name: 'ندوة مركزية: التخصصات المستجدة', hall: '', time: '' },
  { id: 'lecture_11', name: 'ندوة الهندسة الكهربائية والميكانيكية والهندسة الكيميائية والبترولية (الهمك والبتروكيميا)', hall: MAIN_HALL, time: ENGINEERING_TIME },
  { id: 'lecture_14', name: 'ندوة صناعة الحياة الجامعية', hall: '', time: '' },
  { id: 'lecture_15', name: 'ندوة المعاهد المتوسطة والعليا', hall: '', time: '' },
  { id: 'lecture_16', name: 'حفل الختام والتكريم وتوزيع جوائز النقاط', hall: '', time: '' },
];

// السطر اللي بينزل تحت اسم الندوة: "الساعة · القاعة" — والأجزاء الفارغة بتتجاهل.
const lectureSubtitle = (lecture) => [lecture.time, lecture.hall].filter(Boolean).join(' · ');

const StadiumPage = () => {
  const [manualCode, setManualCode] = useState('');
  const [selectedLectureId, setSelectedLectureId] = useState(LECTURES[0].id);
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظف يدوس الزر
  const [isProcessing, setIsProcessing] = useState(false); // guard: يمنع مسح/طلب جديد قبل ما يخلص السابق

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
    if (isProcessing) return; // guard: طلب سابق لسا شغال، منتجاهل هاد المسح

    const code = rawCode.trim();
    if (!code) return;
    if (!/^[RW]-\d{6}$/.test(code)) {
      setResult({ status: 'error', title: 'صيغة الرمز غير صحيحة — تأكد من الشكل R-XXXXXX أو W-XXXXXX', studentName: '', studentCode: code });
      return;
    }

    setIsProcessing(true);

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
          title="مسح عند المدرج"
          username={username}
          role={roleLabel}
          location={lectureSubtitle(selectedLecture)}
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
                disabled={isProcessing}
              >
                {LECTURES.map((lecture) => (
                  <option key={lecture.id} value={lecture.id}>
                    {lectureSubtitle(lecture) ? `${lecture.name} · ${lectureSubtitle(lecture)}` : lecture.name}
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

          
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default StadiumPage;