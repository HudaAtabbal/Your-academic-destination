import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import StepProgress from '../../components/Stepprogress';
import "../../style/RegisterStep3Page.css";

const RegisterStep3Page = () => {
  const navigate = useNavigate();

  const [channel, setChannel] = useState("sms");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const value = phoneNumber.trim();

    // الحقل فارغ
    if (!value) {
      setError(
        channel === "sms"
          ? "يرجى إدخال رقم الهاتف"
          : "يرجى إدخال معرف التيليغرام",
      );
      return;
    }

    // التحقق من رقم الهاتف
    if (channel === "sms") {
      const phoneRegex = /^09\d{8}$/;

      if (!phoneRegex.test(value)) {
        setError("يرجى إدخال رقم هاتف صحيح مكون من 10 أرقام ويبدأ بـ 09");
        return;
      }
    }

    if (channel === "telegram") {
      const telegramRegex = /^@[A-Za-z0-9_]+$/;

      if (!telegramRegex.test(value)) {
        setError(
          "معرف التيليغرام يجب أن يبدأ بـ @ ويحتوي على أحرف إنجليزية وأرقام فقط"
        );
        return;
      }
    }

    // إذا وصلنا لهون فالبيانات صحيحة
    setError("");

    // إرسال رمز التحقق
    console.log("إرسال رمز التحقق عبر:", channel);
    console.log("الرقم/المعرف:", value);

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
            سوف نرسل رمز تحقق عبر الوسيلة يلي تختارها.
          </p>

          <form onSubmit={handleSubmit} className="rs3-form-container">
            {/* Channel Selection */}
            <div className="rs3-channel-group">
              <label className="rs3-input-label">القناة</label>

              <div className="rs3-channel-options">
                <button
                  type="button"
                  className={`rs3-channel-btn ${
                    channel === "sms" ? "selected" : ""
                  }`}
                  onClick={() => {
                    setChannel("sms");
                    setPhoneNumber("");
                    setError("");
                  }}
                >
                  SMS
                </button>

                <button
                  type="button"
                  className={`rs3-channel-btn ${
                    channel === "telegram" ? "selected" : ""
                  }`}
                  onClick={() => {
                    setChannel("telegram");
                    setPhoneNumber("");
                    setError("");
                  }}
                >
                  تيليغرام
                </button>
              </div>
            </div>

            {/* Dynamic Input */}
            <div className="rs3-input-group">
              <label htmlFor="phoneNumber" className="rs3-input-label">
                {channel === "sms" ? "رقم الهاتف" : "معرف التيليغرام"}
              </label>

              <input
                id="phoneNumber"
                name="phoneNumber"
                type="tel"
                placeholder={channel === "sms" ? "09xxxxxxxx" : "@xxxxxxx"}
                value={phoneNumber}
                maxLength={channel === "sms" ? 10 : undefined}
                onChange={(e) => {
                  let value = e.target.value;

                  if (channel === "sms") {
                    // السماح بالأرقام فقط
                    value = value.replace(/\D/g, "");

                    // الحد الأقصى 10 أرقام
                    value = value.slice(0, 10);
                  }

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