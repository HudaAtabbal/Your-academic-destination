import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../../assets/English logo colored-02.png';
import { apiPost, setAuthToken, ApiError } from '../../api/api';
import '../../style/TeamLoginPage.css';

// كل دور بيروح على شاشته الافتراضية بعد الدخول
const ROLE_LANDING_PAGES = {
  super_admin: '/dashboard',
  students_admin: '/gate',
  gate_scanner: '/scan/stadium',
  // مسؤول الكلية بيغطي 3 شاشات مختلفة (جولة/توجيه/استشارة) —
  // مؤقتاً بنوجّهه لشاشة التوجيه كافتراضي، لحد ما يصير في شاشة اختيار حقيقية
  college_staff: '/scan/college',
};

const TeamLoginPage = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.username.trim() || !formData.password.trim()) {
      setError('يرجى تعبئة اسم المستخدم وكلمة السر');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await apiPost('/auth/login', {
        username: formData.username.trim(),
        password: formData.password,
      });

      setAuthToken(response.access_token);
      localStorage.setItem('accountRole', response.role);
      if (response.college) {
        localStorage.setItem('accountCollege', response.college);
      } else {
        localStorage.removeItem('accountCollege');
      }

      const landingPage = ROLE_LANDING_PAGES[response.role] || '/dashboard';
      navigate(landingPage);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <main className="card-body">
          {/* Logo */}
          <div className="logo-container">
            <img src={logo} alt="شعار" className="brand-logo" />
          </div>

          {/* Header Titles */}
          <div className="header-text">
            <h1 className="main-title">دخول فريق العمل</h1>
            <p className="subtitle">وجهتك الأكاديمية 2 — لوحة الإدارة</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="login-form" autoComplete="off">
            <div className="input-group">
              <label htmlFor="username">اسم المستخدم</label>
              <input
                type="text"
                id="username"
                name="username"
                placeholder="username"
                value={formData.username}
                onChange={handleChange}
                required
                dir="ltr"
                autoComplete="off"
              />
            </div>

            <div className="input-group">
              <label htmlFor="password">كلمة السر</label>
              <input
                type="password"
                id="password"
                name="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
                dir="ltr"
                autoComplete="new-password"
              />
            </div>

            {error && <p className="login-error-message">{error}</p>}

            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'جاري الدخول...' : 'دخول'}
            </button>
          </form>

          <p className="footer-notice">الحسابات تُنشأ من قبل المدير العام فقط</p>
        </main>
      </div>
    </div>
  );
};

export default TeamLoginPage;