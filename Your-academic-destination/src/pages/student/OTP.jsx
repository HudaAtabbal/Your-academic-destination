import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import { apiPost, ApiError } from "../../api/api";
import { clearRegistrationData } from "../../api/RegistrationStorage";
import "../../style/OTP.css";

const OTP = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const autoResendDone = useRef(false);

  const [otp, setOtp] = useState(["", "", "", ""]);
  const [status, setStatus] = useState("idle"); // idle | error | success
  const [error, setError] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const inputRefs = useRef([]);

  const verifyCode = async (fullCode) => {
    const uniqueCode = localStorage.getItem("pendingStudentCode");

    if (!uniqueCode) {
      setStatus("error");
      setError("في مشكلة بجلسة التسجيل، يرجى الرجوع والتسجيل من جديد");
      return;
    }

    setIsVerifying(true);

    try {
      const response = await apiPost("/students/otp/verify", {
        unique_code: uniqueCode,
        otp: fullCode,
      });

      setStatus("success");
      setError("");

      clearRegistrationData();

      localStorage.setItem("studentCode", uniqueCode);
      localStorage.removeItem("pendingStudentCode");

      if (response.full_name) {
        localStorage.setItem("studentName", response.full_name);
      }

      setTimeout(() => {
        navigate("/my-card");
      }, 600);
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof ApiError
          ? err.message
          : "صار خطأ غير متوقع، حاولي مرة تانية",
      );
      setOtp(["", "", "", ""]);
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

    if (status === "error") {
      setStatus("idle");
      setError("");
    }

    if (value !== "") {
      if (index < 3) {
        inputRefs.current[index + 1].focus();
      } else {
        const fullCode = newOtp.join("");
        if (fullCode.length === 4) {
          verifyCode(fullCode);
        }
      }
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const fullCode = otp.join("");

    if (fullCode.length < 4) {
      setStatus("error");
      setError("يرجى إدخال الرمز كاملاً");
      return;
    }

    verifyCode(fullCode);
  };

  // إرسال رمز جديد (يدوي من الزر أو تلقائي عند الرجوع وهو غير موثّق)
  const sendResend = async () => {
    const uniqueCode = localStorage.getItem("pendingStudentCode");
    if (!uniqueCode) {
      setError("في مشكلة بجلسة التسجيل، يرجى الرجوع والتسجيل من جديد");
      return;
    }

    setStatus("idle");
    setError("");
    setResendMessage("");
    setOtp(["", "", "", ""]);
    inputRefs.current[0]?.focus();

    try {
      await apiPost("/students/otp/resend", { unique_code: uniqueCode });
      setResendMessage("تم ارسال رمز جديد عبر SMS");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "تعذّر إعادة الإرسال، حاول مرة أخرى",
      );
    }
  };

  const handleResend = () => sendResend();

  // إرسال تلقائي مرة وحدة لما الطالب يرجع وهو غير موثّق
  useEffect(() => {
    if (location.state?.autoResend && !autoResendDone.current) {
      autoResendDone.current = true;
      // نمسح الـ state حتى ما يتكرر الإرسال عند الريفريش
      navigate(location.pathname, { replace: true, state: null });
      sendResend();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <HeaderStep
          title="أدخل رمز التحقق"
          stepText="سيصلك الرمز عبر SMS"
        />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container">
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
                  className={`otp-input ${digit ? "filled" : ""} ${
                    status === "error" ? "otp-error" : ""
                  } ${status === "success" ? "otp-success" : ""}`}
                  autoFocus={index === 0}
                />
              ))}
            </div>

            {error && <p className="error-message">{error}</p>}
            {resendMessage && !error && (
              <p className="resend-success-message">{resendMessage}</p>
            )}

            <p className="resend-text">
              لم يصلك رمز؟{" "}
              <button
                type="button"
                onClick={handleResend}
                className="resend-btn"
              >
                أعد الإرسال
              </button>
            </p>

            <button
              type="button"
              className="otp-back-btn"
              onClick={() => navigate("/register-step3")}
            >
              تعديل رقم الهاتف
            </button>

            <div className="actions">
              <button
                type="submit"
                className={`btn btn-primary ${status === "success" ? "btn-success" : ""}`}
                disabled={isVerifying}
              >
                {isVerifying ? "جاري التحقق..." : "فعّل واستلم بطاقتي"}
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
};

export default OTP;