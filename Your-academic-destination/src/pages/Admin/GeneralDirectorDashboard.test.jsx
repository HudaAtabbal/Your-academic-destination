import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { apiGet } from '../../api/api';
import GeneralDirectorDashboard from './GeneralDirectorDashboard';

vi.mock('../../api/api.js', () => ({
  ApiError: class ApiError extends Error {
    constructor(errorCode, message, details) {
      super(message);
      this.name = 'ApiError';
      this.errorCode = errorCode;
      this.details = details;
    }
  },
  apiGet: vi.fn(),
  apiRequest: vi.fn(),
  clearAuthToken: vi.fn(),
}));

const STATS = {
  registered_online_count: 1,
  students_inside_today: 2,
  students_inside_all_days: 3,
  survey_completed_count: 4,
  registered_no_show_count: 2,
  walkin_pending_count: 5,
  walkin_completed_count: 6,
  game_scans_total: 12,
  union_scans_total: 7,
  total_consultations: 218,
};

const ANALYTICS = {
  college_visits: [],
  lecture_attendance: [{ lecture_name: 'math', label: 'الرياضيات', count: 5 }],
  score_distribution: [],
  year_distribution: [],
  certificate_distribution: [
    { certificate_type: 'scientific', count: 2 },
    { certificate_type: 'literary', count: 1 },
  ],
  union_sections: [
    { section: 'central', label: 'الركن المركزي', count: 2 },
    { section: 'major_guide', label: 'دليل التخصص', count: 1 },
    { section: 'turkish_club', label: 'نادي التركي', count: 0 },
  ],
};

const PRESENCE = {
  avg_minutes_all: 162,
  per_day: [
    { day: 'wed', avg_minutes: 120, students_counted: 10 },
    { day: 'thu', avg_minutes: 162, students_counted: 12 },
    { day: 'sat', avg_minutes: 90, students_counted: 8 },
  ],
  frequency: { one_day: 100, two_days: 50, all_days: 20, total: 170 },
};

const PEAK_HOURS = {
  hours: [9, 10, 11, 12],
  days: [
    { day: 'wed', counts: [1, 2, 3, 4] },
    { day: 'thu', counts: [2, 5, 9, 6] },
    { day: 'sat', counts: [0, 1, 2, 3] },
  ],
  peak: { day: 'thu', hour: 11, count: 9 },
};

const TOP_LECTURES = {
  metric: 'lectures',
  items: [
    { rank: 1, unique_code: 'U001', full_name: 'طالب متميز', value: 8 },
    { rank: 2, unique_code: 'U002', full_name: 'طالب ثاني', value: 7 },
  ],
  page: 1,
  limit: 5,
  total: 12,
  total_pages: 3,
};

const TOP_UNION_ALL = { metric: 'union_all', items: [], page: 1, limit: 1, total: 9, total_pages: 1 };

const TOP_PRESENCE = {
  metric: 'presence',
  items: [{ rank: 1, unique_code: 'U001', full_name: 'طالب متميز', value: 160, days: 2 }],
  page: 1,
  limit: 5,
  total: 1,
  total_pages: 1,
};

const ACCOUNTS = { items: [], total: 37, page: 1, limit: 1 };

const CORNER_JOURNEY = {
  day: 'all',
  total_students: 576,
  multi_corner_students: 329,
  distribution: [
    { bucket: 1, label: 'ركن واحد', count: 212 },
    { bucket: 2, label: 'ركنان', count: 105 },
    { bucket: 3, label: '3 أركان', count: 100 },
    { bucket: 4, label: '4 أركان', count: 52 },
    { bucket: 5, label: '5 أركان فأكثر', count: 72 },
    { bucket: 0, label: 'ندوة فقط', count: 35 },
  ],
  pairs: [
    { source: 'c:arts', target: 'u:central', label: 'كلية الآداب والعلوم الإنسانية + الركن المركزي', count: 99 },
    { source: 'c:informatics', target: 'c:arts', label: 'كلية الهندسة المعلوماتية + كلية الآداب والعلوم الإنسانية', count: 88 },
    { source: 'c:dentistry', target: 'c:sciences', label: 'المجمع الطبي + كلية العلوم', count: 64 },
    { source: 'u:central', target: 'g:game', label: 'الركن المركزي + قسم الترفيه', count: 47 },
    { source: 'c:economics', target: 'u:major_guide', label: 'كلية الاقتصاد + دليل التخصص', count: 33 },
    { source: 'c:law', target: 'c:dentistry', label: 'كلية الحقوق + المجمع الطبي', count: 21 },
    { source: 'c:education', target: 'c:music', label: 'كلية التربية + كلية الموسيقى', count: 12 },
  ],
  total_transitions: 46,
  transitions: [
    { source: 'c:arts', target: 'u:central', label: 'من كلية الآداب والعلوم الإنسانية إلى الركن المركزي', count: 46 },
    { source: 'c:informatics', target: 'c:arts', label: 'من كلية الهندسة المعلوماتية إلى كلية الآداب والعلوم الإنسانية', count: 31 },
    { source: 'u:central', target: 'g:game', label: 'من الركن المركزي إلى قسم الترفيه', count: 18 },
  ],
  generated_at: '2026-09-26T10:00:00',
};

