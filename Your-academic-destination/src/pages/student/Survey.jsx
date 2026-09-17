import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import SurveyQuestionOne from "../../components/SurveyQuestionOne";
import SurveyQuestionTwo from "../../components/SurveyQuestionTwo";
import BottomNav from "../../components/BottomNav";
import { apiPost, ApiError } from "../../api/api";
import { COLLEGE_OPTIONS } from "../../api/colleges";
import "../../style/Survey.css";

const Survey = () => {
  const navigate = useNavigate();
  const [q1Option, setQ1Option] = useState("decided");
  const [q2Major, setQ2Major] = useState("medicine");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // القيم (id) مطابقة بالحرف لـ enum College بالباك — من المصدر الموحّد (src/api/colleges.js)
  const majors = COLLEGE_OPTIONS;

  const isUndecided = q1Option === "undecided";

  const handleSubmit = async (e) => {
    e.preventDefault();

    const studentCode = localStorage.getItem("studentCode");
    if (!studentCode) {
      setError("يوجد مشكلة في جلستك، يرجى الرجوع والتسجيل من جديد");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      await apiPost(`/survey/${studentCode}`, {
        opinion_change: q1Option,
        preferred_major: isUndecided ? null : q2Major,
      });

      navigate("/my-card");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "حدث خطأ غير متوقع، حاول مرة أخرى",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    window.history.back();
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <HeaderStep
          title="سؤالان أخيران قبل الانتهاء"
          stepText="هذه كل المعلومات المطلوبة منك"
          onBack={() => window.history.back()}
        />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container">
            <SurveyQuestionOne
              selectedOption={q1Option}
              onSelect={setQ1Option}
            />

            {!isUndecided && (
              <SurveyQuestionTwo
                selectedMajor={q2Major}
                onChange={setQ2Major}
                majorsList={majors}
              />
            )}

            <div className="actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? "جاري الإرسال..." : "أرسل"}
              </button>
              {/* <button type="button" onClick={handleSkip} className="btn btn-secondary">
                لاحقاً
              </button> */}
            </div>

            {error && <p className="survey-error-message">{error}</p>}
          </form>
        </main>

        <BottomNav />
      </div>
    </div>
  );
};

export default Survey;
