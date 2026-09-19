import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import HeaderStep from "../../components/HeaderStep";
import SurveyQuestionOne from "../../components/SurveyQuestionOne";
import SurveyQuestionTwo from "../../components/SurveyQuestionTwo";
import BottomNav from "../../components/BottomNav";
import { apiGet, apiPost, ApiError } from "../../api/api";
import { showToast } from "../../api/toast";
import { COLLEGE_OPTIONS } from "../../api/colleges";
import "../../style/Survey.css";

const Survey = ({ active = false }) => {
  const navigate = useNavigate();
  const [q1Option, setQ1Option] = useState("decided");
  const [q2Major, setQ2Major] = useState("medicine");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // حالتا الجاهزية: null = لسا عم نتحقق / كائن = موجموع (تبقى مدمجة بالإجابة)
  const [eligibility, setEligibility] = useState(null);

  // القيم (id) مطابقة بالحرف لـ enum College بالباك — من المصدر الموحّد (src/api/colleges.js)
  const majors = COLLEGE_OPTIONS;

  const isUndecided = q1Option === "undecided";

  const studentCode = localStorage.getItem("studentCode");

  // شروط تعبئة الاستبيان: لازم الطالب يكون فات من بوابة الجامعة (campus_entry)
  // وحضر نشاط أكاديمي واحد على الأقل (محاضرة / جولة بالكلية / استشارة فردية).
  // بنسأل الباك عن الجاهزية عند تفعيل التاب — بتظهر للطالب شو الناقص.
  useEffect(() => {
    if (!active || !studentCode) return;

    let cancelled = false;
    apiGet(`/survey/${studentCode}/eligibility`)
      .then((res) => {
        if (!cancelled) setEligibility(res);
      })
      .catch(() => {
        if (!cancelled) setEligibility(null);
      });
    return () => {
      cancelled = true;
    };
  }, [active, studentCode]);

  const missingConditions = () => {
    const missing = [];
    if (eligibility && !eligibility.campus_entry) missing.push("الفوت من بوابة الجامعة");
    if (eligibility && !eligibility.activity)
      missing.push("حضور نشاط أكاديمي (محاضرة / جولة بالكلية / استشارة فردية)");
    return missing;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

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

      showToast("شكراً! تم تسجيل إجاباتك بنجاح", "success");
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

  // لو الطالب عبّى الاستبيان مسبقاً — ما منعرض الفورم إطلاقاً
  if (eligibility && eligibility.answered) {
    return (
      <div className="card-wrapper">
        <div className="card-container">
          <HeaderStep
            title="سؤالان أخيران قبل الانتهاء"
            stepText="هذه كل المعلومات المطلوبة منك"
          />

          <main className="card-body">
            <form className="form-container">
              <p className="survey-already-notice">
                تم تعبئة الاستبيان سابقاً، شكراً لمشاركتك!
              </p>
            </form>
          </main>

          <BottomNav />
        </div>
      </div>
    );
  }

  const notEligible =
    eligibility && !eligibility.eligible && !eligibility.answered;

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <HeaderStep
          title="سؤالان أخيران قبل الانتهاء"
          stepText="هذه كل المعلومات المطلوبة منك"
        />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container">
            <p className="survey-notice">
              يُعبّى الاستبيان مرة واحدة عند الانتهاء من وجهتك الأكاديمية
            </p>

            {notEligible && (
              <div className="survey-eligibility-message">
                <p>ما فيك تعبّي الاستبيان بعد، لسا ناقص:</p>
                <ul>
                  {missingConditions().map((cond) => (
                    <li key={cond}>{cond}</li>
                  ))}
                </ul>
              </div>
            )}

            <SurveyQuestionOne selectedOption={q1Option} onSelect={setQ1Option} />

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
                disabled={isSubmitting || notEligible}
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