import React, { useState } from 'react';
import logo from '../../assets/English logo colored-02.png';
import '../../style/TeamLoginPage.css';

const TeamLoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login attempt:', formData);
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

            <button type="submit" className="btn btn-primary">
              دخول
            </button>
          </form>

          <p className="footer-notice">الحسابات تُنشأ من قبل المدير العام فقط</p>
        </main>
      </div>
    </div>
  );
};

export default TeamLoginPage;