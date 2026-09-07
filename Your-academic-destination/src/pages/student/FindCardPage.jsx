import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import { apiPost, ApiError } from '../../api/api';
import '../../style/FindCardPage.css';

// بنطبّع النص قبل المقارنة (نشيل المسافات الزايدة، نوحّد حالة الأحرف) حتى المقارنة تكون مرنة شوي
const normalize = (text) => text.trim().replace(/\s+/g, ' ').toLowerCase();

const FindCardPage = () => {
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const name = fullName.trim();
    const phone = phoneNumber.trim();

    if (!name || !phone) {
      setError('يرجى تعبئة الاسم الثلاثي ورقم الواتساب');
      return;
    }

    const phoneRegex = /^09\d{8}$/;
    if (!phoneRegex.test(phone)) {
      setError('يرجى إدخال رقم واتساب صحيح مكون من 10 أرقام ويبدأ بـ 09');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const result = await apiPost('/students/lookup-by-contact', {
        contact_platform: 'whatsapp',
        contact_id: phone,
      });

      // الاسم هون طبقة تأكيد إضافية فوق رقم الهاتف
      if (normalize(result.full_name) !== normalize(name)) {
        setError('الاسم ما بيطابق رقم الهاتف يلي دخلتيه، تأكدي من الاثنين');
        return;
      }

      localStorage.setItem('studentCode', result.unique_code);
      localStorage.setItem('studentName', result.full_name);
      navigate('/my-card');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'ما لقينا حساب مرتبط بهالرقم، تأكدي منه وحاولي مرة تانية');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fcp-wrapper">
      <div className="fcp-container">
        <HeaderStep
          title="بطاقتي من قبل"
          stepText="دخّلي بياناتك لاسترجاع بطاقتك"
          onBack={() => window.history.back()}
        />

        <main className="fcp-body">
          <form onSubmit={handleSubmit} className="fcp-form" noValidate>
            <div className="fcp-input-group">
              <label htmlFor="fullName" className="fcp-label">الاسم الثلاثي</label>
              <input
                id="fullName"
                type="text"
                placeholder="مثال: عمر أحمد العسورة"
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  setError('');
                }}
                className={`fcp-input ${error ? 'fcp-input-error' : ''}`}
              />
            </div>

            <div className="fcp-input-group">
              <label htmlFor="phoneNumber" className="fcp-label">رقم الهاتف</label>
              <input
                id="phoneNumber"
                type="tel"
                placeholder="09xxxxxxxx"
                value={phoneNumber}
                maxLength={10}
                onChange={(e) => {
                  const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 10);
                  setPhoneNumber(digitsOnly);
                  setError('');
                }}
                className={`fcp-input ${error ? 'fcp-input-error' : ''}`}
                dir="ltr"
              />
            </div>

            {error && <span className="fcp-error-text">{error}</span>}

            <div className="fcp-actions">
              <button type="submit" className="fcp-btn" disabled={isSubmitting}>
                {isSubmitting ? 'جاري البحث...' : 'استرجاع البطاقة'}
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
};

export default FindCardPage;