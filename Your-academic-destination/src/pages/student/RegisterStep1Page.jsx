import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HeaderStep from '../../components/HeaderStep';
import StepProgress from '../../components/StepProgress';
import InfoBox from '../../components/InfoBox';
import '../../style/RegisterStep1Page.css';

const RegisterStep1Page = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: '',
    birthDay: '',
    birthMonth: '',
    birthYear: '',
    certificateYear: '', // bacc_year بالباك — حقل منفصل عن تاريخ الميلاد
    certificateType: '',
    averageScore: ''
  });

  const [errors, setErrors] = useState({});

  const dayRef = useRef(null);
  const monthRef = useRef(null);
  const yearRef = useRef(null);

  const handleNameChange = (e) => {
    const value = e.target.value;
    const filtered = value.replace(/[^a-zA-Zء-ي\s]/g, '');
    setFormData((prev) => ({ ...prev, fullName: filtered }));
  };

  const handleDayChange = (e) => {
    let value = e.target.value.replace(/[^0-9]/g, '');
    if (value !== '' && Number(value) > 31) value = '31';
    setFormData((prev) => ({ ...prev, birthDay: value }));
    if (value.length === 2) monthRef.current?.focus();
  };

  const handleMonthChange = (e) => {
    let value = e.target.value.replace(/[^0-9]/g, '');
    if (value !== '' && Number(value) > 12) value = '12';
    setFormData((prev) => ({ ...prev, birthMonth: value }));
    if (value.length === 2) yearRef.current?.focus();
  };

  const handleYearChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    setFormData((prev) => ({ ...prev, birthYear: value }));
  };

  const handleMonthKeyDown = (e) => {
    if (e.key === 'Backspace' && formData.birthMonth === '') {
      dayRef.current?.focus();
    }
  };

  const handleYearKeyDown = (e) => {
    if (e.key === 'Backspace' && formData.birthYear === '') {
      monthRef.current?.focus();
    }
  };

  const handleTypeSelect = (type) => {
    setFormData((prev) => ({ ...prev, certificateType: type }));
    setErrors((prev) => ({ ...prev, certificateType: undefined }));
  };

  const handleScoreChange = (e) => {
    let value = e.target.value;
    value = value.replace(/[^0-9.]/g, '');
    const parts = value.split('.');
    if (parts.length > 2) {
      value = parts[0] + '.' + parts.slice(1).join('');
    }
    setFormData((prev) => ({ ...prev, averageScore: value }));
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

    // تاريخ الميلاد الحقيقي (birth_date بالباك)
    const day = Number(formData.birthDay);
    const month = Number(formData.birthMonth);
    const year = Number(formData.birthYear);

    if (!formData.birthDay || !formData.birthMonth || !formData.birthYear) {
      newErrors.birthDate = 'تاريخ الميلاد مطلوب بالكامل';
    } else if (
      day < 1 || day > 31 ||
      month < 1 || month > 12 ||
      formData.birthYear.length !== 4 ||
      year < currentYear - 100 || year > currentYear
    ) {
      newErrors.birthDate = 'تاريخ الميلاد غير صحيح';
    } else {
      const daysInMonth = new Date(year, month, 0).getDate();
      if (day > daysInMonth) {
        newErrors.birthDate = 'تاريخ الميلاد غير صحيح';
      }
    }

    // سنة الشهادة (bacc_year بالباك) — حقل منفصل تماماً عن تاريخ الميلاد
    const certYear = Number(formData.certificateYear);
    if (!formData.certificateYear.trim()) {
      newErrors.certificateYear = 'سنة الشهادة مطلوبة';
    } else if (
      formData.certificateYear.length !== 4 ||
      certYear < currentYear - 100 || certYear > currentYear
    ) {
      newErrors.certificateYear = 'سنة الشهادة غير صحيحة';
    }

    if (!formData.certificateType) {
      newErrors.certificateType = 'يرجى اختيار نوع الشهادة';
    }

    if (!formData.averageScore.trim()) {
      newErrors.averageScore = 'المعدل مطلوب';
    } else if (Number(formData.averageScore) <= 0 || Number(formData.averageScore) > 100) {
      newErrors.averageScore = 'الرجاء إدخال معدل صحيح بين 0 و100';
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
              <label className="input-label">تاريخ الميلاد</label>
              <div className="date-inputs-row">
                <input
                  ref={dayRef}
                  type="text"
                  inputMode="numeric"
                  placeholder="يوم"
                  maxLength={2}
                  value={formData.birthDay}
                  onChange={handleDayChange}
                  className={`custom-input date-input-small ${errors.birthDate ? 'input-error' : ''}`}
                />
                <input
                  ref={monthRef}
                  type="text"
                  inputMode="numeric"
                  placeholder="شهر"
                  maxLength={2}
                  value={formData.birthMonth}
                  onChange={handleMonthChange}
                  onKeyDown={handleMonthKeyDown}
                  className={`custom-input date-input-small ${errors.birthDate ? 'input-error' : ''}`}
                />
                <input
                  ref={yearRef}
                  type="text"
                  inputMode="numeric"
                  placeholder="سنة"
                  maxLength={4}
                  value={formData.birthYear}
                  onChange={handleYearChange}
                  onKeyDown={handleYearKeyDown}
                  className={`custom-input date-input-small ${errors.birthDate ? 'input-error' : ''}`}
                />
              </div>
              {errors.birthDate && <span className="error-text">{errors.birthDate}</span>}
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
              <label className="input-label">نوع الشهادة</label>
              <div className="certificate-type-options">
                <button
                  type="button"
                  className={`type-btn ${formData.certificateType === 'scientific' ? 'selected' : ''}`}
                  onClick={() => handleTypeSelect('scientific')}
                >
                  علمي
                </button>
                <button
                  type="button"
                  className={`type-btn ${formData.certificateType === 'literary' ? 'selected' : ''}`}
                  onClick={() => handleTypeSelect('literary')}
                >
                  أدبي
                </button>
              </div>
              {errors.certificateType && <span className="error-text">{errors.certificateType}</span>}
            </div>

            <div className="input-group">
              <label htmlFor="averageScore" className="input-label">المعدل (النسبة المئوية)</label>
              <input
                id="averageScore"
                name="averageScore"
                type="text"
                inputMode="decimal"
                placeholder="مثال: 76.5"
                value={formData.averageScore}
                onChange={handleScoreChange}
                className={`custom-input ${errors.averageScore ? 'input-error' : ''}`}
              />
              {errors.averageScore && <span className="error-text">{errors.averageScore}</span>}
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