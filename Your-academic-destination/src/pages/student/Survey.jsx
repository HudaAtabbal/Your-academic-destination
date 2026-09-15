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
  const [q2Major, setQ2Major] = useState('medicine');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // القيم (id) هون مطابقة بالحرف لـ enum College بالباك — نفس الترتيب المعتمد.
  const majors = [
    { id: 'medicine', name: 'الطب البشري' },
    { id: 'pharmacy', name: 'الصيدلة' },
    { id: 'dentistry', name: 'طب الأسنان' },
    { id: 'health_labs', name: 'علوم صحيّة مخابر' },
    { id: 'health_nutrition', name: 'علوم صحيّة تغذية' },
    { id: 'health_physiotherapy', name: 'علوم صحية علاج فيزيائي' },
    { id: 'mech_power_eng', name: 'هندسة قوى ميكانيكية' },
    { id: 'control_computer_eng', name: 'هندسة تحكم آلي وحواسيب' },
    { id: 'energy_eng', name: 'هندسة طاقة' },
    { id: 'mechatronics', name: 'ميكاترونك' },
    { id: 'telecom_eng', name: 'هندسة الاتصالات' },
    { id: 'metallurgy_eng', name: 'هندسة المعادن' },
    { id: 'design_production_eng', name: 'هندسة التصميم والإنتاج' },
    { id: 'petroleum_eng', name: 'هندسة بيتروليّة' },
    { id: 'food_eng', name: 'هندسة غذائية' },
    { id: 'chemical_eng', name: 'هندسة كيميائية' },
    { id: 'textile_eng', name: 'هندسة الغزل والنسيج' },
    { id: 'civil', name: 'هندسة مدنيّة' },
    { id: 'tourism', name: 'سياحة' },
    { id: 'architecture', name: 'هندسة معماريّة' },
    { id: 'music', name: 'موسيقا' },
    { id: 'physics', name: 'فيزياء' },
    { id: 'mathematics', name: 'رياضيات' },
    { id: 'statistics', name: 'إحصاء' },
    { id: 'biology', name: 'علم الحياة بيولوجيا' },
    { id: 'geology', name: 'علم الحياة جيولوجيا' },
    { id: 'chemistry', name: 'كيمياء' },
    { id: 'economics', name: 'اقتصاد' },
    { id: 'informatics', name: 'هندسة المعلوماتية' },
    { id: 'applied_science', name: 'كلية تطبيقية' },
    { id: 'arabic', name: 'لغة عربية' },
    { id: 'english', name: 'لغة انكليزية' },
    { id: 'french', name: 'لغة فرنسية' },
    { id: 'persian', name: 'لغة فارسية' },
    { id: 'history', name: 'تاريخ' },
    { id: 'philosophy', name: 'فلسفة' },
    { id: 'agriculture', name: 'هندسة زراعية' },
    { id: 'law', name: 'حقوق' },
    { id: 'curricula', name: 'مناهج وطرق تدريس' },
    { id: 'psychology', name: 'علم نفس' },
    { id: 'kindergarten', name: 'رياض أطفال' },
    { id: 'psychological_counseling', name: 'إرشاد نفسي' },
    { id: 'class_teacher', name: 'معلم صف' },
    { id: 'sharia', name: 'شريعة' },
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