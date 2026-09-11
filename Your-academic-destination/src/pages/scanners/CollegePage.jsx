import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import { showToast } from '../../api/toast';
import '../../style/StaffScan.css';

const OPTION_LABELS = {
  tour: 'جولة الكلية',
  consultation: 'استشارة فردية',
};

// أسماء الأدوار بالعربي — نفس الماب المستخدم بصفحة اختيار المحطة
const ROLE_LABELS = {
  super_admin: 'المدير العام',
  students_admin: 'مدير بيانات الطلاب',
  gate_scanner: 'مسؤول المسح',
  college_staff: 'مسؤول الكلية',
};

const CollegePage = () => {
  const [manualCode, setManualCode] = useState('');
  const [scannedStudent, setScannedStudent] = useState(null);
  const [choice, setChoice] = useState(null);
  const [bookingResult, setBookingResult] = useState(null); // نتيجة التوجيه (نجاح/فشل) بعد اختيار الطالب
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظفة تدوس الزر

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول بـ TeamLoginPage)
  const accountUsername = localStorage.getItem('accountUsername') || '';
  const accountRole = localStorage.getItem('accountRole') || '';
  const accountCollege = localStorage.getItem('accountCollege') || '';
  const roleLabel = ROLE_LABELS[accountRole] || accountRole || 'مسؤول الكلية';

  const loadCount = async () => {
    try {
      const [tourRes, consultRes] = await Promise.all([
        apiGet('/bookings/count/today?booking_type=tour'),
        apiGet('/bookings/count/today?booking_type=consultation'),
      ]);
      setScanCount(tourRes.count + consultRes.count);
    } catch {
      // فشل تحميل العداد مش خطأ حرج
    }
  };

  useEffect(() => {
    loadCount();
  }, []);

  const handleScan = async (rawCode) => {
    const code = rawCode.trim();
    if (!code) return;

    setChoice(null);
    setBookingResult(null); // بدأنا مع طالب جديد — بننضّف نتيجة الطالب السابق

    try {
      // بنستخدم endpoint البطاقة (عام، بلا صلاحيات) بس لجلب اسم الطالب للعرض
      const card = await apiGet(`/students/card/${code}`);
      setScannedStudent({ name: card.full_name, code: card.unique_code });
      setIsCameraPaused(true);
    } catch (err) {
      setScannedStudent(null);
      const message = err instanceof ApiError ? err.message : 'صار خطأ غير متوقع';
      showToast(message, 'error');
      setIsCameraPaused(true);
    }
  };

  const handleResumeCamera = () => {
    setIsCameraPaused(false);
    setBookingResult(null);
  };

  const handleChoice = async (option) => {
    if (!scannedStudent) return;

    try {
      await apiPost(`/bookings/${option}`, { unique_code: scannedStudent.code });
      setChoice(option);
      loadCount(); // نحدّث العداد بعد نجاح الحجز

      // نجح التوجيه — منعرض تأكيد واضح ومنسكّر الأسئلة، جاهزين للطالب التالي
      setBookingResult({
        status: 'success',
        title: `تم التوجيه — ${OPTION_LABELS[option]}`,
        studentName: scannedStudent.name,
        studentCode: scannedStudent.code,
      });
      setScannedStudent(null);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'صار خطأ غير متوقع';
      showToast(message, 'error');
      // منسيب الأسئلة ظاهرة حتى تقدر تجرّبي خيار تاني بدون ما تعيدي المسح
      setBookingResult(null);
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="ركن التوجيه"
          username={accountUsername}
          role={roleLabel}
          location={accountCollege || 'داخل مبنى الكلية'}
        />

        <main className="card-body">
          {/* الكاميرا الفعلية — بتستدعي handleScan تلقائياً بمجرد ما تلتقط رمز */}
          <ScanBox
            caption="وجّهي الكاميرا نحو رمز الطالب لتوجيهه"
            onScan={handleScan}
            paused={isCameraPaused}
            onResume={handleResumeCamera}
          />

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
              بحث
            </button>
          </div>

          {scannedStudent && (
            <div className="orientation-prompt">
              <h3 className="orientation-question">
                وين رايح {scannedStudent.name}؟ ({scannedStudent.code})
              </h3>
              <div className="orientation-options">
                <button
                  type="button"
                  className={`orientation-btn ${choice === 'consultation' ? 'selected' : ''}`}
                  onClick={() => handleChoice('consultation')}
                >
                  استشارة فردية
                </button>
                <button
                  type="button"
                  className={`orientation-btn ${choice === 'tour' ? 'selected' : ''}`}
                  onClick={() => handleChoice('tour')}
                >
                  جولة الكلية
                </button>
              </div>
            </div>
          )}

          <ScanResultCard
            status={bookingResult?.status}
            title={bookingResult?.title}
            studentName={bookingResult?.studentName}
            studentCode={bookingResult?.studentCode}
          />

          <p className="scan-rule-text">
            هاد بس توجيه — الحضور الفعلي بينسجّل عند باب الكلية أو باب الاستشارة تحديداً.
          </p>
        </main>

        <ScannerFooter count={scanCount ?? '—'} countLabel="توجيه اليوم" />
      </div>
    </div>
  );
};

export default CollegePage;