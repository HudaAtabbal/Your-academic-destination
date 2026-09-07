// StaffScanHeader.jsx
const StaffScanHeader = ({ title, username, role, location }) => {
  return (
    <header className="staff-scan-header">
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