import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../../style/StudentDataManagerPage.css';

const StudentDataManagerPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // إذا الصفحة انفتحت بـ presetId (جاي من صفحة البوابة أو من صفحة السجلات الناقصة)،
  // منعبّي خانة البحث فيه تلقائياً بدل ما تضل فاضية
  const [searchId, setSearchId] = useState(location.state?.presetId || 'R-0248');

  const [formData, setFormData] = useState({
    birthDate: '2008/03/14',
    fullName: 'عمر أحمد العسورة',
    handle: '0991234567',
    contactMethod: 'واتساب',
    verificationStatus: 'مفعّل',
    baccalaureateScore: '90',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    console.log('Searching for ID:', searchId);
  };

  const handleSave = (e) => {
    e.preventDefault();
    console.log('Saving student data:', formData);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Top Header */}
        <header className="page-header">
          
          
          <div className="header-brand">
            <div className="brand-text">
              <h1 className="brand-title">وجهتك الأكاديمية 2</h1>
              <p className="brand-subtitle">لوحة التحكم</p>
            </div>
          </div>
          <div className="header-badge">مدير بيانات الطلاب</div>
        </header>

        {/* Scrollable Main Content */}
        <main className="page-body">
          
          {/* Stats Row */}
          <div className="stats-row">
            <button
              type="button"
              className="stat-card stat-card-clickable"
              onClick={() => navigate('/gate-incomplete')}
            >
              <span className="stat-label">سجلات in-walk تنتظر الإكمال</span>
              <span className="stat-value orange-text">٣٧</span>
            </button>
            <div className="stat-card">
              <span className="stat-label">إجمالي الطلاب المسجّلين</span>
              <span className="stat-value primary-text">١٤,٢0٨</span>
            </div>
          </div>

          {/* Search Box */}
          <section className="search-section">
            <h2 className="section-label">البحث برقم الطالب الفريد</h2>
            <form onSubmit={handleSearchSubmit} className="search-box">
              
              <input
                type="text"
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                placeholder="R-0248"
                dir="rtl"
              />
              <button type="submit" className="btn-search">
                بحث
              </button>
            </form>
          </section>

          {/* Edit Form Card */}
          <section className="edit-card">
            <div className="card-header-row">
              <span className="status-chip success">سجل مكتمل</span>
              <h2 className="edit-title">تعديل سجل الطالب — {searchId}</h2>
            </div>

            <form onSubmit={handleSave} className="edit-form">
              {/* Row 1 */}
              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="fullName">الاسم الثلاثي</label>
                  <input
                    type="text"
                    id="fullName"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="birthDate">تاريخ الشهادة</label>
                  <input
                    type="text"
                    id="birthDate"
                    name="birthDate"
                    value={formData.birthDate}
                    onChange={handleInputChange}
                    dir="ltr"
                  />
                </div>
                
              </div>

              {/* Row 2 */}
              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="contactMethod">وسيلة التواصل</label>
                  <input
                    type="text"
                    id="contactMethod"
                    name="contactMethod"
                    value={formData.contactMethod}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="handle">المعرّف</label>
                  <input
                    type="text"
                    id="handle"
                    name="handle"
                    value={formData.handle}
                    onChange={handleInputChange}
                    dir="ltr"
                  />
                </div>
                
              </div>

              {/* Row 3 */}
              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="baccalaureateScore">المعدل </label>
                  <input
                    type="text"
                    id="baccalaureateScore"
                    name="baccalaureateScore"
                    value={formData.baccalaureateScore}
                    onChange={handleInputChange}
                    dir="rtl"
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="verificationStatus">حالة التحقق</label>
                  <div className="verified-input-wrapper">
                    <span className="check-mark">✓</span>
                    <input
                      type="text"
                      id="verificationStatus"
                      name="verificationStatus"
                      value={formData.verificationStatus}
                      onChange={handleInputChange}
                      className="verified-text"
                    />
                  </div>
                </div>
                
              </div>

              {/* Submit Button */}
              <button type="submit" className="btn-save">
                حفظ التعديلات
              </button>
            </form>
          </section>

        </main>
      </div>
    </div>
  );
};

export default StudentDataManagerPage;