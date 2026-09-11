import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { setAuthToken } from '../api/api';
import TeamPrivateRoute from './TeamPrivateRoute';

function renderRoute({ allowedRoles }) {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/team-log" element={<div>TEAM_LOGIN</div>} />
        <Route
          path="/dashboard"
          element={
            <TeamPrivateRoute allowedRoles={allowedRoles}>
              <div>DASHBOARD_CONTENT</div>
            </TeamPrivateRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe('TeamPrivateRoute', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it('redirects to team login when no token is stored', () => {
    renderRoute({});

    expect(screen.getByText('TEAM_LOGIN')).toBeInTheDocument();
    expect(screen.queryByText('DASHBOARD_CONTENT')).not.toBeInTheDocument();
  });

  it('renders children with a token and no allowedRoles restriction', () => {
    setAuthToken('valid-token');
    renderRoute({});

    expect(screen.getByText('DASHBOARD_CONTENT')).toBeInTheDocument();
    expect(screen.queryByText('TEAM_LOGIN')).not.toBeInTheDocument();
  });

  it('renders children when the stored role is in allowedRoles', () => {
    setAuthToken('valid-token');
    localStorage.setItem('accountRole', 'super_admin');
    renderRoute({ allowedRoles: ['super_admin', 'students_admin'] });

    expect(screen.getByText('DASHBOARD_CONTENT')).toBeInTheDocument();
  });

  it('redirects to team login when the stored role is not allowed', () => {
    setAuthToken('valid-token');
    localStorage.setItem('accountRole', 'gate_scanner');
    renderRoute({ allowedRoles: ['super_admin'] });

    expect(screen.getByText('TEAM_LOGIN')).toBeInTheDocument();
    expect(screen.queryByText('DASHBOARD_CONTENT')).not.toBeInTheDocument();
  });

  it('renders children regardless of role when allowedRoles is empty', () => {
    setAuthToken('valid-token');
    localStorage.setItem('accountRole', 'gate_scanner');
    renderRoute({ allowedRoles: [] });

    expect(screen.getByText('DASHBOARD_CONTENT')).toBeInTheDocument();
  });
});