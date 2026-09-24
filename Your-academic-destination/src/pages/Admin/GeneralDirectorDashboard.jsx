import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import { apiGet, apiRequest, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import { FACULTY_LABELS } from '../../api/faculties';
import '../../style/GeneralDirectorDashboard.css';

const TEAM_PAGE_SIZE = 10;

// قسم إحصائية قابل للطي — مقفول افتراضياً، وينفتح لما يكبس عالراس.
// والمقصود "الاحصائيات يلي تحت" بالداشبورد كلها صارت هيك.
const CollapsibleSection = ({ title, badge, children }) => {
  const [open, setOpen] = useState(false);

  return (
    <section className="gd-dash-section-wrapper gd-dash-collapsible">
      <button
        type="button"
        className="gd-dash-collapse-header"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <h2 className="gd-dash-section-heading">{title}</h2>
        {badge}
        <span
          className={`gd-dash-collapse-arrow${open ? ' gd-dash-collapse-arrow-open' : ''}`}
          aria-hidden="true"
        >
          ▾
        </span>
      </button>
      {open && <div className="gd-dash-collapse-body">{children}</div>}
    </section>
  );
};

const mapAccount = (account) => ({
  username: account.username,
  role: ROLE_LABELS[account.role] || account.role,
  roleType: account.role,
  // المفتاح الخام (English) للتحرير + الاسم العربي للعرض
  facultyKey: account.college,
  faculty: FACULTY_LABELS[account.college] || account.college || '—',
});

const GeneralDirectorDashboard = ({ userRole = 'المدير العام' }) => {
  const navigate = useNavigate();

  const [teamMembers, setTeamMembers] = useState([]);
  const [teamPage, setTeamPage] = useState(1);
  const [teamTotal, setTeamTotal] = useState(null);
  const [teamSearch, setTeamSearch] = useState('');
  const [teamQuery, setTeamQuery] = useState('');
  const [teamVersion, setTeamVersion] = useState(0);

  const [stats, setStats] = useState([
    { id: 'registered', label: 'مسجّلون إلكترونياً', value: '—', link: '/gate-registered' },
    { id: 'inside', label: 'داخل الحرم اليوم', value: '—' },
    { id: 'cumulative', label: 'إجمالي الطلاب داخل الجامعة (كل الأيام)', value: '—', link: '/dashboard-students-inside' },
    { id: 'survey', label: 'أكملوا الاستبيان', value: '—', link: '/dashboard-survey-completions' },
    { id: 'consultations', label: 'إجمالي الاستشارات', value: '—' },
    { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: '—', link: '/gate-incomplete' },
    { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: '—' },
    { id: 'no_shows', label: 'مسجّلون بلا حضور', value: '—', link: '/dashboard-no-shows' },
  ]);
  const [smsStatus, setSmsStatus] = useState(null); // null = ما في بيانات حالة المُرسِل لسا
  const [analytics, setAnalytics] = useState(null); // null = ما في بيانات التحليلات لسا
  const [scanTotals, setScanTotals] = useState(null); // إجمالي مسحات ركن الترفيه + الاتحاد (كل الأيام)

  // الإحصاءات — بتتحدث كل 15 ثانية مثل حالة المُرسِل
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
            { id: 'survey', label: 'أكملوا الاستبيان', value: res.survey_completed_count, link: '/dashboard-survey-completions' },
            { id: 'consultations', label: 'إجمالي الاستشارات', value: res.total_consultations },
            { id: 'walkin_pending', label: 'سجلات تنتظر الإكمال', value: res.walkin_pending_count, link: '/gate-incomplete' },
            { id: 'walkin_completed', label: 'سجلات تم إكمالها', value: res.walkin_completed_count },
            { id: 'no_shows', label: 'مسجّلون بلا حضور', value: res.registered_no_show_count ?? 0, link: '/dashboard-no-shows' },
          ]);
          // إجمالي مسحات ركن الترفيه + الاتحاد — الترفيه بيظهر بقسم مخصص، والاتحاد بدونات قسمه
          setScanTotals({
            game: res.game_scans_total ?? 0,
            union: res.union_scans_total ?? 0,
          });
        })
        .catch(() => {});

      // التحليلات التفصيلية (زيارات الكليات، حضور المحاضرات، التوزيعات) — كلها
      // إجمالية لكل الأيام، بتتحدث مع نفس دورة الـ 15 ثانية مثل بقية الداشبورد
      apiGet('/admin/dashboard/analytics')
        .then(setAnalytics)
        .catch(() => {});
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000);

    return () => clearInterval(interval);
  }, []);

  // حسابات فريق العمل — بحث + ترقيم (server-side عبر البحث بالاسم)
  useEffect(() => {
    const timer = setTimeout(() => {
      setTeamPage(1);
      setTeamQuery(teamSearch.trim());
    }, 400);
    return () => clearTimeout(timer);
  }, [teamSearch]);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({
      page: String(teamPage),
      limit: String(TEAM_PAGE_SIZE),
    });
    if (teamQuery) params.set('search', teamQuery);

    apiGet(`/admin/accounts?${params.toString()}`)
      .then((res) => {
        if (cancelled) return;
        setTeamMembers((res.items || []).map(mapAccount));
        setTeamTotal(res.total ?? null);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [teamPage, teamQuery, teamVersion]);

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

  const teamTotalPages = teamTotal === null ? 1 : Math.max(1, Math.ceil(teamTotal / TEAM_PAGE_SIZE));
  const currentTeamPage = Math.min(teamPage, teamTotalPages);

  // تحليلات "علمي/أدبي" — نسب مئوية من إجمالي الحاصلين على فرع محدّد (الفئة
  // اللي بدون بيانات ما بتظهر بالأرقام، شارت الدونات بيشتغل على القيم الفعلية)
  const certData = analytics?.certificate_distribution || [];
  const certTotal = certData.reduce((sum, item) => sum + item.count, 0);
  const certScientific = certData.find((c) => c.certificate_type === 'scientific')?.count || 0;
  const certLiterary = certData.find((c) => c.certificate_type === 'literary')?.count || 0;
  const pctScientific = certTotal > 0 ? Math.round((certScientific / certTotal) * 100) : 0;
  const pctLiterary = certTotal > 0 ? Math.round((certLiterary / certTotal) * 100) : 0;

  // تحليلات مسحات ركن الاتحاد — نسب مئوية من إجمالي المسحات، مقسّمة على الأقسام الثلاثة
  const unionData = analytics?.union_sections || [];
  const unionTotal = unionData.reduce((sum, item) => sum + item.count, 0);
  const unionCount = (key) => unionData.find((u) => u.section === key)?.count || 0;
  const unionCentral = unionCount('central');
  const unionMajorGuide = unionCount('major_guide');
  const unionTurkish = unionCount('turkish_club');
  const pctUnionCentral = unionTotal > 0 ? Math.round((unionCentral / unionTotal) * 100) : 0;
  const pctUnionMajorGuide = unionTotal > 0 ? Math.round((unionMajorGuide / unionTotal) * 100) : 0;
  const pctUnionTurkish = unionTotal > 0 ? Math.round((unionTurkish / unionTotal) * 100) : 0;

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
      setTeamVersion((v) => v + 1);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'صار خطأ غير متوقع، حاولي مرة تانية');
    }
  };

  const handleTeamPrev = () => setTeamPage((p) => Math.max(1, p - 1));
  const handleTeamNext = () => setTeamPage((p) => Math.min(teamTotalPages, p + 1));

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

        {/* Team Accounts Section — بحث بالاسم + ترقيم */}
        <section className="gd-dash-section-wrapper">
          <div className="gd-dash-section-heading-row">
            <h2 className="gd-dash-section-heading">حسابات فريق العمل</h2>
            <button type="button" className="gd-dash-create-btn" onClick={handleCreateAccount}>
              + إنشاء حساب جديد
            </button>
          </div>

          <div className="gd-dash-team-toolbar">
            <input
              type="text"
              dir="rtl"
              className="gd-dash-team-search"
              placeholder="بحث بالاسم..."
              value={teamSearch}
              onChange={(e) => setTeamSearch(e.target.value)}
            />
            {teamTotal !== null && (
              <span className="gd-dash-team-total">
                الإجمالي: {teamTotal} {teamQuery ? `– نتائج "${teamQuery}"` : ''}
              </span>
            )}
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
                {teamMembers.length === 0 && (
                  <tr className="gd-dash-table-row">
                    <td colSpan={4} className="gd-dash-empty-note">
                      ما في حسابات مطابقة
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* ترقيم حسابات الفريق */}
          {teamTotalPages > 1 && (
            <div className="pagination-row gd-dash-pagination-row">
              <button
                type="button"
                className="pagination-btn"
                onClick={handleTeamPrev}
                disabled={currentTeamPage <= 1}
              >
                السابق
              </button>
              <span className="pagination-info">
                صفحة {currentTeamPage} من {teamTotalPages}
              </span>
              <button
                type="button"
                className="pagination-btn"
                onClick={handleTeamNext}
                disabled={currentTeamPage >= teamTotalPages}
              >
                التالي
              </button>
            </div>
          )}
        </section>

        {/* مسحات ركن الاتحاد — تفصيل حسب القسم (إجمالي لكل الأيام) */}
        <CollapsibleSection
          title="مسحات ركن الاتحاد"
          badge={
            analytics?.union_sections && (
              <span className="gd-dash-analytics-total">
                الإجمالي: {analytics.union_sections.reduce((s, v) => s + v.count, 0)}
              </span>
            )
          }
        >
          {analytics?.union_sections && unionTotal > 0 ? (
            <div className="gd-dash-donut-card">
              <svg
                viewBox="0 0 42 42"
                className="gd-dash-donut"
                aria-label="توزيع مسحات ركن الاتحاد"
              >
                <circle cx="21" cy="21" r="15.9" className="gd-dash-donut-track" />
                {pctUnionCentral > 0 && (
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-donut-union-central"
                    strokeDasharray={`${pctUnionCentral} ${100 - pctUnionCentral}`}
                    strokeDashoffset="25"
                  />
                )}
                {pctUnionMajorGuide > 0 && (
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-donut-union-major-guide"
                    strokeDasharray={`${pctUnionMajorGuide} ${100 - pctUnionMajorGuide}`}
                    strokeDashoffset={25 - pctUnionCentral}
                  />
                )}
                {pctUnionTurkish > 0 && (
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-donut-union-turkish"
                    strokeDasharray={`${pctUnionTurkish} ${100 - pctUnionTurkish}`}
                    strokeDashoffset={25 - pctUnionCentral - pctUnionMajorGuide}
                  />
                )}
              </svg>
              <div className="gd-dash-donut-legend">
                <span className="gd-dash-donut-legend-item">
                  <span className="gd-dash-donut-swatch gd-dash-donut-union-central"></span>
                  الركن المركزي: {pctUnionCentral}٪ ({unionCentral})
                </span>
                <span className="gd-dash-donut-legend-item">
                  <span className="gd-dash-donut-swatch gd-dash-donut-union-major-guide"></span>
                  دليل التخصص: {pctUnionMajorGuide}٪ ({unionMajorGuide})
                </span>
                <span className="gd-dash-donut-legend-item">
                  <span className="gd-dash-donut-swatch gd-dash-donut-union-turkish"></span>
                  نادي التركي: {pctUnionTurkish}٪ ({unionTurkish})
                </span>
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في بيانات عن مسحات ركن الاتحاد للآن</p>
          )}
        </CollapsibleSection>

        {/* مسحات ركن الترفيه — إجمالي المسحات (كل الأيام) */}{' '}
        <CollapsibleSection title="مسحات ركن الترفيه">
          {scanTotals && scanTotals.game > 0 ? (
            <div className="gd-dash-scan-card">
              <div className="gd-dash-scan-ringwrap">
                <svg
                  viewBox="0 0 42 42"
                  className="gd-dash-scan-ring"
                  aria-label="إجمالي مسحات ركن الترفيه"
                >
                  <circle cx="21" cy="21" r="15.9" className="gd-dash-donut-track" />
                  <circle
                    cx="21" cy="21" r="15.9"
                    className="gd-dash-donut-segment gd-dash-scan-game"
                    strokeDasharray="100 0"
                    strokeDashoffset="25"
                  />
                </svg>
                <span className="gd-dash-scan-value">{scanTotals.game}</span>
              </div>
              <div className="gd-dash-scan-info">
                <strong>إجمالي مسحات ركن الترفيه</strong>
                <span>كل الأيام · مسح واحد لكل طالب طوال الفعالية</span>
              </div>
            </div>
          ) : (
            <p className="gd-dash-empty-note">ما في مسحات ركن الترفيه للآن</p>
          )}
        </CollapsibleSection>

        {/* زيارات الكلية (ركن التوجيه) — قائمة مرتبة بكل الكليات */}
        <CollapsibleSection
          title="زيارة الكلية (ركن التوجيه)"
          badge={
            analytics && (
              <span className="gd-dash-analytics-total">
                الإجمالي: {analytics.college_visits.reduce((s, v) => s + v.count, 0)}
              </span>
            )
          }
        >
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
        </CollapsibleSection>

        {/* حضور كل محاضرة — أعمدة رأسية */}
        <CollapsibleSection title="حضور كل محاضرة">
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
        </CollapsibleSection>

        {/* توزيع المعدل — أعمدة رأسية (فئات العرض 10) */}
        <CollapsibleSection title="توزيع المعدل (0-10 … 90-100)">
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
        </CollapsibleSection>

        {/* توزيع سنة الشهادة — أعمدة رأسية */}
        <CollapsibleSection title="توزيع سنة الشهادة">
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
        </CollapsibleSection>

        {/* علمي/أدبي — دونات بنسب مئوية */}
        <CollapsibleSection title="علمي / أدبي">
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
        </CollapsibleSection>

      </main>
    </div>
  );
};

export default GeneralDirectorDashboard;