const ATTENDANCE_SPLIT = {
  day: 'all',
  total: 8,
  items: [
    { key: 'registered_in', count: 5 },
    { key: 'walkin_in', count: 2 },
    { key: 'registered_out', count: 1 },
  ],
};

function mockEndpoints({ smsStatus, accounts, collegeVisits, unionSections, cornerJourney, attendanceSplit } = {}) {
  const college = collegeVisits ?? {
    day: 'all',
    mode: 'all',
    total: 2,
    items: [{ college: 'medicine', count: 2 }],
  };
  const union = unionSections ?? {
    day: 'all',
    total: 3,
    items: ANALYTICS.union_sections,
  };
  // الافتراضي لكل مسار — بيضل متاح للاختبارات اللي بدها تبدّل مسار واحد بس
  // (مثلاً كرت الزيارات وقت التبديل بين «الكل» و«فريد»).
  const byDefault = (path) => {
    if (path.startsWith('/admin/accounts'))
      return Promise.resolve(accounts || ACCOUNTS);
    if (path.startsWith('/admin/dashboard/students-inside-count'))
      return Promise.resolve({ day: 'all', count: 3 });
    if (path.startsWith('/admin/dashboard/game-scans'))
      return Promise.resolve({ day: 'all', count: 12 });
    if (path.startsWith('/admin/dashboard/attendance-split'))
      return Promise.resolve(attendanceSplit || ATTENDANCE_SPLIT);
    if (path.startsWith('/admin/dashboard/union-sections'))
      return Promise.resolve(union);
    if (path.startsWith('/admin/dashboard/corner-journey'))
      return Promise.resolve(cornerJourney || CORNER_JOURNEY);
    if (path.startsWith('/admin/dashboard/top-students')) {
      if (path.includes('metric=union_all')) return Promise.resolve(TOP_UNION_ALL);
      if (path.includes('metric=presence')) return Promise.resolve(TOP_PRESENCE);
      return Promise.resolve(TOP_LECTURES);
    }
    if (path === '/admin/dashboard/stats') return Promise.resolve(STATS);
    if (path === '/admin/dashboard/sms-status')
      return Promise.resolve(
        smsStatus || { counts: { pending: 2, sending: 0, sent: 5, failed: 1 }, worker_online: true }
      );
    if (path === '/admin/dashboard/analytics') return Promise.resolve(ANALYTICS);
    if (path === '/admin/dashboard/presence') return Promise.resolve(PRESENCE);
    if (path === '/admin/dashboard/peak-hours') return Promise.resolve(PEAK_HOURS);
    return Promise.reject(new Error(`unexpected path ${path}`));
  };

  defaultEndpoint = byDefault;
  apiGet.mockImplementation((path) =>
    path.startsWith('/admin/dashboard/college-visits') ? Promise.resolve(college) : byDefault(path)
  );
}

let defaultEndpoint = null;

function renderDashboard() {
  return render(
    <MemoryRouter>
      <GeneralDirectorDashboard />
    </MemoryRouter>
  );
}

function cardByHeading(text) {
  return screen.getByText(text).closest('.gd-dash-card');
}

