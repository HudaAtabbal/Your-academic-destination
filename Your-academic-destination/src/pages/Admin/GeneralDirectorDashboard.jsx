import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import { apiGet, apiRequest, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import { FACULTY_LABELS } from '../../api/faculties';
import '../../style/GeneralDirectorDashboard.css';

const GeneralDirectorDashboard = ({ userRole = 'المدير العام' }) => {
  const navigate = useNavigate();

  const [teamMembers, setTeamMembers] = useState([]);
  const [stats, setStats] = useState([
    { id: 'registered', label: 'مسجّلون إلكترونياً', value: '—' },
    { id: 'inside', label: 'داخل الحرم اليوم', value: '—' },
    { id: 'cumulative', label: 'إجمالي الطلاب داخل الجامعة (كل الأيام)', value: '—', link: '/dashboard-students-inside' },
    { id: 'survey', label: 'أكملوا الاستبيان', value: '—' },
    { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: '—', link: '/gate-incomplete' },
    { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: '—' },
  ]);
  const [hallOccupancy, setHallOccupancy] = useState(null); // null = ما في بيانات قاعات لسا
  const [smsStatus, setSmsStatus] = useState(null); // null = ما في بيانات حالة المُرسِل لسا

  // الإحصاءات + إشغال القاعات — بتتحدث كل 15 ثانية مثل حالة المُرسِل
  useEffect(() => {
    const fetchStats = () => {
      // الإحصاءات الست — endpoint جديد مخصص للداشبورد صار متوفر
      apiGet('/admin/dashboard/stats')
        .then((res) => {
          setStats([
            { id: 'registered', label: 'مسجّلون إلكترونياً', value: res.registered_online_count },
            { id: 'inside', label: 'داخل الحرم اليوم', value: res.students_inside_today },
            { id: 'cumulative', label: 'إجمالي الطلاب داخل الجامعة (كل الأيام)', value: res.students_inside_all_days, link: '/dashboard-students-inside' },
            { id: 'survey', label: 'أكملوا الاستبيان', value: res.survey_completed_count },
            { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: res.walkin_pending_count, link: '/gate-incomplete' },
            { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: res.walkin_completed_count },
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
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000);

    return () => clearInterval(interval);
  }, []);

  // حسابات فريق العمل — بتتحمل مرة وحدة فقط (تحريراتها يدوية من الداشبورد)
  useEffect(() => {
    apiGet('/admin/accounts?page=1&limit=50')
      .then((res) => {
        setTeamMembers(
          res.items.map((account) => ({
            username: account.username,
            role: ROLE_LABELS[account.role] || account.role,
            roleType: account.role,
            // المفتاح الخام (English) للتحرير + الاسم العربي للعرض
            facultyKey: account.college,
            faculty: FACULTY_LABELS[account.college] || account.college || '—',
          }))
        );
      })
      .catch(() => {});
  }, []);

  // حالة إرسال الرسائل النصية — بتتحدث كل 15 ثانية عشان مؤشر المُرسِل يبقى صادق
  useEffect(() => {
    const fetchSmsStatus = () => {
      apiGet('/admin/dashboard/sms-status')
        .then((res) => setSmsStatus(res))
        .catch(() => {});
    };

    fetchSmsStatus();
    const interval = setInterval(fetchSmsStatus, 15000);

    return () => clearInterval(interval);
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

  const handleDeleteMember = async (member) => {
    const confirmed = window.confirm(`متأكدة إنك بدك تحذفي حساب "${member.username}"؟`);
    if (!confirmed) return;

    try {
      await apiRequest(`/admin/accounts/${member.username}`, { method: 'DELETE' });
      setTeamMembers((prev) => prev.filter((m) => m.username !== member.username));
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    }
  };

  return (
    <div className="gd-dash-viewport">

      <AdminHeader userRole={userRole} />

      {/* Desktop Main Content Container */}
      <main className="gd-dash-main-container">
        
        {/* Metric Cards Row */}
        <section className="gd-dash-metrics-grid">
          {stats.map((stat) => (
            <div
              key={stat.id}
              className={`gd-dash-metric-card ${stat.link ? 'gd-dash-metric-card-clickable' : ''}`}
              onClick={() => stat.link && navigate(stat.link)}
              role={stat.link ? 'button' : undefined}
            >
              <span className="gd-dash-metric-label">{stat.label}</span>
              <span className="gd-dash-metric-number">{stat.value}</span>
            </div>
          ))}
        </section>

        {/* SMS Sending Status */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">حالة إرسال الرسائل النصية</h2>
          {smsStatus ? (
            <div className="gd-dash-sms-card">
              <div className="gd-dash-sms-status-line">
                <span
                  className={`gd-dash-sms-dot ${
                    smsStatus.worker_online ? 'gd-dash-sms-dot-online' : 'gd-dash-sms-dot-offline'
                  }`}
                ></span>
                <span className="gd-dash-sms-worker-state">
                  {smsStatus.worker_online ? 'المُرسِل متصل' : 'المُرسِل منقطع'}
                </span>
              </div>
              <div className="gd-dash-sms-counts">
                <span className="gd-dash-sms-count">
                  بانتظار الإرسال: <strong>{smsStatus.counts?.pending ?? 0}</strong>
                </span>
                <span className="gd-dash-sms-count">
                  مرسلة: <strong>{smsStatus.counts?.sent ?? 0}</strong>
                </span>
                <span className="gd-dash-sms-count">
                  فاشلة: <strong>{smsStatus.counts?.failed ?? 0}</strong>
                </span>
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن حالة المُرسِل للآن</p>
          )}
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