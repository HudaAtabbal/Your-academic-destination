import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import '../../style/CreateTeamAccountPage.css';

// الكليات المعروفة حالياً بالمشروع (نفس القائمة المستخدمة بصفحات الطالب)
const KNOWN_COLLEGES = [
  'الطب البشري',
  'المعلوماتية',
  'الهندسة المعمارية',
  'الحقوق',
  'الصيدلة',
  'الهندسة الزراعية',
  'التربية',
  'الهندسة المدنية',
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
    editMember?.roleType === 'college_staff' ? editMember.faculty : ''
  );

  const rolesList = [
    { id: 'super_admin', label: 'المدير العام' },
    { id: 'students_admin', label: 'مدير بيانات الطلاب' },
    { id: 'gate_scanner', label: 'مسؤول المسح' },
    { id: 'college_staff', label: 'مسؤول الكلية' },
  ];

  const handleBack = () => {
    navigate('/dashboard');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = { username, password, role, faculty };
    if (onSubmit) {
      onSubmit(payload);
    } else {
      console.log(editMember ? 'Updating account:' : 'Creating account:', payload);
    }
    navigate('/dashboard');
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
                  placeholder="مثال: sara_staff"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  dir="rtl"
                />
              </div>

              <div className="cta-field-group">
                <label className="cta-field-label" htmlFor="cta-password">
                  {editMember ? 'كلمة سر جديدة' : 'كلمة السر المبدئية'}
                </label>
                <input
                  id="cta-password"
                  type="text"
                  className="cta-input-field"
                  placeholder={editMember ? 'اتركها فارغة لعدم التغيير' : 'تُنشأ تلقائياً'}
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
                  <option key={college} value={college}>
                    {college}
                  </option>
                ))}
              </select>
            </div>

            {/* Action Submit Button */}
            <div className="cta-form-actions">
              <button type="submit" className="cta-submit-btn">
                {editMember ? 'حفظ التعديلات' : 'إنشاء الحساب'}
              </button>
            </div>

          </form>
        </div>

      </main>
    </div>
  );
};

export default CreateTeamAccountPage;