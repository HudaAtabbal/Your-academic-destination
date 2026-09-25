import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminHeader from '../../components/AdminHeader';
import { apiGet, apiRequest, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import { FACULTY_LABELS } from '../../api/faculties';
import '../../style/TeamAccountsPage.css';

const TEAM_PAGE_SIZE = 10;

const mapAccount = (account) => ({
  username: account.username,
  role: ROLE_LABELS[account.role] || account.role,
  roleType: account.role,
  // المفتاح الخام (English) للتحرير + الاسم العربي للعرض
  facultyKey: account.college,
  faculty: FACULTY_LABELS[account.college] || account.college || '—',
});

const TeamAccountsPage = ({ userRole = 'المدير العام' }) => {
  const navigate = useNavigate();

  const [teamMembers, setTeamMembers] = useState([]);
  const [teamPage, setTeamPage] = useState(1);
  const [teamTotal, setTeamTotal] = useState(null);
  const [teamSearch, setTeamSearch] = useState('');
  const [teamQuery, setTeamQuery] = useState('');
  const [teamVersion, setTeamVersion] = useState(0);

  // بحث بالاسم مع debounce 400ms مثل لوحة التحكم — يعيد ترقيم الصفحة لصفحة 1
  useEffect(() => {
    const timer = setTimeout(() => {
      setTeamPage(1);
      setTeamQuery(teamSearch.trim());
    }, 400);
    return () => clearTimeout(timer);
  }, [teamSearch]);

  // جلب الحسابات من السيرفر — بحث + ترقيم (server-side عبر البحث بالاسم)
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

  const teamTotalPages = teamTotal === null ? 1 : Math.max(1, Math.ceil(teamTotal / TEAM_PAGE_SIZE));
  const currentTeamPage = Math.min(teamPage, teamTotalPages);

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

      <main className="gd-dash-main-container">
        <section className="gd-dash-section-wrapper">
          <div className="gd-dash-section-heading-row">
            <h1 className="gd-dash-section-heading">حسابات فريق العمل</h1>
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
                            className="ta-pill-btn ta-pill-edit"
                            onClick={() => handleEditMember(member)}
                          >
                            تعديل
                          </button>
                          <button
                            type="button"
                            className="ta-pill-btn ta-pill-delete"
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
      </main>
    </div>
  );
};

export default TeamAccountsPage;