import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import SurveyQuestionOne from '../../components/SurveyQuestionOne';
import SurveyQuestionTwo from '../../components/SurveyQuestionTwo';
import BottomNav from '../../components/BottomNav';
import { apiPost, ApiError } from '../../api/api';
import '../../style/Survey.css';

const Survey = () => {
  const navigate = useNavigate();
  const [q1Option, setQ1Option] = useState('decided');
  const [q2Major, setQ2Major] = useState('college_placeholder_1');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ⚠️ مؤقت للتجربة فقط — القيم مطابقة لـ enum College بالباك (placeholders حالياً).
  // لما يجهز enum الـ42 كلية الفعلي، بدّلي هون بس (name = القيمة الفعلية بالـ enum الجديد،
  // ومنيح تضيفي حقل منفصل للعرض بالعربي إذا بدك تعرضي اسم الكلية الحقيقي بالواجهة).
 const majors = [
    { id: 'medicine', name: 'طب البشري' },
    { id: 'dentistry', name: 'طب الأسنان' },
    { id: 'pharmacy', name: 'صيدلة' },
    { id: 'health_sciences', name: 'علوم صحية' },
    { id: 'informatics', name: 'هندسة المعلوماتية' },
    { id: 'civil', name: 'هندسة مدنية' },
    { id: 'architecture', name: 'هندسة معمارية' },
    { id: 'agriculture', name: 'هندسة الزراعة' },
    { id: 'electrical_mechanical_eng', name: 'هندسة كهربائية وميكانيكية' },
    { id: 'chemical_food_eng', name: 'هندسة كيميائية وغذائية' },
    { id: 'economics', name: 'اقتصاد' },
    { id: 'tourism', name: 'سياحة' },
    { id: 'music', name: 'موسيقى' },
    { id: 'literature', name: 'اداب' },
    { id: 'education', name: 'تربية' },
    { id: 'science', name: 'علوم' },
    { id: 'applied_science', name: 'تطبيقية' },
    { id: 'law', name: 'حقوق' },
    { id: 'institute_agriculture', name: 'معهد تقاني زراعي' },
    { id: 'institute_desert_affairs', name: 'معهد تقاني لشؤون البادية والتصحر' },
    { id: 'institute_engineering', name: 'معهد تقاني هندسي' },
    { id: 'institute_health', name: 'معهد تقاني صحي' },
    { id: 'institute_dentistry', name: 'معهد تقاني طب اسنان' },
    { id: 'institute_applied_industries', name: 'معهد تقاني صناعات تطبيقية' },
    { id: 'institute_computer', name: 'معهد تقاني حاسوب' },
  ];

  const isUndecided = q1Option === 'undecided';

  const handleSubmit = async (e) => {
    e.preventDefault();

    const studentCode = localStorage.getItem('studentCode');
    if (!studentCode) {
      setError('في مشكلة بجلستك، يرجى الرجوع والتسجيل من جديد');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await apiPost(`/survey/${studentCode}`, {
        opinion_change: q1Option,
        preferred_major: isUndecided ? null : q2Major,
      });

      navigate('/my-card');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
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
          title="سؤالان قبل ما تروح"
          stepText="هاد كل شي محتاجينه منك"
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
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'جاري الإرسال...' : 'أرسل'}
              </button>
              <button type="button" onClick={handleSkip} className="btn btn-secondary">
                لاحقاً
              </button>
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