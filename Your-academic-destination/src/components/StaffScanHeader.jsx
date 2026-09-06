import React from 'react';

/**
 * هيدر موحّد لكل شاشات المسح (استشارة، جولة، توجيه، مدرج).
 * الفرق عن HeaderStep: ما فيه زر رجوع، وفيه سطر معلومات
 * (username • الدور • الموقع) بدل نص فرعي بسيط.
 */
const StaffScanHeader = ({ title, username, role, location }) => {
  return (
    <header className="ss-header">
      <h1 className="ss-title">{title}</h1>
      <div className="ss-meta">
        <span>{username}</span>
        <span className="ss-meta-dot">•</span>
        <span>{role}</span>
        <span className="ss-meta-dot">•</span>
        <span>{location}</span>
      </div>
    </header>
  );
};

export default StaffScanHeader;