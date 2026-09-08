import React, { useState, useEffect } from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import { apiGet, ApiError } from '../../api/api';
import '../../style/MyPointsPage.css';

// ⚠️ جدول القيم هون نصوص ثابتة بالفرونت (نفس تعليق الباك: "القيم معلنة ولا تتغير") —
// الباك بيرجّع بس total_points النهائي، مش تفصيل كل محطة، فهاد الجدول للعرض بس
const STATIONS = [
  { name: 'دخول البوابة (مرة يومياً)', points: '5' },
  { name: 'حضور ندوة', points: '10' },
  { name: 'جولة كلية', points: '10' },
  { name: 'استشارة فردية', points: '15' },
  { name: 'الاستبيان البعدي', points: '20' },
];

const MyPointsPage = ({
  footerNote = 'تُحتسب حتى ثلاث ندوات في اليوم — النقاط لتشجيعك على التنوّع لا على الجري.',
  awardsNote = 'الجوائز تُسلَّم في حفل الختام، اليوم الثالث --:16.',
}) => {
  const [points, setPoints] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const studentCode = localStorage.getItem('studentCode');
    if (!studentCode) {
      setError('في مشكلة بجلستك، يرجى الرجوع والتسجيل من جديد');
      return;
    }

    apiGet(`/students/${studentCode}/points`)
      .then((res) => setPoints(res.total_points))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : 'صار خطأ بتحميل نقاطك');
      });
  }, []);

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="نقاطي"
          stepText="احصل على اكبر عدد من النقاط لتدخل السحب على الجوائز"
          onBack={() => window.history.back()}
        />

        {/* Scrollable Main Content */}
        <main className="page-body">
          
          {/* Main Score Card */}
          <div className="score-card">
            <div className="score-value">{points ?? '—'}</div>
            <p className="score-subtitle">نقطة</p>
            {error && <p className="points-error-message">{error}</p>}
          </div>

          {/* Points Breakdown Section */}
          <section className="points-table-card">
            <div className="table-caption">القيم معلنة ولا تتغير</div>
            
            <table className="points-table">
              <thead>
                <tr>
                  <th className="col-name">المحطة</th>
                  <th className="col-points">النقاط</th>
                </tr>
              </thead>
              <tbody>
                {STATIONS.map((item, index) => (
                  <tr key={index}>
                    <td className="col-name">{item.name}</td>
                    <td className="col-points">{item.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="table-note">{footerNote}</p>
          </section>

          {/* Awards Footer Notice */}
          <div className="awards-notice">
            {awardsNote}
          </div>

        </main>

        {/* Bottom Navigation Bar Component */}
        <BottomNav />

      </div>
    </div>
  );
};

export default MyPointsPage;