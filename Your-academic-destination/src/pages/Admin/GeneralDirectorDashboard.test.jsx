import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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
  campus_entries_count: 2,
  activities_today_cumulative: 3,
  survey_completed_count: 4,
};

function mockEndpoints(smsStatus) {
  apiGet.mockImplementation((path) => {
    if (path.startsWith('/admin/accounts')) return Promise.resolve({ items: [] });
    if (path === '/admin/dashboard/stats') return Promise.resolve(STATS);
    if (path === '/admin/dashboard/rooms-occupancy') return Promise.resolve({ rooms: [] });
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
