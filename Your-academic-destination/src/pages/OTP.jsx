import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../components/HeaderStep';
import '../style/OTP.css';

// موك: الكود الصحيح للتجربة فقط، لازم يتبدل بطلب فعلي للباك اند لاحقاً
const MOCK_CORRECT_OTP = '1234';

const OTP = () => {
  const navigate = useNavigate();

  const [otp, setOtp] = useState(['', '', '', '']);
  const [status, setStatus] = useState('idle'); // idle | error | success
  const [error, setError] = useState('');
  const inputRefs = useRef([]);

  // منطق التحقق نفسه، منفصل حتى يستخدم تلقائياً وبالزر كمان
  const verifyCode = (fullCode) => {
    // إرسال الكود للتحقق (حالياً موك، لاحقاً بيصير API call فعلي)
    if (fullCode === MOCK_CORRECT_OTP) {
      setStatus('success');
      setError('');

      // نعطي فرصة يشوف اللون الأخضر قبل ما ننتقل
      setTimeout(() => {
        navigate('/home');
      }, 600);
    } else {
      setStatus('error');
      setError('الرمز المدخل غير صحيح ، حاول مرة اخرى ');
      setOtp(['', '', '', '']);
      inputRefs.current[0]?.focus();
    }
  };

  const handleChange = (index, value) => {
    if (value.length > 1) value = value[value.length - 1];

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // لما يبلش يدخل من جديد بعد خطأ، بننضف حالة الخطأ
    if (status === 'error') {
      setStatus('idle');
      setError('');
    }

    if (value !== '') {
      if (index < 3) {
        // الانتقال التلقائي للحقل التالي عند الإدخال
        inputRefs.current[index + 1].focus();
      } else {
        // آخر خانة اتعبت: نتحقق تلقائياً بدون ما ننتظر ضغطة الزر
        const fullCode = newOtp.join('');
        if (fullCode.length === 4) {
          verifyCode(fullCode);
        }
      }
    }
  };

  const handleKeyDown = (index, e) => {
    // الرجوع للحقل السابق عند ضغط Backspace
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const fullCode = otp.join('');

    if (fullCode.length < 4) {
      setStatus('error');
      setError('يرجى إدخال الرمز كاملاً');
      return;
    }

    verifyCode(fullCode);
  };

  const handleResend = () => {
    setStatus('idle');
    setError('');
    setOtp(['', '', '', '']);
    inputRefs.current[0]?.focus();
    // إعادة إرسال الرمز (لاحقاً API call فعلي)
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="أدخل رمز التحقق"
          stepText="وصلك عالواتساب هلق"
          onBack={() => window.history.back()}
        />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container">

            {/* OTP Input Boxes */}
            <div className="otp-container" dir="ltr">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => (inputRefs.current[index] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className={`otp-input ${digit ? 'filled' : ''} ${
                    status === 'error' ? 'otp-error' : ''
                  } ${status === 'success' ? 'otp-success' : ''}`}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            {error && <p className="error-message">{error}</p>}

            {/* Resend Action */}
            <p className="resend-text">
              ما وصلك شي؟{' '}
              <button type="button" onClick={handleResend} className="resend-btn">
                أعد الإرسال
              </button>
            </p>

            {/* Submit Button */}
            <div className="actions">
              <button
                type="submit"
                className={`btn btn-primary ${status === 'success' ? 'btn-success' : ''}`}
              >
                فعّل واستلم بطاقتي
              </button>
            </div>

          </form>
        </main>

      </div>
    </div>
  );
};

export default OTP;