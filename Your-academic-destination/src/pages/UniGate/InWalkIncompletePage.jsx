import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet, ApiError } from '../../api/api';
import { ROLE_LABELS } from '../../api/roles';
import AdminHeader from '../../components/AdminHeader';
import '../../style/InWalkIncompletePage.css';

// تحويل status الراجعة من الباك لشكل العرض العربي — للتاب الأول (غير مكتملة)
const STATUS_DISPLAY = {
  no_data: { label: 'بلا بيانات', type: 'empty' },
  partial: { label: 'جزئي', type: 'partial' },
  complete: { label: 'مكتمل', type: 'complete' },
};

const PAGE_SIZE = 20;

// إعدادات كل تاب: قيمة الـ status المرسلة للباك + النصوص المرتبطة فيه
const TABS = [
  {
    id: 'incomplete',
    label: 'غير مكتملة',
    statusParam: 'incomplete',
    sectionTitle: 'السجلات بانتظار الإكمال',
    statCardLabel: 'سجلات in-walk غير مكتملة',
    statCardClass: 'orange-text',
    emptyTableMessage: 'لا يوجد سجلات بهاي الصفحة',
    showCompleteAction: true,
  },
  {
    id: 'complete',
    label: 'مكتملة',
    statusParam: 'complete',
    sectionTitle: 'السجلات المكتملة',
    statCardLabel: 'سجلات in-walk مكتملة',
    statCardClass: 'dark-green-text',
    emptyTableMessage: 'لا يوجد سجلات مكتملة بهاي الصفحة',
    showCompleteAction: false,
  },
];

