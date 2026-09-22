import React, { useState, useEffect, useRef } from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import { apiGet, ApiError } from '../../api/api';
import '../../style/MyPointsPage.css';

// ⚠️ جدول القيم هون نصوص ثابتة بالفرونت (نفس تعليق الباك: "القيم معلنة ولا تتغير") —
// الباك بيرجّع total_points + تفاصيل سقوف اليوم (today_lecture_count /
// lectures_capped_today / today_tour_count / tours_capped_today)، فهاد الجدول للعرض بس.
const STATIONS = [
  { name: 'دخول البوابة (مرة يومياً)', points: '5' },
  { name: 'حضور محاضرة (حتى 3 محاضرات يومياً)', points: '10' },
  { name: 'جولة كلية (حتى 3 جولات يومياً)', points: '10' },
  { name: 'استشارة فردية', points: '15' },
  { name: 'الاستبيان البعدي', points: '20' },
];

// النقاط هي المعلومة الوحيدة داخل تطبيق الطالب يلي لازم تبقى طازة —
// منحدّثها بصمت كل ٦٠ ثانية أثناء فتح التاب (حسب موازنة التحميل).
const POINTS_REFRESH_MS = 60000;

const MyPointsPage = ({
  active = false,
  footerNote = 'تُحتسب النقاط حتى 3 محاضرات يومياً و3 جولات يومياً — النقاط لتشجيعك على التنوّع لا على الجري.',
  awardsNote = 'الجوائز تُسلَّم في حفل الختام، اليوم الثالث --:16.',
}) => {
  const [points, setPoints] = useState(null);
  const [lecturesCappedToday, setLecturesCappedToday] = useState(false);
  const [toursCappedToday, setToursCappedToday] = useState(false);
  const [error, setError] = useState('');
  // بنمرّر سولاج فعالية عشان ما نعمل استطلاعات مركّبة فوق بعضها
  const pendingRef = useRef(false);

  useEffect(() => {
    if (!active) return;

    const loadPoints = async () => {
      if (pendingRef.current) return;
      const studentCode = localStorage.getItem('studentCode');
      if (!studentCode) {
        setError('يوجد مشكلة في جلستك، يرجى الرجوع والتسجيل من جديد');
        return;
      }
      pendingRef.current = true;
      try {
        const res = await apiGet(`/students/${studentCode}/points`);
        setPoints(res.total_points);
        setLecturesCappedToday(!!res.lectures_capped_today);
        setToursCappedToday(!!res.tours_capped_today);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'حدث خطأ اثناء تحميل نقاطك');
      } finally {
        pendingRef.current = false;
      }
    };

    loadPoints();

    const timer = setInterval(loadPoints, POINTS_REFRESH_MS);
    return () => clearInterval(timer);
  }, [active]);

  const personalizedNote = () => {
    if (lecturesCappedToday && toursCappedToday) {
      return 'لقد بلغت الحد الأقصى للمحاضرات والجولات اليوم — لن تُحتسب نقاط إضافية على المزيد منهما اليوم.';
    }
    if (lecturesCappedToday) {
      return 'لقد بلغت الحد الأقصى للمحاضرات اليوم — لن تُحتسب نقاط إضافية على المزيد من المحاضرات اليوم.';
    }
    if (toursCappedToday) {
      return 'لقد بلغت الحد الأقصى للجولات اليوم — لن تُحتسب نقاط إضافية على المزيد من الجولات اليوم.';
    }
    return '';
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">

        <HeaderStep
          title="نقاطي"
          stepText="احصل على اكبر عدد من النقاط لتدخل السحب على الجوائز"
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

            {personalizedNote() && (
              <p className="points-cap-note">{personalizedNote()}</p>
            )}
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