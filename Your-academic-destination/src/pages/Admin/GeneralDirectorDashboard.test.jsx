import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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
  walkin_pending_count: 5,
  walkin_completed_count: 6,
  game_scans_total: 12,
  union_scans_total: 7,
};

function mockEndpoints(smsStatus, accountsResponse) {
  apiGet.mockImplementation((path) => {
    if (path.startsWith('/admin/accounts'))
      return Promise.resolve(accountsResponse || { items: [] });
    if (path === '/admin/dashboard/stats') return Promise.resolve(STATS);
    if (path === '/admin/dashboard/rooms-occupancy') return Promise.resolve({ rooms: [] });
    if (path === '/admin/dashboard/analytics')
      return Promise.resolve({
        college_visits: [{ college: 'medicine', count: 2 }],
        lecture_attendance: [],
        score_distribution: [],
        year_distribution: [],
        certificate_distribution: [
          { certificate_type: 'scientific', count: 2 },
          { certificate_type: 'literary', count: 1 },
        ],
      });
    if (path === '/admin/dashboard/sms-status') return Promise.resolve(smsStatus);
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

describe('GeneralDirectorDashboard - SMS status card', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('shows the sender as online with pending/sent/failed counts', async () => {
    mockEndpoints({
      counts: { pending: 2, sending: 0, sent: 5, failed: 1 },
      worker_online: true,
      last_heartbeat: '2026-01-01T12:00:00',
    });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('المُرسِل متصل')).toBeInTheDocument());

    const card = screen.getByText('حالة إرسال الرسائل النصية').closest('section');
    expect(card).toHaveTextContent('بانتظار الإرسال: 2');
    expect(card).toHaveTextContent('مرسلة: 5');
    expect(card).toHaveTextContent('فاشلة: 1');
  });

  it('shows the sender as offline when the worker heartbeat is stale', async () => {
    mockEndpoints({ counts: { pending: 0, sending: 0, sent: 0, failed: 0 }, worker_online: false });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('المُرسِل منقطع')).toBeInTheDocument());
  });

  it('defaults missing counts to zero', async () => {
    mockEndpoints({ counts: {}, worker_online: true });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('المُرسِل متصل')).toBeInTheDocument());

    const card = screen.getByText('حالة إرسال الرسائل النصية').closest('section');
    expect(card).toHaveTextContent('بانتظار الإرسال: 0');
    expect(card).toHaveTextContent('مرسلة: 0');
    expect(card).toHaveTextContent('فاشلة: 0');
  });
});

describe('GeneralDirectorDashboard - team accounts pagination & search', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  function makeAccount(username, role) {
    return { username, role, college: null, password_hash: 'x', token_version: 0 };
  }

  it('renders accounts with pagination info derived from total', async () => {
    const items = Array.from({ length: 10 }, (_, i) => makeAccount(`gt_user_${i}`, 'gate_scanner'));
    mockEndpoints({ counts: {}, worker_online: true }, { items, total: 25, page: 1, limit: 10 });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('gt_user_0')).toBeInTheDocument());

    expect(screen.getByText('الإجمالي: 25')).toBeInTheDocument();
    expect(screen.getByText('صفحة 1 من 3')).toBeInTheDocument();

    const calls = apiGet.mock.calls.map((c) => c[0]);
    expect(calls.some((p) => p.startsWith('/admin/accounts?page=1&limit=10'))).toBe(true);
  });

  it('renders empty state when no accounts match search', async () => {
    mockEndpoints({ counts: {}, worker_online: true }, { items: [], total: 0, page: 1, limit: 10 });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('ما في حسابات مطابقة')).toBeInTheDocument());
    expect(screen.getByText('الإجمالي: 0')).toBeInTheDocument();
  });

  it('debounces the search query and passes it to the backend', async () => {
    mockEndpoints({ counts: {}, worker_online: true }, { items: [], total: 0, page: 1, limit: 10 });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('الإجمالي: 0')).toBeInTheDocument());

    const input = screen.getByPlaceholderText('بحث بالاسم...');
    fireEvent.change(input, { target: { value: 'sedra' } });

    apiGet.mockClear();
    await waitFor(
      () => {
        const calls = apiGet.mock.calls.map((c) => c[0]);
        expect(calls.some((p) => p.startsWith('/admin/accounts?page=1&limit=10&search=sedra'))).toBe(
          true
        );
      },
      { timeout: 2000 }
    );
  });
});

describe('GeneralDirectorDashboard - collapsible analytics sections', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('starts collapsed and expands on click', async () => {
    mockEndpoints({ counts: {}, worker_online: true });
    renderDashboard();

    // العنصر غير ظاهر حتى ينفتح (مقفول افتراضياً)
    await waitFor(() => expect(screen.getByText('المُرسِل متصل')).toBeInTheDocument());
    expect(screen.queryByText(/علمي: \d+٪/)).not.toBeInTheDocument();

    // الكليك على رأس القسم يفتحه
    fireEvent.click(screen.getByText('علمي / أدبي'));
    expect(await screen.findByText(/علمي: 67٪ \(2\)/)).toBeInTheDocument();
  });

  it('shows the scan totals badge on the scientific/literary section header', async () => {
    mockEndpoints({ counts: {}, worker_online: true });
    renderDashboard();

    await waitFor(() => expect(screen.getByText('المُرسِل متصل')).toBeInTheDocument());
    // الـ badge بيظهر براس القسم حتى وهو مقفول (ما بيحتاج فتح القسم)
    expect(
      screen.getByText('مسحات ركن الترفيه: 12 · الاتحاد: 7')
    ).toBeInTheDocument();
  });
});
