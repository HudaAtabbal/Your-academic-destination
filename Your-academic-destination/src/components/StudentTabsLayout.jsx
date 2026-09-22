import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import MyCard from '../pages/student/MyCard';
import YawmiPage from '../pages/student/YawmiPage';
import AcademicGuide from '../pages/student/AcademicGuide';
import MapPage from '../pages/student/MapPage';
import Survey from '../pages/student/Survey';
import MyPointsPage from '../pages/student/MyPointsPage';
import '../style/StudentTabsLayout.css';

// الغلاف اللي بيخلي تابات الطالب (بطاقاتي/الدليل/الاستبيان/نقاطي) حئاة —
// أول صفحة بتتبني لأول زيارة، وبعدها التبديل بين التابات مجرد إظهار/إخفاء
// (hidden) من غير ما تعيد البناء أو تعيد جَلب البيانات من السيرفر.
const TABS = [
  { route: '/my-card', Component: MyCard },
  { route: '/yawmi', Component: YawmiPage },
  { route: '/academic-guide', Component: AcademicGuide },
  { route: '/university-map', Component: MapPage },
  { route: '/survey', Component: Survey },
  { route: '/my-points', Component: MyPointsPage },
];

const StudentTabsLayout = () => {
  const { pathname } = useLocation();

  // الصفحات يلي انزرت فعلياً — الباقي ما بيتبنّى (تحميل كسول)
  const [visited, setVisited] = useState(() => new Set([pathname]));

  useEffect(() => {
    setVisited((prev) => {
      if (prev.has(pathname)) return prev;
      const next = new Set(prev);
      next.add(pathname);
      return next;
    });
  }, [pathname]);

  return (
    <div className="student-tabs-shell">
      {TABS.map(({ route, Component }) =>
        visited.has(route) ? (
          <section key={route} className="student-tab-panel" hidden={pathname !== route}>
            <Component active={pathname === route} />
          </section>
        ) : null,
      )}
    </div>
  );
};

export default StudentTabsLayout;