import React, { useEffect, useRef, useState } from 'react';
import { apiGet, ApiError } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import '../../style/InWalkIncompletePage.css';
import '../../style/StudentsInsideAllDaysPage.css';

const PAGE_SIZE = 20;

// الفلترة/الترتيب الافتراضية: الكل + الأعلى نقاطاً أولاً + بدون قيد نوع التسجيل
const DEFAULT_ORDER = 'desc';

// الفلترة بتشتغل فورياً مع debounce خفيف — ما في زر "تطبيق" بعد اليوم
const DEBOUNCE_MS = 300;

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

  // قيمة حقل الرمز كما يكتبها المستخدم (تتبّع فوري للكتابة)
  const [codeInput, setCodeInput] = useState('');
  // قيم الفلترة المطبّقة فعلياً على الطلب
  const [filters, setFilters] = useState({ code: '', order: DEFAULT_ORDER, regType: '' });

  // مؤقّت مؤجَّل لحقل الرمز — كل كتابة تمهّد المؤقّت حتى يتوقف المستخدم
  const debounceRef = useRef(null);

  useEffect(
    () => () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    },
    []
  );

  // تطبيق رمز مكتوب (فوري عند Enter، أو بعد توقف الكتابة)
  const commitCode = (value) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setPage(1);
    setFilters((prev) => ({ ...prev, code: value.trim() }));
  };

  const handleCodeChange = (e) => {
    const value = e.target.value;
    setCodeInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => commitCode(value), DEBOUNCE_MS);
  };

  const handleCodeKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      commitCode(codeInput);
    }
  };

  const setOrder = (nextOrder) => {
    setPage(1);
    setFilters((prev) => ({ ...prev, order: nextOrder }));
  };

  const toggleRegType = (regType) => {
    setPage(1);
    setFilters((prev) => ({ ...prev, regType: prev.regType === regType ? '' : regType }));
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
        if (filters.regType) params.set('reg_type', filters.regType);

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

            {/* Filter Row — فلترة فورية: رمز + نوع التسجيل (R/W) + ترتيب النقاط */}
            <div className="filter-row">
              <input
                type="text"
                dir="ltr"
                className="filter-input"
                placeholder="الرمز (بحث جزئي)"
                autoComplete="off"
                value={codeInput}
                onChange={handleCodeChange}
                onKeyDown={handleCodeKeyDown}
              />
              <button
                type="button"
                className={`filter-toggle ${filters.regType === 'R' ? 'filter-toggle-active' : ''}`}
                onClick={() => toggleRegType('R')}
                title="المسجّلين (رمز R)"
              >
                مسجلين (R)
              </button>
              <button
                type="button"
                className={`filter-toggle ${filters.regType === 'W' ? 'filter-toggle-active' : ''}`}
                onClick={() => toggleRegType('W')}
                title="ووك إن (رمز W)"
              >
                ووك إن (W)
              </button>
              <button
                type="button"
                className={`filter-toggle ${filters.order === 'desc' ? 'filter-toggle-active' : ''}`}
                onClick={() => setOrder('desc')}
                title="ترتيب مجموع النقاط تنازلياً"
              >
                الأعلى نقاطاً أولاً
              </button>
              <button
                type="button"
                className={`filter-toggle ${filters.order === 'asc' ? 'filter-toggle-active' : ''}`}
                onClick={() => setOrder('asc')}
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
    </div>
  );
};

export default StudentsInsideAllDaysPage;