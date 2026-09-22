import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { apiGet, ApiError } from '../../api/api';
import MyPointsPage from './MyPointsPage';

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
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/my-points']}>
      <MyPointsPage active={true} />
    </MemoryRouter>
  );
}

describe('MyPointsPage', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('studentCode', 'R-999999');
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('shows total points from the backend', async () => {
    apiGet.mockResolvedValue({
      total_points: 35,
      today_lecture_count: 1,
      lectures_capped_today: false,
      today_tour_count: 1,
      tours_capped_today: false,
    });

    renderPage();

    expect(await screen.findByText('35')).toBeInTheDocument();
  });

  it('shows the personal lecture-cap note when lectures_capped_today is true', async () => {
    apiGet.mockResolvedValue({
      total_points: 30,
      today_lecture_count: 3,
      lectures_capped_today: true,
      today_tour_count: 0,
      tours_capped_today: false,
    });

    renderPage();

    expect(
      await screen.findByText(/لقد بلغت الحد الأقصى للمحاضرات اليوم/)
    ).toBeInTheDocument();
  });

  it('shows the personal tour-cap note when tours_capped_today is true', async () => {
    apiGet.mockResolvedValue({
      total_points: 30,
      today_lecture_count: 0,
      lectures_capped_today: false,
      today_tour_count: 3,
      tours_capped_today: true,
    });

    renderPage();

    expect(
      await screen.findByText(/لقد بلغت الحد الأقصى للجولات اليوم/)
    ).toBeInTheDocument();
  });

  it('does not show any cap note when no cap is reached', async () => {
    apiGet.mockResolvedValue({
      total_points: 20,
      today_lecture_count: 2,
      lectures_capped_today: false,
      today_tour_count: 2,
      tours_capped_today: false,
    });

    renderPage();

    await waitFor(() => expect(screen.getByText('20')).toBeInTheDocument());
    expect(screen.queryByText(/لن تُحتسب نقاط إضافية/)).not.toBeInTheDocument();
  });

  it('shows the backend error message when fetching points fails', async () => {
    apiGet.mockRejectedValue(
      new ApiError('account_not_found', 'ما لقينا الحساب')
    );

    renderPage();

    expect(await screen.findByText('ما لقينا الحساب')).toBeInTheDocument();
  });
});