import React from 'react';

/**
 * صندوق المسح — بديل الكاميرا الفعلية لحد ما تتوصل مكتبة سكانر حقيقية.
 * بالمرحلة الحالية: الضغط عليه بيحاكي عملية مسح رمز QR (mock).
 */
const ScanBox = ({ caption = 'وجّه الكاميرا نحو رمز QR تبع الطالب', onScan }) => {
  return (
    <div className="ss-scanbox-wrapper">
      <button type="button" className="ss-scanbox" onClick={onScan} aria-label="مسح رمز QR">
        <span className="ss-scanbox-frame" />
      </button>
      <p className="ss-scan-caption">{caption}</p>
    </div>
  );
};

export default ScanBox;