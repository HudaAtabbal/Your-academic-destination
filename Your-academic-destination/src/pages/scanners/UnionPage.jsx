import React, { useState, useEffect, useRef, useCallback } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import { apiGet, apiPost, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import '../../style/StaffScan.css';

// أقسام ركن الاتحاد — القيمة الخام هي نفسها enum UnionSection بالباك
const UNION_SECTIONS = [
  { id: 'central', label: 'الركن المركزي' },
  { id: 'major_guide', label: 'دليل التخصص' },
  { id: 'turkish_club', label: 'نادي التركي' },
];

const UnionPage = () => {
  const [section, setSection] = useState(null); // القسم المختار — null = لسا ما اختار
  const [manualCode, setManualCode] = useState('');
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(null);
  const [isCameraPaused, setIsCameraPaused] = useState(true); // مقفولة افتراضياً — تفتح بس لما الموظف يدوس الزر
  const [isProcessing, setIsProcessing] = useState(false); // نسخة مرئية للـ guard (زر تعطّل + مؤشر)
  const isProcessingRef = useRef(false); // guard حقيقي: يمنع مسح/طلب جديد قبل ما يخلص السابق

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول بـ TeamLoginPage)
  const accountUsername = localStorage.getItem('accountUsername') || '';
  const accountRole = localStorage.getItem('accountRole') || '';
  const roleLabel = ROLE_LABELS[accountRole] || accountRole || 'مسؤول الاتحاد';

  const selectedLabel = section
    ? (UNION_SECTIONS.find((s) => s.id === section)?.label || section)
    : '';

  // عداد اليوم للقسم المحدد — كل مرة يتغيّر القسم نعيد الجلب من رقم صحيح
  useEffect(() => {
    if (!section) {
      setScanCount(null);
      return;
    }
    apiGet(`/checkins/count/today?activity_type=union&union_section=${section}`)
      .then((res) => setScanCount(res.count))
      .catch(() => {});
  }, [section]);

  // handleScan ثابت المرجع أثناء المسح (يعتمد على القسم فقط) — عشان ScanBox
  // ما يعيد تشغيل الكاميرا بكل مسحة. الـ guard بـ ref بدل state.
  const handleScan = useCallback(
    async (rawCode) => {
      if (!section) return; // لسا ما اختار القسم — ما في مسح
      if (isProcessingRef.current) return; // طلب سابق لسا شغال، منتجاهل هاد المسح

      const code = rawCode.trim();
      if (!code) return;
      if (!/^[RW]-\d{6}$/.test(code)) {
        setResult({ status: 'error', title: 'صيغة الرمز غير صحيحة — تأكد من الشكل R-XXXXXX أو W-XXXXXX', studentName: '', studentCode: code });
        return;
      }

      isProcessingRef.current = true;
      setIsProcessing(true);

      try {
        const response = await apiPost('/checkins/union', {
          unique_code: code,
          union_section: section,
        });
        setResult({
          status: 'success',
          title: `ركن الاتحاد — ${selectedLabel}`,
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
        isProcessingRef.current = false;
        setIsProcessing(false);
      }
    },
    [section, selectedLabel]
  );

  const handleResumeCamera = () => {
    setIsCameraPaused(false);
  };

  const pickSection = (id) => {
    setSection(id);
    setResult(null); // مسح نتائج القسم السابق لما ننتقل لقسم تاني
    setManualCode('');
    setIsCameraPaused(true);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="ركن الاتحاد"
          username={accountUsername}
          role={roleLabel}
          location="الاتحاد"
        />

        <main className="card-body">
          {/* اختيار قسم الركن — يضل ظاهر حتى بعد الاختيار عشان يقدر يرجع لورا ويغيّر */}
          <div className="union-section-prompt">
            <h3 className="union-section-question">اختر قسم ركن الاتحاد</h3>
            <div className="union-section-options">
              {UNION_SECTIONS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  className={`union-section-btn${section === s.id ? ' selected' : ''}`}
                  onClick={() => pickSection(s.id)}
                  disabled={isProcessing}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {section && (
            <>
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
                يكفي أن يدخل الطالب إلى الجامعة اليوم لآلة مسح ركن الاتحاد — والمسح يُسجَّل مرة وحدة لكل قسم باليوم، والطالب قادر يزور الأقسام الثلاثة.
              </p>
            </>
          )}
        </main>

        <ScannerFooter
          count={section ? (scanCount ?? '—') : '—'}
          countLabel="مسحة مرفوعة"
        />
      </div>
    </div>
  );
};

export default UnionPage;