import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { apiGet } from '../../api/api';
import TopStudentsPage from './TopStudentsPage';

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

const METRIC_PAGES = {
  lectures: {
    metric: 'lectures',
    items: [
      { rank: 1, unique_code: 'U001', full_name: 'طالب الأول', value: 8 },
      { rank: 2, unique_code: 'U002', full_name: 'طالب الثاني', value: 7 },
    ],
    total: 12,
    total_pages: 1,
  },
  tours: {
    metric: 'tours',
    items: [
      { rank: 1, unique_code: 'U003', full_name: 'طالب الجولات', value: 12 },
    ],
    total: 3,
    total_pages: 1,
  },
  presence: {
    metric: 'presence',
    items: [
      { rank: 1, unique_code: 'U004', full_name: 'طالب التواجد', value: 160 },
    ],
    total: 1,
    total_pages: 1,
  },
  union_all: {
    metric: 'union_all',
    items: [
      { rank: 1, unique_code: 'U005', full_name: 'طالب الأركان', value: 1 },
    ],
    total: 1,
    total_pages: 1,
  },
};

function mockEndpoints() {
  apiGet.mockImplementation((path) => {
    if (path.startsWith('/admin/dashboard/top-students')) {
      const match = Object.keys(METRIC_PAGES).find((k) => path.includes(`metric=${k}`));
      return Promise.resolve(METRIC_PAGES[match] || METRIC_PAGES.lectures);
    }
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

function renderPage(initialPath = '/dashboard-top-students') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <TopStudentsPage />
    </MemoryRouter>
  );
}

describe('TopStudentsPage', () => {
  beforeEach(() => {
    localStorage.clear();
    mockEndpoints();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('renders the table columns and the default lectures metric values', async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText('طالب الأول')).toBeInTheDocument());
    expect(screen.getByRole('columnheader', { name: '#' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'الاسم' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'الرمز' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'القيمة' })).toBeInTheDocument();
    expect(screen.getByText('8 محاضرة')).toBeInTheDocument();
    expect(screen.getByText('الإجمالي: 12')).toBeInTheDocument();
  });

  it('switches metric, updates the URL and refetches with the new metric', async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText('طالب الأول')).toBeInTheDocument());

    apiGet.mockClear();
    fireEvent.click(screen.getByRole('tab', { name: 'أكثر جولات كليات' }));

    await waitFor(() => {
      const calls = apiGet.mock.calls.map((c) => c[0]);
      expect(
        calls.some((p) => p === '/admin/dashboard/top-students?metric=tours&page=1&limit=20')
      ).toBe(true);
    });

    await waitFor(() => expect(screen.getByText('12 جولة')).toBeInTheDocument());
  });

  it('formats presence values as hours and minutes', async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText('طالب الأول')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('tab', { name: 'أطول تواجد بالجامعة' }));

    await waitFor(() => expect(screen.getByText('2س 40د')).toBeInTheDocument());
  });

  it('renders the union_all value as the three-station label', async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText('طالب الأول')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('tab', { name: 'زاروا كل أركان الاتحاد' }));

    await waitFor(() => expect(screen.getByText('الأركان الثلاثة')).toBeInTheDocument());
  });
});