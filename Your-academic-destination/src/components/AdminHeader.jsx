import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import logo from '../assets/whited-logo-1.png';
import { clearAuthToken } from '../api/api';
import { ROLE_LABELS } from '../api/roles';
import '../style/AdminHeader.css';

const AdminHeader = ({ userRole, smsStatus }) => {
  const navigate = useNavigate();

  // إذا ما مررنا الدور كـ prop، منقرأه من localStorage ونعرض الترجمة العربية
  const effectiveRole =
    userRole || ROLE_LABELS[localStorage.getItem('accountRole')] || 'المدير العام';

  const handleLogout = () => {
    clearAuthToken();
    localStorage.removeItem('accountUsername');
    localStorage.removeItem('accountRole');
    localStorage.removeItem('accountCollege');
    navigate('/team-log');
  };

  // حالة المُرسِل النصي (اختيارية — تمررها لوحة التحكم فقط). النقطة الخضراء/
  // الحمراء تبقى حتى بأصغر المقاسات، والنص التفصيلي يختفي تحت 600px.
  const smsOnline = smsStatus ? Boolean(smsStatus.worker_online) : null;

  return (
    <header className="admin-header">
      <Link to="/dashboard" className="admin-header-brand">
        <img src={logo} alt="شعار" className="admin-logo" />
        <div className="admin-brand-text">
          <span className="admin-brand-title">وجهتك الأكاديمية 2</span>
          <span className="admin-brand-subtitle">لوحة التحكم</span>
        </div>
      </Link>

      <nav className="admin-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `admin-nav-link ${isActive ? 'active' : ''}`}
        >
          الرئيسية
        </NavLink>
        <NavLink
          to="/team-accounts"
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
        {smsStatus && (
          <span className={`admin-sms-pill ${smsOnline ? 'admin-sms-online' : 'admin-sms-offline'}`}>
            <span className="admin-sms-dot"></span>
            <span className="admin-sms-state">{smsOnline ? 'متصل' : 'منقطع'}</span>
            <span className="admin-sms-detail">
              · {smsStatus.counts?.pending ?? 0} بالانتظار · {smsStatus.counts?.failed ?? 0} فاشلة
            </span>
          </span>
        )}
        <span className="admin-user-badge">{effectiveRole}</span>
        <button type="button" className="admin-logout-btn" onClick={handleLogout}>
          تسجيل خروج
        </button>
      </div>
    </header>
  );
};

export default AdminHeader;