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
      { id: 'registered', label: 'مسجّلون إلكترونياً', value: '—', link: '/gate-registered' },
      { id: 'inside', label: 'داخل الحرم اليوم', value: '—' },
    { id: 'cumulative', label: 'إجمالي الطلاب داخل الجامعة (كل الأيام)', value: '—', link: '/dashboard-students-inside' },
    { id: 'survey', label: 'أكملوا الاستبيان', value: '—' },
    { id: 'consultations', label: 'إجمالي الاستشارات', value: '—' },
    { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: '—', link: '/gate-incomplete' },
    { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: '—' },
  ]);
  const [hallOccupancy, setHallOccupancy] = useState(null); // null = ما في بيانات قاعات لسا
  const [smsStatus, setSmsStatus] = useState(null); // null = ما في بيانات حالة المُرسِل لسا
  const [analytics, setAnalytics] = useState(null); // null = ما في بيانات التحليلات لسا

  // الإحصاءات + إشغال القاعات — بتتحدث كل 15 ثانية مثل حالة المُرسِل
  useEffect(() => {
    const fetchStats = () => {
      // الإحصاءات السبع — endpoint جديد مخصص للداشبورد صار متوفر
      apiGet('/admin/dashboard/stats')
        .then((res) => {
          setStats([
            // ✅ الرابط لازم يضل موجود هون كمان، وإلا بيختفي بعد ما توصل البيانات
            { id: 'registered', label: 'مسجّلون إلكترونياً', value: res.registered_online_count, link: '/gate-registered' },
            { id: 'inside', label: 'داخل الحرم اليوم', value: res.students_inside_today },
            { id: 'cumulative', label: 'إجمالي الطلاب داخل الجامعة (كل الأيام)', value: res.students_inside_all_days, link: '/dashboard-students-inside' },
            { id: 'survey', label: 'أكملوا الاستبيان', value: res.survey_completed_count },
            { id: 'consultations', label: 'إجمالي الاستشارات', value: res.total_consultations },
            { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: res.walkin_pending_count, link: '/gate-incomplete' },
            { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: res.walkin_completed_count },
          ]);
        })
        .catch(() => {});

      // التحليلات التفصيلية (زيارات الكليات، حضور المحاضرات، التوزيعات) — كلها
      // إجمالية لكل الأيام، بتتحدث مع نفس دورة الـ 15 ثانية مثل بقية الداشبورد
      apiGet('/admin/dashboard/analytics')
        .then(setAnalytics)
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

  // تحليلات "علمي/أدبي" — نسب مئوية من إجمالي الحاصلين على فرع محدّد (الفئة
  // اللي بدون بيانات ما بتظهر بالأرقام، شارت الدونات بيشتغل على القيم الفعلية)
  const certData = analytics?.certificate_distribution || [];
  const certTotal = certData.reduce((sum, item) => sum + item.count, 0);
  const certScientific = certData.find((c) => c.certificate_type === 'scientific')?.count || 0;
  const certLiterary = certData.find((c) => c.certificate_type === 'literary')?.count || 0;
  const pctScientific = certTotal > 0 ? Math.round((certScientific / certTotal) * 100) : 0;
  const pctLiterary = certTotal > 0 ? Math.round((certLiterary / certTotal) * 100) : 0;

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

        {/* زيارات الكلية (ركن التوجيه) — قائمة مرتبة بكل الكليات */}
        <section className="gd-dash-section-wrapper">
          <div className="gd-dash-section-heading-row">
            <h2 className="gd-dash-section-heading">زيارة الكلية (ركن التوجيه)</h2>
            {analytics && (
              <span className="gd-dash-analytics-total">
                الإجمالي: {analytics.college_visits.reduce((s, v) => s + v.count, 0)}
              </span>
            )}
          </div>
          {analytics ? (
            <div className="gd-dash-ranked-list">
              {analytics.college_visits.map((visit) => (
                <div key={visit.college} className="gd-dash-ranked-item">
                  <span className="gd-dash-ranked-name">
                    {FACULTY_LABELS[visit.college] || visit.college}
                  </span>
                  <span className="gd-dash-ranked-num">{visit.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن زيارات الكليات للآن</p>
          )}
        </section>

        {/* حضور كل محاضرة — أعمدة رأسية */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">حضور كل محاضرة</h2>
          {analytics?.lecture_attendance && analytics.lecture_attendance.length > 0 ? (
            <div className="gd-dash-chart-card">
              <div className="gd-dash-bars">
                {(() => {
                  const max = Math.max(
                    ...analytics.lecture_attendance.map((l) => l.count),
                    1
                  );
                  return analytics.lecture_attendance.map((lecture) => (
                    <div key={lecture.lecture_name} className="gd-dash-bar-col" title={`${lecture.label}: ${lecture.count}`}>
                      <div
                        className="gd-dash-bar"
                        style={{ height: `${(lecture.count / max) * 100}%` }}
                      ></div>
                      <span className="gd-dash-bar-count">{lecture.count}</span>
                      <span className="gd-dash-bar-label gd-dash-bar-label-tiny">
                        {lecture.label}
                      </span>
                    </div>
                  ));
                })()}
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن حضور المحاضرات للآن</p>
          )}
        </section>

        {/* توزيع المعدل — أعمدة رأسية (فئات العرض 10) */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">توزيع المعدل (0-10 … 90-100)</h2>
          {analytics?.score_distribution && analytics.score_distribution.length > 0 ? (
            <div className="gd-dash-chart-card">
              <div className="gd-dash-bars">
                {(() => {
                  const max = Math.max(
                    ...analytics.score_distribution.map((s) => s.count),
                    1
                  );
                  return analytics.score_distribution.map((bucket) => (
                    <div key={bucket.label} className="gd-dash-bar-col" title={`${bucket.label}: ${bucket.count}`}>
                      <div
                        className="gd-dash-bar"
                        style={{ height: `${(bucket.count / max) * 100}%` }}
                      ></div>
                      <span className="gd-dash-bar-count">{bucket.count}</span>
                      <span className="gd-dash-bar-label">{bucket.label}</span>
                    </div>
                  ));
                })()}
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن توزيع المعدل للآن</p>
          )}
        </section>

        {/* توزيع سنة الشهادة — أعمدة رأسية */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">توزيع سنة الشهادة</h2>
          {analytics?.year_distribution && analytics.year_distribution.length > 0 ? (
            <div className="gd-dash-chart-card">
              <div className="gd-dash-bars">
                {(() => {
                  const max = Math.max(
                    ...analytics.year_distribution.map((y) => y.count),
                    1
                  );
                  return analytics.year_distribution.map((year) => (
                    <div key={year.year} className="gd-dash-bar-col" title={`${year.year}: ${year.count}`}>
                      <div
                        className="gd-dash-bar"
                        style={{ height: `${(year.count / max) * 100}%` }}
                      ></div>
                      <span className="gd-dash-bar-count">{year.count}</span>
                      <span className="gd-dash-bar-label">{year.year}</span>
                    </div>
                  ));
                })()}
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن توزيع سنوات الشهادة للآن</p>
          )}
        </section>

        {/* علمي/أدبي — دونات بنسب مئوية */}
        <section className="gd-dash-section-wrapper">
          <h2 className="gd-dash-section-heading">علمي / أدبي</h2>
          {analytics && certTotal > 0 ? (
            <div className="gd-dash-donut-card">
              <svg viewBox="0 0 42 42" className="gd-dash-donut" aria-label="توزيع علمي/أدبي">
                <circle cx="21" cy="21" r="15.9" className="gd-dash-donut-track" />
                {pctScientific > 0 && (
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-donut-scientific"
                    strokeDasharray={`${pctScientific} ${100 - pctScientific}`}
                    strokeDashoffset="25"
                  />
                )}
                {pctLiterary > 0 && (
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-donut-literary"
                    strokeDasharray={`${pctLiterary} ${100 - pctLiterary}`}
                    strokeDashoffset={25 - pctScientific}
                  />
                )}
              </svg>
              <div className="gd-dash-donut-legend">
                <span className="gd-dash-donut-legend-item">
                  <span className="gd-dash-donut-swatch gd-dash-donut-scientific"></span>
                  علمي: {pctScientific}٪ ({certScientific})
                </span>
                <span className="gd-dash-donut-legend-item">
                  <span className="gd-dash-donut-swatch gd-dash-donut-literary"></span>
                  أدبي: {pctLiterary}٪ ({certLiterary})
                </span>
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن توزيع الفرع الثانوي للآن</p>
          )}
        </section>

      </main>
    </div>
  );
};

export default GeneralDirectorDashboard;