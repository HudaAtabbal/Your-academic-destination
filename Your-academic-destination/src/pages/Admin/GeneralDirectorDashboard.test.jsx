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

const ACCOUNTS = { items: [], total: 37, page: 1, limit: 1 };

function mockEndpoints({ smsStatus, accounts, collegeVisits, unionSections } = {}) {
  const college = collegeVisits ?? {
    day: 'all',
    total: 2,
    items: [{ college: 'medicine', count: 2 }],
  };
  const union = unionSections ?? {
    day: 'all',
    total: 3,
    items: ANALYTICS.union_sections,
  };
  apiGet.mockImplementation((path) => {
    if (path.startsWith('/admin/accounts'))
      return Promise.resolve(accounts || ACCOUNTS);
    if (path.startsWith('/admin/dashboard/students-inside-count'))
      return Promise.resolve({ day: 'all', count: 3 });
    if (path.startsWith('/admin/dashboard/game-scans'))
      return Promise.resolve({ day: 'all', count: 12 });
    if (path.startsWith('/admin/dashboard/college-visits'))
      return Promise.resolve(college);
    if (path.startsWith('/admin/dashboard/union-sections'))
      return Promise.resolve(union);
    if (path.startsWith('/admin/dashboard/top-students')) return Promise.resolve(TOP_LECTURES);
    if (path === '/admin/dashboard/stats') return Promise.resolve(STATS);
    if (path === '/admin/dashboard/sms-status')
      return Promise.resolve(
        smsStatus || { counts: { pending: 2, sending: 0, sent: 5, failed: 1 }, worker_online: true }
      );
    if (path === '/admin/dashboard/analytics') return Promise.resolve(ANALYTICS);
    if (path === '/admin/dashboard/presence') return Promise.resolve(PRESENCE);
    if (path === '/admin/dashboard/peak-hours') return Promise.resolve(PEAK_HOURS);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

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

  it('renders the top students leaderboard', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('طالب متميز')).toBeInTheDocument());
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('عرض القائمة الكاملة')).toBeInTheDocument();
  });

  it('shows the team summary bar with the accounts total', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('37 حساب')).toBeInTheDocument());
    expect(screen.getByText('+ إنشاء حساب جديد')).toBeInTheDocument();
  });
});

describe('GeneralDirectorDashboard - day filter refetch', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('refetches day-scoped endpoints when the filter changes', async () => {
    renderDashboard();

    await waitFor(() => expect(screen.getByText('218')).toBeInTheDocument());

    apiGet.mockClear();
    fireEvent.click(screen.getAllByRole('button', { name: 'خميس' })[0]);

    await waitFor(
      () => {
        const calls = apiGet.mock.calls.map((c) => c[0]);
        expect(calls.some((p) => p.startsWith('/admin/dashboard/students-inside-count?day=thu'))).toBe(
          true
        );
        expect(calls.some((p) => p.startsWith('/admin/dashboard/game-scans?day=thu'))).toBe(true);
        expect(calls.some((p) => p.startsWith('/admin/dashboard/college-visits?day=thu'))).toBe(
          true
        );
        expect(calls.some((p) => p.startsWith('/admin/dashboard/union-sections?day=thu'))).toBe(
          true
        );
      },
      { timeout: 2000 }
    );
  });
});

describe('GeneralDirectorDashboard - empty states', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints({
      smsStatus: { counts: {}, worker_online: true },
      collegeVisits: { day: 'all', total: 0, items: [] },
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
    expect(screen.getByText('ما في بيانات عن توزيع المعدل للآن')).toBeInTheDocument();
    expect(screen.getByText('ما في بيانات عن توزيع سنوات الشهادة للآن')).toBeInTheDocument();
  });
});