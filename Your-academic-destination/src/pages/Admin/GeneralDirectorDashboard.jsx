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
import SegmentedControl from './dashboard/SegmentedControl';
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

// وضع عدّ زيارات الكليات — «الكل» بعدد الزيارات، «فريد» بعدد الطلاب
const COLLEGE_MODES = [
  { key: 'all', label: 'الكل' },
  { key: 'unique', label: 'فريد' },
];

// شرائح الحضور — نفس ترتيب الـ API (registered_in / walkin_in / registered_out)
const ATTENDANCE_SLICES = {
  registered_in: { label: 'مسجّل وحضر', color: 'var(--gd-teal)' },
  walkin_in: { label: 'Walk-in وحضروا', color: 'var(--gd-orange)' },
  registered_out: { label: 'مسجّل وبلا حضور', color: 'var(--gd-plum)' },
};

// فترات التحديث حسب القسم (بالمللي ثانية)
const FAST_MS = 15_000;
const MEDIUM_MS = 60_000;
const SLOW_MS = 5 * 60_000;

export default function GeneralDirectorDashboard({ userRole = 'المدير العام' }) {
  // فلاتر الأيام — كل قسم بفلتر مستقل تبعاً لبطاقته
  const [insideDay, setInsideDay] = useState('all');
  const insideDayRef = useRef(insideDay);
  useEffect(() => {
    insideDayRef.current = insideDay;
  }, [insideDay]);

  const [gameDay, setGameDay] = useState('all');
  const gameDayRef = useRef(gameDay);
  useEffect(() => {
    gameDayRef.current = gameDay;
  }, [gameDay]);

  const [collegeDay, setCollegeDay] = useState('all');
  const collegeDayRef = useRef(collegeDay);
  useEffect(() => {
    collegeDayRef.current = collegeDay;
  }, [collegeDay]);

  // وضع عدّ زيارات الكليات: «الكل» يحسب كل زيارة (جولة + استشارة)، و«فريد»
  // بيحسب كل طالب مرة وحدة مهما زار كليات — فالرقم بيتقارن بعدد الناس مش
  // بعدد الخطوات.
  const [collegeMode, setCollegeMode] = useState('all');
  const collegeModeRef = useRef(collegeMode);
  useEffect(() => {
    collegeModeRef.current = collegeMode;
  }, [collegeMode]);

  const [splitDay, setSplitDay] = useState('all');
  const splitDayRef = useRef(splitDay);
  useEffect(() => {
    splitDayRef.current = splitDay;
  }, [splitDay]);

  const [unionDay, setUnionDay] = useState('all');
  const unionDayRef = useRef(unionDay);
  useEffect(() => {
    unionDayRef.current = unionDay;
  }, [unionDay]);

  // حركة الطلاب بين الأركان — فلتر واحد للثلاثة أقسام (توزيع، أزواج، انتقالات)
  const [journeyDay, setJourneyDay] = useState('all');
  const journeyDayRef = useRef(journeyDay);
  useEffect(() => {
    journeyDayRef.current = journeyDay;
  }, [journeyDay]);

  const [metric, setMetric] = useState('lectures');

  const [stats, setStats] = useState(null);
  const [smsStatus, setSmsStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [studentsInsideCount, setStudentsInsideCount] = useState(null);
  const [gameScans, setGameScans] = useState(null);
  const [collegeVisits, setCollegeVisits] = useState(null);
  const [attendanceSplit, setAttendanceSplit] = useState(null);
  const [unionSections, setUnionSections] = useState(null);
  const [presence, setPresence] = useState(null);
  const [peakHours, setPeakHours] = useState(null);
  const [topData, setTopData] = useState(null);
  const [teamTotal, setTeamTotal] = useState(null);
  const [unionAllTotal, setUnionAllTotal] = useState(null);
  const [cornerJourney, setCornerJourney] = useState(null);

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
      const requestedDay = insideDay;
      apiGet(`/admin/dashboard/students-inside-count?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === insideDayRef.current) setStudentsInsideCount(r.count ?? null);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [insideDay]
  );

  usePolling(
    () => {
      const requestedDay = gameDay;
      apiGet(`/admin/dashboard/game-scans?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === gameDayRef.current) setGameScans(r.count ?? null);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [gameDay]
  );

  usePolling(
    () => {
      const requestedDay = collegeDay;
      const requestedMode = collegeMode;
      apiGet(`/admin/dashboard/college-visits?day=${requestedDay}&mode=${requestedMode}`)
        .then((r) => {
          if (requestedDay === collegeDayRef.current && requestedMode === collegeModeRef.current)
            setCollegeVisits(r);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [collegeDay, collegeMode]
  );

  usePolling(
    () => {
      const requestedDay = splitDay;
      apiGet(`/admin/dashboard/attendance-split?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === splitDayRef.current) setAttendanceSplit(r);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [splitDay]
  );

  usePolling(
    () => {
      const requestedDay = unionDay;
      apiGet(`/admin/dashboard/union-sections?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === unionDayRef.current) setUnionSections(r);
        })
        .catch(() => {});
    },
    MEDIUM_MS,
    [unionDay]
  );

  // حركة الطلاب بين الأركان: تجميع SQL على فعالية كاملة — مخزّنة مؤقتاً
  // بالسيرفر (300 ثانية)، فبنفس إيقاع الذروة والطلاب المتميزين (5 دقائق).
  usePolling(
    () => {
      const requestedDay = journeyDay;
      apiGet(`/admin/dashboard/corner-journey?day=${requestedDay}`)
        .then((r) => {
          if (requestedDay === journeyDayRef.current) setCornerJourney(r);
        })
        .catch(() => {});
    },
    SLOW_MS,
    [journeyDay]
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

  // إجمالي معيار "كل الأركان الثلاثة" — يظهر بعلامة التبويب فوراً من غير ما
  // يفتح المستخدم التبويب؛ يُجاب على الجبل وعلى دورة الخمس دقائق
  usePolling(
    () => {
      apiGet('/admin/dashboard/top-students?metric=union_all&page=1&limit=1')
        .then((r) => setUnionAllTotal(r.total ?? null))
        .catch(() => {});
    },
    SLOW_MS,
    []
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
  // الوحدة بتتبع الوضع: بأسلوب «الكل» الرقم عدّ زيارات، وبـ«فريد» بعدد طلاب.
  const collegeTotalText =
    collegeVisits?.total != null
      ? `الإجمالي: ${collegeVisits.total} ${collegeMode === 'unique' ? 'طالب' : 'زيارة'}`
      : null;

  const lectureItems = (analytics?.lecture_attendance || [])
    .map((it) => ({ label: it.label || it.lecture_name, count: it.count }))
    .sort((a, b) => b.count - a.count);
  const lectureTotal = analytics?.lecture_attendance?.reduce((s, it) => s + it.count, 0) ?? null;

  const unionItems = unionSections?.items || [];
  const unionSeries = (unionItems.length ? unionItems : unionDay === 'all' ? analytics?.union_sections || [] : []).map((it) => ({
    key: it.section,
    label: it.label || it.section,
    count: it.count,
    color: UNION_COLORS[it.section] || 'var(--gd-teal)',
  }));

  // مين فات عالجامعة — التسمية واللون جاهزين من الباك، فنربطهم بالمفتاح
  const splitSeries = (attendanceSplit?.items || []).map((it) => ({
    key: it.key,
    label: ATTENDANCE_SLICES[it.key]?.label || it.key,
    count: it.count,
    color: ATTENDANCE_SLICES[it.key]?.color || 'var(--gd-teal)',
  }));
  const splitTotal = attendanceSplit?.total ?? null;

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

  // حركة الطلاب بين الأركان — التسميات جاهزة من الباك
  const journeyFilter = <DayFilter value={journeyDay} onChange={setJourneyDay} />;
  const journeyItems = (cornerJourney?.distribution || []).map((it) => ({
    label: it.label,
    count: it.count,
  }));
  const journeyTotal = cornerJourney?.total_students ?? null;
  const cornerCount = cornerJourney?.multi_corner_students ?? null;
  const pairItems = (cornerJourney?.pairs || []).map((it) => ({
    label: it.label,
    count: it.count,
  }));
  const transitionItems = (cornerJourney?.transitions || []).map((it) => ({
    label: it.label,
    count: it.count,
  }));

  return (
    <div className="gd-dash-viewport">
      <AdminHeader userRole={userRole} smsStatus={smsStatus} />

      <main className="gd-dash-dash-main">
        <HeroStats
          studentsInsideToday={stats?.students_inside_today}
          studentsInsideCount={studentsInsideCount}
          stats={stats}
          day={insideDay}
          onDayChange={setInsideDay}
        />

        <SummaryCards
          stats={stats}
          gameScans={gameScans}
          day={gameDay}
          onDayChange={setGameDay}
        />

        <PresenceRow presence={presence} />

        <div className="gd-dash-sechd">
          <h2 className="gd-dash-sechd__title">التحليلات</h2>
          <span className="gd-dash-sechd__sub">بتتحدث تلقائياً</span>
        </div>

        <PeakHoursHeatmap peakHours={peakHours} />

        <div className="gd-dash-grid2">
          <HorizontalBars
            title="زيارة الكلية"
            items={collegeItems}
            totalText={collegeTotalText}
            filter={
              <>
                <SegmentedControl
                  options={COLLEGE_MODES}
                  value={collegeMode}
                  onChange={setCollegeMode}
                  ariaLabel="طريقة العد"
                />
                <DayFilter value={collegeDay} onChange={setCollegeDay} />
              </>
            }
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

        <div className="gd-dash-grid3">
          <Donut
            title="مين فات عالجامعة"
            headerTotal={splitTotal}
            filter={<DayFilter value={splitDay} onChange={setSplitDay} />}
            series={splitSeries}
            empty="ما في بيانات عن الحضور للآن"
          />
          <Donut
            title="مسحات ركن الاتحاد"
            headerTotal={unionSections?.total ?? null}
            filter={<DayFilter value={unionDay} onChange={setUnionDay} />}
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

        <div className="gd-dash-sechd">
          <h2 className="gd-dash-sechd__title">حركة الطلاب بين الأركان</h2>
          <span className="gd-dash-sechd__sub">
            بتتحدث تلقائياً · الانتقالات محسوبة من المسحات ضمن نفس اليوم
          </span>
        </div>

        <ColumnChart
          title="عدد الطلاب حسب عدد الأركان التي زاروها"
          items={journeyItems}
          totalText={journeyTotal != null ? `إجمالي الطلاب: ${journeyTotal}` : null}
          filter={journeyFilter}
          empty="ما في بيانات عن حركة الطلاب بين الأركان للآن"
        />

        <div className="gd-dash-grid2">
          <HorizontalBars
            title="أكثر الأزواج المشتركة"
            items={pairItems}
            totalText={cornerCount != null ? `زاروا ركنين فأكثر: ${cornerCount}` : null}
            filter={journeyFilter}
            accent="teal"
            empty="ما في بيانات عن الأزواج المشتركة للأركان للآن"
            expandable
            limit={5}
            expandLabel={(n) => `عرض كل الأزواج (${n})`}
          />
          <HorizontalBars
            title="أكثر الانتقالات المباشرة"
            items={transitionItems}
            totalText={
              cornerJourney?.total_transitions != null
                ? `إجمالي الانتقالات: ${cornerJourney.total_transitions}`
                : null
            }
            filter={journeyFilter}
            accent="orange"
            empty="ما في بيانات عن الانتقالات المباشرة بين الأركان للآن"
            expandable
            limit={5}
            expandLabel={(n) => `عرض كل الانتقالات (${n})`}
          />
        </div>

        <TeamSummaryBar total={teamTotal} />
      </main>
    </div>
  );
}