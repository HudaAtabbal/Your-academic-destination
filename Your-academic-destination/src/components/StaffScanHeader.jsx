import React from 'react';
import { useNavigate } from 'react-router-dom';
import { clearAuthToken } from '../api/api';

/**
 * هيدر موحّد لكل شاشات المسح (استشارة، جولة، توجيه، مدرج).
 * الفرق عن HeaderStep: ما فيه زر رجوع، وفيه سطر معلومات
 * (username • الدور • الموقع) بدل نص فرعي بسيط.
 */
const StaffScanHeader = ({ title, username, role, location }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuthToken();
    localStorage.removeItem('accountUsername');
    localStorage.removeItem('accountRole');
    localStorage.removeItem('accountCollege');
    navigate('/team-log');
  };

  return (
    <header className="staff-scan-header">
      <button type="button" className="staff-scan-logout-btn" onClick={handleLogout}>
        تسجيل خروج
      </button>
      <h1 className="staff-scan-title">{title}</h1>
      <div className="staff-scan-meta">
        <span>{username}</span>
        <span className="staff-scan-dot">•</span>
        <span>{role}</span>
        <span className="staff-scan-dot">•</span>
        <span>{location}</span>
      </div>
    </header>
  );
};

export default StaffScanHeader;