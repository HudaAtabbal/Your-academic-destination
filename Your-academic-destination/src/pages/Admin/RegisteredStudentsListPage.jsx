import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/api';
import AdminHeader from '../../components/AdminHeader';
import '../../style/RegisteredStudentsListPage.css';

const PAGE_SIZE = 20;

// عرض حالة التحقق بالعربي — نفس اصطلاح باقي اللوحات
const VERIFICATION_DISPLAY = {
  verified: { label: 'موثّق', type: 'complete' },
  pending: { label: 'قيد التحقق', type: 'partial' },
};

const RegisteredStudentsListPage = () => {
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await apiGet(
          `/admin/students/registered?page=${page}&limit=${PAGE_SIZE}`
        );
        setRecords(response.items);
        setTotalCount(response.total);
      } catch (err) {
        setError(err.message || 'صار خطأ بتحميل السجلات');
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [page]);

  const totalPages = totalCount ? Math.max(1, Math.ceil(totalCount / PAGE_SIZE)) : 1;

  return (
    <div className="gd-dash-viewport">
      <AdminHeader />

      <main className="page-body">
        {/* نت #1 — عدد المسجّلين */}
        <section className="stats-row">
          <div className="stat-card">
            <span className="stat-label">مسجّلون إلكترونياً</span>
            <span className="stat-value dark-green-text">{totalCount ?? '—'}</span>
          </div>
        </section>

        <section className="table-section">
          <h2 className="section-title">قائمة المسجّلين إلكترونياً</h2>

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
                      <th>سنة الشهادة</th>
                      <th>نوع الشهادة</th>
                      <th>المعدل</th>
                      <th>الحالة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((item) => {
                      const verdict = VERIFICATION_DISPLAY[item.verification_status] || {
                        label: item.verification_status,
                        type: 'empty',
                      };
                      return (
                        <tr key={item.unique_code}>
                          <td className="code-cell" dir="ltr">{item.unique_code}</td>
                          <td className="name-cell">{item.full_name || '—'}</td>
                          <td className="phone-cell" dir="ltr">{item.contact_id || '—'}</td>
                          <td>{item.bacc_year ?? '—'}</td>
                          <td>{item.certificate_type ? (item.certificate_type === 'scientific' ? 'علمي' : item.certificate_type === 'literary' ? 'أدبي' : item.certificate_type) : '—'}</td>
                          <td>{item.bacc_average ?? '—'}</td>
                          <td>
                            <span className={`status-badge ${verdict.type}`}>
                              {verdict.label}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                    {records.length === 0 && (
                      <tr>
                        <td colSpan={7} className="empty-cell">
                          لا يوجد مسجّلون إلكترونياً بعد
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* ترقيم الصفحات */}
              {totalPages > 1 && (
                <div className="pagination-row">
                  <button
                    type="button"
                    className="pagination-btn"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
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
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
  );
};

export default RegisteredStudentsListPage;
