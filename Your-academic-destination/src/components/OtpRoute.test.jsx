import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import OtpRoute from './OtpRoute';

function renderRoute() {
  return render(
    <MemoryRouter initialEntries={['/otp']}>
      <Routes>
        <Route path="/register-step1" element={<div>REGISTER_PAGE</div>} />
        <Route path="/my-card" element={<div>CARD_PAGE</div>} />
        <Route
          path="/otp"
          element={
            <OtpRoute>
              <div>OTP_CONTENT</div>
            </OtpRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe('OtpRoute', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('redirects to register-step1 when opened directly with no state', () => {
    renderRoute();

    expect(screen.getByText('REGISTER_PAGE')).toBeInTheDocument();
    expect(screen.queryByText('OTP_CONTENT')).not.toBeInTheDocument();
  });

  it('allows access when a pendingStudentCode exists', () => {
    localStorage.setItem('pendingStudentCode', 'P-123456');
    renderRoute();

    expect(screen.getByText('OTP_CONTENT')).toBeInTheDocument();
  });

  it('redirects verified students to their card', () => {
    localStorage.setItem('studentCode', 'R-123456');
    localStorage.setItem('studentName', 'طالب');
    renderRoute();

    expect(screen.getByText('CARD_PAGE')).toBeInTheDocument();
    expect(screen.queryByText('OTP_CONTENT')).not.toBeInTheDocument();
  });

  it('does not allow access with only studentCode (not verified)', () => {
    localStorage.setItem('studentCode', 'R-123456');
    renderRoute();

    expect(screen.getByText('REGISTER_PAGE')).toBeInTheDocument();
    expect(screen.queryByText('OTP_CONTENT')).not.toBeInTheDocument();
  });
});
