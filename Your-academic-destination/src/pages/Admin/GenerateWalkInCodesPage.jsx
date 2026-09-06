import React, { useState } from 'react';
import '../../style/GenerateWalkInCodesPage.css';

const GenerateWalkInCodesPage = ({
  userRole = 'المدير العام',
  onBack,
  onPrint,
}) => {
  const [count, setCount] = useState('50');
  const [startCode, setStartCode] = useState('W-0001');

  // نماذج بطاقات الـ QR المخففة
  const sampleCodes = Array.from({ length: 12 }, (_, i) => {
    const num = (i + 1).toString().padStart(4, '0');
    return `W-${num}`;
  });

  const handleGenerate = (e) => {
    e.preventDefault();
    // تنفيذ عملية توليد الرموز هنا
  };

  return (
    <div className="gwic-viewport">
      
      {/* Top Application Header */}
      <header className="gwic-header">
        
        
        <div className="gwic-header-brand">
          <div className="gwic-brand-text">
            <span className="gwic-brand-title">وجهتك الأكاديمية 2</span>
            <span className="gwic-brand-subtitle">لوحة التحكم</span>
          </div>
          <div className="gwic-header-user">
          <span className="gwic-user-badge">{userRole}</span>
        </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="gwic-main-container">
        
        {/* Back Button Link */}
        <div className="gwic-back-wrapper">
          <button type="button" className="gwic-back-btn" onClick={onBack}>
            <span className="gwic-back-arrow">←</span> رجوع
          </button>
        </div>

        {/* Top Control Form Card */}
        <div className="gwic-card-panel">
          <h1 className="gwic-panel-title">توليد دفعة رموز جديدة (Walk-in)</h1>

          <form onSubmit={handleGenerate} className="gwic-generate-form">
            <div className="gwic-form-row">
              
              <div className="gwic-field-group">
                <label className="gwic-field-label" htmlFor="gwic-count-input">
                  عدد الرموز
                </label>
                <input
                  id="gwic-count-input"
                  type="text"
                  className="gwic-input-field gwic-input-center"
                  value={count}
                  onChange={(e) => setCount(e.target.value)}
                />
              </div>

              <div className="gwic-field-group">
                <label className="gwic-field-label" htmlFor="gwic-start-input">
                  يبدأ من الرقم
                </label>
                <input
                  id="gwic-start-input"
                  type="text"
                  className="gwic-input-field gwic-input-center"
                  value={startCode}
                  onChange={(e) => setStartCode(e.target.value)}
                  dir="ltr"
                />
              </div>

              <div className="gwic-action-group">
                <button type="submit" className="gwic-submit-btn">
                  توليد
                </button>
              </div>

            </div>
          </form>
        </div>

        {/* Output Section */}
        <div className="gwic-output-header">
          <h2 className="gwic-batch-title">
            دفعة اليوم — ٥٠ رمزاَ (W-0001 إلى W-0050)
          </h2>
          <button type="button" className="gwic-print-btn" onClick={onPrint}>
            طباعة الدفعة
          </button>
        </div>

        {/* QR Codes Grid Card */}
        <div className="gwic-card-panel gwic-qr-panel">
          <div className="gwic-qr-grid">
            {sampleCodes.map((code) => (
              <div key={code} className="gwic-qr-card">
                {/* Simulated Stylized QR Graphic */}
                <div className="gwic-qr-graphic">
                  <div className="gwic-qr-corner gwic-qr-tl"></div>
                  <div className="gwic-qr-corner gwic-qr-tr"></div>
                  <div className="gwic-qr-corner gwic-qr-bl"></div>
                  <div className="gwic-qr-center-dots">
                    <span className="gwic-qr-dot d1"></span>
                    <span className="gwic-qr-dot d2"></span>
                    <span className="gwic-qr-dot d3"></span>
                    <span className="gwic-qr-dot d4"></span>
                    <span className="gwic-qr-dot d5"></span>
                  </div>
                </div>
                <span className="gwic-qr-code-text">{code}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Helper Note */}
        <p className="gwic-footer-instruction">
          اطبع هاي الورقة وقصها لبطاقات مفردة، وسلّمها لموظف الاستقبال قبل بداية الفعالية.
        </p>

      </main>
    </div>
  );
};

export default GenerateWalkInCodesPage;