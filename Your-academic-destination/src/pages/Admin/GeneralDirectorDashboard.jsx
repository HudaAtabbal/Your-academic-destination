import React from 'react';
import { useNavigate } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import '../../style/GeneralDirectorDashboard.css';

const GeneralDirectorDashboard = ({
  userRole = 'المدير العام',
  stats = [
    { id: 'registered', label: 'مسجّلون إلكترونياً', value: '14,208' },
    { id: 'inside', label: 'داخل الحرم الآن', value: '3,946' },
    { id: 'cumulative', label: 'حضروا اليوم تراكمياً', value: '5,117' },
    { id: 'survey', label: 'أكملوا الاستبيان', value: '1,204' },
  ],
  teamMembers = [
    { username: 'rima_staff', role: 'مسؤول الكلية', roleType: 'college_staff', faculty: 'الطب البشري' },
    { username: 'hadi_gate', role: 'مسؤول المسح', roleType: 'gate_scanner', faculty: '—' },
    { username: 'sedra_admin', role: 'مدير بيانات الطلاب', roleType: 'students_admin', faculty: '—' },
    { username: 'taher_super', role: 'المدير العام', roleType: 'super_admin', faculty: '—' },
  ],
  hallOccupancy = {
    title: 'مدرج 3 • الطب البشري',
    time: '11:20',
    current: 296,
    total: 300,
  },
}) => {
  const navigate = useNavigate();
  const percentage = Math.round((hallOccupancy.current / hallOccupancy.total) * 100);

  const handleCreateAccount = () => {
    navigate('/create-team-account');
  };

  const handleEditMember = (member) => {
    // بنمرر بيانات العضو الحالية حتى فورم الإنشاء يفتح بوضع "تعديل" ومعبّى مسبقاً
    navigate('/create-team-account', { state: { editMember: member } });
  };

  return (
    <div className="gd-dash-viewport">

      <AdminHeader userRole={userRole} />

      {/* Desktop Main Content Container */}
      <main className="gd-dash-main-container">
        
        {/* Metric Cards Row */}
        <section className="gd-dash-metrics-grid">
          {stats.map((stat) => (
            <div key={stat.id} className="gd-dash-metric-card">
              <span className="gd-dash-metric-label">{stat.label}</span>
              <span className="gd-dash-metric-number">{stat.value}</span>
            </div>
          ))}
        </section>

        {/* Team Accounts Section */}
        <section className="gd-dash-section-wrapper">
          <div className="gd-dash-section-heading-row">
            <h2 className="gd-dash-section-heading">حسابات فريق العمل</h2>
            <button type="button" className="gd-dash-create-btn" onClick={handleCreateAccount}>
              + إنشاء حساب جديد
            </button>
          </div>
          
          <div className="gd-dash-table-card">
            <table className="gd-dash-team-table">
              <thead>
                <tr>
                  <th className="gd-dash-th-action"></th>
                  <th className="gd-dash-th-faculty">الكلية المرتبطة</th>
                  <th className="gd-dash-th-role">الدور</th>
                  <th className="gd-dash-th-user">اسم المستخدم</th>
                </tr>
              </thead>
              <tbody>
                {teamMembers.map((member, idx) => (
                  <tr key={idx} className="gd-dash-table-row">
                    <td className="gd-dash-td-action">
                      <button
                        type="button"
                        className="gd-dash-edit-btn"
                        onClick={() => handleEditMember(member)}
                      >
                        تعديل
                      </button>
                    </td>
                    <td className="gd-dash-td-faculty">{member.faculty}</td>
                    <td className="gd-dash-td-role">
                      <span className={`gd-dash-role-chip gd-dash-role-${member.roleType}`}>
                        {member.role}
                      </span>
                    </td>
                    <td className="gd-dash-td-user">{member.username}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Hall Occupancy Section */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">إشغال القاعات الآن</h2>
          
          <div className="gd-dash-occupancy-card">
            <div className="gd-dash-occupancy-info">
              <span className="gd-dash-occupancy-count">
                {hallOccupancy.current} / {hallOccupancy.total}
              </span>
              <span className="gd-dash-occupancy-location">
                {hallOccupancy.title} • {hallOccupancy.time}
              </span>
            </div>
            
            <div className="gd-dash-progress-track">
              <div 
                className="gd-dash-progress-fill" 
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
};

export default GeneralDirectorDashboard;