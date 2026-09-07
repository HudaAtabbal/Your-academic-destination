import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import logo from '../assets/English logo white-01.png';
import { clearAuthToken } from '../api/api';
import '../style/AdminHeader.css';

const AdminHeader = ({ userRole = 'المدير العام' }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuthToken();
    localStorage.removeItem('accountUsername');
    localStorage.removeItem('accountRole');
    localStorage.removeItem('accountCollege');
    navigate('/team-log');
  };

  return (
    <header className="admin-header">
      <div className="admin-header-brand">
        <img src={logo} alt="شعار" className="admin-logo" />
        <div className="admin-brand-text">
          <span className="admin-brand-title">وجهتك الأكاديمية 2</span>
          <span className="admin-brand-subtitle">لوحة التحكم</span>
        </div>
      </div>

      <nav className="admin-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          الرئيسية
        </NavLink>
        <NavLink
          to="/create-team-account"
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          حسابات الفريق
        </NavLink>
        <NavLink
          to="/generate-walkin-code"
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          رموز Walk-in
        </NavLink>
      </nav>

      <div className="admin-header-user">
        <span className="admin-user-badge">{userRole}</span>
        <button type="button" className="admin-logout-btn" onClick={handleLogout}>
          تسجيل خروج
        </button>
      </div>
    </header>
  );
};

export default AdminHeader;