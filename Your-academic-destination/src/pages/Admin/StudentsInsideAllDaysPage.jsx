import React, { useEffect, useMemo, useState } from 'react';
import { apiGet, ApiError } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import '../../style/InWalkIncompletePage.css';
import '../../style/StudentsInsideAllDaysPage.css';

const PAGE_SIZE = 20;

// الفلترة/الترتيب الافتراضية: الكل + الأعلى نقاطاً أولاً + بدون قيد نوع التسجيل
const DEFAULT_ORDER = 'desc';

// هاد النهج "موازن": بنجيب كل السجلات مرة وحدة عنده فتح الواجهة (حتى ١٠ صفحات ×
// ١٠٠ = ١٠٠٠ صف)، وبعدها الفلترة/الترتيب/الترقيم كلهم محليين على المتصفح بدون أي
// طلبات سيرفر. وبالتوازي بنعمل تحديث صامت خلفي كل ٣٠ ثانية حتى الإدارة تشوف
// بيانات طازة بدون ما نكسر تفاعل المستخدم السريع.
const REFRESH_MS = 30000;
const FETCH_LIMIT = 100;
const MAX_PAGES = 10;

// نجيب كل صفوف الطلاب داخل الجامعة (كل الأيام) دفعة وحدة متسلسلة
const fetchAllStudentsInside = async () => {
  const items = [];
  let page = 1;
  let total = 0;
  while (page <= MAX_PAGES) {
    const params = new URLSearchParams({
      page: String(page),
      limit: String(FETCH_LIMIT),
      order: 'desc',
    });
    const response = await apiGet(`/admin/dashboard/students-inside?${params.toString()}`);
    items.push(...(response.items || []));
    total = response.total;
    if (items.length >= total) break;
    page += 1;
  }
  return { items, total };
};

const StudentsInsideAllDaysPage = () => {
  // الدور محفوظ بالـ localStorage وقت تسجيل الدخول (accountRole) — منقرأه هون
  // مباشرة لأن النمط المعتمد بالمشروع هو القراءة من localStorage (راجع
  // InWalkIncompletePage). صفحة الطلاب داخل الجامعة متاحة للمدير العام فقط.
  const userRole = localStorage.getItem('accountRole');
  const isSuperAdmin = userRole === 'super_admin';

  // كل السجلات المحمّلة مرة وحدة + الفلاتر/الترتيب الحيليين
  const [allItems, setAllItems] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [page, setPage] = useState(1);
  // قيمة حقل الرمز كما يكتبها المستخدم — بتصير فلترة حيّة محلية فوراً
  const [codeInput, setCodeInput] = useState('');
  const [order, setOrder] = useState(DEFAULT_ORDER);
  const [regType, setRegType] = useState('');

  // تحميل أولي + تحديث صامت دوري
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const { items, total } = await fetchAllStudentsInside();
        if (cancelled) return;
        setAllItems(items);
        setTotalCount(total);
        setError('');
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل السجلات');
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    load();
    const timer = setInterval(() => {
      if (!cancelled) load();
    }, REFRESH_MS);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  // الفلترة الحيّة المحلية — ما في أي طلب باك، فورّي
  const filteredItems = useMemo(() => {
    const keyword = codeInput.trim().toLowerCase();
    return allItems.filter((item) => {
      const code = (item.unique_code || '').toLowerCase();
      if (keyword && !code.includes(keyword)) return false;
      if (regType === 'R' && !code.startsWith('r-')) return false;
      if (regType === 'W' && !code.startsWith('w-')) return false;
      return true;
    });
  }, [allItems, codeInput, regType]);

  // الترتيب المحلي (تنازلي/تصاعدي بالنقاط مع ربط بالرمز) — بدون سيرفر
  const sortedItems = useMemo(() => {
    const sorted = [...filteredItems];
    sorted.sort((a, b) => {
      const diff =
        order === 'desc'
          ? b.total_points - a.total_points
          : a.total_points - b.total_points;
      if (diff !== 0) return diff;
      return String(a.unique_code).localeCompare(String(b.unique_code));
    });
    return sorted;
  }, [filteredItems, order]);

  // الترقيم المحلي
  const totalPages = sortedItems.length
    ? Math.max(1, Math.ceil(sortedItems.length / PAGE_SIZE))
    : 1;
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const pageItems = sortedItems.slice(startIndex, startIndex + PAGE_SIZE);

  const handleCodeChange = (e) => {
    setCodeInput(e.target.value);
    setPage(1);
  };

  const handleOrder = (nextOrder) => {
    setOrder(nextOrder);
    setPage(1);
  };

  const handleRegType = (nextRegType) => {
    setRegType((prev) => (prev === nextRegType ? '' : nextRegType));
    setPage(1);
  };

  const handlePrevPage = () => setPage((p) => Math.max(1, p - 1));
  const handleNextPage = () => setPage((p) => Math.min(totalPages, p + 1));

  return (
    <div className="gd-dash-viewport">
      {isSuperAdmin && <AdminHeader />}

      <div className={`card-wrapper ${isSuperAdmin ? 'admin-gate-mode' : ''}`}>
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

            {/* Filter Row — فلترة فورية محلية: رمز + نوع التسجيل (R/W) + ترتيب النقاط */}
            <div className="filter-row">
              <input
                type="text"
                dir="ltr"
                className="filter-input"
                placeholder="الرمز (بحث جزئي)"
                autoComplete="off"
                value={codeInput}
                onChange={handleCodeChange}
              />
              <button
                type="button"
                className={`filter-toggle ${regType === 'R' ? 'filter-toggle-active' : ''}`}
                onClick={() => handleRegType('R')}
                title="المسجّلين (رمز R)"
              >
                مسجلين (R)
              </button>
              <button
                type="button"
                className={`filter-toggle ${regType === 'W' ? 'filter-toggle-active' : ''}`}
                onClick={() => handleRegType('W')}
                title="ووك إن (رمز W)"
              >
                ووك إن (W)
              </button>
              <button
                type="button"
                className={`filter-toggle ${order === 'desc' ? 'filter-toggle-active' : ''}`}
                onClick={() => handleOrder('desc')}
                title="ترتيب مجموع النقاط تنازلياً"
              >
                الأعلى نقاطاً أولاً
              </button>
              <button
                type="button"
                className={`filter-toggle ${order === 'asc' ? 'filter-toggle-active' : ''}`}
                onClick={() => handleOrder('asc')}
                title="ترتيب مجموع النقاط تصاعدياً"
              >
                الأقل نقاطاً أولاً
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
                        {pageItems.map((item) => (
                          <tr key={item.unique_code}>
                            <td className="code-cell" dir="ltr">{item.unique_code}</td>
                            <td className="name-cell">{item.full_name || 'لم يُدخل بعد'}</td>
                            <td className="phone-cell" dir="ltr">{item.contact_id || '—'}</td>
                            <td className="points-cell">{item.total_points}</td>
                          </tr>
                        ))}
                        {pageItems.length === 0 && (
                          <tr>
                            <td colSpan={4} className="empty-cell">
                              لا يوجد طلاب مطابقون للفلترة
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
                        disabled={currentPage <= 1}
                      >
                        السابق
                      </button>
                      <span className="pagination-info">
                        صفحة {currentPage} من {totalPages}
                      </span>
                      <button
                        type="button"
                        className="pagination-btn"
                        onClick={handleNextPage}
                        disabled={currentPage >= totalPages}
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
    </div>
  );
};

export default StudentsInsideAllDaysPage;