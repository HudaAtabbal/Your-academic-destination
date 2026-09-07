import React from 'react';

const InfoCard = ({ title, text }) => {
  return (
    <div className="info-box" dir='rtl'>
      <h3 className="info-title">{title}</h3>
      <p className="info-text">
  التسجيل شرط الدخول. بتاخد بطاقة برمز <bdi>QR</bdi> خاص فيك، وبتربطك بكل نشاط تحضره.
</p>
    </div>
  );
};

export default InfoCard;