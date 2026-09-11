import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { apiPost, ApiError } from '../../api/api';
import FindCardPage from './FindCardPage';

vi.mock('../../api/api.js', () => ({
  ApiError: class ApiError extends Error {
    constructor(errorCode, message, details) {
      super(message);
      this.name = 'ApiError';
      this.errorCode = errorCode;
      this.details = details;
    }
  },
  apiPost: vi.fn(),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/find-card']}>
      <Routes>
        <Route path="/find-card" element={<FindCardPage />} />
        <Route path="/my-card" element={<div>MYCARD_OK</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('FindCardPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('requires both name and phone to be filled', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'استرجاع البطاقة' }));

    expect(screen.getByText('يرجى تعبئة الاسم الثلاثي ورقم الهاتف')).toBeInTheDocument();
    expect(apiPost).not.toHaveBeenCalled();
  });

  it('rejects a phone number that is not 09 followed by 8 digits', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText('الاسم الثلاثي'), 'خالد طليمات');
    await user.type(screen.getByLabelText('رقم الهاتف'), '09123');
    await user.click(screen.getByRole('button', { name: 'استرجاع البطاقة' }));

    expect(screen.getByText(/يرجى إدخال رقم الهاتف صحيح/)).toBeInTheDocument();
    expect(apiPost).not.toHaveBeenCalled();
  });

  it('submits the lookup with whatsapp platform, phone and name', async () => {
    apiPost.mockResolvedValue({
      unique_code: 'R-123456',
      full_name: 'خالد طليمات',
    });
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText('الاسم الثلاثي'), '   خالد طليمات   ');
    await user.type(screen.getByLabelText('رقم الهاتف'), '0912345678');
    await user.click(screen.getByRole('button', { name: 'استرجاع البطاقة' }));

    expect(apiPost).toHaveBeenCalledWith('/students/lookup-by-contact', {
      contact_platform: 'whatsapp',
      contact_id: '0912345678',
      full_name: 'خالد طليمات',
    });

    await waitFor(() => expect(screen.getByText('MYCARD_OK')).toBeInTheDocument());
    expect(localStorage.getItem('studentCode')).toBe('R-123456');
    expect(localStorage.getItem('studentName')).toBe('خالد طليمات');
  });

  it('shows the backend error message when the lookup fails with ApiError', async () => {
    apiPost.mockRejectedValue(
      new ApiError('not_found', 'ما لقينا حساب مرتبط بهالرقم', null)
    );
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText('الاسم الثلاثي'), 'خالد طليمات');
    await user.type(screen.getByLabelText('رقم الهاتف'), '0912345678');
    await user.click(screen.getByRole('button', { name: 'استرجاع البطاقة' }));

    expect(await screen.findByText('ما لقينا حساب مرتبط بهالرقم')).toBeInTheDocument();
    expect(localStorage.getItem('studentCode')).toBeNull();
  });

  it('shows a fallback message on non-ApiError failures', async () => {
    apiPost.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText('الاسم الثلاثي'), 'خالد طليمات');
    await user.type(screen.getByLabelText('رقم الهاتف'), '0912345678');
    await user.click(screen.getByRole('button', { name: 'استرجاع البطاقة' }));

    expect(await screen.findByText('ما لقينا حساب مرتبط بهالرقم، تأكدي منه وحاولي مرة تانية')).toBeInTheDocument();
  });
});