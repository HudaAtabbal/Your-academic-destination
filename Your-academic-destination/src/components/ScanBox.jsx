import React from 'react';

/**
 * صندوق المسح — بديل الكاميرا الفعلية لحد ما تتوصل مكتبة سكانر حقيقية.
 * بالمرحلة الحالية: الضغط عليه بيحاكي عملية مسح رمز QR (mock).
 */
const ScanBox = ({ caption = 'وجّه الكاميرا نحو رمز QR تبع الطالب', onScan }) => {
  return (
    <div className="scan-box-wrapper">
      <button type="button" className="scan-box" onClick={onScan} aria-label="مسح رمز QR">
        <span className="scan-box-frame" />
      </button>
      <p className="scan-caption">{caption}</p>
    </div>
  );
};

export default ScanBox;