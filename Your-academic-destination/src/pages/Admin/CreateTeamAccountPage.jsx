import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import { apiPost, apiPatch, ApiError } from '../../api/api';
import '../../style/CreateTeamAccountPage.css';

// قائمة "الكلية المرتبطة" لحسابات مسؤولي الكليات — نفس قيم (id) enum Faculty
// بالباك وبنفس ترتيبه المعتمد (قائمة منفصلة عن اختيارات الطلاب).
const KNOWN_COLLEGES = [
  { value: 'medicine', label: 'الطب البشري' },
  { value: 'dentistry', label: 'طب الأسنان' },
  { value: 'pharmacy', label: 'الصيدلة' },
  { value: 'health_sciences', label: 'كلية العلوم الصحية' },
  { value: 'informatics', label: 'كلية الهندسةالمعلوماتية' },
  { value: 'civil_engineering', label: 'كلية الهندسة المدنية' },
  { value: 'architecture', label: 'كلية الهندسة المعمارية' },
  { value: 'agriculture', label: 'كلية الهندسة الزراعية' },
  { value: 'electrical_mechanical', label: 'كلية الهندسة الكهربائية والميكانيكية' },
  { value: 'chemical_food', label: 'كلية الهندسة الكيميائية والغذائية' },
  { value: 'economics', label: 'كلية الاقتصاد' },
  { value: 'tourism', label: 'كلية السياحة' },
  { value: 'music', label: 'كلية الموسيقى' },
  { value: 'arts', label: 'كلية الآداب والعلوم الإنسانية' },
  { value: 'education', label: 'كلية التربية' },
  { value: 'sciences', label: 'كلية العلوم' },
  { value: 'applied', label: 'الكلية التطبيقية' },
  { value: 'law', label: 'كلية الحقوق' },
  { value: 'institute_agriculture', label: 'معهد تقاني زراعي' },
  { value: 'institute_desert_affairs', label: 'معهد تقاني لشؤون البادية والتصحر' },
  { value: 'institute_engineering', label: 'معهد تقاني هندسي' },
  { value: 'institute_health', label: 'معهد تقاني صحي' },
  { value: 'institute_dentistry', label: 'معهد تقاني طب اسنان' },
  { value: 'institute_applied_industries', label: 'معهد تقاني صناعات تطبيقية' },
  { value: 'institute_computer', label: 'معهد تقاني حاسوب' },
];

