import React from 'react';

/**
 * كرت النتيجة بعد المسح — أخضر فاتح للنجاح، أحمر فاتح للتحذير/التكرار.
 */
const ScanResultCard = ({ status, title, studentName, studentCode }) => {
  if (!status) return null;

  const isError = status === 'error';

  return (
    <div className={`scan-result-card ${isError ? 'scan-result-error' : 'scan-result-success'}`}>
      <div className="scan-result-text">
        <h3 className="scan-result-title">{title}</h3>
        <p className="scan-result-subtitle">
          {studentName} <span className="scan-result-dot">·</span> {studentCode}
        </p>
      </div>
      <div className="scan-result-icon">{isError ? '!' : '✓'}</div>
    </div>
  );
};

export default ScanResultCard;