import React from 'react';
import QRCode from 'react-qr-code'; // يمكنك استخدام مكتبة react-qr-code أو صورة QR جاهزة
import logo from '../assets/English logo white-01.png';
import '../style/MyCard.css';

const MyCard = () => {
  const cardData = {
    name: 'عمر أحمد العسورة',
    code: 'R-0248',
    status: 'بانتظار التفعيل',
    qrValue: 'R-0248-OMAR-ALASOORA'
  };

  const handleSaveCard = () => {
    // كود حفظ البطاقة أو التقاط شاشة
  };

  return (
    <div className="card-wrapper">
      <div className="card-container scrollable">
        
        {/* Header */}
        <header className="card-main-header">
            <div className="header-text">
            <h1 className="brand-name">بطاقتي</h1>
            <span className="brand-subtitle">وجهتك الأكاديمية 2 • جامعة حمص</span>
          </div>
          <div className="header-icon">
            <img src={logo} alt="شعار" className="header-logo" />
          </div>
          
        </header>

        <main className="card-body">
          
          {/* Digital ID Card Section */}
          <div className="id-card-box">
            <div className="qr-wrapper">
              <QRCode 
                value={cardData.qrValue} 
                size={140}
                fgColor="#134F47"
                bgColor="#FFFFFF"
                level="L"
              />
            </div>
            <h2 className="user-name">{cardData.name}</h2>
            <p className="user-code">{cardData.code}</p>
            <div className="status-badge">
              {cardData.status}
            </div>
          </div>

          {/* Features Info Box */}
          <div className="info-card-box">
            <h3 className="info-box-title">شو بتعمل هالبطاقة؟</h3>
            <ul className="info-list">
              <li>بتفتحلك الدخول عبوابة الحرم الجامعي</li>
              <li>بتسجّل حضورك بأي محاضرة أو جولة أو استشارة</li>
              <li>تعمل بدون إنترنت &mdash; لقطة شاشة كافية</li>
            </ul>
          </div>

          {/* Action Button */}
          <div className="actions">
            <button type="button" onClick={handleSaveCard} className="btn btn-primary">
              احفظ البطاقة
            </button>
          </div>

        </main>

      </div>
    </div>
  );
};

export default MyCard;