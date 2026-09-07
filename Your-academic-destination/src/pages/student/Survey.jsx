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
  const [q2Major, setQ2Major] = useState('الطب البشري');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const majors = [
    { id: 1, name: 'الطب البشري' },
    { id: 2, name: 'المعلوماتية' },
    { id: 3, name: 'الهندسة المعمارية' },
    { id: 4, name: 'الحقوق' },
    { id: 5, name: 'الصيدلة' },
    { id: 6, name: 'الهندسة المدنية' },
  ];

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
      // ⚠️ preferred_major بالباك لسا enum فيه بس قيمتين placeholder (مش الـ42 كلية الحقيقية)،
      // يعني إرسال اسم الكلية العربي (زي "الطب البشري") رح يفشل بـ 422 لحد ما يجهز enum الكليات الفعلي
      await apiPost(`/survey/${studentCode}`, {
        opinion_change: q1Option,
        preferred_major: q2Major,
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

            <SurveyQuestionTwo 
              selectedMajor={q2Major} 
              onChange={setQ2Major} 
              majorsList={majors} 
            />

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