describe('GeneralDirectorDashboard - live data', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('shows the hero number for students inside today', async () => {
    const { container } = renderDashboard();

    await waitFor(() => {
      const big = container.querySelector('.gd-dash-hero__big');
      expect(big).not.toBeNull();
      expect(big.textContent.trim()).toBe('2');
    });
  });

  it('shows the SMS worker status in the header pill', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('متصل')).toBeInTheDocument());
  });

  it('renders summary cards with registration and walk-in splits', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const reg = cardByHeading('التسجيل الإلكتروني');
    expect(reg).toHaveTextContent('بلا حضور');
    expect(within(reg).getByText('2')).toBeInTheDocument();

    const walk = cardByHeading('سجلات Walk-in');
    expect(walk).toHaveTextContent('تم إكمالها');
    expect(within(walk).getByText('5')).toBeInTheDocument();

    const consult = cardByHeading('إجمالي الاستشارات');
    expect(consult).toHaveTextContent('218');

    const game = cardByHeading('مسحات ركن الترفيه');
    expect(game).toHaveTextContent('12');
  });

  it('renders the college visits card with the counting-mode control', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const college = cardByHeading('زيارة الكلية');
    // الوضع الافتراضي «الكل» → الإجمالي بعدد الزيارات
    expect(within(college).getByText('الإجمالي: 2 زيارة')).toBeInTheDocument();
    // أزرار الوضع: الكل / فريد
    const modes = within(college).getByRole('group', { name: 'طريقة العد' });
    expect(within(modes).getByRole('button', { name: 'الكل' })).toHaveAttribute('aria-pressed', 'true');
    expect(within(modes).getByRole('button', { name: 'فريد' })).toHaveAttribute('aria-pressed', 'false');
    // وفلتر الأيام لسا موجود بنفس الكارت
    expect(within(college).getByRole('group', { name: 'فلترة حسب اليوم' })).toBeInTheDocument();
  });

  it('switches the college card to unique counting and changes the unit', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const college = cardByHeading('زيارة الكلية');
    expect(
      apiGet.mock.calls.some((c) => c[0].startsWith('/admin/dashboard/college-visits?day=all&mode=all'))
    ).toBe(true);

    // «فريد» بترجع نفس الأرقام بس بإجمالي طلاب
    const restOfEndpoints = defaultEndpoint;
    apiGet.mockImplementation((path) =>
      path.startsWith('/admin/dashboard/college-visits')
        ? Promise.resolve({ day: 'all', mode: 'unique', total: 1, items: [{ college: 'medicine', count: 1 }] })
        : restOfEndpoints(path)
    );

    fireEvent.click(within(college).getByRole('button', { name: 'فريد' }));

    await waitFor(() => {
      expect(
        apiGet.mock.calls.some((c) => c[0].startsWith('/admin/dashboard/college-visits?day=all&mode=unique'))
      ).toBe(true);
    }, { timeout: 2000 });

    await waitFor(() =>
      expect(within(college).getByText('الإجمالي: 1 طالب')).toBeInTheDocument()
    );
  });

  it('renders the attendance split donut with slice labels', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const split = cardByHeading('مين فات عالجامعة');
    // الإجمالي 8 بتظهر مرتين: مرة بترويسة الكارت ومرة بنص الدونات
    expect(within(split).getByText('8', { selector: '.gd-dash-tot' })).toBeInTheDocument();
    expect(split.querySelector('.gd-dash-donut__val').textContent).toBe('8');
    expect(within(split).getByText('مسجّل وحضر')).toBeInTheDocument();
    expect(within(split).getByText('Walk-in وحضروا')).toBeInTheDocument();
    expect(within(split).getByText('مسجّل وبلا حضور')).toBeInTheDocument();
    // 5 من 8 = 63٪
    expect(within(split).getByText('63٪ (5)')).toBeInTheDocument();
    // كل كارت دونات إلها فلتر يومي مستقل
    expect(within(split).getByRole('group', { name: 'فلترة حسب اليوم' })).toBeInTheDocument();
  });

  it('puts the three donuts in a three-column row', async () => {
    const { container } = renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const row = container.querySelector('.gd-dash-grid3');
    expect(row).not.toBeNull();
    ['مين فات عالجامعة', 'مسحات ركن الاتحاد', 'علمي / أدبي'].forEach((t) => {
      expect(within(row).getByText(t)).toBeInTheDocument();
    });
  });

  it('shows the presence average and per-day durations', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('2:42')).toBeInTheDocument());

    const presenceCard = cardByHeading('متوسط مدة التواجد');
    expect(presenceCard).toHaveTextContent('2س 42د');

    const freqCard = cardByHeading('تكرار الحضور');
    expect(freqCard).toHaveTextContent('170 طالب');
    expect(freqCard).toHaveTextContent('20');
    expect(freqCard).toHaveTextContent('12٪');
  });

  it('shows the peak hours heatmap with its peak hint', async () => {
    renderDashboard();

    await waitFor(() =>
      expect(screen.getByText('الذروة: خميس 11:00 – 12:00')).toBeInTheDocument()
    );

    expect(screen.getByText('9:00')).toBeInTheDocument();
    const peakCells = document.querySelectorAll('.gd-dash-heat__c.is-peak');
    expect(peakCells.length).toBe(1);
  });

  it('renders the union donut with section percentages', async () => {
    renderDashboard();

    await waitFor(() => {
      const items = screen.getAllByText('67٪ (2)');
      expect(items.length).toBeGreaterThan(0);
    });
  });

  it('renders the corner journey section under the top students', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('حركة الطلاب بين الأركان')).toBeInTheDocument());

    // عنوان القسم يوضّح قاعدة الانتقالات
    expect(
      screen.getByText('بتتحدث تلقائياً · الانتقالات محسوبة من المسحات ضمن نفس اليوم')
    ).toBeInTheDocument();

    // 1) توزيع الطلاب حسب عدد الأركان — 6 أعمدة بإجمالي الطلاب
    const dist = cardByHeading('عدد الطلاب حسب عدد الأركان التي زاروها');
    expect(dist).toHaveTextContent('إجمالي الطلاب: 576');
    const distItems = dist.querySelectorAll('.gd-dash-cols__col');
    expect(distItems.length).toBe(6);
    ['ركن واحد', 'ركنان', '3 أركان', '4 أركان', '5 أركان فأكثر', 'ندوة فقط'].forEach((label) => {
      expect(within(dist).getByText(label)).toBeInTheDocument();
    });
    expect(within(dist).getByText('212')).toBeInTheDocument();

    // 2) الأزواج المشتركة — أول 5 صفوف + زر توسيع
    const pairs = cardByHeading('أكثر الأزواج المشتركة');
    expect(pairs).toHaveTextContent('زاروا ركنين فأكثر: 329');
    expect(pairs.querySelectorAll('.gd-dash-hb__r').length).toBe(5);
    expect(within(pairs).getByText('كلية الآداب والعلوم الإنسانية + الركن المركزي')).toBeInTheDocument();
    expect(within(pairs).getByText('عرض كل الأزواج (7)')).toBeInTheDocument();

    fireEvent.click(within(pairs).getByText('عرض كل الأزواج (7)'));
    await waitFor(() => expect(pairs.querySelectorAll('.gd-dash-hb__r').length).toBe(7));
    expect(within(pairs).getByText('عرض أقل')).toBeInTheDocument();

    // 3) الانتقالات المباشرة — بنفس ستايل الأشرطة مع لون برتقالي
    const transitions = cardByHeading('أكثر الانتقالات المباشرة');
    expect(transitions).toHaveTextContent('إجمالي الانتقالات: 46');
    expect(transitions.querySelector('.gd-dash-hb').className).toContain('gd-dash-hb--orange');
    expect(
      within(transitions).getByText('من كلية الآداب والعلوم الإنسانية إلى الركن المركزي')
    ).toBeInTheDocument();
  });

  it('gives every corner journey card its own day filter', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('حركة الطلاب بين الأركان')).toBeInTheDocument());

    [
      'عدد الطلاب حسب عدد الأركان التي زاروها',
      'أكثر الأزواج المشتركة',
      'أكثر الانتقالات المباشرة',
    ].forEach((heading) => {
      expect(
        within(cardByHeading(heading)).getByRole('group', { name: 'فلترة حسب اليوم' })
      ).toBeInTheDocument();
    });
  });

  it('renders the top students leaderboard', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('طالب متميز')).toBeInTheDocument());
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('عرض القائمة الكاملة')).toBeInTheDocument();
  });

  it('hero items are divs and only the CTA is a link', async () => {
    const { container } = renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    const items = container.querySelectorAll('.gd-dash-trio__item');
    expect(items.length).toBe(3);
    items.forEach((el) => expect(el.tagName.toLowerCase()).toBe('div'));

    const links = screen.getAllByRole('link', { name: 'عرض القائمة' });
    expect(links.length).toBe(3);
    const hrefs = links.map((l) => l.getAttribute('href')).sort();
    expect(hrefs).toEqual(
      ['/gate-registered', '/dashboard-students-inside', '/dashboard-survey-completions'].sort()
    );
  });

  it('shows the union tab total without opening the tab', async () => {
    renderDashboard();

    await waitFor(() =>
      expect(screen.getByRole('tab', { name: 'زاروا كل أركان الاتحاد (9)' })).toBeInTheDocument()
    );
  });

  it('shows presence values with the days count', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('tab', { name: 'أطول تواجد بالجامعة' }));

    await waitFor(() =>
      expect(screen.getByText('2س 40د · على يومين')).toBeInTheDocument()
    );
  });

  it('shows the team summary bar with the accounts total', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('37 حساب')).toBeInTheDocument());
    expect(screen.getByText('+ إنشاء حساب جديد')).toBeInTheDocument();
  });
});

