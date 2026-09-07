import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet, ApiError } from '../../api/api';
import '../../style/InWalkIncompletePage.css';

// تحويل status الراجعة من الباك ("no_data" | "partial") لشكل العرض العربي
const STATUS_DISPLAY = {
  no_data: { label: 'بلا بيانات', type: 'empty' },
  partial: { label: 'جزئي', type: 'partial' },
};

const InWalkIncompletePage = () => {
  const navigate = useNavigate();

  const [records, setRecords] = useState([]);
  const [totalIncomplete, setTotalIncomplete] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await apiGet('/admin/students/walkin-incomplete?page=1&limit=20');
        setRecords(response.items);
        setTotalIncomplete(response.total);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل السجلات');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleCompleteData = (uniqueCode) => {
    // بننقل لصفحة إدارة بيانات الطالب مع تمرير رقم السجل حتى تنعبى خانة البحث فيه تلقائياً
    navigate('/gate-manage', { state: { presetId: uniqueCode } });
  };

  const handleBack = () => {
    navigate('/gate-manage');
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Top Header */}
        <header className="page-header">
          <div className="header-badge">مدير بيانات الطلاب</div>
          
          <div className="header-brand">
            <div className="brand-text">
              <h1 className="brand-title">وجهتك الأكاديمية 2</h1>
              <p className="brand-subtitle">لوحة التحكم</p>
            </div>
          </div>
        </header>

        {/* Scrollable Main Body */}
        <main className="page-body">
          
          {/* Back Navigation Link */}
          <div className="back-link-container">
            <button type="button" onClick={handleBack} className="back-link">
              ← رجوع للبحث عن طالب
            </button>
          </div>

          {/* Top 3 Stat Cards */}
          <div className="stats-row">
            {/* ⚠️ هالكرتين (حضرت نشاط واحد / بلا أي بيانات) ما عندهن endpoint مخصص بالباك لسا،
                فضلين موك مؤقتاً — لازم نطلب من الباك إضافتهن لـ StudentStatsResponse */}
            <div className="stat-card">
              <span className="stat-label">حضرت نشاط واحد على الأقل</span>
              <span className="stat-value dark-green-text">١٥</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">بلا أي بيانات مدوّنة</span>
              <span className="stat-value reddish-text">٢٢</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">سجلات in-walk غير مكتملة</span>
              <span className="stat-value orange-text">{totalIncomplete ?? '—'}</span>
            </div>
          </div>

          {/* Table Container Section */}
          <section className="table-section">
            <h2 className="section-title">السجلات بانتظار الإكمال</h2>

            {error && <p className="table-error-message">{error}</p>}
            {isLoading && <p className="table-loading-message">جاري التحميل...</p>}

            {!isLoading && !error && (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>الرمز</th>
                      <th>الاسم الثلاثي</th>
                      <th>رقم التواصل</th>
                      <th>الحالة</th>
                      <th></th>
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
                          <td className="action-cell">
                            <button
                              type="button"
                              className="btn-action"
                              onClick={() => handleCompleteData(item.unique_code)}
                            >
                              أكمل البيانات
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Footer Warning Notice */}
          <p className="footer-warning">
            سجل بلا أي نشاط حضور ولم يُستخدم إطلاقاً يُعتبر فارغاً ويُحذف ضمن التنظيف اللاحق للحدث. أما أي سجل عليه نشاط واحد على الأقل، فلا يُحذف أبداً حتى لو ظلّت بياناته الشخصية ناقصة.
          </p>

        </main>
      </div>
    </div>
  );
};

export default InWalkIncompletePage;