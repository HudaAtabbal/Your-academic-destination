import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import StepProgress from '../../components/StepProgress';
import "../../style/RegisterStep3Page.css";

const RegisterStep3Page = () => {
  const navigate = useNavigate();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const value = phoneNumber.trim();

    // الحقل فارغ
    if (!value) {
      setError("يرجى إدخال رقم الواتساب");
      return;
    }

    // التحقق من رقم الواتساب
    const phoneRegex = /^09\d{8}$/;
    if (!phoneRegex.test(value)) {
      setError("يرجى إدخال رقم واتساب صحيح مكون من 10 أرقام ويبدأ بـ 09");
      return;
    }

    // إذا وصلنا لهون فالبيانات صحيحة
    setError("");

    // إرسال رمز التحقق (channel ثابتة دايماً whatsapp — مطابقة لـ enum الباك)
    console.log("إرسال رمز التحقق عبر:", "whatsapp");
    console.log("الرقم:", value);

    navigate("/otp");
  };

  return (
    <div className="rs3-card-wrapper">
      <div className="rs3-card-container">
        <HeaderStep
          title="كيف نوصلك؟"
          stepText="خطوة 3 من 3"
          onBack={() => window.history.back()}
        />

        <StepProgress totalSteps={3} currentStep={3} />

        <main className="rs3-card-body">
          <p className="rs3-step-description">
            سوف نرسل رمز تحقق عبر الواتساب.
          </p>

          <form onSubmit={handleSubmit} className="rs3-form-container">
            {/* Phone Input */}
            <div className="rs3-input-group">
              <label htmlFor="phoneNumber" className="rs3-input-label">
                رقم الواتساب
              </label>

              <input
                id="phoneNumber"
                name="phoneNumber"
                type="tel"
                placeholder="09xxxxxxxx"
                value={phoneNumber}
                maxLength={10}
                onChange={(e) => {
                  let value = e.target.value;
                  // السماح بالأرقام فقط
                  value = value.replace(/\D/g, "");
                  // الحد الأقصى 10 أرقام
                  value = value.slice(0, 10);

                  setPhoneNumber(value);
                  setError("");
                }}
                className={`rs3-custom-input rs3-phone-input ${
                  error ? "rs3-input-error" : ""
                }`}
                dir="ltr"
              />

              {error && <p className="rs3-error-message">{error}</p>}
            </div>

            {/* Action Button */}
            <div className="rs3-actions">
              <button type="submit" className="rs3-btn rs3-btn-primary">
                أرسل رمز التحقق
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
};

export default RegisterStep3Page;