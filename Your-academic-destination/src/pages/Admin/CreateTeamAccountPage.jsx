import React, { useState } from 'react';
import '../../style/CreateTeamAccountPage.css';

const CreateTeamAccountPage = ({
  userRole = 'المدير العام',
  onBack,
  onSubmit,
}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('scanner'); // 'general', 'data', 'scanner', 'college'
  const [faculty, setFaculty] = useState('');

  const rolesList = [
    { id: 'general', label: 'المدير العام' },
    { id: 'data', label: 'مدير بيانات الطلاب' },
    { id: 'scanner', label: 'مسؤول المسح' },
    { id: 'college', label: 'مسؤول الكلية' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit({ username, password, role, faculty });
    }
  };

  return (
    <div className="cta-page-viewport">
      
      {/* Top Application Header */}
      <header className="cta-page-header">
        
        
        <div className="cta-header-brand">
          <div className="cta-brand-text">
            <span className="cta-brand-title">وجهتك الأكاديمية 2</span>
            <span className="cta-brand-subtitle">لوحة التحكم</span>
          </div>
          <div className="cta-header-user">
          <span className="cta-user-badge">{userRole}</span>
        </div>
        </div>
      </header>

      {/* Main Form Area */}
      <main className="cta-main-container">
        
        {/* Back Link */}
        <div className="cta-back-wrapper">
          <button type="button" className="cta-back-btn" onClick={onBack}>
            <span className="cta-back-arrow">←</span> رجوع لقائمة الحسابات
          </button>
        </div>

        {/* Card Form */}
        <div className="cta-form-card">
          <h1 className="cta-form-title">إنشاء حساب فريق عمل جديد</h1>

          <form onSubmit={handleSubmit} className="cta-form-body">
            
            {/* Inputs Row 1: Username & Password */}
            <div className="cta-form-row cta-grid-2col">
              
              <div className="cta-field-group">
                <label className="cta-field-label" htmlFor="cta-username">
                  اسم المستخدم
                </label>
                <input
                  id="cta-username"
                  type="text"
                  className="cta-input-field"
                  placeholder="مثال: sara_staff"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  dir="rtl"
                />
              </div>

              <div className="cta-field-group">
                <label className="cta-field-label" htmlFor="cta-password">
                  كلمة السر المبدئية
                </label>
                <input
                  id="cta-password"
                  type="text"
                  className="cta-input-field"
                  placeholder="تُنشأ تلقائياً"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

            </div>

            {/* Inputs Row 2: Role Selector */}
            <div className="cta-field-group">
              <label className="cta-field-label">الدور</label>
              <div className="cta-roles-selector">
                {rolesList.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`cta-role-btn ${role === item.id ? 'active' : ''}`}
                    onClick={() => setRole(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Inputs Row 3: Faculty Selection (Active only for 'college' role) */}
            <div className="cta-field-group">
              <label className="cta-field-label">
                الكلية المرتبطة <span className="cta-label-hint">(يظهر فقط لدور "مسؤول الكلية")</span>
              </label>
              <input
                type="text"
                className={`cta-input-field ${role !== 'college' ? 'disabled' : ''}`}
                placeholder={role === 'college' ? 'اختر الكلية...' : '— غير مطلوب لهذا الدور —'}
                value={role === 'college' ? faculty : ''}
                onChange={(e) => setFaculty(e.target.value)}
                disabled={role !== 'college'}
              />
            </div>

            {/* Action Submit Button */}
            <div className="cta-form-actions">
              <button type="submit" className="cta-submit-btn">
                إنشاء الحساب
              </button>
            </div>

          </form>
        </div>

      </main>
    </div>
  );
};

export default CreateTeamAccountPage;