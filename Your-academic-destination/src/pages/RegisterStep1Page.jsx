import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../components/HeaderStep';
import StepProgress from '../components/Stepprogress';
import InfoBox from '../components/InfoBox';
import '../style/RegisterStep1Page.css';

const RegisterStep1Page = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: '',
    certificateYear: '',
    baccalaureateScore: ''
  });

  const [errors, setErrors] = useState({});

  const handleNameChange = (e) => {
    const value = e.target.value;
    const filtered = value.replace(/[^a-zA-Zء-ي\s]/g, '');
    setFormData((prev) => ({ ...prev, fullName: filtered }));
  };

  const handleScoreChange = (e) => {
    let value = e.target.value;
    value = value.replace(/[^0-9.]/g, '');
    const parts = value.split('.');
    if (parts.length > 2) {
      value = parts[0] + '.' + parts.slice(1).join('');
    }
    setFormData((prev) => ({ ...prev, baccalaureateScore: value }));
  };

  const handleCertificateYearChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 4);
    setFormData((prev) => ({ ...prev, certificateYear: value }));
  };

  // التحقق من صحة كل الحقول
  const validate = () => {
    const newErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = 'الاسم الثلاثي مطلوب';
    } else if (formData.fullName.trim().split(/\s+/).length < 3) {
      newErrors.fullName = 'الرجاء إدخال الاسم الثلاثي كامل';
    }

    const currentYear = new Date().getFullYear();
    const year = Number(formData.certificateYear);

    if (!formData.certificateYear.trim()) {
      newErrors.certificateYear = 'سنة الشهادة مطلوبة';
    } else if (
      formData.certificateYear.length !== 4 ||
      year < currentYear - 100 || year > currentYear
    ) {
      newErrors.certificateYear = 'سنة الشهادة غير صحيحة';
    }

    if (!formData.baccalaureateScore.trim()) {
      newErrors.baccalaureateScore = 'مجموع البكالوريا مطلوب';
    } else if (Number(formData.baccalaureateScore) <= 0 || Number(formData.baccalaureateScore) > 300) {
      newErrors.baccalaureateScore = 'الرجاء إدخال مجموع صحيح';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    navigate('/register-step2'); // الانتقال للخطوة التالية
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="من أنت؟"
          stepText="خطوة 1 من 3"
          onBack={() => window.history.back()}
        />

        <StepProgress totalSteps={3} currentStep={1} />

        <main className="card-body">
          <form onSubmit={handleSubmit} className="form-container" noValidate>

            <div className="input-group">
              <label htmlFor="fullName" className="input-label">الاسم الثلاثي</label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                placeholder="مثال: عمر أحمد العسورة"
                value={formData.fullName}
                onChange={handleNameChange}
                className={`custom-input ${errors.fullName ? 'input-error' : ''}`}
              />
              {errors.fullName && <span className="error-text">{errors.fullName}</span>}
            </div>

            <div className="input-group">
              <label htmlFor="certificateYear" className="input-label">سنة الشهادة</label>
              <input
                id="certificateYear"
                name="certificateYear"
                type="text"
                inputMode="numeric"
                placeholder="مثال: 2024"
                maxLength={4}
                value={formData.certificateYear}
                onChange={handleCertificateYearChange}
                className={`custom-input ${errors.certificateYear ? 'input-error' : ''}`}
              />
              {errors.certificateYear && <span className="error-text">{errors.certificateYear}</span>}
            </div>

            <div className="input-group">
              <label htmlFor="baccalaureateScore" className="input-label">مجموع البكالوريا</label>
              <input
                id="baccalaureateScore"
                name="baccalaureateScore"
                type="text"
                inputMode="decimal"
                placeholder="مثال: 228.5"
                value={formData.baccalaureateScore}
                onChange={handleScoreChange}
                className={`custom-input ${errors.baccalaureateScore ? 'input-error' : ''}`}
              />
              {errors.baccalaureateScore && <span className="error-text">{errors.baccalaureateScore}</span>}
            </div>

            <InfoBox text="بياناتك بتُستخدم بس لتنظيم الدخول ومتابعة أثر الفعالية، وما بتتشارك مع أي جهة تانية." />

            <div className="actions">
              <button
                type="submit"
                className="btn btn-primary"
              >
                تابع
              </button>
            </div>

          </form>
        </main>

      </div>
    </div>
  );
};

export default RegisterStep1Page;