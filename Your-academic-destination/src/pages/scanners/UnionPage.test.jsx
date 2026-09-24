import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { apiGet, apiPost, ApiError } from '../../api/api';
import UnionPage from './UnionPage';

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
  apiPost: vi.fn(),
}));

// الكاميرا مش قابلة للاختبار في jsdom — نستبدلها بمكوّن وهمي يسلّم كأنه الثبوت
vi.mock('../../components/ScanBox', () => ({
  default: ({ paused, onResume }) => (
    <div>
      <span>mock-camera</span>
      {paused && (
        <button type="button" onClick={onResume}>
          ▶ تشغيل الكاميرا
        </button>
      )}
    </div>
  ),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <UnionPage />
    </MemoryRouter>
  );
}

describe('UnionPage', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('accountUsername', 'sara_union');
    localStorage.setItem('accountRole', 'union');
    apiGet.mockResolvedValue({ count: 3 });
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('shows the three union sections to pick from', () => {
    renderPage();

    expect(screen.getByText('اختر قسم ركن الاتحاد')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'الركن المركزي' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'دليل التخصص' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'نادي التركي' })).toBeInTheDocument();
    // لسا ما اختار قسم — ما فيه إدخال يدوي ولا عداد
    expect(screen.queryByPlaceholderText(/بديل يدوي/)).not.toBeInTheDocument();
    expect(apiGet).not.toHaveBeenCalled();
  });

  it('shows the scan UI only after picking a section and loads its count', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'الركن المركزي' }));

    expect(await screen.findByPlaceholderText(/بديل يدوي/)).toBeInTheDocument();
    expect(apiGet).toHaveBeenCalledWith(
      '/checkins/count/today?activity_type=union&union_section=central'
    );
    const footer = screen.getByText(/مسحة مرفوعة/).closest('footer');
    expect(footer).toHaveTextContent('3');
  });

  it('posts a scan with the selected section and shows the result', async () => {
    apiPost.mockResolvedValue({ student_name: 'فاطمة رستم', checked_in_at: '2026-09-24T10:00:00' });
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'دليل التخصص' }));
    const input = await screen.findByPlaceholderText(/بديل يدوي/);
    await user.type(input, 'R-024865');
    await user.click(screen.getByRole('button', { name: 'تحقق' }));

    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/checkins/union', {
        unique_code: 'R-024865',
        union_section: 'major_guide',
      })
    );
    expect(await screen.findByText('ركن الاتحاد — دليل التخصص')).toBeInTheDocument();
    expect(screen.getByText(/فاطمة رستم/)).toBeInTheDocument();
  });

  it('shows the backend error message on a duplicate scan', async () => {
    apiPost.mockRejectedValue(
      new ApiError('duplicate_checkin', 'الطالب فاطمة رستم سجّل الاتحاد (نادي التركي) مسبقاً الساعة 09:30', null)
    );
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'نادي التركي' }));
    const input = await screen.findByPlaceholderText(/بديل يدوي/);
    await user.type(input, 'W-111111');
    await user.click(screen.getByRole('button', { name: 'تحقق' }));

    expect(await screen.findByText(/سجّل الاتحاد/)).toBeInTheDocument();
  });
});