import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet, ApiError } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import '../../style/InWalkIncompletePage.css';
import '../../style/TopStudentsPage.css';

const PAGE_SIZE = 20;

const DASH = '—';

// نفس معايير "الطلاب المتميزون" بالداشبورد — الربط عبر ?metric=
const METRICS = [
  { key: 'lectures', label: 'أكثر حضور محاضرات', unit: 'محاضرة' },
  { key: 'tours', label: 'أكثر جولات كليات', unit: 'جولة' },
  { key: 'presence', label: 'أطول تواجد بالجامعة' },
  { key: 'union_all', label: 'زاروا كل أركان الاتحاد' },
];

const METRIC_KEYS = METRICS.map((m) => m.key);

function fmtPresence(val) {
  const n = Number(val);
  if (Number.isNaN(n) || !Number.isFinite(n)) return DASH;
  const h = Math.floor(n / 60);
  const m = Math.round(n % 60);
  if (h === 0) return `${m}د`;
  if (m === 0) return `${h}س`;
  return `${h}س ${m}د`;
}

function formatValue(metric, value) {
  if (value == null) return DASH;
  if (metric === 'union_all') return 'الأركان الثلاثة';
  if (metric === 'presence') return fmtPresence(value);
  const meta = METRICS.find((m) => m.key === metric);
  const unit = meta && meta.unit;
  return unit ? `${value} ${unit}` : String(value);
}

const TopStudentsPage = ({ userRole = 'المدير العام' }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  // المعيار من الـ URL مع fallback آمن لأي قيمة غير معروفة
  const rawMetric = searchParams.get('metric') || 'lectures';
  const metric = METRIC_KEYS.includes(rawMetric) ? rawMetric : 'lectures';

  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // ترقيم خادمي حسب المعيار والصفحة — بدون سلامة كسر التحميل عند التبديل
  useEffect(() => {
    let cancelled = false;

    apiGet(
      `/admin/dashboard/top-students?metric=${metric}&page=${page}&limit=${PAGE_SIZE}`
    )
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError('');
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل القائمة');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [metric, page]);

  const items = data?.items || [];
  const total = data?.total ?? null;
  const totalPages = data?.total_pages
    ?? (total == null ? 1 : Math.max(1, Math.ceil(total / PAGE_SIZE)));
  const currentPage = Math.min(page, totalPages);

  const handleMetric = (key) => {
    if (key === metric) return;
    setPage(1);
    setSearchParams({ metric: key });
  };

  const handlePrevPage = () => setPage((p) => Math.max(1, p - 1));
  const handleNextPage = () => setPage((p) => Math.min(totalPages, p + 1));

  return (
    <div className="gd-dash-viewport">
      <AdminHeader userRole={userRole} />

      <div className="card-wrapper admin-gate-mode">
        <div className="card-container">
          <main className="page-body">

            <div className="tsp-head">
              <h1 className="tsp-title">الطلاب المتميزون</h1>
              {total !== null && <span className="tsp-total">الإجمالي: {total}</span>}
            </div>

            <div className="tsp-tabs" role="tablist" aria-label="المعيار">
              {METRICS.map((m) => (
                <button
                  key={m.key}
                  type="button"
                  role="tab"
                  aria-selected={metric === m.key}
                  className={metric === m.key ? 'tsp-tab is-on' : 'tsp-tab'}
                  onClick={() => handleMetric(m.key)}
                >
                  {m.label}
                </button>
              ))}
            </div>

            <section className="table-section">
              {error && <p className="table-error-message">{error}</p>}
              {isLoading && <p className="table-loading-message">جاري التحميل...</p>}

              {!isLoading && !error && (
                <>
                  <div className="table-wrapper">
                    <table className="data-table tsp-table">
                      <thead>
                        <tr>
                          <th className="tsp-th-rank">#</th>
                          <th className="tsp-th-name">الاسم</th>
                          <th className="tsp-th-code">الرمز</th>
                          <th className="tsp-th-value">القيمة</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((s) => (
                          <tr key={s.unique_code || s.rank}>
                            <td className="tsp-rank">{s.rank}</td>
                            <td className="tsp-name">{s.full_name || DASH}</td>
                            <td className="tsp-code" dir="ltr">{s.unique_code || DASH}</td>
                            <td className="tsp-value">{formatValue(metric, s.value)}</td>
                          </tr>
                        ))}
                        {items.length === 0 && (
                          <tr>
                            <td colSpan={4} className="empty-cell">
                              ما في طلاب متميزين بهالمعيار للآن
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

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

export default TopStudentsPage;