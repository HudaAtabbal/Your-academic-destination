import React from 'react';
import BottomNav from '../../components/BottomNav'; // قم بتعديل المسار حسب مكان حفظك لمكون BottomNav
import '../../style/MyPointsPage.css';

const MyPointsPage = ({
  points = 35,
  rankText = 'ترتيبك التقريبي بين أعلى 50',
  stations = [
    { name: 'دخول البوابة (مرة يومياً)', points: '5' },
    { name: 'حضور ندوة', points: '10' },
    { name: 'جولة كلية', points: '10' },
    { name: 'استشارة فردية', points: '15' },
    { name: 'الاستبيان البعدي', points: '20' },
  ],
  footerNote = 'تُحتسب حتى ثلاث ندوات في اليوم — النقاط لتشجيعك على التنوّع لا على الجري.',
  awardsNote = 'الجوائز تُسلَّم في حفل الختام، اليوم الثالث --:16.',
}) => {
  return (
    <div className="card-wrapper">
      <div className="card-container">
        
        {/* Title Header */}
        <header className="page-header">
          <h1 className="header-title">نقاطي</h1>
        </header>

        {/* Scrollable Main Content */}
        <main className="page-body">
          
          {/* Main Score Card */}
          <div className="score-card">
            <div className="score-value">{points}</div>
            <p className="score-subtitle">
              نقطة <span className="dot">•</span> {rankText}
            </p>
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
                {stations.map((item, index) => (
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