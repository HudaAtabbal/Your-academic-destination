import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import { apiGet } from '../../api/api';
import '../../style/GeneralDirectorDashboard.css';

// أسماء الأدوار بالعربي — الباك بيرجّع القيمة enum بس (زي college_staff)، مش النص العربي
const ROLE_LABELS = {
  super_admin: 'المدير العام',
  students_admin: 'مدير بيانات الطلاب',
  gate_scanner: 'مسؤول المسح',
  college_staff: 'مسؤول الكلية',
};

const GeneralDirectorDashboard = ({ userRole = 'المدير العام' }) => {
  const navigate = useNavigate();

  const [teamMembers, setTeamMembers] = useState([]);
  const [stats, setStats] = useState([
    { id: 'registered', label: 'مسجّلون إلكترونياً', value: '—' },
    { id: 'inside', label: 'داخل الحرم الآن', value: '—' },
    { id: 'cumulative', label: 'حضروا اليوم تراكمياً', value: '—' },
    { id: 'survey', label: 'أكملوا الاستبيان', value: '—' },
  ]);
  const [hallOccupancy, setHallOccupancy] = useState(null); // null = ما في بيانات قاعات لسا

  useEffect(() => {
    // حسابات فريق العمل
    apiGet('/admin/accounts?page=1&limit=50')
      .then((res) => {
        setTeamMembers(
          res.items.map((account) => ({
            username: account.username,
            role: ROLE_LABELS[account.role] || account.role,
            roleType: account.role,
            faculty: account.college || '—',
          }))
        );
      })
      .catch(() => {});

    // الإحصاءات الأربع — endpoint جديد مخصص للداشبورد صار متوفر
    apiGet('/admin/dashboard/stats')
      .then((res) => {
        setStats([
          { id: 'registered', label: 'مسجّلون إلكترونياً', value: res.registered_online_count },
          { id: 'inside', label: 'داخل الحرم الآن', value: res.campus_entries_count },
          { id: 'cumulative', label: 'حضروا اليوم تراكمياً', value: res.activities_today_cumulative },
          { id: 'survey', label: 'أكملوا الاستبيان', value: res.survey_completed_count },
        ]);
      })
      .catch(() => {});

    // إشغال القاعات — بناخد أول قاعة نشطة بالقائمة للعرض (الكرت مصمم لقاعة وحدة حالياً)
    apiGet('/admin/dashboard/rooms-occupancy')
      .then((res) => {
        if (res.rooms && res.rooms.length > 0) {
          const room = res.rooms[0];
          setHallOccupancy({
            title: room.hall_label,
            time: new Date(room.last_updated).toLocaleTimeString('ar', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            current: room.current_count,
            // ⚠️ الباك ما بيرجّع السعة القصوى للقاعة، فمؤقتاً حاطة رقم ثابت لحد ما تنضاف
            total: 300,
          });
        }
      })
      .catch(() => {});
  }, []);

  const percentage = hallOccupancy
    ? Math.round((hallOccupancy.current / hallOccupancy.total) * 100)
    : 0;

  const handleCreateAccount = () => {
    navigate('/create-team-account');
  };

  const handleEditMember = (member) => {
    // بنمرر بيانات العضو الحالية حتى فورم الإنشاء يفتح بوضع "تعديل" ومعبّى مسبقاً
    navigate('/create-team-account', { state: { editMember: member } });
  };

  const handleDeleteMember = (member) => {
    // ⚠️ لسا مافي endpoint حذف حساب بالباك — هاد بس تأكيد بصري مؤقت.
    // لما يجهز الباك (مثلاً DELETE /admin/accounts/{username})، بدّلي هون
    // بطلب apiRequest فعلي، وبعد نجاحه احذفي العضو من teamMembers محلياً.
    const confirmed = window.confirm(
      `متأكدة إنك بدك تحذفي حساب "${member.username}"؟ (هالميزة لسا مش مفعّلة من الباك)`
    );
    if (!confirmed) return;

    console.log('طلب حذف حساب (بانتظار endpoint من الباك):', member.username);
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
                      {member.roleType !== 'super_admin' && (
                        <div className="gd-dash-action-buttons">
                          <button
                            type="button"
                            className="gd-dash-edit-btn"
                            onClick={() => handleEditMember(member)}
                          >
                            تعديل
                          </button>
                          <button
                            type="button"
                            className="gd-dash-delete-btn"
                            onClick={() => handleDeleteMember(member)}
                          >
                            حذف
                          </button>
                        </div>
                      )}
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
          
          {hallOccupancy ? (
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
          ) : (
            <p className="gd-dash-empty-note">ما في قاعات فيها نشاط حالياً</p>
          )}
        </section>

      </main>
    </div>
  );
};

export default GeneralDirectorDashboard;