const CreateTeamAccountPage = ({ userRole = 'المدير العام', onSubmit }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // إذا الصفحة انفتحت بوضع تعديل (جاي من لوحة التحكم عبر زر "تعديل")،
  // منعبّي الفورم ببيانات العضو الحالية بدل ما تضل فاضية
  const editMember = location.state?.editMember || null;

  const [username, setUsername] = useState(editMember?.username || '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState(editMember?.roleType || 'gate_scanner'); // 'super_admin', 'students_admin', 'gate_scanner', 'college_staff'
  const [faculty, setFaculty] = useState(
    editMember?.roleType === 'college_staff' &&
    KNOWN_COLLEGES.some((c) => c.value === editMember.faculty)
      ? editMember.faculty
      : ''
  );
  const [error, setError] = useState('');
  const [successInfo, setSuccessInfo] = useState(''); // بيعرض كلمة السر المتولّدة بعد الإنشاء
  const [isSubmitting, setIsSubmitting] = useState(false);

  const rolesList = [
    { id: 'super_admin', label: 'المدير العام' },
    { id: 'students_admin', label: 'مدير بيانات الطلاب' },
    { id: 'gate_scanner', label: 'مسؤول المسح' },
    { id: 'college_staff', label: 'مسؤول الكلية' },
  ];

  // مثال اسم مستخدم مختلف حسب الدور المختار، حتى يبين الشكل المتوقع فوراً
  const USERNAME_PLACEHOLDERS = {
    super_admin: 'مثال: sara_super',
    students_admin: 'مثال: sara_admin',
    gate_scanner: 'مثال: sara_staff',
    college_staff: 'مثال: sara_it',
  };

  const handleBack = () => {
    navigate('/dashboard');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username.trim()) {
      setError('يرجى إدخال اسم المستخدم');
      return;
    }
    if (role === 'college_staff' && !faculty) {
      setError('يرجى اختيار الكلية لدور مسؤول الكلية');
      return;
    }

    setError('');
    setSuccessInfo('');
    setIsSubmitting(true);

    try {
      if (editMember) {
        const payload = {
          role,
          college: role === 'college_staff' ? faculty : null,
        };
        if (password.trim()) {
          payload.password = password;
        }
        await apiPatch(`/admin/accounts/${editMember.username}`, payload);
      } else {
        const payload = {
          username: username.trim(),
          password: password.trim() || null,
          role,
          college: role === 'college_staff' ? faculty : null,
        };
        const response = await apiPost('/admin/accounts', payload);

        if (response.generated_password) {
          // كلمة السر بترجع مرة وحدة بس — لازم نعرضها فوراً حتى تنكتب/تتسلّم لصاحب الحساب
          setSuccessInfo(
            `تم إنشاء الحساب. كلمة السر: ${response.generated_password} — احفظيها الآن، ما رح ترجع تظهر تاني`
          );
          setIsSubmitting(false);
          return; // ما بننقل تلقائياً حتى تضمن إنها شافت/نسخت كلمة السر
        }
      }

      if (onSubmit) onSubmit();
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="cta-page-viewport">

      <AdminHeader userRole={userRole} />

      {/* Main Form Area */}
      <main className="cta-main-container">
        
        {/* Back Link */}
        <div className="cta-back-wrapper">
          <button type="button" className="cta-back-btn" onClick={handleBack}>
            <span className="cta-back-arrow">←</span> رجوع لقائمة الحسابات
          </button>
        </div>

        {/* Card Form */}
        <div className="cta-form-card">
          <h1 className="cta-form-title">
            {editMember ? `تعديل حساب — ${editMember.username}` : 'إنشاء حساب فريق عمل جديد'}
          </h1>

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
                  placeholder={USERNAME_PLACEHOLDERS[role]}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={!!editMember}
                  dir="rtl"
                />
              </div>

              <div className="cta-field-group">
                <label className="cta-field-label" htmlFor="cta-password">
                  {editMember ? 'كلمة سر جديدة' : 'كلمة السر '}
                </label>
                <input
                  id="cta-password"
                  type="text"
                  className="cta-input-field"
                  placeholder={editMember ? 'اتركها فارغة لعدم التغيير' : 'ادخل كلمة المرور  '}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

            </div>

            {/* Inputs Row 2: Role Selector */}
            <div className="cta-field-group">
              <label className="cta-field-label">
                الدور
                {editMember && (
                  <span className="cta-label-hint">
                    {' '}(ثابت بعد الإنشاء — لأنو اسم المستخدم مبني عليه، وتغييره بيسبب عدم تطابق)
                  </span>
                )}
              </label>
              <div className="cta-roles-selector">
                {rolesList.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`cta-role-btn ${role === item.id ? 'active' : ''} ${editMember ? 'locked' : ''}`}
                    onClick={() => {
                      if (!editMember) setRole(item.id);
                    }}
                    disabled={!!editMember}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Inputs Row 3: Faculty Selection (Active only for 'college_staff' role) */}
            <div className="cta-field-group">
              <label className="cta-field-label">
                الكلية المرتبطة <span className="cta-label-hint">(يظهر فقط لدور "مسؤول الكلية")</span>
              </label>
              <select
                className={`cta-input-field cta-select-field ${role !== 'college_staff' ? 'disabled' : ''}`}
                value={role === 'college_staff' ? faculty : ''}
                onChange={(e) => setFaculty(e.target.value)}
                disabled={role !== 'college_staff'}
              >
                <option value="" disabled>
                  {role === 'college_staff' ? 'اختر الكلية...' : '— غير مطلوب لهذا الدور —'}
                </option>
                {KNOWN_COLLEGES.map((college) => (
                  <option key={college.value} value={college.value}>
                    {college.label}
                  </option>
                ))}
              </select>
            </div>

            {error && <p className="cta-error-message">{error}</p>}
            {successInfo && <p className="cta-success-message">{successInfo}</p>}

            {/* Action Submit Button */}
            <div className="cta-form-actions">
              <button type="submit" className="cta-submit-btn" disabled={isSubmitting}>
                {isSubmitting ? 'جاري الحفظ...' : editMember ? 'حفظ التعديلات' : 'إنشاء الحساب'}
              </button>
            </div>

          </form>
        </div>

      </main>
    </div>
  );
};

export default CreateTeamAccountPage;