import React from 'react';
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
    { username: 'rima_staff', role: 'مسؤول الكلية', roleType: 'college', faculty: 'الطب البشري' },
    { username: 'hadi_gate', role: 'مسؤول المسح', roleType: 'scanner', faculty: '—' },
    { username: 'sedra_admin', role: 'مدير بيانات الطلاب', roleType: 'data', faculty: '—' },
    { username: 'taher_super', role: 'المدير العام', roleType: 'general', faculty: '—' },
  ],
  hallOccupancy = {
    title: 'مدرج 3 • الطب البشري',
    time: '11:20',
    current: 296,
    total: 300,
  },
}) => {
  const percentage = Math.round((hallOccupancy.current / hallOccupancy.total) * 100);

  return (
    <div className="gd-dash-viewport">
      
      {/* Top Application Header */}
      <header className="gd-dash-header">
        
        
        <div className="gd-dash-header-brand">
          <div className="gd-dash-brand-text">
            <span className="gd-dash-brand-title">وجهتك الأكاديمية 2</span>
            <span className="gd-dash-brand-subtitle">لوحة التحكم</span>
          </div>
          <div className="gd-dash-header-user">
          <span className="gd-dash-user-badge">{userRole}</span>
        </div>
        </div>
      </header>

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
          <h2 className="gd-dash-section-heading">حسابات فريق العمل</h2>
          
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
                      <button type="button" className="gd-dash-edit-btn">تعديل</button>
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