import { useEffect, useRef, useState } from 'react';
import AdminHeader from '../../components/AdminHeader';
import { apiGet } from '../../api/api';
import { FACULTY_LABELS } from '../../api/faculties';
import usePolling from '../../hooks/usePolling';
import HeroStats from './dashboard/HeroStats';
import SummaryCards from './dashboard/SummaryCards';
import PresenceRow from './dashboard/PresenceRow';
import PeakHoursHeatmap from './dashboard/PeakHoursHeatmap';
import HorizontalBars from './dashboard/HorizontalBars';
import Donut from './dashboard/Donut';
import ColumnChart from './dashboard/ColumnChart';
import TopStudents from './dashboard/TopStudents';
import TeamSummaryBar from './dashboard/TeamSummaryBar';
import DayFilter from './dashboard/DayFilter';
import '../../style/GeneralDirectorDashboard.css';

const COLLEGE_VISIT_LABELS = {
  ...FACULTY_LABELS,
  dentistry: 'المجمع الطبي',
};

const UNION_COLORS = {
  central: 'var(--gd-teal)',
  major_guide: 'var(--gd-orange)',
  turkish_club: 'var(--gd-plum)',
};

// فترات التحديث حسب القسم (بالمللي ثانية)
const FAST_MS = 15_000;
const MEDIUM_MS = 60_000;
const SLOW_MS = 5 * 60_000;

