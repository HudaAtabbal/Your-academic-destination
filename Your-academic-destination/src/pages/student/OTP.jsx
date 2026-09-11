import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import { apiPost, ApiError } from '../../api/api';
import '../../style/OTP.css';

const OTP = () => {
  const navigate = useNavigate();

  const [otp, setOtp] = useState(['', '', '', '']);
  const [status, setStatus] = useState('idle'); // idle | error | success
  const [error, setError] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [resendMessage, setResendMessage] = useState('');
  const inputRefs = useRef([]);

  // منطق التحقق نفسه، منفصل حتى يستخدم تلقائياً وبالزر كمان
  const verifyCode = async (fullCode) => {
    const uniqueCode = localStorage.getItem('studentCode');

    if (!uniqueCode) {
      // ما في كود مخزّن أصلاً — يعني الطالب وصل لهون بدون ما يخلّص التسجيل
      setStatus('error');
      setError('في مشكلة بجلسة التسجيل، يرجى الرجوع والتسجيل من جديد');
      return;
    }

    setIsVerifying(true);

    try {
      const response = await apiPost('/students/otp/verify', {
        unique_code: uniqueCode,
        otp: fullCode,
      });

      setStatus('success');
      setError('');

      // بنخزّن اسم الطالب كمان حتى صفحة البطاقة (MyCard) تعرضه الحقيقي بدل الموك
      if (response.full_name) {
        localStorage.setItem('studentName', response.full_name);
      }

      // نعطي فرصة يشوف اللون الأخضر قبل ما ننتقل
      setTimeout(() => {
        navigate('/my-card');
      }, 600);
    } catch (err) {
      setStatus('error');
      setError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
      setOtp(['', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsVerifying(false);
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

  const handleResend = async () => {
    const uniqueCode = localStorage.getItem('studentCode');
    if (!uniqueCode) {
      setError('في مشكلة بجلسة التسجيل، يرجى الرجوع والتسجيل من جديد');
      return;
    }

    setStatus('idle');
    setError('');
    setResendMessage('');
    setOtp(['', '', '', '']);
    inputRefs.current[0]?.focus();

    try {
      await apiPost('/students/otp/resend', { unique_code: uniqueCode });
      setResendMessage('تم إرسال رمز جديد لواتسابك');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'تعذّر إعادة الإرسال، حاولي مرة تانية');
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="أدخل رمز التحقق"
          stepText="سيصلك الرمز عبر SMS"
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
                  disabled={isVerifying}
                  className={`otp-input ${digit ? 'filled' : ''} ${
                    status === 'error' ? 'otp-error' : ''
                  } ${status === 'success' ? 'otp-success' : ''}`}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            {error && <p className="error-message">{error}</p>}
            {resendMessage && !error && <p className="resend-success-message">{resendMessage}</p>}

            {/* Resend Action */}
            <p className="resend-text">
               لم يصلك رمز؟{' '}
              <button type="button" onClick={handleResend} className="resend-btn">
                أعد الإرسال
              </button>
            </p>

            {/* Submit Button */}
            <div className="actions">
              <button
                type="submit"
                className={`btn btn-primary ${status === 'success' ? 'btn-success' : ''}`}
                disabled={isVerifying}
              >
                {isVerifying ? 'جاري التحقق...' : 'فعّل واستلم بطاقتي'}
              </button>
            </div>

          </form>
        </main>

      </div>
    </div>
  );
};

export default OTP;