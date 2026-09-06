import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../components/HeaderStep";
import StepProgress from '../components/Stepprogress';
import "../style/RegisterStep3Page.css";

const RegisterStep3Page = () => {
  const navigate = useNavigate();

  const [channel, setChannel] = useState("whatsapp");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const value = phoneNumber.trim();

    // الحقل فارغ
    if (!value) {
      setError(
        channel === "whatsapp"
          ? "يرجى إدخال رقم الواتساب"
          : "يرجى إدخال معرف التيليغرام",
      );
      return;
    }

    // التحقق من رقم الواتساب
    if (channel === "whatsapp") {
      const phoneRegex = /^09\d{8}$/;

      if (!phoneRegex.test(value)) {
        setError("يرجى إدخال رقم واتساب صحيح مكون من 10 أرقام ويبدأ بـ 09");
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
    <div className="card-wrapper">
      <div className="card-container">
        <HeaderStep
          title="كيف نوصلك؟"
          stepText="خطوة 3 من 3"
          onBack={() => window.history.back()}
        />

        <StepProgress totalSteps={3} currentStep={3} />

        <main className="card-body">
          <p className="step-description">
            سوف نرسل رمز تحقق عبر الوسيلة يلي تختارها.
          </p>

          <form onSubmit={handleSubmit} className="form-container">
            {/* Channel Selection */}
            <div className="channel-group">
              <label className="input-label">القناة</label>

              <div className="channel-options">
                <button
                  type="button"
                  className={`channel-btn ${
                    channel === "whatsapp" ? "selected" : ""
                  }`}
                  onClick={() => {
                    setChannel("whatsapp");
                    setPhoneNumber("");
                    setError("");
                  }}
                >
                  واتساب
                </button>

                <button
                  type="button"
                  className={`channel-btn ${
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
            <div className="input-group">
              <label htmlFor="phoneNumber" className="input-label">
                {channel === "whatsapp" ? "رقم الواتساب" : "معرف التيليغرام"}
              </label>

              <input
                id="phoneNumber"
                name="phoneNumber"
                type="tel"
                placeholder={channel === "whatsapp" ? "09xxxxxxxx" : "@xxxxxxx"}
                value={phoneNumber}
                maxLength={channel === "whatsapp" ? 10 : undefined}
                onChange={(e) => {
                  let value = e.target.value;

                  if (channel === "whatsapp") {
                    // السماح بالأرقام فقط
                    value = value.replace(/\D/g, "");

                    // الحد الأقصى 10 أرقام
                    value = value.slice(0, 10);
                  }

                  setPhoneNumber(value);
                  setError("");
                }}
                className={`custom-input phone-input ${
                  error ? "input-error" : ""
                }`}
                dir="ltr"
              />

              {error && <p className="error-message">{error}</p>}
            </div>

            {/* Action Button */}
            <div className="actions">
              <button type="submit" className="btn btn-primary">
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