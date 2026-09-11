import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import StudentPrivateRoute from './StudentPrivateRoute';

function renderRoute() {
  return render(
    <MemoryRouter initialEntries={['/my-card']}>
      <Routes>
        <Route path="/" element={<div>HOME_PAGE</div>} />
        <Route
          path="/my-card"
          element={
            <StudentPrivateRoute>
              <div>PROTECTED_CONTENT</div>
            </StudentPrivateRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe('StudentPrivateRoute', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('redirects to home when no studentCode is stored', () => {
    renderRoute();

    expect(screen.getByText('HOME_PAGE')).toBeInTheDocument();
    expect(screen.queryByText('PROTECTED_CONTENT')).not.toBeInTheDocument();
  });

  it('redirects to home when studentCode is empty', () => {
    localStorage.setItem('studentCode', '');
    renderRoute();

    expect(screen.getByText('HOME_PAGE')).toBeInTheDocument();
    expect(screen.queryByText('PROTECTED_CONTENT')).not.toBeInTheDocument();
  });

  it('renders the protected children when studentCode exists', () => {
    localStorage.setItem('studentCode', 'R-123456');
    renderRoute();

    expect(screen.getByText('PROTECTED_CONTENT')).toBeInTheDocument();
    expect(screen.queryByText('HOME_PAGE')).not.toBeInTheDocument();
  });
});