describe('GeneralDirectorDashboard - independent day filters', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const calledPaths = () => apiGet.mock.calls.map((c) => c[0]);

  it('hero filter refetches only students-inside-count', async () => {
    const { container } = renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    const hero = container.querySelector('.gd-dash-hero');
    fireEvent.click(within(hero).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(
        calledPaths().some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))
      ).toBe(true);
    }, { timeout: 2000 });

    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(false);
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
      false
    );
  });

  it('game card filter refetches only game-scans', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    const gameCard = cardByHeading('مسحات ركن الترفيه');
    fireEvent.click(within(gameCard).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(
        true
      );
    }, { timeout: 2000 });

    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
      false
    );
  });

  it('attendance card filter refetches only attendance-split', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    const splitCard = cardByHeading('مين فات عالجامعة');
    fireEvent.click(within(splitCard).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/attendance-split?day=thu'))).toBe(
        true
      );
    }, { timeout: 2000 });

    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(false);
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
      false
    );
  });

  it('college card filter refetches only college-visits', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    const collegeCard = cardByHeading('زيارة الكلية');
    fireEvent.click(within(collegeCard).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
        true
      );
    }, { timeout: 2000 });

    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(false);
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
      false
    );
  });

  it('corner journey filter refetches only corner-journey', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('حركة الطلاب بين الأركان')).toBeInTheDocument());

    apiGet.mockClear();
    const pairsCard = cardByHeading('أكثر الأزواج المشتركة');
    fireEvent.click(within(pairsCard).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/corner-journey?day=thu'))).toBe(
        true
      );
    }, { timeout: 2000 });

    // باقي الأقسام ما بتتأثر
    ['students-inside-count', 'game-scans', 'college-visits', 'union-sections', 'attendance-split'].forEach(
      (endpoint) => {
        expect(calledPaths().some((p) => p.startsWith(`/admin/dashboard/${endpoint}?day=thu`))).toBe(
          false
        );
      }
    );
  });

  it('union card filter refetches only union-sections', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    const unionCard = cardByHeading('مسحات ركن الاتحاد');
    fireEvent.click(within(unionCard).getByRole('button', { name: 'خميس' }));

    await waitFor(() => {
      expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
        true
      );
    }, { timeout: 2000 });

    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))).toBe(
      false
    );
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(false);
    expect(calledPaths().some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
      false
    );
  });
});

describe('GeneralDirectorDashboard - empty states', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints({
      smsStatus: { counts: {}, worker_online: true },
      collegeVisits: { day: 'all', mode: 'all', total: 0, items: [] },
      attendanceSplit: { day: 'all', total: 0, items: [] },
      cornerJourney: {
        day: 'all',
        total_students: 0,
        multi_corner_students: 0,
        distribution: [],
        pairs: [],
        total_transitions: 0,
        transitions: [],
      },
    });
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('shows empty messages for sections without data', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());
    expect(screen.getByText('ما في بيانات عن زيارات الكليات للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن الحضور للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن توزيع المعدل للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن توزيع سنوات الشهادة للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن حركة الطلاب بين الأركان للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن الأزواج المشتركة للأركان للآن')).toBeInTheDocument();
    expect(
      screen.getByText('ما في بيانات عن الانتقالات المباشرة بين الأركان للآن')
    ).toBeInTheDocument();
  });
});