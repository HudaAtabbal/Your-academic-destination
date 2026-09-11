import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiGet, apiPatch, ApiError } from '../../api/api';
import '../../style/StudentDataManagerPage.css';

// تحويل استجابة الباك (snake_case) لشكل formData الداخلي تبع الصفحة
const mapStudentDetailToFormData = (detail) => ({
  fullName: detail.full_name || '',
  birthDate: detail.birth_date || '',
  certificateYear: detail.bacc_year != null ? String(detail.bacc_year) : '',
  phoneNumber: detail.contact_id || '',
  verificationStatus: detail.verification_status || 'pending',
  baccalaureateScore: detail.bacc_average != null ? String(detail.bacc_average) : '',
});

const StudentDataManagerPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // searchInput: قيمة خانة الكتابة نفسها (بتتحدث بكل حرف)
  // activeId: الرقم يلي فعلياً منعرض بياناته/عنوانه، ما بيتغير إلا بعد ضغط "بحث"
  const [searchInput, setSearchInput] = useState(location.state?.presetId || '');
  const [activeId, setActiveId] = useState('');
  const [studentDbId, setStudentDbId] = useState(null); // id الداخلي بقاعدة البيانات، لازم للـ PATCH لاحقاً
  const [formData, setFormData] = useState(null); // null = ما في طالب محمّل لسا
  const [searchError, setSearchError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [stats, setStats] = useState({ total_registered: null, walkin_pending_count: null });

  useEffect(() => {
    apiGet('/admin/students/stats')
      .then(setStats)
      .catch(() => {
        // فشل تحميل الإحصائيات مش خطأ حرج يوقف الصفحة، بنسيبها "—" وبس
      });
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCertificateYearChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, '').slice(0, 4);
    setFormData((prev) => ({ ...prev, certificateYear: value }));
  };

  const runSearch = async (code) => {
    const trimmed = code.trim();
    if (!trimmed) {
      setSearchError('يرجى إدخال رقم الطالب');
      return;
    }

    setIsSearching(true);
    setSearchError('');
    setSaveMessage('');

    try {
      const detail = await apiGet(`/admin/students/search?code=${encodeURIComponent(trimmed)}`);
      setStudentDbId(detail.id);
      setActiveId(detail.unique_code);
      setFormData(mapStudentDetailToFormData(detail));
    } catch (err) {
      setFormData(null);
      setStudentDbId(null);
      setActiveId('');
      setSearchError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    runSearch(searchInput);
  };

  // لو الصفحة انفتحت جايّة من صفحة تانية (مثلاً "أكمل البيانات") ومعها presetId جاهز،
  // بنبحث عنه تلقائياً بدون ما ننتظر ضغطة زر
  React.useEffect(() => {
    if (location.state?.presetId) {
      runSearch(location.state.presetId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // بيانات السجل "مكتملة" فقط إذا الحقول الأساسية معبّأة فعلاً وحالة التحقق مفعّلة —
  // بدل ما نعرض "سجل مكتمل" بشكل ثابت بغض النظر عن محتوى البيانات الحقيقي
  const isRecordComplete = Boolean(
    formData &&
      formData.fullName &&
      formData.phoneNumber &&
      formData.birthDate &&
      formData.certificateYear &&
      formData.baccalaureateScore &&
      formData.verificationStatus === 'verified'
  );

  const handleSave = async (e) => {
    e.preventDefault();
    if (!studentDbId) return;

    setIsSaving(true);
    setSaveMessage('');

    const toNumberOrNull = (raw) => {
      const trimmed = String(raw ?? '').trim();
      if (!trimmed) return null;
      const parsed = Number(trimmed);
      return Number.isFinite(parsed) ? parsed : null;
    };

    const payload = {
      full_name: formData.fullName,
      birth_date: formData.birthDate,
      contact_id: formData.phoneNumber,
      bacc_year: toNumberOrNull(formData.certificateYear),
      bacc_average: toNumberOrNull(formData.baccalaureateScore),
      verification_status: formData.verificationStatus,
    };

    try {
      const updated = await apiPatch(`/admin/students/${studentDbId}`, payload);
      setFormData(mapStudentDetailToFormData(updated));
      setSaveMessage('تم حفظ التعديلات بنجاح');
    } catch (err) {
      setSaveMessage(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    } finally {
      setIsSaving(false);
    }
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
              <span className="stat-value orange-text">{stats.walkin_pending_count ?? '—'}</span>
            </button>
            <div className="stat-card">
              <span className="stat-label">إجمالي الطلاب المسجّلين</span>
              <span className="stat-value primary-text">{stats.total_registered ?? '—'}</span>
            </div>
          </div>

          {/* Search Box */}
          <section className="search-section">
            <h2 className="section-label">البحث برقم الطالب الفريد</h2>
            <form onSubmit={handleSearchSubmit} className="search-box">
              
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="R-0248"
                dir="rtl"
              />
              <button type="submit" className="btn-search" disabled={isSearching}>
                {isSearching ? '...' : 'بحث'}
              </button>
            </form>
            {searchError && <p className="search-error-message">{searchError}</p>}
          </section>

          {/* Edit Form Card — ما بيظهر إلا بعد ما نلاقي طالب فعلي */}
          {formData && (
            <section className="edit-card">
              <div className="card-header-row">
                <span className={`status-chip ${isRecordComplete ? 'success' : 'warning'}`}>
                  {isRecordComplete ? 'سجل مكتمل' : 'بيانات ناقصة'}
                </span>
                <h2 className="edit-title">تعديل سجل الطالب — {activeId}</h2>
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
                    <label htmlFor="birthDate">تاريخ الميلاد</label>
                    <input
                      type="date"
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
                    <label htmlFor="certificateYear">سنة الشهادة</label>
                    <input
                      type="text"
                      id="certificateYear"
                      name="certificateYear"
                      inputMode="numeric"
                      maxLength={4}
                      value={formData.certificateYear}
                      onChange={handleCertificateYearChange}
                      dir="ltr"
                    />
                  </div>
                  <div className="input-group">
                    <label htmlFor="phoneNumber">رقم الهاتف</label>
                    <input
                      type="text"
                      id="phoneNumber"
                      name="phoneNumber"
                      value={formData.phoneNumber}
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
                  
                </div>

                {/* Row 4 */}
                <div className="form-row">
                  <div className="input-group">
                    <label htmlFor="verificationStatus">حالة التحقق</label>
                    <div className="verified-input-wrapper">
                      {formData.verificationStatus === 'verified' && (
                        <span className="check-mark">✓</span>
                      )}
                      <select
                        id="verificationStatus"
                        name="verificationStatus"
                        value={formData.verificationStatus}
                        onChange={handleInputChange}
                        className={`select-field verified-text ${
                          formData.verificationStatus === 'verified' ? 'is-verified' : ''
                        }`}
                      >
                        <option value="pending">بانتظار التفعيل</option>
                        <option value="verified">مفعّل</option>
                      </select>
                    </div>
                  </div>
                  
                </div>

                {saveMessage && <p className="save-feedback-message">{saveMessage}</p>}

                {/* Submit Button */}
                <button type="submit" className="btn-save" disabled={isSaving}>
                  {isSaving ? 'جاري الحفظ...' : 'حفظ التعديلات'}
                </button>
              </form>
            </section>
          )}

        </main>
      </div>
    </div>
  );
};

export default StudentDataManagerPage;