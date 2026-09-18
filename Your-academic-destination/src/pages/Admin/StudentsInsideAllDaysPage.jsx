import React, { useEffect, useState } from 'react';
import { apiGet, ApiError } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import '../../style/InWalkIncompletePage.css';
import '../../style/StudentsInsideAllDaysPage.css';

const PAGE_SIZE = 20;

// الفلترة/الترتيب الافتراضية: الكل + الأعلى نقاطاً أولاً
const DEFAULT_ORDER = 'desc';

const StudentsInsideAllDaysPage = () => {
  // الدور محفوظ بالـ localStorage وقت تسجيل الدخول (accountRole) — منقرأه هون
  // مباشرة لأن النمط المعتمد بالمشروع هو القراءة من localStorage (راجع
  // InWalkIncompletePage). صفحة الطلاب داخل الجامعة متاحة للمدير العام فقط.
  const userRole = localStorage.getItem('accountRole');
  const isSuperAdmin = userRole === 'super_admin';

  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // قيم حقول الفلترة كما يكتبها المستخدم (ما بتروح للباك إلا بعد "تطبيق")
  const [codeInput, setCodeInput] = useState('');
  // قيم الفلترة المطبّقة فعلياً على الطلب
  const [filters, setFilters] = useState({ code: '', order: DEFAULT_ORDER });

  const handleApply = () => {
    setPage(1);
    setFilters({ code: codeInput.trim(), order: filters.order });
  };

  const handleClear = () => {
    setCodeInput('');
    setPage(1);
    setFilters({ code: '', order: DEFAULT_ORDER });
  };

  const toggleOrder = () => {
    const nextOrder = filters.order === 'desc' ? 'asc' : 'desc';
    setPage(1);
    setFilters((prev) => ({ ...prev, order: nextOrder }));
  };

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const params = new URLSearchParams({
          page: String(page),
          limit: String(PAGE_SIZE),
          order: filters.order,
        });
        if (filters.code) params.set('code', filters.code);

        const response = await apiGet(`/admin/dashboard/students-inside?${params.toString()}`);
        setRecords(response.items);
        setTotalCount(response.total);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل السجلات');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [page, filters]);

  const totalPages = totalCount ? Math.max(1, Math.ceil(totalCount / PAGE_SIZE)) : 1;

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

        {!isSuperAdmin && (
          <header className="page-header">
            <div className="header-brand">
              <div className="brand-text">
                <h1 className="brand-title">وجهتك الأكاديمية 2</h1>
                <p className="brand-subtitle">لوحة التحكم</p>
              </div>
            </div>
          </header>
        )}

        <main className="page-body">

          {/* Top Stat Card — يلخّص إجمالي الطلاب داخل الجامعة (كل الأيام) */}
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-label">إجمالي الطلاب داخل الجامعة (كل الأيام)</span>
              <span className="stat-value dark-green-text">{totalCount ?? '—'}</span>
            </div>
          </div>

          {/* Filter Row — فلترة بالرمز + ترتيب النقاط */}
          <div className="filter-row">
            <input
              type="text"
              dir="ltr"
              className="filter-input"
              placeholder="الرمز (بحث جزئي)"
              value={codeInput}
              onChange={(e) => setCodeInput(e.target.value)}
            />
            <button
              type="button"
              className={`filter-toggle ${filters.order === 'asc' ? 'filter-toggle-active' : ''}`}
              onClick={toggleOrder}
              title="تبديل ترتيب النقاط"
            >
              {filters.order === 'desc' ? 'الأعلى نقاطاً أولاً' : 'الأقل نقاطاً أولاً'}
            </button>
            <button type="button" className="filter-btn filter-btn-primary" onClick={handleApply}>
              تطبيق
            </button>
            <button type="button" className="filter-btn filter-btn-secondary" onClick={handleClear}>
              مسح
            </button>
          </div>

          {/* Table Container Section */}
          <section className="table-section">
            <h2 className="section-title">الطلاب ممن دخلوا الجامعة (كل الأيام)</h2>

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
                        <th>مجموع النقاط</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((item) => (
                        <tr key={item.unique_code}>
                          <td className="code-cell" dir="ltr">{item.unique_code}</td>
                          <td className="name-cell">{item.full_name || 'لم يُدخل بعد'}</td>
                          <td className="phone-cell" dir="ltr">{item.contact_id || '—'}</td>
                          <td className="points-cell">{item.total_points}</td>
                        </tr>
                      ))}
                      {records.length === 0 && (
                        <tr>
                          <td colSpan={4} className="empty-cell">
                            لا يوجد طلاب بهاي الصفحة
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

        </main>
      </div>
    </div>
  );
};

export default StudentsInsideAllDaysPage;