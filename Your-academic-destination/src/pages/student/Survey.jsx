import React, { useState } from 'react';
import HeaderStep from '../../components/HeaderStep';
import SurveyQuestionOne from '../../components/SurveyQuestionOne';
import SurveyQuestionTwo from '../../components/SurveyQuestionTwo';
import BottomNav from '../../components/BottomNav';
import '../../style/Survey.css';

const Survey = () => {
  const [q1Option, setQ1Option] = useState('decided');
  const [q2Major, setQ2Major] = useState('الطب البشري');

  const majors = [
    { id: 1, name: 'الطب البشري' },
    { id: 2, name: 'المعلوماتية' },
    { id: 3, name: 'الهندسة المعمارية' },
    { id: 4, name: 'الحقوق' },
    { id: 5, name: 'الصيدلة' },
    { id: 6, name: 'الهندسة المدنية' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log({ q1Option, q2Major });
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
              <button type="submit" className="btn btn-primary">
                أرسل
              </button>
              <button type="button" onClick={handleSkip} className="btn btn-secondary">
                لاحقاً
              </button>
            </div>

          </form>
        </main>

        <BottomNav />

      </div>
    </div>
  );
};

export default Survey;