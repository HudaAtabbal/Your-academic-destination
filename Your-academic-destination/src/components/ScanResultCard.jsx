import React from 'react';

/**
 * كرت النتيجة بعد المسح — أخضر فاتح للنجاح، أحمر فاتح للتحذير/التكرار.
 */
const ScanResultCard = ({ status, title, studentName, studentCode }) => {
  if (!status) return null;

  const isError = status === 'error';

  return (
    <div className={`ss-result-card ${isError ? 'ss-result-error' : 'ss-result-success'}`}>
      <div className="ss-result-text">
        <h3 className="ss-result-title">{title}</h3>
        <p className="ss-result-subtitle">
          {studentName} <span className="ss-result-dot">·</span> {studentCode}
        </p>
      </div>
      <div className="ss-result-icon">{isError ? '!' : '✓'}</div>
    </div>
  );
};

export default ScanResultCard;