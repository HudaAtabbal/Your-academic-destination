import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../style/InWalkIncompletePage.css';

const InWalkIncompletePage = () => {
  const navigate = useNavigate();

  const records = [
    { id: 'W-0014', name: 'لم يُدخل بعد', phone: '—', status: 'بلا بيانات', statusType: 'empty' },
    { id: 'W-0027', name: 'أحمد فارس دياب', phone: '—', status: 'بلا بيانات', statusType: 'empty' },
    { id: 'W-0035', name: 'لم يُدخل بعد', phone: '—', status: 'بلا بيانات', statusType: 'empty' },
    { id: 'W-0041', name: 'غنى محمد سلوم', phone: '0991122334', status: 'جزئي', statusType: 'partial' },
    { id: 'W-0052', name: 'لم يُدخل بعد', phone: '—', status: 'بلا بيانات', statusType: 'empty' },
  ];

  const handleCompleteData = (id) => {
    // بننقل لصفحة إدارة بيانات الطالب مع تمرير رقم السجل حتى تنعبى خانة البحث فيه تلقائياً
    navigate('/gate-manage', { state: { presetId: id } });
  };

  const handleBack = () => {
    navigate('/gate-manage');
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Top Header */}
        <header className="page-header">
          
          
          <div className="header-brand">
            <div className="brand-text">
              <h1 className="brand-title">وجهتك الأكاديمية 2</h1>
              <p className="brand-subtitle">لوحة التحكم</p>
            </div>
          </div>
          <div className="header-badge">مدير بيانات الطلاب</div>
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
            <div className="stat-card">
              <span className="stat-label">حضرت نشاط واحد على الأقل</span>
              <span className="stat-value dark-green-text">15</span>
            </div>
            <div className="stat-card">
              <span className="stat-label"> بلا أي بيانات مدوّنة</span>
              <span className="stat-value reddish-text">22</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">سجلات  غير مكتملة</span>
              <span className="stat-value orange-text">37</span>
            </div>
          </div>

          {/* Table Container Section */}
          <section className="table-section">
            <h2 className="section-title">السجلات بانتظار الإكمال</h2>

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
                  {records.map((item) => (
                    <tr key={item.id}>
                      <td className="code-cell" dir="ltr">{item.id}</td>
                      <td className="name-cell">{item.name}</td>
                      <td className="phone-cell" dir="ltr">{item.phone}</td>
                      <td>
                        <span className={`status-badge ${item.statusType}`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="action-cell">
                        <button
                          type="button"
                          className="btn-action"
                          onClick={() => handleCompleteData(item.id)}
                        >
                          أكمل البيانات
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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