const InWalkIncompletePage = () => {
  const navigate = useNavigate();

  // الدور محفوظ بالـ localStorage وقت تسجيل الدخول (accountRole) — منقرأه هون
  // مباشرة بدل ما نعتمد على تمريره كـ prop، لأنه التنقّل بالمشروع كله
  // عن طريق navigate() ومافي تمرير props بين الصفحات
  const userRole = localStorage.getItem('accountRole');

  // المدير العام بيشوف الهيدر الإداري الموحّد فوق الصفحة، وباقي الأدوار
  // المعنية بهاي الصفحة بتشوف الكرت العادي
  const isSuperAdmin = userRole === 'super_admin';

  const [activeTab, setActiveTab] = useState('incomplete');
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const currentTab = TABS.find((t) => t.id === activeTab) || TABS[0];

  const handleTabChange = (tabId) => {
    if (tabId === activeTab) return;
    setActiveTab(tabId);
    setPage(1); // بنرجع لأول صفحة كل ما بنبدّل تاب حتى ما نضل واقفين بصفحة مش موجودة بالقائمة التانية
  };

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await apiGet(
          `/admin/students/walkin-incomplete?status=${currentTab.statusParam}&page=${page}&limit=${PAGE_SIZE}`
        );
        setRecords(response.items);
        setTotalCount(response.total);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل السجلات');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [page, activeTab, currentTab.statusParam]);

  const totalPages = totalCount ? Math.max(1, Math.ceil(totalCount / PAGE_SIZE)) : 1;

  const handleCompleteData = (uniqueCode) => {
    // بننقل لصفحة إدارة بيانات الطالب مع تمرير رقم السجل حتى تنعبى خانة البحث فيه تلقائياً
    navigate('/gate-manage', { state: { presetId: uniqueCode } });
  };

  const handlePrevPage = () => {
    setPage((p) => Math.max(1, p - 1));
  };

  const handleNextPage = () => {
    setPage((p) => Math.min(totalPages, p + 1));
  };

  return (
    <div className={`card-wrapper ${isSuperAdmin ? 'admin-gate-mode' : ''}`}>
      {isSuperAdmin && <AdminHeader />}
      <div className="card-container">
        
        {/* Top Header — للمدير العام بنستبدله بالهيدر الإداري الموحّد،
            بينما باقي الأدوار بشوفوا الكرت العادي مع شارة الدور */}
        {!isSuperAdmin && (
          <header className="page-header">
            <div className="header-brand">
              <div className="brand-text">
                <h1 className="brand-title">وجهتك الأكاديمية 2</h1>
                <p className="brand-subtitle">لوحة التحكم</p>
              </div>
            </div>
            <div className="header-badge">{ROLE_LABELS[userRole] || 'مدير بيانات الطلاب'}</div>
          </header>
        )}

        {/* Scrollable Main Body */}
        <main className="page-body">
          
          {/* Top Stat Card — بيتبدّل رقمه وعنوانه حسب التاب المفعّل */}
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-label">{currentTab.statCardLabel}</span>
              <span className={`stat-value ${currentTab.statCardClass}`}>{totalCount ?? '—'}</span>
            </div>
          </div>

          {/* Tabs — غير مكتملة / مكتملة */}
          <div className="tabs-row" role="tablist" aria-label="تبويب السجلات">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'tab-btn-active' : ''}`}
                onClick={() => handleTabChange(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Table Container Section */}
          <section className="table-section">
            <h2 className="section-title">{currentTab.sectionTitle}</h2>

            {error && <p className="table-error-message">{error}</p>}
            {isLoading && <p className="table-loading-message">جاري التحميل...</p>}

            {!isLoading && !error && (
              <>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>الرمز</th>
                        <th>الاسم الثلاثي</th>
                        <th>رقم التواصل</th>
                        <th>الحالة</th>
                        {currentTab.showCompleteAction && <th></th>}
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((item) => {
                        const statusInfo = STATUS_DISPLAY[item.status] || {
                          label: item.status,
                          type: 'empty',
                        };
                        return (
                          <tr key={item.unique_code}>
                            <td className="code-cell" dir="ltr">{item.unique_code}</td>
                            <td className="name-cell">{item.full_name || 'لم يُدخل بعد'}</td>
                            <td className="phone-cell" dir="ltr">{item.contact_id || '—'}</td>
                            <td>
                              <span className={`status-badge ${statusInfo.type}`}>
                                {statusInfo.label}
                              </span>
                            </td>
                            {currentTab.showCompleteAction && (
                              <td className="action-cell">
                                <button
                                  type="button"
                                  className="btn-action"
                                  onClick={() => handleCompleteData(item.unique_code)}
                                >
                                  أكمل البيانات
                                </button>
                              </td>
                            )}
                          </tr>
                        );
                      })}
                      {records.length === 0 && (
                        <tr>
                          <td colSpan={currentTab.showCompleteAction ? 5 : 4} className="empty-cell">
                            {currentTab.emptyTableMessage}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                  <div className="pagination-row">
                    <button
                      type="button"
                      className="pagination-btn"
                      onClick={handlePrevPage}
                      disabled={page <= 1}
                    >
                      السابق
                    </button>
                    <span className="pagination-info">
                      صفحة {page} من {totalPages}
                    </span>
                    <button
                      type="button"
                      className="pagination-btn"
                      onClick={handleNextPage}
                      disabled={page >= totalPages}
                    >
                      التالي
                    </button>
                  </div>
                )}
              </>
            )}
          </section>

          {/* Footer Warning Notice — بتخص سياسة حذف السجلات غير المكتملة فقط، فما إلها معنى بتاب "مكتملة" */}
          {activeTab === 'incomplete' && (
            <p className="footer-warning">
              سجل بلا أي نشاط حضور ولم يُستخدم إطلاقاً يُعتبر فارغاً ويُحذف ضمن التنظيف اللاحق للحدث. أما أي سجل عليه نشاط واحد على الأقل، فلا يُحذف أبداً حتى لو ظلّت بياناته الشخصية ناقصة.
            </p>
          )}

        </main>
      </div>
    </div>
  );
};

export default InWalkIncompletePage;