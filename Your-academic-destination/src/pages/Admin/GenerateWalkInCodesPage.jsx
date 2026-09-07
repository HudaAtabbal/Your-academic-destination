import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import QRCode from 'react-qr-code';
import AdminHeader from '../../components/AdminHeader';
import { apiPost, ApiError } from '../../api/api';
import '../../style/GenerateWalkInCodesPage.css';

const GenerateWalkInCodesPage = ({ userRole = 'المدير العام', onPrint }) => {
  const navigate = useNavigate();
  const [count, setCount] = useState('50');
  const [error, setError] = useState('');
  const [generatedCodes, setGeneratedCodes] = useState([]);
  const [batchInfo, setBatchInfo] = useState(null); // { total, start, end }
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async (e) => {
    e.preventDefault();

    const parsedCount = parseInt(count, 10);
    if (!parsedCount || parsedCount <= 0) {
      setError('يرجى إدخال عدد رموز صحيح أكبر من صفر');
      return;
    }

    setError('');
    setIsGenerating(true);

    try {
      // الباك هو يلي بيحدد رقم البداية تلقائياً (آخر رقم متوقف عنده بالدفعة السابقة)
      const response = await apiPost('/admin/walkin-codes/generate', { count: parsedCount });
      const codes = response.codes;

      setGeneratedCodes(codes);
      setBatchInfo({
        total: codes.length,
        start: codes[0],
        end: codes[codes.length - 1],
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  const handlePrint = () => {
    if (onPrint) {
      onPrint();
    } else {
      // كل كود QR رح يطلع فعلياً بالطباعة (حتى لو أكتر من الـ 24 يلي معروضين بالمعاينة)
      // بفضل قسم الطباعة المخفي (.gwic-print-only) يلي بيظهر بس وقت الطباعة
      window.print();
    }
  };

  // بنعرض أول 24 كود كمعاينة بس، حتى ما يصير الجدول ثقيل لو الدفعة كبيرة (مثلاً 500 كود)
  const previewCodes = generatedCodes.slice(0, 24);
  const remainingCount = generatedCodes.length - previewCodes.length;

  return (
    <div className="gwic-viewport">

      <AdminHeader userRole={userRole} />

      {/* Main Content Area */}
      <main className="gwic-main-container">
        
        {/* Back Button Link */}
        <div className="gwic-back-wrapper">
          <button type="button" className="gwic-back-btn" onClick={handleBack}>
            <span className="gwic-back-arrow">←</span> رجوع
          </button>
        </div>

        {/* Top Control Form Card */}
        <div className="gwic-card-panel">
          <h1 className="gwic-panel-title">توليد دفعة رموز جديدة (Walk-in)</h1>

          <form onSubmit={handleGenerate} className="gwic-generate-form">
            <div className="gwic-form-row gwic-form-row-simplified">
              
              <div className="gwic-field-group">
                <label className="gwic-field-label" htmlFor="gwic-count-input">
                  عدد الرموز
                </label>
                <input
                  id="gwic-count-input"
                  type="text"
                  inputMode="numeric"
                  className="gwic-input-field gwic-input-center"
                  value={count}
                  onChange={(e) => setCount(e.target.value.replace(/[^0-9]/g, ''))}
                />
              </div>

              <div className="gwic-action-group">
                <button type="submit" className="gwic-submit-btn" disabled={isGenerating}>
                  {isGenerating ? 'جاري التوليد...' : 'توليد'}
                </button>
              </div>

            </div>
            {error && <p className="gwic-error-text">{error}</p>}
          </form>
        </div>

        {/* Output Section — ما بيظهر إلا بعد توليد ناجح */}
        {batchInfo && (
          <>
            <div className="gwic-output-header">
              <h2 className="gwic-batch-title">
                دفعة اليوم — {batchInfo.total} رمزاً ({batchInfo.start} إلى {batchInfo.end})
              </h2>
              <button type="button" className="gwic-print-btn" onClick={handlePrint}>
                طباعة الدفعة
              </button>
            </div>

            {/* QR Codes Grid Card — معاينة على الشاشة (أول 24 كود بس) */}
            <div className="gwic-card-panel gwic-qr-panel">
              <div className="gwic-qr-grid">
                {previewCodes.map((code) => (
                  <div key={code} className="gwic-qr-card">
                    <QRCode
                      value={code}
                      size={64}
                      fgColor="#0F3B34"
                      bgColor="#FFFFFF"
                      level="L"
                    />
                    <span className="gwic-qr-code-text">{code}</span>
                  </div>
                ))}
              </div>
              {remainingCount > 0 && (
                <p className="gwic-more-note">و{remainingCount} كود إضافي بنفس الدفعة (بيطلعوا كلهم بالطباعة)</p>
              )}
            </div>

            {/* قسم مخفي بالشاشة، بيظهر بس وقت الطباعة، وفيه كل أكواد الدفعة كاملة */}
            <div className="gwic-print-only">
              <h2 className="gwic-print-title">
                دفعة الرموز — {batchInfo.total} رمزاً ({batchInfo.start} إلى {batchInfo.end})
              </h2>
              <div className="gwic-qr-grid gwic-print-grid">
                {generatedCodes.map((code) => (
                  <div key={code} className="gwic-qr-card">
                    <QRCode
                      value={code}
                      size={64}
                      fgColor="#0F3B34"
                      bgColor="#FFFFFF"
                      level="L"
                    />
                    <span className="gwic-qr-code-text">{code}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Footer Helper Note */}
        <p className="gwic-footer-instruction">
          اطبع هاي الورقة وقصها لبطاقات مفردة، وسلّمها لموظف الاستقبال قبل بداية الفعالية.
        </p>

      </main>
    </div>
  );
};

export default GenerateWalkInCodesPage;