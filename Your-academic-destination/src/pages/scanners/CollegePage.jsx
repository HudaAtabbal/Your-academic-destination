import React, { useState, useEffect } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import '../../style/StaffScan.css';

const CollegePage = () => {
  const [manualCode, setManualCode] = useState('');
  const [scannedStudent, setScannedStudent] = useState(null);
  const [choice, setChoice] = useState(null);
  const [choiceError, setChoiceError] = useState('');
  const [scanCount, setScanCount] = useState(null);
  const [lookupError, setLookupError] = useState('');

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

    setLookupError('');
    setChoice(null);
    setChoiceError('');

    try {
      // بنستخدم endpoint البطاقة (عام، بلا صلاحيات) بس لجلب اسم الطالب للعرض
      const card = await apiGet(`/students/card/${code}`);
      setScannedStudent({ name: card.full_name, code: card.unique_code });
    } catch (err) {
      setScannedStudent(null);
      setLookupError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع');
    }
  };

  const handleChoice = async (option) => {
    if (!scannedStudent) return;

    setChoiceError('');

    try {
      await apiPost(`/bookings/${option}`, { unique_code: scannedStudent.code });
      setChoice(option);
      loadCount(); // نحدّث العداد بعد نجاح الحجز
    } catch (err) {
      setChoiceError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع');
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="ركن التوجيه"
          username="rima_staff"
          role="مسؤول الكلية"
          location="داخل مبنى الكلية"
        />

        <main className="card-body">
          {/* الكاميرا الفعلية — بتستدعي handleScan تلقائياً بمجرد ما تلتقط رمز */}
          <ScanBox caption="وجّهي الكاميرا نحو رمز الطالب لتوجيهه" onScan={handleScan} />

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

          {lookupError && <p className="scan-error-text">{lookupError}</p>}

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
              {choiceError && <p className="scan-error-text">{choiceError}</p>}
            </div>
          )}

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