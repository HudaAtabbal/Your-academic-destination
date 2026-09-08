import React, { useRef } from 'react';
import QRCode from 'react-qr-code'; // يمكنك استخدام مكتبة react-qr-code أو صورة QR جاهزة
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import '../../style/MyCard.css';

const MyCard = () => {
  const qrWrapperRef = useRef(null);

  // بنقرأ الكود من localStorage (اتخزن هناك بصفحة OTP بعد نجاح التحقق)
  // بدل ما يكون ثابت بالكود؛ الاسم لسا موك لحد ما نربط API فعلي يرجّعه
  const studentCode = localStorage.getItem('studentCode') || 'R-0248';
  const studentName = localStorage.getItem('studentName') || 'عمر أحمد العسورة';

  const cardData = {
    name: studentName,
    code: studentCode,
    status: 'بانتظار التفعيل',
  };

  const handleLogout = () => {
    localStorage.removeItem('studentCode');
    localStorage.removeItem('studentName');
    window.location.href = '/';
  };

  const handleSaveCard = () => {
    try {
      // بنلاقي الـ SVG يلي مكتبة react-qr-code رندرته جوا qr-wrapper
      const svg = qrWrapperRef.current?.querySelector('svg');
      if (!svg) {
        console.error('ما تم إيجاد عنصر الـ SVG جوا qr-wrapper');
        return;
      }

      // بعض المتصفحات محتاجة width/height صريحة على الـ SVG
      // (بدون هيك الصورة بتطلع بحجم 0 والكانفاس بيصير فاضي)
      const qrSize = 140; // نفس القيمة يلي مررناها لـ <QRCode size={140} />
      svg.setAttribute('width', qrSize);
      svg.setAttribute('height', qrSize);

      const svgData = new XMLSerializer().serializeToString(svg);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const svgUrl = URL.createObjectURL(svgBlob);

      const img = new Image();

      img.onerror = (err) => {
        console.error('فشل تحميل صورة الـ SVG', err);
        URL.revokeObjectURL(svgUrl);
      };

      img.onload = () => {
        try {
          const scale = 4;
          const width = (img.width || qrSize) * scale;
          const height = (img.height || qrSize) * scale;

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;

          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#FFFFFF';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

          URL.revokeObjectURL(svgUrl);

          const pngUrl = canvas.toDataURL('image/png');

          const link = document.createElement('a');
          link.href = pngUrl;
          link.download = `${cardData.code}-QR.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (err) {
          console.error('فشل تحويل الصورة أو تنزيلها', err);
        }
      };

      img.src = svgUrl;
    } catch (err) {
      console.error('خطأ عام أثناء حفظ البطاقة', err);
    }
  };

  return (
    <div className="mc-card-wrapper">
      <div className="mc-card-container">

        <HeaderStep
          title="بطاقتي"
          stepText="وجهتك الأكاديمية 2 • جامعة حمص"
          onBack={() => window.history.back()}
        />

        <main className="mc-card-body">

          {/* Digital ID Card Section */}
          <div className="mc-id-card-box">
            <div className="mc-qr-wrapper" ref={qrWrapperRef}>
              {/* الـ QR بيحمل بس unique_code تبع الطالب (زي R-0248)،
                  بدون أي بيانات شخصية زي الاسم. لما موظف السكانر يمسحه،
                  الباك اند هو يلي بيرجّع اسم الطالب وكل بياناته من قاعدة البيانات. */}
              <QRCode
                value={cardData.code}
                size={140}
                fgColor="#134F47"
                bgColor="#FFFFFF"
                level="L"
              />
            </div>
            <h2 className="mc-user-name">{cardData.name}</h2>
            <p className="mc-user-code">{cardData.code}</p>
            <div className="mc-status-badge">
              {cardData.status}
            </div>
          </div>

          {/* Features Info Box */}
          <div className="mc-info-card-box">
            <h3 className="mc-info-box-title">ماذا تفعل هذه البطاقة ؟</h3>
            <ul className="mc-info-list">
              <li>تسمح لك بالدخول عند بوابة الحرم الجامعي</li>
              <li>تسجّل حضورك بأي محاضرة أو جولة أو استشارة</li>
              <li>تعمل بدون إنترنت &mdash; لقطة شاشة كافية</li>
            </ul>
          </div>

          {/* Action Button */}
          <div className="mc-actions">
            <button type="button" onClick={handleSaveCard} className="mc-btn mc-btn-primary">
              احفظ البطاقة
            </button>
          </div>

          {/* Logout Button */}
          <div className="mc-logout-actions">
            <button type="button" onClick={handleLogout} className="mc-btn mc-btn-logout">
              تسجيل خروج
            </button>
          </div>

        </main>

        <BottomNav />

      </div>
    </div>
  );
};

export default MyCard;