import React, { useEffect, useState } from 'react';
import { apiGet, ApiError } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import { COLLEGE_LABELS } from '../../api/colleges';
import '../../style/InWalkIncompletePage.css';
import '../../style/StudentsInsideAllDaysPage.css';

const PAGE_SIZE = 20;

// تحويل جواب السؤال الأول (opinion_change) للعرض — نفس نصوص صفحة الاستبيان
const OPINION_LABELS = {
  decided: 'صار عندي قرار',
  changed_completely: 'تغيّر تماماً',
  confirmed_choice: 'تأكّد اللي كنت ناويه',
  still_confused: 'لسا محتار',
};

const formatDateTime = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString('ar-SY', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
};

const SurveyCompletionsPage = () => {
  const userRole = localStorage.getItem('accountRole');
  const isSuperAdmin = userRole === 'super_admin';

  const [items, setItems] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [page, setPage] = useState(1);
  const [codeInput, setCodeInput] = useState('');
  const [codeQuery, setCodeQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // تباطؤ البحث بالرمز — بتشتغل بعد 400ms من آخر كتابة (نفس نمط البحث بالداشبورد)
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      setCodeQuery(codeInput.trim());
    }, 400);
    return () => clearTimeout(timer);
  }, [codeInput]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError('');
      try {
        const params = new URLSearchParams({
          page: String(page),
          limit: String(PAGE_SIZE),
        });
        if (codeQuery) params.set('code', codeQuery);

        const response = await apiGet(
          `/admin/dashboard/survey-completions?${params.toString()}`
        );
        if (cancelled) return;
        setItems(response.items || []);
        setTotalCount(response.total ?? null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل السجلات');
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [page, codeQuery]);

  const totalPages = totalCount ? Math.max(1, Math.ceil(totalCount / PAGE_SIZE)) : 1;
  const currentPage = Math.min(page, totalPages);

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
            <h2 className="section-title">أكملوا الاستبيان</h2>

            <div className="stats-row">
              <div className="stat-card">
                <span className="stat-label">إجمالي من أكملوا الاستبيان</span>
                <span className="stat-value dark-green-text">{totalCount ?? '—'}</span>
              </div>
            </div>

            <div className="filter-row">
              <input
                type="text"
                dir="rtl"
                className="filter-input"
                placeholder="بحث بالاسم أو الرمز..."
                autoComplete="off"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
              />
            </div>

            <section className="table-section">
              {error && <p className="table-error-message">{error}</p>}
              {isLoading && <p className="table-loading-message">جاري التحميل...</p>}

              {!isLoading && !error && (
                <>
                  <div className="table-wrapper">
                    <table className="data-table survey-table">
                      <thead>
                        <tr>
                          <th>الرمز</th>
                          <th>الاسم</th>
                          <th>رقم التواصل</th>
                          <th>وقت الدخول</th>
                          <th>التخصصات المختارة</th>
                          <th>جواب السؤال الأول</th>
                          <th>التخصص الحالي</th>
                          <th>وقت الإجابة</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => (
                          <tr key={item.unique_code}>
                            <td className="code-cell" dir="ltr">{item.unique_code}</td>
                            <td className="name-cell">{item.full_name || 'لم يُدخل بعد'}</td>
                            <td className="phone-cell" dir="ltr">{item.contact_id || '—'}</td>
                            <td className="time-cell">{formatDateTime(item.first_campus_entry_at)}</td>
                            <td className="majors-cell">
                              {(item.chosen_colleges || []).length > 0
                                ? item.chosen_colleges
                                    .map((c) => COLLEGE_LABELS[c] || c)
                                    .join('، ')
                                : '—'}
                            </td>
                            <td className="opinion-cell">
                              {OPINION_LABELS[item.opinion_change] || item.opinion_change || '—'}
                            </td>
                            <td className="major-cell">
                              {item.survey_college
                                ? COLLEGE_LABELS[item.survey_college] || item.survey_college
                                : '—'}
                            </td>
                            <td className="time-cell">{formatDateTime(item.answered_at)}</td>
                          </tr>
                        ))}
                        {items.length === 0 && (
                          <tr>
                            <td colSpan={8} className="empty-cell">
                              لا يوجد من أكملوا الاستبيان مطابقون للفلترة
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

export default SurveyCompletionsPage;