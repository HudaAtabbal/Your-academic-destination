import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import StepProgress from '../../components/StepProgress';
import { apiPost, ApiError } from '../../api/api';
import { getRegistrationData, updateRegistrationData, clearRegistrationData } from '../../api/RegistrationStorage';
import "../../style/RegisterStep3Page.css";

const RegisterStep3Page = () => {
  const navigate = useNavigate();

  // بنحمّل رقم الهاتف المحفوظ لو الطالب رجع لهالخطوة بعد ريفريش
  const [phoneNumber, setPhoneNumber] = useState(() => getRegistrationData().contactId || "");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // حفظ تلقائي بكل تغيير بالرقم — بلا ما ننتظر ضغطة الإرسال
  useEffect(() => {
    if (phoneNumber) {
      updateRegistrationData({ contactPlatform: "whatsapp", contactId: phoneNumber });
    }
  }, [phoneNumber]);

  const handleSubmit = async (e) => {
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

    setError("");
    setIsSubmitting(true);

    // بنجمّع بيانات الخطوات السابقة من السلة (رقم الهاتف أصلاً محفوظ فيها عبر الحفظ التلقائي فوق)
    const previousSteps = getRegistrationData();

    const payload = {
      full_name: previousSteps.fullName,
      birth_date: previousSteps.birthDate,
      certificate_year: Number(previousSteps.certificateYear),
      certificate_type: previousSteps.certificateType,
      average_score: Number(previousSteps.averageScore),
      initial_preferred_major: previousSteps.initialPreferredMajor,
      contact_platform: "whatsapp",
      contact_id: value,
    };

    try {
      const response = await apiPost("/students/register", payload);

      // بنخزّن الكود الفريد حتى صفحة OTP تقدر تتحقق منه، وMyCard تعرضه بعدين
      localStorage.setItem("studentCode", response.unique_code);

      // خلصت مهمة السلة المؤقتة — منضفيها حتى ما تضل بيانات قديمة لو حدا رجع يسجّل من جديد
      clearRegistrationData();

      navigate("/otp");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("صار خطأ غير متوقع، حاولي مرة تانية");
      }
    } finally {
      setIsSubmitting(false);
    }
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
            سوف نرسل رمز تحقق عبر SMS.
          </p>

          <form onSubmit={handleSubmit} className="rs3-form-container">
            {/* Phone Input */}
            <div className="rs3-input-group">
              <label htmlFor="phoneNumber" className="rs3-input-label">
                رقم الهاتف
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
              <button type="submit" className="rs3-btn rs3-btn-primary" disabled={isSubmitting}>
                {isSubmitting ? "جاري الإرسال..." : "أرسل رمز التحقق"}
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
};

export default RegisterStep3Page;