export default function GeneralDirectorDashboard({ userRole = 'المدير العام' }) {
  const [day, setDay] = useState('all');
  const dayRef = useRef(day);
  useEffect(() => {
    dayRef.current = day;
  }, [day]);
  const [metric, setMetric] = useState('lectures');

  const [stats, setStats] = useState(null);
  const [smsStatus, setSmsStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [studentsInsideCount, setStudentsInsideCount] = useState(null);
  const [gameScans, setGameScans] = useState(null);
  const [collegeVisits, setCollegeVisits] = useState(null);
  const [unionSections, setUnionSections] = useState(null);
  const [presence, setPresence] = useState(null);
  const [peakHours, setPeakHours] = useState(null);
  const [topData, setTopData] = useState(null);
  const [teamTotal, setTeamTotal] = useState(null);

  // كاش لكل معيار في الطلاب المتميزون — أول مرة بنجيب المعيار بنحفظه حتى
  // التنقل بين التابات ما يسبب إعادة جلب
  const [topCache, setTopCache] = useState({});

  usePolling(
    () => {
      apiGet('/admin/dashboard/stats').then(setStats).catch(() => {});
    },
    FAST_MS,
    []
  );

  usePolling(
    () => {
      apiGet('/admin/dashboard/sms-status').then(setSmsStatus).catch(() => {});
    },
    FAST_MS,
    []
  );

  usePolling(
    () => {
      const requestedDay = day;
      apiGet(`/admin/dashboard/students-inside-count?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === dayRef.current) setStudentsInsideCount(r.count ?? null);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [day]
  );

  usePolling(
    () => {
      const requestedDay = day;
      apiGet(`/admin/dashboard/game-scans?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === dayRef.current) setGameScans(r.count ?? null);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [day]
  );

  usePolling(
    () => {
      const requestedDay = day;
      apiGet(`/admin/dashboard/college-visits?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === dayRef.current) setCollegeVisits(r);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [day]
  );

  usePolling(
    () => {
      const requestedDay = day;
      apiGet(`/admin/dashboard/union-sections?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === dayRef.current) setUnionSections(r);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [day]
  );

  usePolling(
    () => {
      apiGet('/admin/dashboard/analytics').then((r) => setAnalytics(r)).catch(() => {});
    },
    MEDIUM_MS,
    []
  );

  usePolling(
    () => {
      apiGet('/admin/dashboard/presence').then(setPresence).catch(() => {});
    },
    SLOW_MS,
    []
  );

  usePolling(
    () => {
      apiGet('/admin/dashboard/peak-hours').then(setPeakHours).catch(() => {});
    },
    SLOW_MS,
    []
  );

  usePolling(
    () => {
      apiGet(`/admin/dashboard/top-students?metric=${metric}&page=1&limit=5`)
        .then((r) => {
          setTopCache((prev) => ({ ...prev, [metric]: r }));
          setTopData(r);
        })
        .catch(() => {});
    },
    SLOW_MS,
    [metric]
  );

  usePolling(
    () => {
      apiGet('/admin/accounts?page=1&limit=1')
        .then((r) => setTeamTotal(r.total ?? r.items?.length ?? null))
        .catch(() => {});
    },
    MEDIUM_MS,
    []
  );

  // —— تجهيز البيانات للعرض ——

  const collegeItems = (collegeVisits?.items || [])
    .map((it) => ({ label: COLLEGE_VISIT_LABELS[it.college] || it.college || it.label || it.college, count: it.count }))
    .sort((a, b) => b.count - a.count);

  const lectureItems = (analytics?.lecture_attendance || [])
    .map((it) => ({ label: it.label || it.lecture_name, count: it.count }))
    .sort((a, b) => b.count - a.count);
  const lectureTotal = analytics?.lecture_attendance?.reduce((s, it) => s + it.count, 0) ?? null;

  const unionItems = unionSections?.items || [];
  const unionSeries = (unionItems.length ? unionItems : day === 'all' ? analytics?.union_sections || [] : []).map((it) => ({
    key: it.section,
    label: it.label || it.section,
    count: it.count,
    color: UNION_COLORS[it.section] || 'var(--gd-teal)',
  }));

  const certItems = analytics?.certificate_distribution || [];
  const certScientific = certItems.find((c) => c.certificate_type === 'scientific')?.count || 0;
  const certLiterary = certItems.find((c) => c.certificate_type === 'literary')?.count || 0;
  const sciLitSeries = [
    { key: 'scientific', label: 'علمي', count: certScientific, color: 'var(--gd-teal)' },
    { key: 'literary', label: 'أدبي', count: certLiterary, color: 'var(--gd-orange)' },
  ];
  const sciLitTotal = certScientific + certLiterary;

  const scoreItems = (analytics?.score_distribution || []).map((it) => ({ label: it.label, count: it.count }));
  const yearItems = (analytics?.year_distribution || []).map((it) => ({ label: it.year, count: it.count }));

  const topStudents = topCache[metric] || (topData?.metric === metric ? topData : null);
  const unionAllTotal =
    topCache.union_all?.total ?? (topData?.metric === 'union_all' ? topData.total : null);

  return (
    <div className="gd-dash-viewport">
      <AdminHeader userRole={userRole} smsStatus={smsStatus} />

      <main className="gd-dash-dash-main">
        <HeroStats
          studentsInsideToday={stats?.students_inside_today}
          studentsInsideCount={studentsInsideCount}
          stats={stats}
          day={day}
          onDayChange={setDay}
        />

        <SummaryCards stats={stats} gameScans={gameScans} day={day} onDayChange={setDay} />

        <PresenceRow presence={presence} />

        <div className="gd-dash-sechd">
          <h2 className="gd-dash-sechd__title">التحليلات</h2>
          <span className="gd-dash-sechd__sub">بتتحدث كل 15 ثانية</span>
        </div>

        <PeakHoursHeatmap peakHours={peakHours} />

        <div className="gd-dash-grid2">
          <HorizontalBars
            title="زيارة الكلية"
            items={collegeItems}
            totalText={collegeVisits?.total ?? null}
            filter={<DayFilter value={day} onChange={setDay} />}
            accent="teal"
            empty="ما في بيانات عن زيارات الكليات للآن"
            expandable
            expandLabel={(n) => `عرض كل الكليات (${n})`}
          />
          <HorizontalBars
            title="حضور كل محاضرة"
            items={lectureItems}
            totalText={lectureTotal != null ? `الإجمالي: ${lectureTotal}` : null}
            accent="orange"
            empty="ما في بيانات عن حضور المحاضرات للآن"
          />
        </div>

        <div className="gd-dash-grid2">
          <Donut
            title="مسحات ركن الاتحاد"
            headerTotal={unionSections?.total ?? null}
            filter={<DayFilter value={day} onChange={setDay} />}
            series={unionSeries}
            empty="ما في بيانات عن مسحات ركن الاتحاد للآن"
          />
          <Donut
            title="علمي / أدبي"
            headerTotal={sciLitTotal || null}
            series={sciLitSeries}
            empty="ما في بيانات عن توزيع الفرع الثانوي للآن"
          />
        </div>

        <div className="gd-dash-grid2">
          <ColumnChart title="توزيع المعدل" items={scoreItems} empty="ما في بيانات عن توزيع المعدل للآن" />
          <ColumnChart title="توزيع سنة الشهادة" items={yearItems} empty="ما في بيانات عن توزيع سنوات الشهادة للآن" />
        </div>

        <TopStudents metric={metric} onMetricChange={setMetric} data={topStudents} unionTotal={unionAllTotal} />

        <TeamSummaryBar total={teamTotal} />
      </main>
    </div>
  );
}